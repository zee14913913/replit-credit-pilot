#!/usr/bin/env python3
"""
批量上传AmBank Islamic信用卡账单
客户：CHEOK JUN YOON
账单月份：2025年5-9月
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import get_db
from ingest.statement_parser import parse_statement_auto
from validate.categorizer import categorize_transaction

def batch_upload_ambank_islamic():
    """批量上传AmBank Islamic账单"""
    
    # 客户ID
    customer_id = 6  # CHEOK JUN YOON
    
    # 账单文件列表（最新版本）
    files = [
        'attached_assets/AMB IS 28:05:2025_1760482588883.pdf',  # 5月
        'attached_assets/AMB IS 28:06:2025_1760482588883.pdf',  # 6月
        'attached_assets/AMB IS 28:07:2025_1760482588883.pdf',  # 7月
        'attached_assets/AMB IS 28:08:2025_1760482588884.pdf',  # 8月
        'attached_assets/AMB IS 28:09:2025_1760482588884.pdf',  # 9月
    ]
    
    print("=" * 80)
    print(f"开始批量上传AmBank Islamic账单")
    print(f"客户ID: {customer_id} (CHEOK JUN YOON)")
    print(f"账单数量: {len(files)}")
    print("=" * 80)
    
    total_transactions = 0
    success_count = 0
    
    for file_path in files:
        if not os.path.exists(file_path):
            print(f"❌ 文件不存在: {file_path}")
            continue
        
        print(f"\n📄 处理文件: {os.path.basename(file_path)}")
        
        try:
            # 解析账单
            statement_info, transactions = parse_statement_auto(file_path)
            
            if not statement_info or not transactions:
                print(f"   ❌ 解析失败：无法提取账单数据")
                continue
            
            # 获取或创建信用卡
            with get_db() as conn:
                cursor = conn.cursor()
                
                # 检查信用卡是否存在
                cursor.execute('''
                    SELECT id FROM credit_cards 
                    WHERE customer_id = ? AND card_number_last4 = ?
                ''', (customer_id, statement_info.get('card_last4')))
                
                card = cursor.fetchone()
                if not card:
                    # 创建新信用卡
                    cursor.execute('''
                        INSERT INTO credit_cards (customer_id, bank_name, card_number_last4, credit_limit, due_date)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        customer_id,
                        statement_info.get('bank', 'AmBank Islamic'),
                        statement_info.get('card_last4'),
                        15000.00,  # 默认额度
                        17  # 默认还款日
                    ))
                    card_id = cursor.lastrowid
                else:
                    card_id = card[0]
                
                # 插入账单记录
                cursor.execute('''
                    INSERT INTO statements (
                        card_id, statement_date, statement_total, 
                        file_path, due_date, previous_balance
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    card_id,
                    statement_info.get('statement_date'),
                    statement_info.get('total', 0.0),
                    file_path,
                    statement_info.get('due_date'),
                    statement_info.get('previous_balance', 0.0)
                ))
                statement_id = cursor.lastrowid
                
                # 插入交易记录
                for trans in transactions:
                    # Get category - handle tuple return
                    category_result = categorize_transaction(trans.get('description', ''))
                    if isinstance(category_result, tuple):
                        category = category_result[0]  # Get category from tuple
                    else:
                        category = category_result
                    
                    # Map parser type to database transaction_type
                    # Parser returns: 'debit' (消费DR) / 'credit' (付款CR)
                    # Database expects: 'purchase' (消费) / 'payment' (付款)
                    parser_type = trans.get('type', 'debit')
                    db_transaction_type = 'payment' if parser_type == 'credit' else 'purchase'
                    
                    cursor.execute('''
                        INSERT INTO transactions (
                            statement_id, transaction_date, description, 
                            amount, category, transaction_type
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        statement_id,
                        trans.get('posting_date') or trans.get('date'),
                        trans.get('description'),
                        abs(trans.get('amount', 0)),
                        category or 'Uncategorized',
                        db_transaction_type
                    ))
                
                conn.commit()
            
            print(f"   ✅ 成功上传")
            print(f"   📅 账单日期: {statement_info.get('statement_date', 'N/A')}")
            print(f"   💳 卡号尾数: {statement_info.get('card_last4', 'N/A')}")
            print(f"   📊 交易数量: {len(transactions)}")
            print(f"   💰 账单金额: RM {statement_info.get('total', 0):,.2f}")
            
            total_transactions += len(transactions)
            success_count += 1
                
        except Exception as e:
            import traceback
            print(f"   ❌ 处理失败: {str(e)}")
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print(f"批量上传完成！")
    print(f"成功: {success_count}/{len(files)} 个账单")
    print(f"总交易数: {total_transactions}")
    print("=" * 80)
    
    # 显示客户信用卡信息
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, bank_name, card_number_last4, credit_limit
            FROM credit_cards
            WHERE customer_id = ?
        ''', (customer_id,))
        cards = cursor.fetchall()
        
        if cards:
            print(f"\n客户信用卡列表:")
            for card in cards:
                print(f"  • {card[1]} ****{card[2]} (限额: RM {card[3]:,.2f})")

if __name__ == "__main__":
    batch_upload_ambank_islamic()
