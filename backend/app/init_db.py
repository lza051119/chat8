import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import engine
from app.db.models import Base

Base.metadata.create_all(bind=engine)
print("数据库表已创建")