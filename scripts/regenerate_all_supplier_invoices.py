#!/usr/bin/env python3
"""
基于填充好supplier_name的数据重新生成所有供应商发票
Regenerate all supplier invoices from populated transaction data
"""

import sqlite3
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.invoice_generator import SupplierInvoiceGenerator
from db.database import get_db


def regenerate_all_invoices():
    """重新生成所有供应商发票"""
    
    print("="*80)
    print("重新生成所有供应商发票（按supplier分组）")
    print("="*80)
    
    generator = SupplierInvoiceGenerator()
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 步骤1：获取所有有supplier_name的INFINITE交易，按customer + month + supplier + DATE分组
        print("\n步骤1: 查询所有INFINITE交易（按客户+月份+供应商+日期分组）...")
        cursor.execute('''
            SELECT 
                ms.customer_id,
                ms.statement_month,
                t.supplier_name,
                t.transaction_date,
                c.name as customer_name,
                c.customer_code,
                SUM(t.amount) as total_amount,
                COUNT(*) as txn_count
            FROM transactions t
            JOIN monthly_statements ms ON t.monthly_statement_id = ms.id
            JOIN customers c ON ms.customer_id = c.id
            WHERE t.owner_flag = 'INFINITE'
              AND t.supplier_name IS NOT NULL
              AND t.supplier_name != ''
            GROUP BY ms.customer_id, ms.statement_month, t.supplier_name, t.transaction_date
            ORDER BY c.name, ms.statement_month, t.supplier_name, t.transaction_date
        ''')
        
        invoice_groups = cursor.fetchall()
        
        print(f"   找到 {len(invoice_groups)} 个发票组（客户+月份+供应商+日期）")
        
        if len(invoice_groups) == 0:
            print("   没有需要处理的记录，退出")
            return
        
        # 步骤2：为每个日期的供应商交易生成单独发票
        print("\n步骤2: 为每个日期的供应商交易生成单独发票...")
        total_invoices = 0
        total_pdfs = 0
        errors = 0
        
        for group in invoice_groups:
            customer_id = group['customer_id']
            statement_month = group['statement_month']
            supplier_name = group['supplier_name']
            transaction_date = group['transaction_date']
            customer_name = group['customer_name']
            customer_code = group['customer_code']
            group_total = group['total_amount']
            txn_count = group['txn_count']
            
            print(f"\n   📄 {transaction_date} | {customer_name} | {supplier_name} | RM{group_total:.2f} ({txn_count} 笔)")
            
            # 获取该客户该月所有monthly_statement_id
            cursor.execute('''
                SELECT id FROM monthly_statements
                WHERE customer_id = ? AND statement_month = ?
                LIMIT 1
            ''', (customer_id, statement_month))
            
            ms_row = cursor.fetchone()
            if not ms_row:
                print(f"      ⚠️  找不到monthly_statement，跳过")
                errors += 1
                continue
            
            monthly_statement_id = ms_row['id']
            
            # 获取该客户该月该供应商该日期的所有INFINITE交易
            cursor.execute('''
                SELECT 
                    t.transaction_date,
                    t.description,
                    t.amount
                FROM transactions t
                JOIN monthly_statements ms ON t.monthly_statement_id = ms.id
                WHERE ms.customer_id = ?
                  AND ms.statement_month = ?
                  AND t.owner_flag = 'INFINITE'
                  AND t.supplier_name = ?
                  AND t.transaction_date = ?
                ORDER BY t.transaction_date
            ''', (customer_id, statement_month, supplier_name, transaction_date))
            
            transactions = cursor.fetchall()
            
            # 准备发票交易列表
            supplier_txns = []
            for txn in transactions:
                supplier_txns.append({
                    'transaction_date': txn['transaction_date'],
                    'transaction_details': txn['description'],
                    'amount': txn['amount'],
                    'supplier_fee': txn['amount'] * 0.01  # 1%费用
                })
            try:
                # 生成发票编号（包含日期以确保唯一性）
                # 格式: INF-YYYYMMDD-SUPPLIER
                date_str = transaction_date.replace('-', '').replace(' ', '')[:8]  # YYYYMMDD
                safe_supplier = supplier_name.upper().replace(' ', '')[:10]
                invoice_number = f"INF-{date_str}-{safe_supplier}"
                
                # 生成PDF（使用实际交易日期）
                pdf_path = generator.generate_invoice(
                    supplier_name=supplier_name,
                    transactions=supplier_txns,
                    customer_name=customer_name,
                    customer_code=customer_code,
                    statement_date=transaction_date,  # 使用实际交易日期
                    invoice_number=invoice_number
                )
                
                # 计算总额
                total_amount = sum(t['amount'] for t in supplier_txns)
                total_fee = sum(t['supplier_fee'] for t in supplier_txns)
                
                # 检查是否已存在（使用invoice_number作为唯一标识）
                cursor.execute('''
                    SELECT id FROM supplier_invoices
                    WHERE invoice_number = ?
                ''', (invoice_number,))
                
                if cursor.fetchone():
                    # 更新
                    cursor.execute('''
                        UPDATE supplier_invoices
                        SET pdf_path = ?,
                            total_amount = ?,
                            supplier_fee = ?,
                            invoice_date = ?
                        WHERE invoice_number = ?
                    ''', (pdf_path, total_amount, total_fee, transaction_date, invoice_number))
                else:
                    # 插入
                    cursor.execute('''
                        INSERT INTO supplier_invoices
                        (customer_id, monthly_statement_id, supplier_name, invoice_number,
                         total_amount, supplier_fee, invoice_date, pdf_path)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (customer_id, monthly_statement_id, supplier_name, invoice_number,
                          total_amount, total_fee, transaction_date, pdf_path))
                
                conn.commit()
                
                print(f"      ✅ RM {total_amount:.2f} (费用: RM {total_fee:.2f}) - PDF已生成")
                total_invoices += 1
                total_pdfs += 1
                
            except Exception as e:
                print(f"      ❌ 生成失败: {e}")
                errors += 1
                import traceback
                traceback.print_exc()
                continue
        
        # 步骤3：验证结果
        print("\n步骤3: 验证结果...")
        cursor.execute('SELECT COUNT(*) as cnt FROM supplier_invoices')
        final_count = cursor.fetchone()['cnt']
        
        cursor.execute('''
            SELECT COUNT(*) as cnt FROM supplier_invoices
            WHERE pdf_path IS NOT NULL AND pdf_path != ''
        ''')
        with_pdf_count = cursor.fetchone()['cnt']
        
        print(f"   📊 发票记录总数: {final_count}")
        print(f"   ✅ 有PDF的发票: {with_pdf_count}")
        print(f"   📄 PDF生成率: {(with_pdf_count/final_count*100):.1f}%" if final_count > 0 else "   N/A")
        
        print("\n" + "="*80)
        print("✅ 发票重新生成完成！")
        print("="*80)
        print("📊 总结:")
        print(f"   - 处理发票组: {len(invoice_groups)} 个")
        print(f"   - 生成发票: {total_invoices} 张")
        print(f"   - 生成PDF: {total_pdfs} 个")
        print(f"   - 错误数: {errors} 个")
        print("="*80)


if __name__ == "__main__":
    regenerate_all_invoices()
