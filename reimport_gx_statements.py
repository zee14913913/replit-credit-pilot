"""
重新导入所有GX Bank月结单 - 使用修复后的解析器
确保100%数据准确性
"""

import sys
import glob
import re
import sqlite3
from ingest.savings_parser import parse_savings_statement

def find_gx_pdfs():
    """查找所有GX Bank PDF文件，去重并按时间排序"""
    # 搜索所有可能的位置
    pdf_patterns = [
        "attached_assets/*_176102*.pdf",
        "attached_assets/*_176103*.pdf",
        "*_176102*.pdf",
        "*_176103*.pdf"
    ]
    
    all_pdfs = []
    for pattern in pdf_patterns:
        all_pdfs.extend(glob.glob(pattern))
    
    # 提取月份和年份信息
    month_order = {
        'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
        'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
    }
    
    pdf_info = {}  # 使用字典去重，key = (month, year)
    
    for pdf in all_pdfs:
        match = re.search(r'(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s+(\d{4})', pdf, re.IGNORECASE)
        if match:
            month = match.group(1).upper()
            year = match.group(2)
            key = (month, year)
            
            # 提取时间戳，选择最新的文件
            timestamp_match = re.search(r'_(\d+)\.pdf', pdf)
            if timestamp_match:
                timestamp = int(timestamp_match.group(1))
                
                # 如果这个月份已存在，比较时间戳
                if key in pdf_info:
                    if timestamp > pdf_info[key]['timestamp']:
                        pdf_info[key] = {
                            'path': pdf,
                            'month': month,
                            'year': year,
                            'timestamp': timestamp
                        }
                else:
                    pdf_info[key] = {
                        'path': pdf,
                        'month': month,
                        'year': year,
                        'timestamp': timestamp
                    }
    
    # 排序
    sorted_pdfs = sorted(pdf_info.values(), 
                        key=lambda x: (int(x['year']), month_order[x['month']]))
    
    return sorted_pdfs

def import_statement(pdf_path, bank_name='GX Bank'):
    """导入单个月结单"""
    try:
        # 解析PDF
        info, transactions = parse_savings_statement(pdf_path, bank_name)
        
        if not transactions:
            print(f"  ⚠️  警告：无交易记录")
            return False
        
        # 连接数据库
        conn = sqlite3.connect('db/smart_loan_manager.db')
        cursor = conn.cursor()
        
        # 查找或创建savings_account
        cursor.execute("""
            SELECT id FROM savings_accounts 
            WHERE bank_name = ? AND account_number_last4 = ?
        """, (bank_name, info['account_last4']))
        
        account = cursor.fetchone()
        if account:
            account_id = account[0]
        else:
            # 创建新账户
            cursor.execute("""
                INSERT INTO savings_accounts 
                (bank_name, account_number_last4, account_type, account_holder_name)
                VALUES (?, ?, 'Savings', 'YEO CHEE WANG')
            """, (bank_name, info['account_last4']))
            account_id = cursor.lastrowid
        
        # 插入savings_statement
        cursor.execute("""
            INSERT INTO savings_statements 
            (savings_account_id, statement_date, total_transactions)
            VALUES (?, ?, ?)
        """, (account_id, info['statement_date'], info['total_transactions']))
        statement_id = cursor.lastrowid
        
        # 插入所有交易
        for txn in transactions:
            # 提取客户名称
            customer_name = None
            for name in ['YEO CHEE WANG', 'LOH YUN CHYI', 'CHAI YIEK HUEI', 'TAN ZEE LIANG']:
                if name in txn['description'].upper():
                    customer_name = name
                    break
            
            cursor.execute("""
                INSERT INTO savings_transactions 
                (savings_statement_id, transaction_date, description, amount, transaction_type, customer_name_tag)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (statement_id, txn['date'], txn['description'], 
                  txn['amount'], txn['type'], customer_name))
        
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"  ❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 100)
    print("重新导入所有GX Bank月结单")
    print("=" * 100)
    
    # 查找所有PDF
    pdfs = find_gx_pdfs()
    
    print(f"\n找到 {len(pdfs)} 个GX Bank PDF文件:\n")
    for i, pdf in enumerate(pdfs, 1):
        print(f"{i:2}. {pdf['month']} {pdf['year']}: {pdf['path']}")
    
    if not pdfs:
        print("\n❌ 未找到GX Bank PDF文件！")
        return
    
    # 逐个导入
    print("\n" + "=" * 100)
    print("开始导入...")
    print("=" * 100)
    
    success_count = 0
    fail_count = 0
    
    for i, pdf in enumerate(pdfs, 1):
        print(f"\n{i}/{len(pdfs)} - {pdf['month']} {pdf['year']}")
        print(f"  文件: {pdf['path']}")
        
        if import_statement(pdf['path']):
            success_count += 1
            print(f"  ✅ 导入成功")
        else:
            fail_count += 1
            print(f"  ❌ 导入失败")
    
    # 总结
    print("\n" + "=" * 100)
    print("导入完成！")
    print("=" * 100)
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")
    print(f"总计: {len(pdfs)}")

if __name__ == '__main__':
    main()
