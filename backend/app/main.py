from fastapi import FastAPI, WebSocket, Depends
from contextlib import asynccontextmanager
import logging
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()
from app.websocket.manager import ConnectionManager
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import friends, messages, keys, auth, signaling, avatar, security, local_storage, upload, user_status, user_profile, encryption, user_keys
from app.api import steganography
from app.websocket.events import websocket_endpoint
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from fastapi.exception_handlers import RequestValidationError
from fastapi.exceptions import HTTPException
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
from app.core.security import decode_access_token
from app.services.user_states_update import initialize_user_states_service, cleanup_user_states_service
from app.db.database import SessionLocal
from app.db.models import User
from app.core.config import UPLOADS_DIR

# 创建 ConnectionManager 单例
connection_manager = ConnectionManager()



# 定义一个依赖项，用于获取 ConnectionManager 实例
def get_connection_manager():
    return connection_manager

async def reset_all_users_offline():
    """重置所有用户状态为离线
    
    在服务器启动时调用，确保数据库中的用户状态正确
    """
    try:
        db = SessionLocal()
        # 将所有用户状态设置为离线
        online_users = db.query(User).filter(User.status == 'online').all()
        count = 0
        for user in online_users:
            user.status = 'offline'
            count += 1
        
        db.commit()
        db.close()
        
        print(f"[应用启动] 已重置 {count} 个用户状态为离线")
    except Exception as e:
        print(f"[应用启动] 重置用户状态失败: {str(e)}")
        if 'db' in locals():
            db.rollback()
            db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[应用启动] 服务已启动")
    
    # 初始化用户状态服务
    try:
        user_states_service = initialize_user_states_service(connection_manager)
        await user_states_service.start_heartbeat_monitor()
        
        # 重置所有用户状态为离线（服务器重启时）
        await reset_all_users_offline()
        
        print("[应用启动] 用户状态服务初始化成功")
    except Exception as e:
        print(f"[应用启动] 用户状态服务初始化失败: {str(e)}")
    
    yield
    
    # 清理用户状态服务
    try:
        await cleanup_user_states_service()
        print("[应用关闭] 用户状态服务清理完成")
    except Exception as e:
        print(f"[应用关闭] 用户状态服务清理失败: {str(e)}")
    
    print("[应用关闭] 服务已关闭")

app = FastAPI(lifespan=lifespan)

# 添加禁用图片API日志的中间件


# 配置CORS
origins = [
    "http://localhost:8080",  # 允许的前端源
    "http://127.0.0.1:8080",
    "http://localhost:8081",  # 新的前端端口
    "http://127.0.0.1:8081",
    "http://localhost:8082",  # 新的前端端口
    "http://127.0.0.1:8082",
    "http://localhost:8083",  # 备用前端端口
    "http://127.0.0.1:8083",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# 注册API路由
app.include_router(auth.router, prefix="/api/v1")
app.include_router(friends.router, prefix="/api/v1")
app.include_router(messages.router, prefix="/api/v1")
app.include_router(keys.router, prefix="/api/v1")
app.include_router(user_keys.router, prefix="/api/v1")
app.include_router(signaling.router, prefix="/api/v1")
app.include_router(avatar.router, prefix="/api/v1")
app.include_router(security.router, prefix="/api/v1")
app.include_router(user_status.router, prefix="/api/v1")
app.include_router(user_profile.router, prefix="/api/v1")
app.include_router(local_storage.router, prefix="/api/v1")
app.include_router(upload.router, prefix="/api/v1")
app.include_router(encryption.router, prefix="/api/v1/encryption")
app.include_router(steganography.router, prefix="/api/steganography", tags=["steganography"])

app.mount("/static", StaticFiles(directory=str(UPLOADS_DIR)), name="static")

@app.get("/api/ping")
def ping():
    return {"msg": "pong"}

@app.websocket("/ws/{user_id}")
async def websocket_route(websocket: WebSocket, user_id: int, manager: ConnectionManager = Depends(get_connection_manager)):
    # 从query参数获取token进行验证
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return
    try:
        username = decode_access_token(token)
    except Exception:
        await websocket.close(code=1008)
        return
    
    # 验证用户ID是否匹配
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username, User.id == user_id).first()
        if not user:
            await websocket.close(code=1008)
            return
    except Exception as e:
        print(f"[WebSocket] 用户验证失败: {str(e)}")
        await websocket.close(code=1008)
        return
    finally:
        db.close()
    
    await websocket_endpoint(websocket, user_id, manager)

ERROR_CODE_MAP = {
    401: "UNAUTHORIZED",
    404: "NOT_FOUND",
    422: "BAD_REQUEST",
    500: "INTERNAL_SERVER_ERROR"
}

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    code = ERROR_CODE_MAP.get(exc.status_code, str(exc.status_code))
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "error": code
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "请求参数错误",
            "error": "BAD_REQUEST",
            "details": exc.errors()
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    error_traceback = traceback.format_exc()
    print(f"[全局异常处理] 请求路径: {request.url}")
    print(f"[全局异常处理] 异常类型: {type(exc).__name__}")
    print(f"[全局异常处理] 异常信息: {str(exc)}")
    print(f"[全局异常处理] 异常堆栈:\n{error_traceback}")
    
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": f"服务器内部错误: {str(exc)}",
            "error": "INTERNAL_SERVER_ERROR"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)