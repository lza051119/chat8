from app.db.database import engine
from app.db.models import Base

Base.metadata.create_all(bind=engine)
print("数据库表已创建")