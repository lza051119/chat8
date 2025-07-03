from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr
from typing import List
import os
from pathlib import Path
import logging

# 开发模式标志
DEVELOPMENT_MODE = os.getenv("DEVELOPMENT_MODE", "true").lower() == "true"

# 邮件配置
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME", "your_email@gmail.com"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", "your_app_password"),
    MAIL_FROM=os.getenv("MAIL_FROM", "your_email@gmail.com"),
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent.parent / 'templates'
)

fastmail = FastMail(conf)

async def send_verification_email(email: EmailStr, verification_code: str, username: str):
    """发送验证码邮件"""
    
    # 开发模式下不实际发送邮件，只记录日志
    if DEVELOPMENT_MODE:
        logging.info(f"[开发模式] 模拟发送验证码邮件到 {email}，验证码: {verification_code}")
        print(f"[开发模式] 验证码邮件模拟发送成功 - 收件人: {email}, 验证码: {verification_code}")
        return
    
    html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #f8f9fa; padding: 30px; border-radius: 10px; text-align: center;">
                <h2 style="color: #333; margin-bottom: 20px;">密码重置验证码</h2>
                <p style="color: #666; font-size: 16px; margin-bottom: 20px;">亲爱的 {username}，</p>
                <p style="color: #666; font-size: 16px; margin-bottom: 30px;">您请求重置密码，请使用以下验证码：</p>
                <div style="background-color: #007bff; color: white; font-size: 24px; font-weight: bold; padding: 15px 30px; border-radius: 5px; display: inline-block; letter-spacing: 3px; margin-bottom: 30px;">
                    {verification_code}
                </div>
                <p style="color: #666; font-size: 14px; margin-bottom: 10px;">此验证码将在10分钟后过期。</p>
                <p style="color: #666; font-size: 14px;">如果您没有请求重置密码，请忽略此邮件。</p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="color: #999; font-size: 12px;">此邮件由系统自动发送，请勿回复。</p>
            </div>
        </body>
    </html>
    """
    
    try:
        message = MessageSchema(
            subject="密码重置验证码",
            recipients=[email],
            body=html,
            subtype="html"
        )
        
        await fastmail.send_message(message)
        logging.info(f"验证码邮件发送成功到 {email}")
    except Exception as e:
        logging.error(f"邮件发送失败: {str(e)}")
        raise Exception(f"邮件发送失败: {str(e)}")