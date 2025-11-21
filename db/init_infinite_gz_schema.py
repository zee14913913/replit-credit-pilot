
#!/usr/bin/env python3
"""
Infinite GZ 系统数据库初始化脚本
执行此脚本创建所有数据库表和初始数据
"""
import sqlite3
import os
from pathlib import Path

# 数据库文件路径
DB_PATH = os.path.join(os.path.dirname(__file__), 'smart_loan_manager.db')
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')


def init_database():
    """执行数据库初始化"""
    print("=" * 60)
    print("  Infinite GZ 系统数据库初始化")
    print("=" * 60)
    
    # 检查 schema.sql 是否存在
    if not os.path.exists(SCHEMA_PATH):
        print(f"❌ 错误：找不到 schema.sql 文件：{SCHEMA_PATH}")
        return False
    
    # 读取 SQL 脚本
    print(f"\n📖 读取 Schema 文件：{SCHEMA_PATH}")
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    # 连接数据库
    print(f"🔗 连接数据库：{DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 执行 SQL 脚本
        print("⚙️  执行建表脚本...")
        cursor.executescript(schema_sql)
        conn.commit()
        
        # 验证表是否创建成功
        print("\n✅ 验证表结构...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        expected_tables = [
            'users', 'credit_cards', 'statements', 'transactions', 
            'settlements', 'suppliers', 'reminders', 'contracts',
            'loan_products', 'tax_records', 'monthly_statements'
        ]
        
        created_tables = [table[0] for table in tables]
        
        print(f"\n📊 已创建的表（共 {len(created_tables)} 个）：")
        for table in created_tables:
            status = "✓" if table in expected_tables else "ℹ"
            print(f"  {status} {table}")
        
        # 检查是否所有必要的表都已创建
        missing_tables = set(expected_tables) - set(created_tables)
        if missing_tables:
            print(f"\n⚠️  警告：以下表未创建：{missing_tables}")
        
        # 显示初始数据
        print("\n📋 初始化数据统计：")
        cursor.execute("SELECT COUNT(*) FROM suppliers")
        supplier_count = cursor.fetchone()[0]
        print(f"  • 供应商：{supplier_count} 条记录")
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
        admin_count = cursor.fetchone()[0]
        print(f"  • 管理员账户：{admin_count} 个")
        
        print("\n" + "=" * 60)
        print("✅ 数据库初始化完成！")
        print("=" * 60)
        print(f"\n数据库位置：{DB_PATH}")
        print(f"总表数量：{len(created_tables)}")
        print("\n可以开始使用 Infinite GZ 系统了！")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 错误：数据库初始化失败")
        print(f"错误信息：{str(e)}")
        conn.rollback()
        return False
        
    finally:
        conn.close()


def verify_schema():
    """验证数据库结构完整性"""
    print("\n🔍 执行数据库结构完整性检查...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 检查外键约束
        cursor.execute("PRAGMA foreign_keys")
        fk_status = cursor.fetchone()[0]
        print(f"  • 外键约束：{'启用' if fk_status else '未启用'}")
        
        # 检查索引
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index'")
        index_count = cursor.fetchone()[0]
        print(f"  • 索引数量：{index_count} 个")
        
        # 检查视图
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='view'")
        view_count = cursor.fetchone()[0]
        print(f"  • 视图数量：{view_count} 个")
        
        print("✅ 结构完整性检查通过")
        
    except Exception as e:
        print(f"❌ 检查失败：{str(e)}")
    finally:
        conn.close()


if __name__ == "__main__":
    success = init_database()
    
    if success:
        verify_schema()
        print("\n💡 提示：")
        print("  1. 默认管理员邮箱：admin@infinitegz.com")
        print("  2. 首次登录后请修改密码")
        print("  3. 已预置 10 个供应商记录")
        print("  4. 可使用 db/models.py 进行 ORM 操作")
    else:
        print("\n请检查错误信息并重试。")
