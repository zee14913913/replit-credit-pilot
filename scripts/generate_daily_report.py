#!/usr/bin/env python3
import sqlite3
import requests
import json
from datetime import datetime

def generate_daily_report():
    """生成每日运维报告"""
    print("="*60)
    print("📝 生成每日运维报告")
    print("="*60)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    report = []
    report.append("# CreditPilot 每日运维报告")
    report.append(f"\n**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report.append("---\n")
    
    # 1. API健康检查
    report.append("## 🏥 API健康检查\n")
    try:
        response = requests.get('http://localhost:5000/api/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            report.append(f"✅ **健康状态**: {data.get('status', 'unknown')}")
            report.append(f"✅ **响应时间**: {response.elapsed.total_seconds():.3f}s\n")
        else:
            report.append(f"❌ **健康检查失败**: HTTP {response.status_code}\n")
    except Exception as e:
        report.append(f"❌ **健康检查异常**: {str(e)}\n")
    
    # 2. 数据库统计
    report.append("## 📊 数据库统计\n")
    try:
        conn = sqlite3.connect('db/smart_loan_manager.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM customers")
        customers = cursor.fetchone()[0]
        report.append(f"- **客户总数**: {customers}")
        
        cursor.execute("SELECT COUNT(*) FROM statements")
        statements = cursor.fetchone()[0]
        report.append(f"- **账单总数**: {statements}")
        
        cursor.execute("SELECT COUNT(*) FROM transactions")
        transactions = cursor.fetchone()[0]
        report.append(f"- **交易总数**: {transactions:,}")
        
        cursor.execute("SELECT COUNT(*) FROM credit_cards")
        cards = cursor.fetchone()[0]
        report.append(f"- **信用卡数**: {cards}\n")
        
        cursor.execute("""
            SELECT 
                ROUND(SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END), 2) as expenses,
                ROUND(SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END), 2) as payments
            FROM transactions
        """)
        row = cursor.fetchone()
        expenses = row[0] or 0
        payments = row[1] or 0
        balance = round(expenses - payments, 2)
        
        report.append(f"- **总费用**: RM {expenses:,.2f}")
        report.append(f"- **总还款**: RM {payments:,.2f}")
        report.append(f"- **净余额**: RM {balance:,.2f}\n")
        
        conn.close()
    except Exception as e:
        report.append(f"❌ **数据库查询失败**: {str(e)}\n")
    
    # 3. API端点测试
    report.append("## 🧪 API端点测试\n")
    endpoints = [
        ('GET', '/api/health', '健康检查'),
        ('GET', '/api/customers', '客户列表'),
        ('GET', '/api/dashboard/summary', '仪表板汇总'),
        ('GET', '/api/bill/ocr-status', 'OCR状态')
    ]
    
    passed = 0
    failed = 0
    
    for method, path, name in endpoints:
        try:
            url = f'http://localhost:5000{path}'
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                report.append(f"✅ **{name}**: PASS (HTTP {response.status_code})")
                passed += 1
            else:
                report.append(f"❌ **{name}**: FAIL (HTTP {response.status_code})")
                failed += 1
        except Exception as e:
            report.append(f"❌ **{name}**: ERROR ({str(e)})")
            failed += 1
    
    report.append(f"\n**测试结果**: {passed} 通过, {failed} 失败\n")
    
    # 4. 异常清单
    report.append("## 🚨 异常清单\n")
    if failed == 0:
        report.append("✅ **无异常**\n")
    else:
        report.append(f"⚠️ **{failed} 个API端点测试失败**\n")
    
    # 5. 环境配置状态
    report.append("## ⚙️ 环境配置状态\n")
    import os
    critical_vars = ['GOOGLE_PROJECT_ID', 'DOCPARSER_API_KEY']
    for var in critical_vars:
        if os.getenv(var):
            report.append(f"✅ **{var}**: 已配置")
        else:
            report.append(f"⚠️ **{var}**: 未配置")
    
    report.append("\n---\n")
    report.append("**报告生成完成**")
    
    # 保存报告
    filename = f"logs/daily_report_{datetime.now().strftime('%Y%m%d')}.md"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    # 同时更新主报告
    with open('api_validation_report.md', 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print(f"✅ 报告已生成: {filename}")
    print(f"✅ 主报告已更新: api_validation_report.md\n")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(generate_daily_report())
