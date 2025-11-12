"""
Database Migration v5.1 - Comprehensive Update
包含两大功能：
1. 手续费拆分规则更新（Supplier Fee Split Logic）
2. 智能排卡优化系统（Card Usage Optimizer）

执行顺序：
- Phase 1: 更新现有表字段
- Phase 2: 创建新表
"""

import sqlite3
from datetime import datetime

DB_PATH = 'db/smart_loan_manager.db'

def migrate():
    """执行完整的数据库迁移"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("="*80)
        print("开始数据库迁移 v5.1")
        print("="*80)
        
        # ==================== Phase 1: 更新现有表 ====================
        print("\n📝 Phase 1: 更新现有表字段...")
        
        # 1.1 更新 credit_cards 表
        print("  → 为 credit_cards 表添加账单日和到期日字段...")
        
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(credit_cards)")
        existing_columns = [col[1] for col in cursor.fetchall()]
        
        if 'statement_cutoff_day' not in existing_columns:
            cursor.execute('''
                ALTER TABLE credit_cards 
                ADD COLUMN statement_cutoff_day INTEGER DEFAULT NULL
            ''')
            print("    ✅ 添加 statement_cutoff_day 字段")
        else:
            print("    ⏭️  statement_cutoff_day 字段已存在")
        
        if 'payment_due_day' not in existing_columns:
            cursor.execute('''
                ALTER TABLE credit_cards 
                ADD COLUMN payment_due_day INTEGER DEFAULT NULL
            ''')
            print("    ✅ 添加 payment_due_day 字段")
        else:
            print("    ⏭️  payment_due_day 字段已存在")
        
        if 'min_payment_rate' not in existing_columns:
            cursor.execute('''
                ALTER TABLE credit_cards 
                ADD COLUMN min_payment_rate REAL DEFAULT 5.0
            ''')
            print("    ✅ 添加 min_payment_rate 字段（默认5%）")
        else:
            print("    ⏭️  min_payment_rate 字段已存在")
        
        # 1.2 更新 transactions 表（手续费拆分相关）
        print("\n  → 为 transactions 表添加手续费拆分字段...")
        
        cursor.execute("PRAGMA table_info(transactions)")
        existing_columns = [col[1] for col in cursor.fetchall()]
        
        if 'is_fee_split' not in existing_columns:
            cursor.execute('''
                ALTER TABLE transactions 
                ADD COLUMN is_fee_split INTEGER DEFAULT 0
            ''')
            print("    ✅ 添加 is_fee_split 字段（标记是否已拆分手续费）")
        else:
            print("    ⏭️  is_fee_split 字段已存在")
        
        if 'fee_reference_id' not in existing_columns:
            cursor.execute('''
                ALTER TABLE transactions 
                ADD COLUMN fee_reference_id INTEGER DEFAULT NULL
            ''')
            print("    ✅ 添加 fee_reference_id 字段（关联原始交易）")
        else:
            print("    ⏭️  fee_reference_id 字段已存在")
        
        if 'is_merchant_fee' not in existing_columns:
            cursor.execute('''
                ALTER TABLE transactions 
                ADD COLUMN is_merchant_fee INTEGER DEFAULT 0
            ''')
            print("    ✅ 添加 is_merchant_fee 字段（标记是否为手续费记录）")
        else:
            print("    ⏭️  is_merchant_fee 字段已存在")
        
        # ==================== Phase 2: 创建新表（智能排卡系统） ====================
        print("\n📝 Phase 2: 创建智能排卡系统表...")
        
        # 2.1 card_usage_plans - 排卡计划表
        print("  → 创建 card_usage_plans 表...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS card_usage_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                plan_month TEXT NOT NULL,
                status TEXT DEFAULT 'draft',
                total_expected_spend REAL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                notes TEXT,
                
                FOREIGN KEY (customer_id) REFERENCES customers(id),
                UNIQUE(customer_id, plan_month)
            )
        ''')
        print("    ✅ card_usage_plans 表创建成功")
        
        # 2.2 card_recommendations - 刷卡建议表
        print("  → 创建 card_recommendations 表...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS card_recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id INTEGER NOT NULL,
                card_id INTEGER NOT NULL,
                priority_rank INTEGER NOT NULL,
                
                recommended_start_date DATE NOT NULL,
                recommended_end_date DATE NOT NULL,
                estimated_float_days INTEGER,
                
                recommended_spend_limit REAL,
                current_utilization REAL,
                projected_utilization REAL,
                
                reason TEXT,
                risk_level TEXT DEFAULT 'low',
                score REAL,
                
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (plan_id) REFERENCES card_usage_plans(id),
                FOREIGN KEY (card_id) REFERENCES credit_cards(id)
            )
        ''')
        print("    ✅ card_recommendations 表创建成功")
        
        # 2.3 payment_schedules - 还款计划表
        print("  → 创建 payment_schedules 表...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payment_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id INTEGER NOT NULL,
                card_id INTEGER NOT NULL,
                
                due_date DATE NOT NULL,
                minimum_payment REAL,
                recommended_payment REAL,
                priority_order INTEGER,
                
                funding_source TEXT DEFAULT 'self',
                payment_status TEXT DEFAULT 'pending',
                
                notes TEXT,
                risk_warning TEXT,
                
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                executed_at DATETIME,
                
                FOREIGN KEY (plan_id) REFERENCES card_usage_plans(id),
                FOREIGN KEY (card_id) REFERENCES credit_cards(id)
            )
        ''')
        print("    ✅ payment_schedules 表创建成功")
        
        # 2.4 risk_consents - 风险确认记录表
        print("  → 创建 risk_consents 表...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS risk_consents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                plan_id INTEGER,
                
                risk_type TEXT NOT NULL,
                risk_description TEXT NOT NULL,
                
                consent_given INTEGER DEFAULT 0,
                consent_timestamp DATETIME,
                ip_address TEXT,
                user_agent TEXT,
                
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (customer_id) REFERENCES customers(id),
                FOREIGN KEY (plan_id) REFERENCES card_usage_plans(id)
            )
        ''')
        print("    ✅ risk_consents 表创建成功")
        
        # ==================== Phase 3: 创建索引 ====================
        print("\n📝 Phase 3: 创建索引优化查询性能...")
        
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_card_usage_plans_customer ON card_usage_plans(customer_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_card_usage_plans_month ON card_usage_plans(plan_month)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_card_recommendations_plan ON card_recommendations(plan_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_payment_schedules_plan ON payment_schedules(plan_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_payment_schedules_due ON payment_schedules(due_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_risk_consents_customer ON risk_consents(customer_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_fee_split ON transactions(is_fee_split)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_merchant_fee ON transactions(is_merchant_fee)')
            print("    ✅ 所有索引创建成功")
        except Exception as idx_error:
            print(f"    ⚠️  索引创建警告: {idx_error}")
            print("    → 继续执行...")
        
        # 提交所有更改
        conn.commit()
        
        print("\n" + "="*80)
        print("✅ 数据库迁移 v5.1 完成！")
        print("="*80)
        print("\n新增功能：")
        print("  ✓ 手续费拆分逻辑支持")
        print("  ✓ 信用卡账单日/到期日管理")
        print("  ✓ 智能排卡优化系统")
        print("  ✓ 免息期计算引擎")
        print("  ✓ 还款优先级管理")
        print("  ✓ 风险告知与合规记录")
        print("\n" + "="*80)
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    finally:
        conn.close()


def rollback():
    """回滚迁移（谨慎使用）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("⚠️  开始回滚迁移...")
        
        # 删除新表
        cursor.execute('DROP TABLE IF EXISTS risk_consents')
        cursor.execute('DROP TABLE IF EXISTS payment_schedules')
        cursor.execute('DROP TABLE IF EXISTS card_recommendations')
        cursor.execute('DROP TABLE IF EXISTS card_usage_plans')
        
        conn.commit()
        print("✅ 回滚完成")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 回滚失败: {e}")
        raise
    
    finally:
        conn.close()


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'rollback':
        rollback()
    else:
        migrate()
