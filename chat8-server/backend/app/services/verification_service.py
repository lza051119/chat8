import random
import string
from datetime import datetime, timedelta
from typing import Optional, Dict
import asyncio

class VerificationCodeService:
    """验证码服务"""
    
    # 内存存储验证码（生产环境建议使用Redis）
    _codes: Dict[str, Dict] = {}
    
    @classmethod
    def generate_code(cls, length: int = 6) -> str:
        """生成随机验证码"""
        return ''.join(random.choices(string.digits, k=length))
    
    @classmethod
    def store_code(cls, email: str, code: str, expire_minutes: int = 10) -> None:
        """存储验证码"""
        expire_time = datetime.now() + timedelta(minutes=expire_minutes)
        cls._codes[email] = {
            'code': code,
            'expire_time': expire_time,
            'attempts': 0
        }
        
        # 异步清理过期验证码
        asyncio.create_task(cls._cleanup_expired_code(email, expire_minutes * 60))
    
    @classmethod
    def verify_code(cls, email: str, code: str, max_attempts: int = 3) -> bool:
        """验证验证码"""
        if email not in cls._codes:
            return False
        
        code_info = cls._codes[email]
        
        # 检查是否过期
        if datetime.now() > code_info['expire_time']:
            del cls._codes[email]
            return False
        
        # 检查尝试次数
        if code_info['attempts'] >= max_attempts:
            del cls._codes[email]
            return False
        
        # 验证码错误，增加尝试次数
        if code_info['code'] != code:
            code_info['attempts'] += 1
            return False
        
        # 验证成功，删除验证码
        del cls._codes[email]
        return True
    
    @classmethod
    def verify_code_without_delete(cls, email: str, code: str, max_attempts: int = 3) -> bool:
        """验证验证码但不删除（用于重置密码流程）"""
        if email not in cls._codes:
            return False
        
        code_info = cls._codes[email]
        
        # 检查是否过期
        if datetime.now() > code_info['expire_time']:
            del cls._codes[email]
            return False
        
        # 检查尝试次数
        if code_info['attempts'] >= max_attempts:
            del cls._codes[email]
            return False
        
        # 验证码错误，但不增加尝试次数（因为这是只读验证）
        if code_info['code'] != code:
            return False
        
        # 验证成功，但不删除验证码
        return True
    
    @classmethod
    def has_valid_code(cls, email: str) -> bool:
        """检查是否有有效的验证码"""
        if email not in cls._codes:
            return False
        
        code_info = cls._codes[email]
        if datetime.now() > code_info['expire_time']:
            del cls._codes[email]
            return False
        
        return True
    
    @classmethod
    async def _cleanup_expired_code(cls, email: str, delay_seconds: int):
        """异步清理过期验证码"""
        await asyncio.sleep(delay_seconds)
        if email in cls._codes:
            code_info = cls._codes[email]
            if datetime.now() > code_info['expire_time']:
                del cls._codes[email]
    
    @classmethod
    def get_remaining_time(cls, email: str) -> Optional[int]:
        """获取验证码剩余时间（秒）"""
        if email not in cls._codes:
            return None
        
        code_info = cls._codes[email]
        remaining = (code_info['expire_time'] - datetime.now()).total_seconds()
        return max(0, int(remaining))
    
    @classmethod
    def clear_code(cls, email: str) -> bool:
        """清除指定邮箱的验证码"""
        if email in cls._codes:
            del cls._codes[email]
            return True
        return False
    
    @classmethod
    def clear_all_codes(cls) -> None:
        """清除所有验证码（用于调试）"""
        cls._codes.clear()