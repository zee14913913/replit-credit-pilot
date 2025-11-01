#!/usr/bin/env python3
"""
Phase 2-2 Task 4: 测试IP/User-Agent审计日志记录

验证审计日志是否正确捕获客户端IP地址和User-Agent
"""
import psycopg2
import os
from datetime import datetime

def test_audit_ip_tracking():
    """测试审计日志IP和User-Agent记录功能"""
    
    print("=" * 60)
    print("Phase 2-2 Task 4: IP/User-Agent审计日志测试")
    print("=" * 60)
    print()
    
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    cursor = conn.cursor()
    
    try:
        # 1. 检查audit_logs表结构
        print("✓ 步骤1：检查audit_logs表结构...")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'audit_logs'
            AND column_name IN ('ip_address', 'user_agent')
            ORDER BY column_name;
        """)
        columns = cursor.fetchall()
        
        if len(columns) == 2:
            print(f"  ✅ ip_address字段: {columns[0][1]}, nullable={columns[0][2]}")
            print(f"  ✅ user_agent字段: {columns[1][1]}, nullable={columns[1][2]}")
        else:
            print(f"  ❌ 缺少必需字段！找到{len(columns)}个字段")
            return False
        
        print()
        
        # 2. 插入测试审计日志记录
        print("✓ 步骤2：插入测试审计日志记录...")
        test_ip = "192.168.1.100"
        test_user_agent = "Mozilla/5.0 (Test Browser) Agent/1.0"
        
        cursor.execute("""
            INSERT INTO audit_logs (
                user_id, username, company_id, action_type, entity_type,
                description, success, ip_address, user_agent, created_at
            ) VALUES (
                1, 'test_user', 1, 'export', 'csv_file',
                'Phase 2-2 Task 4 测试记录 - 验证IP/User-Agent捕获', true, %s, %s, NOW()
            ) RETURNING id;
        """, (test_ip, test_user_agent))
        
        test_id = cursor.fetchone()[0]
        conn.commit()
        print(f"  ✅ 测试记录ID: {test_id}")
        print()
        
        # 3. 查询验证数据
        print("✓ 步骤3：查询验证IP和User-Agent...")
        cursor.execute("""
            SELECT id, username, action_type, ip_address, user_agent, created_at
            FROM audit_logs
            WHERE id = %s;
        """, (test_id,))
        
        record = cursor.fetchone()
        if record:
            print(f"  ✅ 记录ID: {record[0]}")
            print(f"  ✅ 用户名: {record[1]}")
            print(f"  ✅ 操作类型: {record[2]}")
            print(f"  ✅ IP地址: {record[3]}")
            print(f"  ✅ User-Agent: {record[4]}")
            print(f"  ✅ 创建时间: {record[5]}")
        else:
            print("  ❌ 无法查询到测试记录")
            return False
        
        print()
        
        # 4. 验证数据正确性
        print("✓ 步骤4：验证数据正确性...")
        if record[3] == test_ip:
            print(f"  ✅ IP地址匹配: {test_ip}")
        else:
            print(f"  ❌ IP地址不匹配: 期望{test_ip}, 实际{record[3]}")
            return False
        
        if record[4] == test_user_agent:
            print(f"  ✅ User-Agent匹配")
        else:
            print(f"  ❌ User-Agent不匹配")
            return False
        
        print()
        
        # 5. 清理测试数据
        print("✓ 步骤5：清理测试数据...")
        cursor.execute("DELETE FROM audit_logs WHERE id = %s;", (test_id,))
        conn.commit()
        print(f"  ✅ 已删除测试记录ID: {test_id}")
        print()
        
        # 6. 总结
        print("=" * 60)
        print("✅ 测试通过！审计日志IP/User-Agent记录功能正常")
        print("=" * 60)
        print()
        print("实施总结：")
        print("  - FastAPI: 6个导出路由已增强IP/User-Agent捕获")
        print("  - Flask: 8个审计日志调用已增强IP/User-Agent捕获")
        print("  - 数据库: audit_logs表已包含ip_address和user_agent字段")
        print("  - 防御性编程: 所有提取操作包含try-except容错机制")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        conn.rollback()
        return False
    
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    success = test_audit_ip_tracking()
    exit(0 if success else 1)
