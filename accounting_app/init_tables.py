"""
统一数据库初始化脚本
1. 创建所有新表
2. 迁移现有表添加新字段
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from accounting_app.db import init_database, engine
from sqlalchemy import text


def migrate_existing_tables():
    """
    为现有表添加新字段
    每个操作独立执行，避免事务回滚影响其他操作
    """
    print("\n🔄 开始迁移现有表...")
    
    def execute_safely(sql, success_msg):
        """安全执行单个SQL语句"""
        try:
            with engine.begin() as conn:
                conn.execute(text(sql))
            print(f"  ✅ {success_msg}")
            return True
        except Exception as e:
            print(f"  ⚠️ {success_msg} 失败: {str(e)[:100]}")
            return False
    
    # 1. 为 exceptions 表添加新字段
    execute_safely("""
        ALTER TABLE exceptions 
        ADD COLUMN IF NOT EXISTS next_action VARCHAR(50);
    """, "next_action 字段添加")
    
    execute_safely("""
        ALTER TABLE exceptions 
        ADD COLUMN IF NOT EXISTS retryable BOOLEAN DEFAULT FALSE;
    """, "retryable 字段添加")
    
    execute_safely("""
        ALTER TABLE exceptions 
        ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0;
    """, "retry_count 字段添加")
    
    execute_safely("""
        ALTER TABLE exceptions 
        ADD COLUMN IF NOT EXISTS last_retry_at TIMESTAMP WITH TIME ZONE;
    """, "last_retry_at 字段添加")
    
    # 2. 更新 exception_type CHECK 约束
    execute_safely("""
        ALTER TABLE exceptions 
        DROP CONSTRAINT IF EXISTS exceptions_exception_type_check;
    """, "删除旧 exception_type 约束")
    
    execute_safely("""
        ALTER TABLE exceptions 
        ADD CONSTRAINT exceptions_exception_type_check 
        CHECK (exception_type IN (
            'pdf_parse', 'ocr_error', 'customer_mismatch', 'supplier_mismatch', 
            'posting_error', 'ingest_validation_failed', 'missing_source', 'duplicate_record'
        ));
    """, "添加新 exception_type 约束（支持新类型）")
    
    # 3. 添加 next_action CHECK 约束
    execute_safely("""
        ALTER TABLE exceptions 
        DROP CONSTRAINT IF EXISTS exceptions_next_action_check;
    """, "删除旧 next_action 约束")
    
    execute_safely("""
        ALTER TABLE exceptions 
        ADD CONSTRAINT exceptions_next_action_check 
        CHECK (next_action IN (
            'retry_parse', 'retry_posting', 'manual_match', 
            'upload_new_file', 'review_source', 'contact_support'
        ) OR next_action IS NULL);
    """, "添加 next_action CHECK 约束")
    
    # 4. 修改 auto_posting_rules.company_id 允许 NULL
    execute_safely("""
        ALTER TABLE auto_posting_rules 
        ALTER COLUMN company_id DROP NOT NULL;
    """, "auto_posting_rules.company_id 允许 NULL（支持全局规则）")
    
    # 5. 创建索引
    execute_safely("""
        CREATE INDEX IF NOT EXISTS idx_exceptions_retryable 
        ON exceptions(retryable) WHERE retryable = TRUE;
    """, "异常可重试索引创建")
    
    print("✅ 现有表迁移完成\n")


if __name__ == "__main__":
    print("=" * 60)
    print("  数据库初始化 & 迁移脚本")
    print("=" * 60)
    
    # 步骤1：创建所有新表（通过SQLAlchemy ORM）
    print("\n🔄 步骤1：创建新表...")
    init_database()
    
    # 步骤2：迁移现有表
    print("\n🔄 步骤2：迁移现有表...")
    migrate_existing_tables()
    
    # 步骤3：初始化RBAC权限系统
    print("\n🔄 步骤3：初始化RBAC权限系统...")
    try:
        from accounting_app.rbac import init_default_permissions
        init_default_permissions()
    except Exception as e:
        print(f"⚠️ RBAC初始化警告: {str(e)[:200]}")
    
    print("\n" + "=" * 60)
    print("  ✅ 数据库初始化完成！")
    print("=" * 60)
    print("\n新增的表：")
    print("  - report_snapshots (报表版本化)")
    print("  - period_closing (期间锁定)")
    print("  - system_config_versions (配置版本锁)")
    print("  - upload_staging (上传暂存区)")
    print("  - permissions (权限定义)")
    print("  - role_permissions (角色权限映射)")
    print("\n更新的表：")
    print("  - exceptions (添加 next_action, retryable 等字段)")
    print("  - auto_posting_rules (company_id 支持 NULL)")
    print()
