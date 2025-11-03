"""
数据库迁移脚本
添加新表和字段以支持系统升级
"""
from sqlalchemy import text
from accounting_app.db import engine


def run_migration():
    """
    执行数据库迁移
    """
    with engine.begin() as conn:
        # 1. 为 exceptions 表添加新字段
        try:
            conn.execute(text("""
                ALTER TABLE exceptions 
                ADD COLUMN IF NOT EXISTS next_action VARCHAR(50),
                ADD COLUMN IF NOT EXISTS retryable BOOLEAN DEFAULT FALSE,
                ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0,
                ADD COLUMN IF NOT EXISTS last_retry_at TIMESTAMP WITH TIME ZONE;
            """))
            print("✅ exceptions 表字段添加成功")
        except Exception as e:
            print(f"⚠️ exceptions 表迁移警告: {str(e)[:200]}")
        
        # 2. 修改 auto_posting_rules 表的 company_id 允许 NULL
        try:
            conn.execute(text("""
                ALTER TABLE auto_posting_rules 
                ALTER COLUMN company_id DROP NOT NULL;
            """))
            print("✅ auto_posting_rules.company_id 已允许 NULL（支持全局规则）")
        except Exception as e:
            print(f"⚠️ auto_posting_rules 迁移警告: {str(e)[:200]}")
        
        # 3. 创建索引
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_exceptions_retryable 
                ON exceptions(retryable) WHERE retryable = TRUE;
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_exceptions_next_action 
                ON exceptions(next_action) WHERE next_action IS NOT NULL;
            """))
            print("✅ 异常中心索引创建成功")
        except Exception as e:
            print(f"⚠️ 索引创建警告: {str(e)[:200]}")


if __name__ == "__main__":
    print("🔄 开始数据库迁移...")
    run_migration()
    print("✅ 数据库迁移完成")
