"""
测试月度汇总报告PDF导出功能
"""

import sqlite3
from services.monthly_summary_report import MonthlySummaryReport
import os

def test_pdf_export():
    """测试PDF导出功能"""
    
    # 初始化报告生成器
    reporter = MonthlySummaryReport()
    
    # 1. 查找有数据的客户
    conn = sqlite3.connect('db/smart_loan_manager.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT DISTINCT c.id, c.name, c.customer_code
        FROM customers c
        JOIN infinite_monthly_ledger iml ON c.id = iml.customer_id
        LIMIT 1
    ''')
    
    customer = cursor.fetchone()
    
    if not customer:
        print("❌ 没有找到有INFINITE账本数据的客户")
        conn.close()
        return False
    
    customer_id, customer_name, customer_code = customer
    print(f"✅ 找到测试客户: {customer_name} ({customer_code})")
    
    # 2. 查找该客户的月度数据
    cursor.execute('''
        SELECT DISTINCT substr(month_start, 1, 7) as period
        FROM infinite_monthly_ledger
        WHERE customer_id = ?
        ORDER BY period DESC
        LIMIT 1
    ''', (customer_id,))
    
    period_row = cursor.fetchone()
    
    if not period_row:
        print("❌ 该客户没有月度数据")
        conn.close()
        return False
    
    period = period_row[0]
    year, month = period.split('-')
    year = int(year)
    month = int(month)
    
    print(f"✅ 找到测试期间: {year}年{month}月")
    
    conn.close()
    
    # 3. 测试月度PDF生成
    print("\n📄 测试月度PDF生成...")
    try:
        pdf_path = reporter.generate_monthly_pdf(customer_id, year, month)
        print(f"✅ 月度PDF生成成功!")
        print(f"   文件路径: {pdf_path}")
        print(f"   文件大小: {os.path.getsize(pdf_path):,} 字节")
        print(f"   文件存在: {os.path.exists(pdf_path)}")
    except Exception as e:
        print(f"❌ 月度PDF生成失败: {str(e)}")
        return False
    
    # 4. 测试年度PDF生成
    print(f"\n📄 测试{year}年度PDF生成...")
    try:
        yearly_pdf_path = reporter.generate_yearly_pdf(customer_id, year)
        print(f"✅ 年度PDF生成成功!")
        print(f"   文件路径: {yearly_pdf_path}")
        print(f"   文件大小: {os.path.getsize(yearly_pdf_path):,} 字节")
        print(f"   文件存在: {os.path.exists(yearly_pdf_path)}")
    except Exception as e:
        print(f"❌ 年度PDF生成失败: {str(e)}")
        return False
    
    # 5. 验证文件存储位置
    print(f"\n📁 验证文件存储位置...")
    expected_dir = f"static/uploads/customers/{customer_code}/reports/monthly_summary"
    print(f"   预期目录: {expected_dir}")
    print(f"   目录存在: {os.path.exists(expected_dir)}")
    
    if os.path.exists(expected_dir):
        files = os.listdir(expected_dir)
        print(f"   目录内文件数: {len(files)}")
        for f in files:
            print(f"   - {f}")
    
    print("\n✅ 所有测试通过!")
    return True

if __name__ == '__main__':
    success = test_pdf_export()
    exit(0 if success else 1)
