#!/usr/bin/env python3
"""
批量导入Alliance Bank信用卡账单
客户：CHANG CHOON CHOW (ID: 10)
账单月份：2024年9月 - 2025年8月（共12个月）
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import get_db
from ingest.statement_parser import parse_statement_auto
from validate.categorizer import categorize_transaction

def batch_import_alliance():
    """批量导入Alliance Bank账单"""
    
    customer_id = 10  # CHANG CHOON CHOW
    
    # Alliance Bank账单文件列表（2024-09 to 2025-08）
    files = [
        'attached_assets/12:09:2024_1761109756243.pdf',  # 2024-09
        'attached_assets/12:10:2024_1761109756243.pdf',  # 2024-10
        'attached_assets/12:11:2024_1761109782320.pdf',  # 2024-11
        'attached_assets/12:12:2024_1761109782323.pdf',  # 2024-12
        'attached_assets/12:01:2025_1761109756240.pdf',  # 2025-01
        'attached_assets/12:02:2025_1761109756242.pdf',  # 2025-02
        'attached_assets/12:03:2025_1761109756242.pdf',  # 2025-03
        'attached_assets/12:04:1025_1761109756242.pdf',  # 2025-04 (注意：文件名有typo)
        'attached_assets/12:05:2025_1761109756242.pdf',  # 2025-05
        'attached_assets/12:06:2025_1761109756242.pdf',  # 2025-06
        'attached_assets/12:07:2025_1761109756242.pdf',  # 2025-07
        'attached_assets/12:08:2025_1761109756243.pdf',  # 2025-08
    ]
    
    print("=" * 80)
    print(f"开始批量导入Alliance Bank账单")
    print(f"客户：CHANG CHOON CHOW (ID: {customer_id})")
    print(f"账单数量: {len(files)}")
    print(f"时间范围: 2024年9月 - 2025年8月")
    print("=" * 80)
    
    total_transactions = 0
    success_count = 0
    
    for file_path in files:
        if not os.path.exists(file_path):
            print(f"❌ 文件不存在: {file_path}")
            continue
        
        print(f"\n📄 处理文件: {os.path.basename(file_path)}")
        
        try:
            # 手动解析Alliance Bank账单（因为银行名称在第2-3页）
            from ingest.statement_parser import parse_alliance_statement
            
            statement_info, transactions = parse_alliance_statement(file_path)
            
            if not statement_info or not transactions:
                print(f"   ❌ 解析失败：无法提取账单数据")
                continue
            
            # 使用现有的Alliance Bank卡（ID: 33, ****4514）
            card_id = 33
            
            # 从文件名提取账单日期（格式：12:MM:YYYY）
            import re
            filename = os.path.basename(file_path)
            date_match = re.search(r'12:(\d{2}):(\d{3,4})', filename)
            
            if date_match:
                month = date_match.group(1)
                year = date_match.group(2)
                # 修正typo：1025应该是2025
                if year == '1025':
                    year = '2025'
                elif len(year) == 3:
                    year = '2' + year[1:]
                statement_date = f"{year}-{month}-12"
            else:
                print(f"   ❌ 无法从文件名提取日期：{filename}")
                continue
            
            print(f"   📅 账单日期：{statement_date}")
            
            with get_db() as conn:
                cursor = conn.cursor()
                
                # 检查账单是否已存在
                cursor.execute('''
                    SELECT id FROM statements 
                    WHERE card_id = ? AND statement_date = ?
                ''', (card_id, statement_date))
                
                if cursor.fetchone():
                    print(f"   ⚠️  账单已存在，跳过：{statement_date}")
                    continue
                
                # 组织文件存储
                from services.statement_organizer import StatementOrganizer
                organizer = StatementOrganizer()
                
                # 获取客户名称
                cursor.execute('SELECT name FROM customers WHERE id = ?', (customer_id,))
                customer_name = cursor.fetchone()[0]
                
                # 组织文件
                card_info = {
                    'bank_name': 'Alliance Bank',
                    'last_4_digits': '4514'
                }
                result = organizer.organize_statement(
                    file_path,
                    customer_name,
                    statement_date,
                    card_info,
                    category='credit_cards'
                )
                organized_path = result['archived_path']
                
                # 插入账单记录
                cursor.execute('''
                    INSERT INTO statements (
                        card_id, statement_date, statement_total, 
                        file_path, file_type, due_date, previous_balance,
                        is_confirmed, validation_score
                    )
                    VALUES (?, ?, ?, ?, 'pdf', ?, ?, 1, 100.0)
                ''', (
                    card_id,
                    statement_date,
                    statement_info.get('total', 0.0),
                    organized_path,
                    statement_info.get('due_date'),
                    statement_info.get('previous_balance', 0.0)
                ))
                statement_id = cursor.lastrowid
                
                # 插入交易记录
                txn_count = 0
                for trans in transactions:
                    # Get category - handle tuple return
                    category_result = categorize_transaction(trans.get('description', ''))
                    if isinstance(category_result, tuple):
                        category = category_result[0]
                    else:
                        category = category_result
                    
                    cursor.execute('''
                        INSERT INTO transactions (
                            statement_id, transaction_date, description, 
                            amount, transaction_type, category
                        )
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        statement_id,
                        trans.get('date'),
                        trans.get('description'),
                        trans.get('amount', 0.0),
                        trans.get('type', 'debit'),
                        category
                    ))
                    txn_count += 1
                
                conn.commit()
                
                total_transactions += txn_count
                success_count += 1
                
                print(f"   ✅ 成功导入：{statement_date}")
                print(f"   账单总额：RM {statement_info.get('total', 0):.2f}")
                print(f"   交易数量：{txn_count} 笔")
                print(f"   文件路径：{organized_path}")
                
        except Exception as e:
            print(f"   ❌ 错误：{str(e)}")
            import traceback
            traceback.print_exc()
            continue
    
    print("\n" + "=" * 80)
    print(f"导入完成！")
    print(f"成功：{success_count}/{len(files)} 个账单")
    print(f"总交易数：{total_transactions} 笔")
    print("=" * 80)

if __name__ == "__main__":
    batch_import_alliance()
