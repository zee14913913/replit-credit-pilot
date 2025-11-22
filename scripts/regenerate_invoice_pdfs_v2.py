#!/usr/bin/env python3
"""
基于monthly_statements重新生成所有供应商发票PDF
Regenerate all supplier invoice PDFs based on monthly_statements
"""

import sqlite3
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.invoice_generator import SupplierInvoiceGenerator
from db.database import get_db


def regenerate_invoices_from_monthly_ledger():
    """从infinite_monthly_ledger重新生成所有供应商发票PDF"""
    
    print("="*80)
    print("基于月度账本重新生成所有供应商发票PDF")
    print("="*80)
    
    generator = SupplierInvoiceGenerator()
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 获取所有有INFINITE支出的月度记录
        cursor.execute('''
            SELECT DISTINCT
                iml.month_start,
                iml.card_id,
                iml.customer_id,
                c.name as customer_name,
                c.customer_code,
                cc.bank_name,
                cc.card_number_last4,
                iml.infinite_spend,
                iml.supplier_fee
            FROM infinite_monthly_ledger iml
            JOIN customers c ON iml.customer_id = c.id
            JOIN credit_cards cc ON iml.card_id = cc.id
            WHERE iml.infinite_spend > 0
            ORDER BY iml.month_start, c.name, cc.bank_name
        ''')
        
        ledger_records = cursor.fetchall()
        
        print(f"\n找到 {len(ledger_records)} 条月度账本记录（有INFINITE支出）")
        print(f"开始生成发票...\n")
        
        success_count = 0
        skip_count = 0
        error_count = 0
        
        for record in ledger_records:
            month_start = record['month_start']
            card_id = record['card_id']
            customer_id = record['customer_id']
            customer_name = record['customer_name']
            customer_code = record['customer_code']
            bank_name = record['bank_name']
            last4 = record['card_number_last4']
            
            print(f"\n📅 处理: {month_start} | {customer_name} | {bank_name} *{last4}")
            
            # 获取该月该卡的monthly_statement_id（月度格式：YYYY-MM）
            year_month = month_start[:7]  # 从"2025-05-01"提取"2025-05"
            cursor.execute('''
                SELECT id FROM monthly_statements
                WHERE customer_id = ? AND statement_month = ?
            ''', (customer_id, year_month))
            
            ms_row = cursor.fetchone()
            if not ms_row:
                print(f"   ⚠️  找不到对应的monthly_statement，跳过")
                skip_count += 1
                continue
            
            monthly_statement_id = ms_row['id']
            
            # 获取该月该卡的所有INFINITE交易（按supplier分组）
            cursor.execute('''
                SELECT 
                    supplier_name,
                    transaction_date,
                    description,
                    amount,
                    supplier_fee
                FROM transactions
                WHERE monthly_statement_id = ?
                  AND card_last4 = ?
                  AND owner_flag IN ('0', 'infinite')
                  AND supplier_name IS NOT NULL
                  AND supplier_name != ''
                ORDER BY supplier_name, transaction_date
            ''', (monthly_statement_id, last4))
            
            transactions = cursor.fetchall()
            
            if not transactions:
                print(f"   ⚠️  没有找到INFINITE交易，跳过")
                skip_count += 1
                continue
            
            print(f"   找到 {len(transactions)} 笔INFINITE交易")
            
            # 按supplier分组
            suppliers_dict = {}
            for txn in transactions:
                supplier = txn['supplier_name']
                if supplier not in suppliers_dict:
                    suppliers_dict[supplier] = []
                
                suppliers_dict[supplier].append({
                    'transaction_date': txn['transaction_date'],
                    'transaction_details': txn['description'],
                    'amount': txn['amount'],
                    'supplier_fee': txn['supplier_fee'] or 0
                })
            
            print(f"   涉及 {len(suppliers_dict)} 个供应商")
            
            # 为每个supplier生成发票
            for supplier_name, supplier_txns in suppliers_dict.items():
                try:
                    # 生成发票编号
                    year_month = month_start[:7]
                    safe_supplier = supplier_name.upper().replace(' ', '')[:10]
                    invoice_number = f"INF-{year_month.replace('-', '')}-{safe_supplier}"
                    
                    # 检查PDF是否已存在
                    cursor.execute('''
                        SELECT pdf_path FROM supplier_invoices
                        WHERE customer_id = ? 
                          AND invoice_date LIKE ?
                          AND supplier_name = ?
                    ''', (customer_id, f'{year_month}%', supplier_name))
                    
                    existing = cursor.fetchone()
                    if existing and existing['pdf_path']:
                        pdf_file = os.path.join('static/uploads', existing['pdf_path'])
                        if os.path.exists(pdf_file):
                            print(f"      ✅ {supplier_name} - PDF已存在，跳过")
                            skip_count += 1
                            continue
                    
                    # 生成PDF
                    invoice_date = month_start  # 使用月初作为发票日期
                    pdf_path = generator.generate_invoice(
                        supplier_name=supplier_name,
                        transactions=supplier_txns,
                        customer_name=customer_name,
                        customer_code=customer_code,
                        statement_date=invoice_date,
                        invoice_number=invoice_number
                    )
                    
                    # 计算总额
                    total_amount = sum(t['amount'] for t in supplier_txns)
                    total_fee = sum(t['supplier_fee'] for t in supplier_txns)
                    
                    # 更新或插入数据库
                    cursor.execute('''
                        SELECT id FROM supplier_invoices
                        WHERE customer_id = ? 
                          AND invoice_date LIKE ?
                          AND supplier_name = ?
                    ''', (customer_id, f'{year_month}%', supplier_name))
                    
                    if cursor.fetchone():
                        # 更新
                        cursor.execute('''
                            UPDATE supplier_invoices
                            SET pdf_path = ?,
                                total_amount = ?,
                                supplier_fee = ?,
                                invoice_number = ?
                            WHERE customer_id = ? 
                              AND invoice_date LIKE ?
                              AND supplier_name = ?
                        ''', (pdf_path, total_amount, total_fee, invoice_number,
                              customer_id, f'{year_month}%', supplier_name))
                    else:
                        # 插入（使用monthly_statement_id而不是旧的statement_id）
                        cursor.execute('''
                            INSERT INTO supplier_invoices
                            (customer_id, statement_id, supplier_name, invoice_number,
                             total_amount, supplier_fee, invoice_date, pdf_path)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (customer_id, monthly_statement_id, supplier_name, invoice_number,
                              total_amount, total_fee, invoice_date, pdf_path))
                    
                    conn.commit()
                    
                    print(f"      ✅ {supplier_name} - RM {total_amount:.2f} (费用: RM {total_fee:.2f})")
                    success_count += 1
                    
                except Exception as e:
                    print(f"      ❌ {supplier_name} - 生成失败: {e}")
                    error_count += 1
                    import traceback
                    traceback.print_exc()
                    continue
        
        print("\n" + "="*80)
        print("发票PDF生成完成！")
        print("="*80)
        print(f"✅ 成功生成: {success_count} 张")
        print(f"⏭️  跳过（已存在）: {skip_count} 个")
        print(f"❌ 生成失败: {error_count} 张")
        print("="*80)


if __name__ == "__main__":
    regenerate_invoices_from_monthly_ledger()
