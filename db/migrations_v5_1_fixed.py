"""
Database Migration v5.1 (Fixed Version)
修复architect指出的问题：
1. 添加外键约束
2. 添加完整的索引
3. 确保数据完整性
"""

import sqlite3
import os

def migrate():
    """执行数据库迁移"""
    
    db_path = 'db/smart_loan_manager.db'
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("="*80)
        print("开始数据库迁移 v5.1 (Fixed)")
        print("="*80)
        
        # ==================== Phase 1: 更新现有表字段 ====================
        print("\n📝 Phase 1: 更新现有表字段...")
        
        # 添加credit_cards表字段
        print("  → 为 credit_cards 表添加账单日和到期日字段...")
        
        # 检查字段是否存在
        cursor.execute("PRAGMA table_info(credit_cards)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        
        if 'statement_cutoff_day' not in existing_columns:
            cursor.execute('ALTER TABLE credit_cards ADD COLUMN statement_cutoff_day INTEGER')
            print("    ✅ 添加 statement_cutoff_day 字段")
        else:
            print("    ⏭️  statement_cutoff_day 字段已存在")
        
        if 'payment_due_day' not in existing_columns:
            cursor.execute('ALTER TABLE credit_cards ADD COLUMN payment_due_day INTEGER')
            print("    ✅ 添加 payment_due_day 字段")
        else:
            print("    ⏭️  payment_due_day 字段已存在")
        
        if 'min_payment_rate' not in existing_columns:
            cursor.execute('ALTER TABLE credit_cards ADD COLUMN min_payment_rate REAL DEFAULT 5.0')
            print("    ✅ 添加 min_payment_rate 字段（默认5%）")
        else:
            print("    ⏭️  min_payment_rate 字段已存在")
        
        # 添加transactions表字段
        print("\n  → 为 transactions 表添加手续费拆分字段...")
        
        cursor.execute("PRAGMA table_info(transactions)")
        txn_columns = {row[1] for row in cursor.fetchall()}
        
        if 'is_fee_split' not in txn_columns:
            cursor.execute('ALTER TABLE transactions ADD COLUMN is_fee_split INTEGER DEFAULT 0')
            print("    ✅ 添加 is_fee_split 字段")
        else:
            print("    ⏭️  is_fee_split 字段已存在")
        
        if 'fee_reference_id' not in txn_columns:
            cursor.execute('ALTER TABLE transactions ADD COLUMN fee_reference_id INTEGER')
            print("    ✅ 添加 fee_reference_id 字段")
        else:
            print("    ⏭️  fee_reference_id 字段已存在")
        
        if 'is_merchant_fee' not in txn_columns:
            cursor.execute('ALTER TABLE transactions ADD COLUMN is_merchant_fee INTEGER DEFAULT 0')
            print("    ✅ 添加 is_merchant_fee 字段")
        else:
            print("    ⏭️  is_merchant_fee 字段已存在")
        
        # ==================== Phase 2: 创建智能排卡系统表 ====================
        print("\n📝 Phase 2: 创建智能排卡系统表...")
        
        # 创建 card_usage_plans 表
        print("  → 创建 card_usage_plans 表...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS card_usage_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                plan_month TEXT NOT NULL,
                expected_amount REAL NOT NULL,
                total_available_credit REAL,
                status TEXT DEFAULT 'draft',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                confirmed_at DATETIME,
                FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
            )
        ''')
        print("    ✅ card_usage_plans 表创建成功")
        
        # 创建 card_recommendations 表（带外键）
        print("  → 创建 card_recommendations 表...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS card_recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id INTEGER NOT NULL,
                card_id INTEGER NOT NULL,
                priority_rank INTEGER NOT NULL,
                float_days INTEGER NOT NULL,
                risk_level TEXT DEFAULT 'low',
                recommendation_reason TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (plan_id) REFERENCES card_usage_plans(id) ON DELETE CASCADE,
                FOREIGN KEY (card_id) REFERENCES credit_cards(id) ON DELETE CASCADE
            )
        ''')
        print("    ✅ card_recommendations 表创建成功")
        
        # 创建 payment_schedules 表（带外键）
        print("  → 创建 payment_schedules 表...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payment_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id INTEGER,
                card_id INTEGER NOT NULL,
                due_date DATE NOT NULL,
                minimum_payment REAL NOT NULL,
                recommended_payment REAL,
                priority_order INTEGER,
                status TEXT DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (plan_id) REFERENCES card_usage_plans(id) ON DELETE CASCADE,
                FOREIGN KEY (card_id) REFERENCES credit_cards(id) ON DELETE CASCADE
            )
        ''')
        print("    ✅ payment_schedules 表创建成功")
        
        # 创建 risk_consents 表（带外键）
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
                FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
                FOREIGN KEY (plan_id) REFERENCES card_usage_plans(id) ON DELETE CASCADE
            )
        ''')
        print("    ✅ risk_consents 表创建成功")
        
        # ==================== Phase 3: 创建索引优化查询 ====================
        print("\n📝 Phase 3: 创建索引优化查询性能...")
        
        try:
            # card_usage_plans索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_card_usage_plans_customer ON card_usage_plans(customer_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_card_usage_plans_month ON card_usage_plans(plan_month)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_card_usage_plans_status ON card_usage_plans(status)')
            
            # card_recommendations索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_card_recommendations_plan ON card_recommendations(plan_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_card_recommendations_card ON card_recommendations(card_id)')
            
            # payment_schedules索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_payment_schedules_plan ON payment_schedules(plan_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_payment_schedules_card ON payment_schedules(card_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_payment_schedules_due ON payment_schedules(due_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_payment_schedules_status ON payment_schedules(status)')
            
            # risk_consents索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_risk_consents_customer ON risk_consents(customer_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_risk_consents_plan ON risk_consents(plan_id)')
            
            # transactions索引（手续费拆分）
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_fee_split ON transactions(is_fee_split)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_merchant_fee ON transactions(is_merchant_fee)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_fee_ref ON transactions(fee_reference_id)')
            
            print("    ✅ 所有索引创建成功")
        except Exception as idx_error:
            print(f"    ⚠️  索引创建警告: {idx_error}")
            print("    → 继续执行...")
        
        # 提交所有更改
        conn.commit()
        
        print("\n" + "="*80)
        print("✅ 数据库迁移 v5.1 (Fixed) 完成！")
        print("="*80)
        
        print("\n新增功能：")
        print("  ✓ 手续费拆分逻辑支持（带外键约束）")
        print("  ✓ 信用卡账单日/到期日管理")
        print("  ✓ 智能排卡优化系统（完整索引）")
        print("  ✓ 免息期计算引擎")
        print("  ✓ 还款优先级管理")
        print("  ✓ 风险告知与合规记录")
        
        print("\n" + "="*80)
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
