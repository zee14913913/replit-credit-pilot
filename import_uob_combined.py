#!/usr/bin/env python3
"""
导入UOB Combined Limit账单
客户：CHANG CHOON CHOW
账单：2024-09-21
结构：3张卡共享RM 30,000限额
"""

import sqlite3
from datetime import datetime
from db.database import get_db

def import_uob_2024_09_21():
    """导入UOB 2024-09-21账单（3张卡）"""
    
    # 账单基本信息
    customer_id = 2  # CHANG CHOON CHOW
    bank_name = "UOB"
    statement_date = "2024-09-21"
    payment_due_date = "2024-10-11"
    
    # 账单汇总数据（整体）
    summary = {
        'previous_balance': 3837.96,
        'credits_payments': 4034.07,
        'debits_fees': 79.80,
        'retail_purchase': 2114.16,
        'cash_advance': 0.00,
        'total_balance_due': 1997.85
    }
    
    # 3张卡信息
    cards_info = [
        {
            'card_last4': '2195',
            'card_full': '4141-7000-0404-2195',
            'card_type': 'ONE PLATINUM VISA',
            'cardholder_name': 'JOE CHANG',
            'previous_bal': 1349.40,
            'subtotal': 361.39,
            'min_payment': 50.00
        },
        {
            'card_last4': '4288',
            'card_full': '4377-6601-0051-4288',
            'card_type': 'VISA INFINITE',
            'cardholder_name': 'JOE CHANG',
            'previous_bal': 2008.76,
            'subtotal': 1156.66,
            'min_payment': 232.00
        },
        {
            'card_last4': '9282',
            'card_full': '4599-1499-0138-9282',
            'card_type': 'VISA FLEXI-CREDIT-PLAN',
            'cardholder_name': 'JOE CHANG',
            'previous_bal': 479.80,
            'subtotal': 479.80,
            'min_payment': 479.80
        }
    ]
    
    # 交易明细
    transactions_data = {
        '2195': [
            {'date': '22 AUG', 'description': 'BHPETROL JALAN CHERAS 1 & KUALA LUMPUR MY', 'amount': 93.35, 'type': 'debit'},
            {'date': '27 AUG', 'description': 'BHPETROL KARAK-KL HIGHWAY PAHANG MY', 'amount': 70.10, 'type': 'debit'},
            {'date': '29 AUG', 'description': 'CELCOM RPS136941226 KUALA LUMPUR MY', 'amount': 191.85, 'type': 'debit'},
            {'date': '31 AUG', 'description': 'BHPETROL TAMAN SRI ENDAH KUALA LUMPUR MY', 'amount': 101.44, 'type': 'debit'},
            {'date': '04 SEP', 'description': 'PETRON ML3 JLN KLG LAM KUALA LUMPUR MY', 'amount': 100.76, 'type': 'debit'},
            {'date': '07 SEP', 'description': 'ANNUAL FEE WAIVER', 'amount': 195.00, 'type': 'credit'},
            {'date': '08 SEP', 'description': "PAYMENT REC'D WITH THANKS-PIB", 'amount': 1349.40, 'type': 'credit'},
            {'date': '21 SEP', 'description': 'CASH REBATE OTHERS', 'amount': 0.38, 'type': 'credit'},
            {'date': '21 SEP', 'description': 'CASH REBATE PETROL', 'amount': 0.73, 'type': 'credit'},
        ],
        '4288': [
            {'date': '05 SEP', 'description': 'UOB PL-EPP INSTALMENT 08/24', 'amount': 183.33, 'type': 'debit'},
            {'date': '10 SEP', 'description': 'AIA BHD-RECURRING 7814815A05 MY', 'amount': 506.00, 'type': 'debit'},
            {'date': '11 SEP', 'description': 'AIA BHD-RECURRING 7814846A01 MY', 'amount': 467.33, 'type': 'debit'},
            {'date': '07 SEP', 'description': 'ANNUAL FEE WAIVER', 'amount': 600.00, 'type': 'credit'},
            {'date': '08 SEP', 'description': "PAYMENT REC'D WITH THANKS-PIB", 'amount': 1408.76, 'type': 'credit'},
        ],
        '9282': [
            {'date': '04 SEP', 'description': 'FCP INTEREST 15/60 - 3.990%', 'amount': 79.80, 'type': 'debit'},
            {'date': '04 SEP', 'description': 'FCP INSTALLMENT 15/60 - 3.990%', 'amount': 400.00, 'type': 'debit'},
            {'date': '08 SEP', 'description': "PAYMENT REC'D WITH THANKS-PIB", 'amount': 479.80, 'type': 'credit'},
        ]
    }
    
    print("=" * 80)
    print(f"开始导入UOB Combined Limit账单")
    print(f"客户ID: {customer_id} (CHANG CHOON CHOW)")
    print(f"账单日期: {statement_date}")
    print(f"账单结构: 3张卡 (Combined Limit RM 30,000)")
    print("=" * 80)
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 步骤1：创建/获取3张信用卡记录
        card_ids = {}
        for card_info in cards_info:
            card_last4 = card_info['card_last4']
            
            # 检查卡是否存在
            cursor.execute('''
                SELECT id FROM credit_cards 
                WHERE customer_id = ? AND card_number_last4 = ?
            ''', (customer_id, card_last4))
            
            existing_card = cursor.fetchone()
            
            if existing_card:
                card_id = existing_card[0]
                print(f"✅ 信用卡已存在：#{card_last4} (ID: {card_id})")
            else:
                # 创建新信用卡记录
                cursor.execute('''
                    INSERT INTO credit_cards (customer_id, bank_name, card_number_last4, credit_limit, due_date)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    customer_id,
                    bank_name,
                    card_last4,
                    30000.00,  # Combined Limit
                    11  # 还款日 (11号)
                ))
                card_id = cursor.lastrowid
                print(f"✅ 创建新信用卡：#{card_last4} ({card_info['card_type']}) - ID: {card_id}")
            
            card_ids[card_last4] = card_id
        
        # 步骤2：检查账单是否已存在
        for card_last4, card_id in card_ids.items():
            cursor.execute('''
                SELECT id FROM statements 
                WHERE card_id = ? AND statement_date = ?
            ''', (card_id, statement_date))
            
            existing_stmt = cursor.fetchone()
            if existing_stmt:
                print(f"⚠️ 账单已存在：卡#{card_last4} 的 {statement_date} 账单已导入")
                return
        
        # 步骤3：为每张卡创建账单记录（使用statements表）
        statement_ids = {}
        for card_info in cards_info:
            card_last4 = card_info['card_last4']
            card_id = card_ids[card_last4]
            
            cursor.execute('''
                INSERT INTO statements (
                    card_id, statement_date, statement_total, 
                    file_path, file_type, is_confirmed
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                card_id,
                statement_date,
                card_info['subtotal'],  # 使用各卡的subtotal作为statement total
                'attached_assets/21:09:2024_1761870046750.pdf',
                'PDF',
                1  # 已确认
            ))
            
            statement_id = cursor.lastrowid
            statement_ids[card_last4] = statement_id
            print(f"✅ 创建账单记录：卡#{card_last4} - 账单ID: {statement_id}")
        
        # 步骤4：导入每张卡的交易明细
        total_transactions = 0
        for card_last4, transactions in transactions_data.items():
            card_id = card_ids[card_last4]
            statement_id = statement_ids[card_last4]
            
            for txn in transactions:
                # 转换日期格式 (DD MMM -> 2024-MM-DD)
                date_str = txn['date']
                try:
                    # 解析 "22 AUG" 格式
                    month_map = {
                        'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4,
                        'MAY': 5, 'JUN': 6, 'JUL': 7, 'AUG': 8,
                        'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
                    }
                    parts = date_str.split()
                    day = int(parts[0])
                    month = month_map[parts[1]]
                    
                    # 确定年份（8月之前是2024，9月是账单月）
                    year = 2024
                    
                    transaction_date = f"{year}-{month:02d}-{day:02d}"
                except:
                    transaction_date = statement_date
                
                cursor.execute('''
                    INSERT INTO transactions (
                        statement_id, transaction_date, 
                        description, amount, category
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    statement_id,
                    transaction_date,
                    txn['description'],
                    txn['amount'],
                    '未分类'
                ))
                
                total_transactions += 1
            
            print(f"   ✅ 卡#{card_last4}: 导入 {len(transactions)} 笔交易")
        
        conn.commit()
        
        print("\n" + "=" * 80)
        print("✅ 导入完成！")
        print(f"   - 信用卡数量: {len(card_ids)}")
        print(f"   - 月结账单数量: {len(statement_ids)}")
        print(f"   - 交易总数: {total_transactions}")
        print(f"   - Previous Balance (总): RM {summary['previous_balance']:.2f}")
        print(f"   - Total Balance Due (总): RM {summary['total_balance_due']:.2f}")
        print("=" * 80)

if __name__ == '__main__':
    import_uob_2024_09_21()
