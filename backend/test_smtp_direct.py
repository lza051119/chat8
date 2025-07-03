#!/usr/bin/env python3
"""
直接测试SMTP连接
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_smtp_connection():
    # 邮件配置
    smtp_server = "smtp.qq.com"
    port = 465  # SSL端口
    sender_email = os.getenv("MAIL_USERNAME", "future_234@qq.com")
    password = os.getenv("MAIL_PASSWORD", "jdohplssrqzkceag")
    receiver_email = "petrichor_umut@163.com"
    
    print(f"测试SMTP连接...")
    print(f"服务器: {smtp_server}:{port}")
    print(f"发件人: {sender_email}")
    print(f"收件人: {receiver_email}")
    print(f"密码长度: {len(password)}")
    
    # 创建邮件内容
    message = MIMEMultipart("alternative")
    message["Subject"] = "测试邮件 - 密码重置验证码"
    message["From"] = sender_email
    message["To"] = receiver_email
    
    # 创建HTML内容
    html = """
    <html>
      <body>
        <h2>密码重置验证码</h2>
        <p>您的验证码是: <strong>123456</strong></p>
        <p>此验证码将在10分钟后过期。</p>
      </body>
    </html>
    """
    
    part = MIMEText(html, "html")
    message.attach(part)
    
    # 创建SSL上下文
    context = ssl.create_default_context()
    
    server = None
    try:
        # 连接到服务器并发送邮件
        print("正在连接到SMTP服务器...")
        server = smtplib.SMTP_SSL(smtp_server, port, context=context)
        print("连接成功，正在登录...")
        server.login(sender_email, password)
        print("登录成功，正在发送邮件...")
        text = message.as_string()
        server.sendmail(sender_email, receiver_email, text)
        print("邮件发送成功!")
        
    except Exception as e:
        print(f"发送失败: {str(e)}")
        print(f"错误类型: {type(e).__name__}")
        import traceback
        traceback.print_exc()
    finally:
        if server:
            try:
                server.quit()
            except:
                pass  # 忽略关闭连接时的错误

if __name__ == "__main__":
    test_smtp_connection()