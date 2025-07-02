from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
import os
import tempfile
from services.steganography import embed, extract

router = APIRouter()

@router.post("/embed")
async def embed_message(
    image: UploadFile = File(...),
    secret_message: str = Form(...),
    password: str = Form(...)
):
    """
    在图像中嵌入秘密信息
    
    Args:
        image: 上传的图像文件
        secret_message: 要隐藏的秘密信息
        password: 用于加密的密码
    
    Returns:
        包含隐藏信息的图像文件
    """
    # 验证文件类型
    if not image.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="上传的文件必须是图像格式")
    
    try:
        # 创建临时文件来保存上传的图像
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_input:
            content = await image.read()
            temp_input.write(content)
            temp_input_path = temp_input.name
        
        # 创建输出文件路径
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_output:
            temp_output_path = temp_output.name
        
        # 执行嵌入操作
        embed(temp_input_path, secret_message, password, temp_output_path)
        
        # 清理输入临时文件
        os.unlink(temp_input_path)
        
        # 返回包含隐藏信息的图像
        return FileResponse(
            temp_output_path,
            media_type="image/png",
            filename=f"steganography_{image.filename}",
            background=lambda: os.unlink(temp_output_path)  # 在响应发送后删除临时文件
        )
        
    except Exception as e:
        # 清理临时文件
        if 'temp_input_path' in locals() and os.path.exists(temp_input_path):
            os.unlink(temp_input_path)
        if 'temp_output_path' in locals() and os.path.exists(temp_output_path):
            os.unlink(temp_output_path)
        
        raise HTTPException(status_code=500, detail=f"嵌入操作失败: {str(e)}")

@router.post("/extract")
async def extract_message(
    image: UploadFile = File(...),
    password: str = Form(...)
):
    """
    从图像中提取隐藏的信息
    
    Args:
        image: 包含隐藏信息的图像文件
        password: 用于解密的密码
    
    Returns:
        提取出的秘密信息
    """
    # 验证文件类型
    if not image.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="上传的文件必须是图像格式")
    
    try:
        # 创建临时文件来保存上传的图像
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
            content = await image.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # 执行提取操作
        secret_message = extract(temp_file_path, password)
        
        # 清理临时文件
        os.unlink(temp_file_path)
        
        if secret_message is None:
            raise HTTPException(status_code=400, detail="提取失败，可能是密码错误或图像中没有隐藏信息")
        
        return {"secret_message": secret_message}
        
    except HTTPException:
        raise
    except Exception as e:
        # 清理临时文件
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        
        raise HTTPException(status_code=500, detail=f"提取操作失败: {str(e)}")

@router.get("/test")
async def test_steganography():
    """
    测试隐写术功能是否正常工作
    """
    return {"message": "隐写术API正常工作"}