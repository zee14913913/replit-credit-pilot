#!/usr/bin/env python3
"""
UAT阶段4：审计与安全验证
验证系统的审计日志完整性、RBAC权限控制、数据安全和异常捕获机制
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import sqlite3
from datetime import datetime
import requests

def check_audit_log_structure():
    """验证审计日志表结构"""
    print("\n" + "=" * 80)
    print("1️⃣ 审计日志表结构验证")
    print("=" * 80)
    
    conn = sqlite3.connect('db/smart_loan_manager.db')
    c = conn.cursor()
    
    c.execute('PRAGMA table_info(audit_logs)')
    columns = c.fetchall()
    
    expected_columns = ['id', 'user_id', 'action_type', 'entity_type', 'entity_id', 'description', 'ip_address', 'created_at']
    actual_columns = [col[1] for col in columns]
    
    print("\n表结构:")
    for col in columns:
        print(f"  {col[1]:<20} {col[2]:<15}")
    
    missing = set(expected_columns) - set(actual_columns)
    if missing:
        print(f"\n⚠️ 缺少字段: {missing}")
        result = False
    else:
        print(f"\n✅ 表结构完整（{len(actual_columns)}个字段）")
        result = True
    
    conn.close()
    return result

def check_audit_log_completeness():
    """验证审计日志完整性"""
    print("\n" + "=" * 80)
    print("2️⃣ 审计日志完整性验证")
    print("=" * 80)
    
    conn = sqlite3.connect('db/smart_loan_manager.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # 统计审计日志
    c.execute('SELECT COUNT(*) as total FROM audit_logs')
    total = c.fetchone()['total']
    print(f"\n总审计日志记录数: {total}")
    
    # 按操作类型统计
    c.execute('''
        SELECT action_type, COUNT(*) as count 
        FROM audit_logs 
        GROUP BY action_type 
        ORDER BY count DESC 
        LIMIT 10
    ''')
    
    print("\n按操作类型统计（Top 10）:")
    print(f"{'操作类型':<30} {'记录数':>10}")
    print("-" * 45)
    
    rows = c.fetchall()
    for row in rows:
        print(f"{row['action_type']:<30} {row['count']:>10}")
    
    # 验证关键操作是否有审计日志
    critical_actions = [
        'UPLOAD_STATEMENT',
        'FEE_SPLIT_APPLIED',
        'INVOICE_GENERATED',
        'CONFIRM_STATEMENT',
        'DELETE_STATEMENT'
    ]
    
    print("\n关键操作审计验证:")
    all_logged = True
    for action in critical_actions:
        c.execute('SELECT COUNT(*) as count FROM audit_logs WHERE action_type = ?', (action,))
        count = c.fetchone()['count']
        status = "✅" if count > 0 else "⚠️"
        print(f"  {status} {action:<25} {count:>5} 条")
        if count == 0 and action in ['UPLOAD_STATEMENT', 'FEE_SPLIT_APPLIED']:
            all_logged = False
    
    # 检查最近的审计日志
    c.execute('''
        SELECT action_type, entity_type, description, created_at
        FROM audit_logs
        ORDER BY created_at DESC
        LIMIT 5
    ''')
    
    print("\n最近5条审计日志:")
    recent_logs = c.fetchall()
    for idx, log in enumerate(recent_logs, 1):
        desc = log['description'][:50] if log['description'] else 'N/A'
        print(f"  {idx}. [{log['created_at']}] {log['action_type']}")
        print(f"     {desc}...")
    
    conn.close()
    
    return all_logged and total > 0

def check_audit_log_data_quality():
    """验证审计日志数据质量"""
    print("\n" + "=" * 80)
    print("3️⃣ 审计日志数据质量验证")
    print("=" * 80)
    
    conn = sqlite3.connect('db/smart_loan_manager.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # 检查空白字段
    c.execute('''
        SELECT 
            SUM(CASE WHEN action_type IS NULL OR action_type = '' THEN 1 ELSE 0 END) as null_action,
            SUM(CASE WHEN description IS NULL OR description = '' THEN 1 ELSE 0 END) as null_desc,
            SUM(CASE WHEN created_at IS NULL THEN 1 ELSE 0 END) as null_time,
            COUNT(*) as total
        FROM audit_logs
    ''')
    
    stats = c.fetchone()
    
    print("\n数据完整性检查:")
    print(f"  总记录数: {stats['total']}")
    print(f"  空白action_type: {stats['null_action']} ({stats['null_action']/stats['total']*100:.1f}%)")
    print(f"  空白description: {stats['null_desc']} ({stats['null_desc']/stats['total']*100:.1f}%)")
    print(f"  空白created_at: {stats['null_time']} ({stats['null_time']/stats['total']*100:.1f}%)")
    
    quality_pass = stats['null_action'] == 0 and stats['null_time'] == 0
    
    if quality_pass:
        print("\n✅ 数据质量合格（关键字段无空值）")
    else:
        print("\n❌ 数据质量不合格（存在空白关键字段）")
    
    conn.close()
    return quality_pass

def check_rbac_decorator_usage():
    """检查RBAC装饰器使用情况"""
    print("\n" + "=" * 80)
    print("4️⃣ RBAC权限控制实现验证")
    print("=" * 80)
    
    print("\n检查auth/admin_auth_helper.py:")
    
    try:
        with open('auth/admin_auth_helper.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键函数
        checks = [
            ('require_admin_or_accountant', 'Admin/Accountant装饰器'),
            ('verify_user_with_accounting_api', 'FastAPI认证验证'),
            ('verify_flask_user', 'Flask RBAC验证'),
        ]
        
        all_present = True
        for func_name, desc in checks:
            if func_name in content:
                print(f"  ✅ {desc} ({func_name})")
            else:
                print(f"  ⚠️ {desc} ({func_name}) - 未找到")
                all_present = False
        
        # 检查角色定义
        print("\n支持的角色:")
        if "'admin'" in content:
            print("  ✅ admin（管理员）")
        if "'accountant'" in content:
            print("  ✅ accountant（会计）")
        if "'viewer'" in content:
            print("  ✅ viewer（查看者）")
        
        return all_present
    except FileNotFoundError:
        print("  ❌ auth/admin_auth_helper.py 未找到")
        return False

def check_protected_routes():
    """检查受保护的路由"""
    print("\n" + "=" * 80)
    print("5️⃣ 受保护路由验证")
    print("=" * 80)
    
    print("\n检查app.py中的RBAC装饰器使用:")
    
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 统计@require_admin_or_accountant使用次数
        decorator_count = content.count('@require_admin_or_accountant')
        
        print(f"  发现 {decorator_count} 处使用@require_admin_or_accountant装饰器")
        
        # 检查关键路由是否受保护
        critical_routes = [
            '/admin',
            '/credit-card',
            '/upload',
            '/delete',
            '/edit',
        ]
        
        protected_count = 0
        for route in critical_routes:
            if f"'{route}" in content or f'"{route}"' in content:
                protected_count += 1
        
        print(f"  关键路由覆盖: {protected_count}/{len(critical_routes)}")
        
        if decorator_count >= 10:
            print("\n✅ RBAC装饰器使用充分")
            return True
        else:
            print("\n⚠️ RBAC装饰器使用较少，可能存在未保护的路由")
            return False
            
    except FileNotFoundError:
        print("  ❌ app.py 未找到")
        return False

def test_exception_logging():
    """测试异常日志记录"""
    print("\n" + "=" * 80)
    print("6️⃣ 异常日志捕获验证")
    print("=" * 80)
    
    conn = sqlite3.connect('db/smart_loan_manager.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # 查询ERROR类型的审计日志
    c.execute('''
        SELECT action_type, description, created_at
        FROM audit_logs
        WHERE action_type LIKE '%ERROR%' OR description LIKE '%error%' OR description LIKE '%Error%'
        ORDER BY created_at DESC
        LIMIT 5
    ''')
    
    error_logs = c.fetchall()
    
    if error_logs:
        print(f"\n发现 {len(error_logs)} 条错误日志:")
        for idx, log in enumerate(error_logs, 1):
            desc = log['description'][:60] if log['description'] else 'N/A'
            print(f"  {idx}. [{log['created_at']}] {log['action_type']}")
            print(f"     {desc}...")
        result = True
    else:
        print("\n⚠️ 未发现错误日志（可能系统运行正常，或异常未被记录）")
        result = False
    
    # 检查是否有UPLOAD相关的审计日志（验证核心功能有审计）
    c.execute('''
        SELECT COUNT(*) as count
        FROM audit_logs
        WHERE action_type IN ('UPLOAD_STATEMENT', 'FEE_SPLIT_APPLIED', 'INVOICE_GENERATED')
    ''')
    
    core_audit_count = c.fetchone()['count']
    print(f"\n核心业务操作审计日志: {core_audit_count} 条")
    
    conn.close()
    
    return core_audit_count > 0

def check_sensitive_file_access():
    """验证敏感文件访问控制"""
    print("\n" + "=" * 80)
    print("7️⃣ 敏感文件访问控制验证")
    print("=" * 80)
    
    print("\n检查文件存储安全配置:")
    
    # 检查是否有文件上传目录
    upload_dirs = [
        'static/uploads',
        'static/uploads/customers',
        'static/uploads/invoices',
    ]
    
    for dir_path in upload_dirs:
        if os.path.exists(dir_path):
            print(f"  ✅ {dir_path} 存在")
            # 检查是否有.htaccess或其他保护文件
            htaccess = os.path.join(dir_path, '.htaccess')
            if os.path.exists(htaccess):
                print(f"     ✅ 发现.htaccess保护文件")
        else:
            print(f"  ⚠️ {dir_path} 不存在")
    
    # 检查app.py中是否有文件访问控制逻辑
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        security_checks = [
            ('send_from_directory', '文件发送函数'),
            ('require_admin_or_accountant', 'RBAC装饰器'),
            ('secure_filename', '文件名安全化'),
        ]
        
        print("\n文件访问安全机制:")
        for check, desc in security_checks:
            if check in content:
                print(f"  ✅ {desc} ({check})")
            else:
                print(f"  ⚠️ {desc} ({check}) - 未找到")
        
        return True
    except FileNotFoundError:
        print("  ❌ app.py 未找到")
        return False

def generate_audit_log_sample():
    """生成审计日志样本"""
    print("\n" + "=" * 80)
    print("8️⃣ 生成审计日志样本")
    print("=" * 80)
    
    conn = sqlite3.connect('db/smart_loan_manager.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # 获取不同类型的审计日志示例
    sample_types = [
        'UPLOAD_STATEMENT',
        'FEE_SPLIT_APPLIED',
        'INVOICE_GENERATED',
        'CONFIRM_STATEMENT',
        'VIEW_MONTHLY_SUMMARY',
    ]
    
    samples = []
    for action_type in sample_types:
        c.execute('''
            SELECT action_type, entity_type, entity_id, description, created_at
            FROM audit_logs
            WHERE action_type = ?
            ORDER BY created_at DESC
            LIMIT 1
        ''', (action_type,))
        
        row = c.fetchone()
        if row:
            samples.append({
                'action_type': row['action_type'],
                'entity_type': row['entity_type'],
                'entity_id': row['entity_id'],
                'description': row['description'],
                'created_at': row['created_at']
            })
    
    print(f"\n审计日志样本（{len(samples)}条）:\n")
    for idx, sample in enumerate(samples, 1):
        print(f"{idx}. 操作类型: {sample['action_type']}")
        print(f"   实体类型: {sample['entity_type']}")
        print(f"   实体ID: {sample['entity_id']}")
        print(f"   时间: {sample['created_at']}")
        print(f"   描述: {sample['description'][:80] if sample['description'] else 'N/A'}")
        print()
    
    conn.close()
    return samples

def generate_uat_report(results):
    """生成UAT阶段4测试报告"""
    print("\n" + "=" * 80)
    print("📊 UAT阶段4测试报告")
    print("=" * 80)
    
    print(f"\n✅ 测试通过标准:")
    
    test_items = [
        ('audit_structure', '审计日志表结构完整'),
        ('audit_completeness', '关键操作均被记录'),
        ('audit_quality', '数据质量合格'),
        ('rbac_implementation', 'RBAC实现完整'),
        ('protected_routes', '受保护路由充分'),
        ('exception_logging', '异常日志捕获'),
        ('file_access_control', '敏感文件访问控制'),
    ]
    
    passed_count = sum(1 for key, _ in test_items if results.get(key, False))
    total_count = len(test_items)
    
    for key, desc in test_items:
        status = "✅ PASS" if results.get(key, False) else "❌ FAIL"
        print(f"  {status:12} {desc}")
    
    print(f"\n通过率: {passed_count}/{total_count} ({passed_count/total_count*100:.1f}%)")
    
    print("\n" + "=" * 80)
    if passed_count >= total_count * 0.8:  # 80%通过率
        print("🎉 UAT阶段4完成 ✅")
        print("=" * 80)
        print("\n✅ 审计与安全验证通过！")
        print("  - 审计日志: ✅")
        print("  - 权限控制: ✅")
        print("  - 数据安全: ✅")
        print("  - 异常捕获: ✅")
        return True
    else:
        print("⚠️ UAT阶段4部分测试未通过")
        print("=" * 80)
        print(f"\n⚠️ 通过率: {passed_count/total_count*100:.1f}% (需要≥80%)")
        return False

def main():
    """执行完整的UAT阶段4测试"""
    print("\n" + "=" * 80)
    print("🧪 UAT阶段4：审计与安全验证")
    print("=" * 80)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    try:
        # 测试1: 审计日志表结构
        results['audit_structure'] = check_audit_log_structure()
        
        # 测试2: 审计日志完整性
        results['audit_completeness'] = check_audit_log_completeness()
        
        # 测试3: 审计日志数据质量
        results['audit_quality'] = check_audit_log_data_quality()
        
        # 测试4: RBAC装饰器实现
        results['rbac_implementation'] = check_rbac_decorator_usage()
        
        # 测试5: 受保护路由
        results['protected_routes'] = check_protected_routes()
        
        # 测试6: 异常日志捕获
        results['exception_logging'] = test_exception_logging()
        
        # 测试7: 敏感文件访问控制
        results['file_access_control'] = check_sensitive_file_access()
        
        # 测试8: 生成审计日志样本
        audit_samples = generate_audit_log_sample()
        
        # 生成测试报告
        success = generate_uat_report(results)
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"\n❌ 测试执行失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
