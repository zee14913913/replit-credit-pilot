"""
数据库连接模块
使用PostgreSQL + SQLAlchemy
"""
import os
from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator

# 从环境变量读取数据库URL
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL 环境变量未设置！请检查 .env 文件或 Replit Secrets")

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # 自动重连
    pool_size=10,
    max_overflow=20,
    echo=False  # 生产环境关闭SQL日志
)

# 创建SessionLocal类
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建Base类
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI依赖注入：获取数据库session
    用法: def my_route(db: Session = Depends(get_db))
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_database():
    """
    初始化数据库：创建所有表
    在main.py启动时调用
    """
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表初始化完成")


def execute_sql_file(sql_file_path: str):
    """
    执行SQL文件（用于初始化会计科目等）
    """
    with open(sql_file_path, 'r', encoding='utf-8') as f:
        sql_script = f.read()
    
    with engine.connect() as conn:
        # 分割SQL语句并执行
        for statement in sql_script.split(';'):
            statement = statement.strip()
            if statement and not statement.startswith('--') and not statement.startswith('COMMENT'):
                try:
                    conn.execute(text(statement))
                    conn.commit()
                except Exception as e:
                    print(f"警告：SQL执行失败: {str(e)[:100]}")
                    continue
    
    print("✅ SQL文件执行完成")
