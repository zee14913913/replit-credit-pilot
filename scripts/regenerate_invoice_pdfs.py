#!/usr/bin/env python3
"""
重新生成所有供应商发票PDF
Regenerate all supplier invoice PDFs
"""

import sqlite3
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.invoice_generator import SupplierInvoiceGenerator
from db.database import get_db


def regenerate_all_invoices():
    """为所有供应商发票生成PDF文件"""
    
    print("="*80)
    print("开始重新生成所有供应商发票PDF")
    print("="*80)
    
    generator = SupplierInvoiceGenerator()
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 获取所有发票记录
        cursor.execute('''
            SELECT 
                si.id,
                si.customer_id,
                si.statement_id,
                si.supplier_name,
                si.invoice_number,
                si.total_amount,
                si.supplier_fee,
                si.invoice_date,
                si.pdf_path,
                c.name as customer_name,
                c.customer_code
            FROM supplier_invoices si
            JOIN customers c ON si.customer_id = c.id
            ORDER BY si.invoice_date, si.supplier_name
        ''')
        
        invoices = cursor.fetchall()
        
        print(f"\n找到 {len(invoices)} 张发票记录")
        print(f"开始生成PDF文件...\n")
        
        success_count = 0
        skip_count = 0
        error_count = 0
        
        for invoice in invoices:
            invoice_id = invoice['id']
            customer_id = invoice['customer_id']
            statement_id = invoice['statement_id']
            supplier_name = invoice['supplier_name']
            invoice_number = invoice['invoice_number']
            total_amount = invoice['total_amount']
            supplier_fee = invoice['supplier_fee']
            invoice_date = invoice['invoice_date']
            current_pdf_path = invoice['pdf_path']
            customer_name = invoice['customer_name']
            customer_code = invoice['customer_code']
            
            print(f"📄 处理: {invoice_number} - {supplier_name} (RM {total_amount:.2f})")
            
            # 如果已有PDF路径，检查文件是否存在
            if current_pdf_path:
                full_path = os.path.join('static/uploads', current_pdf_path)
                if os.path.exists(full_path):
                    print(f"   ✅ PDF已存在，跳过: {current_pdf_path}")
                    skip_count += 1
                    continue
            
            try:
                # 获取该发票的所有交易
                cursor.execute('''
                    SELECT 
                        transaction_date,
                        description,
                        amount,
                        supplier_fee
                    FROM transactions
                    WHERE statement_id = ?
                      AND supplier_name = ?
                      AND owner_flag = '0'
                    ORDER BY transaction_date
                ''', (statement_id, supplier_name))
                
                transactions = cursor.fetchall()
                
                if not transactions:
                    print(f"   ⚠️  警告: 没有找到交易记录，跳过")
                    skip_count += 1
                    continue
                
                # 转换为字典格式
                txn_list = []
                for txn in transactions:
                    txn_list.append({
                        'transaction_date': txn['transaction_date'],
                        'transaction_details': txn['description'],
                        'amount': txn['amount'],
                        'supplier_fee': txn['supplier_fee']
                    })
                
                # 生成PDF
                pdf_path = generator.generate_invoice(
                    supplier_name=supplier_name,
                    transactions=txn_list,
                    customer_name=customer_name,
                    customer_code=customer_code,
                    statement_date=invoice_date,
                    invoice_number=invoice_number
                )
                
                # 更新数据库
                cursor.execute('''
                    UPDATE supplier_invoices
                    SET pdf_path = ?
                    WHERE id = ?
                ''', (pdf_path, invoice_id))
                
                conn.commit()
                
                print(f"   ✅ PDF已生成: {pdf_path}")
                success_count += 1
                
            except Exception as e:
                print(f"   ❌ 生成失败: {e}")
                error_count += 1
                continue
        
        print("\n" + "="*80)
        print("发票PDF生成完成！")
        print("="*80)
        print(f"✅ 成功生成: {success_count} 张")
        print(f"⏭️  跳过（已存在）: {skip_count} 张")
        print(f"❌ 生成失败: {error_count} 张")
        print(f"📊 总计: {len(invoices)} 张")
        print("="*80)


if __name__ == "__main__":
    regenerate_all_invoices()
