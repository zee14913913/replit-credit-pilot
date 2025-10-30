#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新分类CHEOK JUN YOON的所有交易并更新monthly_statements
"""

import sqlite3
import sys
sys.path.insert(0, '.')

from db.database import get_db
from decimal import Decimal

# Supplier名单（这些是INFINITE分类）
# 根据实际交易数据更新的完整列表
SUPPLIER_KEYWORDS = [
    'INFINITE',
    'GZ SMART',
    'AI SMART',  # 匹配 "AI SMART TECH"
    'HUAWEI',
    'UAWEI',  # 匹配 "H UAWEI" (带空格的情况)
    'TFE',  # 匹配 "TFE PERFUME & COSMETICS"
    'PUCHONG HERBS',
    'GUARDIAN',
    'PHARMACARE',
    'WATSONS',
    'CARING',
    'BIG',
    'RIMAN'  # 匹配 "RIMAN MALAYSIA"
]

def is_supplier_transaction(description):
    """判断是否为Supplier交易"""
    if not description:
        return False
    
    desc_upper = description.upper()
    for keyword in SUPPLIER_KEYWORDS:
        if keyword in desc_upper:
            return True
    return False

def reclassify_transactions(customer_id):
    """重新分类客户的所有交易"""
    print(f"重新分类客户ID {customer_id} 的所有交易...")
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 获取所有信用卡
        cursor.execute("""
            SELECT id, bank_name, card_number_last4
            FROM credit_cards
            WHERE customer_id = ?
        """, (customer_id,))
        
        cards = cursor.fetchall()
        print(f"找到 {len(cards)} 张信用卡")
        
        total_updated = 0
        
        for card in cards:
            card_id = card['id']
            
            # 获取这张卡的所有月度账单
            cursor.execute("""
                SELECT id, statement_month
                FROM monthly_statements
                WHERE customer_id = ?
                AND bank_name = ?
            """, (customer_id, card['bank_name']))
            
            monthly_stmts = cursor.fetchall()
            
            for stmt in monthly_stmts:
                stmt_id = stmt['id']
                
                # 获取这个月度账单的所有交易（从transactions表）
                # 注意：我们需要找到与这个月度账单关联的交易
                # monthly_statements.statement_month格式为YYYY-MM
                year_month = stmt['statement_month']
                year, month = year_month.split('-')
                
                cursor.execute("""
                    SELECT 
                        t.id,
                        t.transaction_date,
                        t.description,
                        t.amount,
                        t.transaction_type,
                        t.owner_flag
                    FROM transactions t
                    JOIN statements s ON t.statement_id = s.id
                    WHERE s.card_id = ?
                    AND strftime('%Y', s.statement_date) = ?
                    AND strftime('%m', s.statement_date) = ?
                """, (card_id, year, month))
                
                transactions = cursor.fetchall()
                
                if not transactions:
                    continue
                
                # 重新分类每个交易
                for trans in transactions:
                    old_classification = trans['owner_flag']
                    
                    if is_supplier_transaction(trans['description']):
                        new_classification = 'INFINITE'
                    else:
                        new_classification = 'OWNER'
                    
                    if old_classification != new_classification:
                        cursor.execute("""
                            UPDATE transactions
                            SET owner_flag = ?
                            WHERE id = ?
                        """, (new_classification, trans['id']))
                        total_updated += 1
                
                # 重新计算monthly_statements的六大分类
                recalculate_monthly_statement(conn, stmt_id)
        
        conn.commit()
        print(f"✓ 共更新了 {total_updated} 笔交易的分类")

def recalculate_monthly_statement(conn, monthly_stmt_id):
    """重新计算某个月度账单的六大分类"""
    cursor = conn.cursor()
    
    # 获取月度账单信息
    cursor.execute("""
        SELECT customer_id, bank_name, statement_month
        FROM monthly_statements
        WHERE id = ?
    """, (monthly_stmt_id,))
    
    stmt_info = cursor.fetchone()
    if not stmt_info:
        return
    
    year_month = stmt_info['statement_month']
    year, month = year_month.split('-')
    
    # 获取这个银行+月份的所有信用卡
    cursor.execute("""
        SELECT id
        FROM credit_cards
        WHERE customer_id = ?
        AND bank_name = ?
    """, (stmt_info['customer_id'], stmt_info['bank_name']))
    
    card_ids = [row['id'] for row in cursor.fetchall()]
    
    if not card_ids:
        return
    
    # 获取所有交易
    placeholders = ','.join('?' * len(card_ids))
    cursor.execute(f"""
        SELECT 
            t.amount,
            t.transaction_type,
            t.owner_flag
        FROM transactions t
        JOIN statements s ON t.statement_id = s.id
        WHERE s.card_id IN ({placeholders})
        AND strftime('%Y', s.statement_date) = ?
        AND strftime('%m', s.statement_date) = ?
    """, (*card_ids, year, month))
    
    transactions = cursor.fetchall()
    
    # 计算六大分类
    owner_expenses = Decimal('0.00')
    owner_payments = Decimal('0.00')
    gz_expenses = Decimal('0.00')
    gz_payments = Decimal('0.00')
    
    for trans in transactions:
        amount = Decimal(str(abs(trans['amount'])))  # 使用绝对值
        trans_type = (trans['transaction_type'] or '').lower()
        classification = trans['owner_flag']
        
        if classification == 'OWNER':
            if trans_type in ['purchase', 'debit', 'dr']:
                owner_expenses += amount
            else:  # payment, credit, cr
                owner_payments += amount
        else:  # INFINITE
            if trans_type in ['purchase', 'debit', 'dr']:
                gz_expenses += amount
            else:  # payment, credit, cr
                gz_payments += amount
    
    # 计算余额
    owner_balance = owner_expenses - owner_payments
    gz_balance = gz_expenses - gz_payments
    
    # 更新monthly_statements
    cursor.execute("""
        UPDATE monthly_statements
        SET 
            owner_expenses = ?,
            owner_payments = ?,
            gz_expenses = ?,
            gz_payments = ?,
            owner_balance = ?,
            gz_balance = ?
        WHERE id = ?
    """, (
        float(owner_expenses),
        float(owner_payments),
        float(gz_expenses),
        float(gz_payments),
        float(owner_balance),
        float(gz_balance),
        monthly_stmt_id
    ))

def main():
    """主函数"""
    print("="*80)
    print("重新分类CHEOK JUN YOON的交易")
    print("="*80)
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 获取客户ID
        cursor.execute("""
            SELECT id, name FROM customers
            WHERE name LIKE '%CHEOK%'
        """)
        
        customer = cursor.fetchone()
        if not customer:
            print("找不到客户")
            return
        
        print(f"客户: {customer['name']} (ID: {customer['id']})")
    
    # 重新分类
    reclassify_transactions(customer['id'])
    
    print("✓ 完成！现在可以运行 recalculate_cheok_monthly_reports.py 查看结果")

if __name__ == '__main__':
    main()
