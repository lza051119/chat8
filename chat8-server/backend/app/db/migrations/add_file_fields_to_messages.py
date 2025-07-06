from sqlalchemy import text
from app.db.database import engine

def upgrade():
    """添加文件相关字段到messages表"""
    with engine.connect() as connection:
        # 添加file_path字段
        connection.execute(text("""
            ALTER TABLE messages 
            ADD COLUMN file_path VARCHAR(512)
        """))
        
        # 添加file_name字段
        connection.execute(text("""
            ALTER TABLE messages 
            ADD COLUMN file_name VARCHAR(256)
        """))
        
        connection.commit()
        print("Successfully added file_path and file_name columns to messages table")

def downgrade():
    """移除文件相关字段"""
    with engine.connect() as connection:
        # 移除file_name字段
        connection.execute(text("""
            ALTER TABLE messages 
            DROP COLUMN file_name
        """))
        
        # 移除file_path字段
        connection.execute(text("""
            ALTER TABLE messages 
            DROP COLUMN file_path
        """))
        
        connection.commit()
        print("Successfully removed file_path and file_name columns from messages table")

if __name__ == "__main__":
    upgrade()