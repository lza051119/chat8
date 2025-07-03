import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pydantic import EmailStr
from typing import List
import os
from pathlib import Path
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time

# 开发模式标志 - 设置为false启用真实邮件发送
DEVELOPMENT_MODE = os.getenv("DEVELOPMENT_MODE", "false").lower() == "true"

# 邮件配置
MAIL_USERNAME = os.getenv("MAIL_USERNAME", "future_234@qq.com")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "your_qq_auth_code")
MAIL_FROM = os.getenv("MAIL_FROM", "future_234@qq.com")
MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.qq.com")
MAIL_PORT = 465

def _send_email_sync(email: str, verification_code: str, username: str):
    """同步发送邮件函数"""
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
    
    # 创建邮件
    message = MIMEMultipart("alternative")
    message["Subject"] = "密码重置验证码"
    message["From"] = MAIL_FROM
    message["To"] = email
    
    # 添加HTML内容
    part = MIMEText(html, "html")
    message.attach(part)
    
    # 创建SSL上下文
    context = ssl.create_default_context()
    
    # 重试机制
    max_retries = 3
    for attempt in range(max_retries):
        server = None
        try:
            logging.info(f"第{attempt + 1}次尝试连接到SMTP服务器 {MAIL_SERVER}:{MAIL_PORT}")
            server = smtplib.SMTP_SSL(MAIL_SERVER, MAIL_PORT, context=context)
            logging.info("SMTP连接成功，正在登录...")
            server.login(MAIL_USERNAME, MAIL_PASSWORD)
            logging.info("SMTP登录成功，正在发送邮件...")
            text = message.as_string()
            server.sendmail(MAIL_FROM, email, text)
            logging.info(f"验证码邮件发送成功到 {email}")
            print(f"邮件发送成功到 {email}")
            return  # 成功发送，退出函数
        except Exception as e:
            logging.error(f"第{attempt + 1}次发送失败: {str(e)}")
            if attempt == max_retries - 1:  # 最后一次尝试
                raise e
            time.sleep(2)  # 等待2秒后重试
        finally:
            if server:
                try:
                    server.quit()
                    logging.info("SMTP连接已关闭")
                except:
                    pass  # 忽略关闭连接时的错误

async def send_verification_email(email: EmailStr, verification_code: str, username: str):
    """发送验证码邮件"""
    
    # 开发模式下不实际发送邮件，只记录日志
    if DEVELOPMENT_MODE:
        logging.info(f"[开发模式] 模拟发送验证码邮件到 {email}，验证码: {verification_code}")
        print(f"[开发模式] 验证码邮件模拟发送成功 - 收件人: {email}, 验证码: {verification_code}")
        return
    
    try:
        # 使用线程池执行同步邮件发送
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=1) as executor:
            await loop.run_in_executor(executor, _send_email_sync, email, verification_code, username)
                    
    except Exception as e:
        logging.error(f"邮件发送失败: {str(e)}")
        raise Exception(f"邮件发送失败: {str(e)}")