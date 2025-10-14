import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_DIR = DATA_DIR / "database"
UPLOADS_DIR = DATA_DIR / "uploads"
LOGS_DIR = DATA_DIR / "logs"

# 确保目录存在
DATABASE_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

SECRET_KEY = os.getenv('SECRET_KEY', 'your_secret_key')
DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{DATABASE_DIR}/chat8.db')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 60