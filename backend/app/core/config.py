import os

SECRET_KEY = os.getenv('SECRET_KEY', 'your_secret_key')
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./chat8.db')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 60 