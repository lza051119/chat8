from fastapi import FastAPI, WebSocket, Depends
from websocket.manager import ConnectionManager
from fastapi.middleware.cors import CORSMiddleware
from api.v1.endpoints import friends, messages, keys, auth, presence, signaling, avatar, security, local_storage, upload
from api import steganography
from websocket.events import websocket_endpoint
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from fastapi.exception_handlers import RequestValidationError
from fastapi.exceptions import HTTPException
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
from core.security import decode_access_token
from services.unified_presence_service import unified_presence

app = FastAPI()

# 创建 ConnectionManager 单例
connection_manager = ConnectionManager()

# 定义一个依赖项，用于获取 ConnectionManager 实例
def get_connection_manager():
    return connection_manager

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化服务"""
    await unified_presence.start_service()

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    await unified_presence.stop_service()


# 配置CORS
origins = [
    "http://localhost:8080",  # 允许的前端源
    "http://127.0.0.1:8080",
    "http://localhost:8081",  # 新的前端端口
    "http://127.0.0.1:8081",
    "http://localhost:8082",  # 新的前端端口
    "http://127.0.0.1:8082",
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
app.include_router(auth.router, prefix="/api")
app.include_router(friends.router, prefix="/api")
app.include_router(messages.router, prefix="/api")
app.include_router(keys.router, prefix="/api")
app.include_router(signaling.router, prefix="/api")
app.include_router(avatar.router, prefix="/api")
app.include_router(security.router, prefix="/api")
app.include_router(presence.router, prefix="/api")
app.include_router(local_storage.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(steganography.router, prefix="/api/steganography", tags=["steganography"])

app.mount("/static", StaticFiles(directory="static"), name="static")

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
    from db.database import SessionLocal
    from db.models import User
    db = SessionLocal()
    user = db.query(User).filter(User.username == username, User.id == user_id).first()
    db.close()
    if not user:
        await websocket.close(code=1008)
        return
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
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "服务器内部错误",
            "error": "INTERNAL_SERVER_ERROR"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)