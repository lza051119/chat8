from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# 使用 aiosqlite 驱动的异步 DSN
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./Server.db"

# 创建异步引擎
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    future=True
)

# 创建异步会话工厂
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine, 
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

async def get_db() -> AsyncSession:
    """
    异步的数据库会话依赖。
    """
    async with SessionLocal() as session:
        yield session