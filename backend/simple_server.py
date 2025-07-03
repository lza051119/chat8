from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import tempfile
import os
from app.services.steganography import embed, extract

app = FastAPI(title="Chat8 隐写术服务")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Chat8 隐写术服务正在运行"}

@app.post("/api/steganography/embed")
async def embed_message(
    image: UploadFile = File(...),
    secret_message: str = Form(...),
    password: str = Form(...)
):
    """
    在图像中嵌入秘密信息
    """
    try:
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            # 保存上传的图像
            input_path = os.path.join(temp_dir, "input.png")
            with open(input_path, "wb") as f:
                content = await image.read()
                f.write(content)
            
            # 设置输出路径
            output_path = os.path.join(temp_dir, "output.png")
            
            # 执行嵌入操作
            result = embed(input_path, secret_message, password, output_path)
            
            if result is None:
                raise HTTPException(status_code=400, detail="嵌入失败，可能是图像容量不足或其他错误")
            
            # 返回嵌入后的图像
            return FileResponse(
                output_path,
                media_type="image/png",
                filename="embedded_image.png"
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理过程中发生错误: {str(e)}")

@app.post("/api/steganography/extract")
async def extract_message(
    image: UploadFile = File(...),
    password: str = Form(...)
):
    """
    从图像中提取秘密信息
    """
    try:
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            # 保存上传的图像
            input_path = os.path.join(temp_dir, "input.png")
            with open(input_path, "wb") as f:
                content = await image.read()
                f.write(content)
            
            # 执行提取操作
            extracted_message = extract(input_path, password)
            
            if extracted_message is None:
                raise HTTPException(status_code=400, detail="提取失败，可能是密码错误或图像中没有隐藏信息")
            
            return {"message": extracted_message}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理过程中发生错误: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)