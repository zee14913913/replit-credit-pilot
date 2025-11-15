"""
INFINITE GZ 信用卡系统 - Supplier Invoice 自动生成器
按照任务书第7节规范：每笔Supplier消费必须生成Invoice

功能：
1. 自动生成Invoice编号
2. 计算1% Fee
3. 生成PDF/HTML格式
4. 自动存入数据库
"""

import sqlite3
import os
from datetime import datetime
from typing import Dict, Optional, List
import json

DB_PATH = os.path.join(os.path.dirname(__file__), '../db/smart_loan_manager.db')
INVOICE_DIR = os.path.join(os.path.dirname(__file__), '../static/uploads/supplier_invoices/')

class SupplierInvoiceGenerator:
    """Supplier Invoice自动生成器"""
    
    def __init__(self):
        # 确保Invoice目录存在
        os.makedirs(INVOICE_DIR, exist_ok=True)
    
    def get_db_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(DB_PATH)
    
    def generate_invoice_number(
        self, 
        customer_id: int, 
        statement_month: str, 
        supplier_name: str
    ) -> str:
        """
        生成Invoice编号
        格式：INV-{customer_id}-{YYYYMM}-{supplier_abbr}-{seq}
        例如：INV-001-202501-7SL-001
        """
        # Supplier缩写
        supplier_abbr = supplier_name.upper().replace(' ', '')[:6]
        
        # 查询当月该客户该Supplier的Invoice数量
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM supplier_invoices
            WHERE customer_id = ? 
            AND statement_month = ? 
            AND supplier_name = ?
        ''', (customer_id, statement_month, supplier_name))
        
        count = cursor.fetchone()[0]
        seq = count + 1
        
        conn.close()
        
        # 格式化月份（移除横杠）
        month_str = statement_month.replace('-', '')
        
        invoice_number = f"INV-{customer_id:03d}-{month_str}-{supplier_abbr}-{seq:03d}"
        return invoice_number
    
    def create_invoice_from_transaction(
        self, 
        transaction: Dict
    ) -> Optional[int]:
        """
        从交易记录创建Invoice
        
        任务书第7节要求字段：
        - Supplier名称
        - 客户名称/GZ名义
        - 金额
        - 日期
        - 信用卡后四位
        - 1% Fee
        - Statement Month
        """
        # 验证是否为Supplier交易
        if not transaction.get('is_supplier_transaction'):
            return None
        
        if not transaction.get('supplier_name'):
            return None
        
        # 获取客户信息
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT name FROM customers WHERE id = ?', (transaction['customer_id'],))
        customer_row = cursor.fetchone()
        customer_name = customer_row[0] if customer_row else f"Customer {transaction['customer_id']}"
        
        # 生成Invoice编号
        invoice_number = self.generate_invoice_number(
            transaction['customer_id'],
            transaction['statement_month'],
            transaction['supplier_name']
        )
        
        # 计算金额
        amount = abs(transaction['amount'])
        fee_percentage = 0.01
        fee_amount = round(amount * fee_percentage, 2)
        total_amount = round(amount + fee_amount, 2)
        
        # 生成HTML内容
        html_content = self.generate_invoice_html(
            invoice_number=invoice_number,
            customer_name=customer_name,
            supplier_name=transaction['supplier_name'],
            amount=amount,
            fee_amount=fee_amount,
            total_amount=total_amount,
            invoice_date=transaction['date'],
            statement_month=transaction['statement_month'],
            card_last4=transaction['card_last4'],
            bank_name=transaction['bank_name']
        )
        
        # 保存HTML文件
        html_filename = f"{invoice_number}.html"
        html_path = os.path.join(INVOICE_DIR, html_filename)
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # 保存到数据库
        cursor.execute('''
            INSERT INTO supplier_invoices (
                customer_id, transaction_id, supplier_name, invoice_number,
                invoice_date, statement_month, amount, fee_percentage,
                fee_amount, total_amount, card_last4, bank_name,
                file_path, is_generated, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
        ''', (
            transaction['customer_id'],
            transaction.get('id'),
            transaction['supplier_name'],
            invoice_number,
            transaction['date'],
            transaction['statement_month'],
            amount,
            fee_percentage,
            fee_amount,
            total_amount,
            transaction['card_last4'],
            transaction['bank_name'],
            html_path,
            datetime.now()
        ))
        
        invoice_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return invoice_id
    
    def generate_invoice_html(
        self,
        invoice_number: str,
        customer_name: str,
        supplier_name: str,
        amount: float,
        fee_amount: float,
        total_amount: float,
        invoice_date: str,
        statement_month: str,
        card_last4: str,
        bank_name: str
    ) -> str:
        """
        生成Invoice HTML内容
        符合专业Invoice格式
        """
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Invoice {invoice_number}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }}
        .invoice-container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .invoice-header {{
            border-bottom: 3px solid #FF007F;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .company-name {{
            font-size: 28px;
            font-weight: 700;
            color: #000000;
            margin-bottom: 5px;
        }}
        .invoice-title {{
            font-size: 24px;
            font-weight: 600;
            color: #FF007F;
            margin-top: 10px;
        }}
        .invoice-number {{
            font-size: 16px;
            color: #666;
            margin-top: 5px;
        }}
        .info-section {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 30px;
        }}
        .info-block {{
            flex: 1;
        }}
        .info-label {{
            font-weight: 600;
            color: #333;
            margin-bottom: 8px;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .info-value {{
            color: #666;
            margin-bottom: 10px;
            font-size: 15px;
        }}
        .items-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
        }}
        .items-table th {{
            background: #322446;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        .items-table td {{
            padding: 12px;
            border-bottom: 1px solid #e0e0e0;
        }}
        .items-table tr:last-child td {{
            border-bottom: none;
        }}
        .text-right {{
            text-align: right;
        }}
        .totals-section {{
            margin-left: auto;
            width: 300px;
        }}
        .total-row {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #e0e0e0;
        }}
        .total-row.grand-total {{
            background: #322446;
            color: white;
            padding: 15px;
            margin-top: 10px;
            font-size: 18px;
            font-weight: 700;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #e0e0e0;
            text-align: center;
            color: #999;
            font-size: 13px;
        }}
        .highlight {{
            color: #FF007F;
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <div class="invoice-container">
        <!-- Header -->
        <div class="invoice-header">
            <div class="company-name">INFINITE GZ SDN BHD</div>
            <div class="invoice-title">SUPPLIER INVOICE</div>
            <div class="invoice-number">Invoice #: {invoice_number}</div>
        </div>

        <!-- Client & Invoice Info -->
        <div class="info-section">
            <div class="info-block">
                <div class="info-label">Bill To:</div>
                <div class="info-value"><strong>{customer_name}</strong></div>
                <div class="info-value">Statement Month: {statement_month}</div>
                <div class="info-value">Card: {bank_name} ****{card_last4}</div>
            </div>
            <div class="info-block" style="text-align: right;">
                <div class="info-label">Invoice Details:</div>
                <div class="info-value">Date: {invoice_date}</div>
                <div class="info-value">Supplier: <span class="highlight">{supplier_name.upper()}</span></div>
            </div>
        </div>

        <!-- Items Table -->
        <table class="items-table">
            <thead>
                <tr>
                    <th>Description</th>
                    <th class="text-right">Amount (RM)</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>
                        <strong>{supplier_name.upper()}</strong> - Supplier Transaction<br>
                        <small style="color: #999;">Credit Card Purchase via INFINITE GZ</small>
                    </td>
                    <td class="text-right">{amount:,.2f}</td>
                </tr>
                <tr>
                    <td>
                        Management Fee (1%)<br>
                        <small style="color: #999;">INFINITE GZ Service Charge</small>
                    </td>
                    <td class="text-right">{fee_amount:,.2f}</td>
                </tr>
            </tbody>
        </table>

        <!-- Totals -->
        <div class="totals-section">
            <div class="total-row">
                <span>Subtotal:</span>
                <span>RM {amount:,.2f}</span>
            </div>
            <div class="total-row">
                <span>Service Fee (1%):</span>
                <span>RM {fee_amount:,.2f}</span>
            </div>
            <div class="total-row grand-total">
                <span>TOTAL DUE:</span>
                <span>RM {total_amount:,.2f}</span>
            </div>
        </div>

        <!-- Footer -->
        <div class="footer">
            <p><strong>INFINITE GZ SDN BHD</strong></p>
            <p>This is a computer-generated invoice for Supplier transaction management.</p>
            <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>"""
        
        return html
    
    def get_invoice_by_id(self, invoice_id: int) -> Optional[Dict]:
        """获取Invoice详情"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM supplier_invoices WHERE id = ?', (invoice_id,))
        row = cursor.fetchone()
        
        if row:
            columns = [desc[0] for desc in cursor.description]
            invoice = dict(zip(columns, row))
            conn.close()
            return invoice
        
        conn.close()
        return None
    
    def get_customer_invoices(
        self, 
        customer_id: int, 
        statement_month: Optional[str] = None
    ) -> List[Dict]:
        """获取客户的所有Invoice"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        if statement_month:
            cursor.execute('''
                SELECT * FROM supplier_invoices 
                WHERE customer_id = ? AND statement_month = ?
                ORDER BY created_at DESC
            ''', (customer_id, statement_month))
        else:
            cursor.execute('''
                SELECT * FROM supplier_invoices 
                WHERE customer_id = ?
                ORDER BY created_at DESC
            ''', (customer_id,))
        
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        invoices = [dict(zip(columns, row)) for row in rows]
        conn.close()
        
        return invoices


# ========== 工具函数 ==========

def auto_generate_invoices_for_transactions(transactions: List[Dict]) -> List[int]:
    """
    批量为Supplier交易生成Invoice
    返回生成的Invoice ID列表
    """
    generator = SupplierInvoiceGenerator()
    invoice_ids = []
    
    for trans in transactions:
        if trans.get('is_supplier_transaction'):
            invoice_id = generator.create_invoice_from_transaction(trans)
            if invoice_id:
                invoice_ids.append(invoice_id)
    
    return invoice_ids


# ========== 测试代码 ==========

if __name__ == '__main__':
    print("=" * 80)
    print("INFINITE GZ Supplier Invoice生成器测试")
    print("=" * 80)
    
    generator = SupplierInvoiceGenerator()
    
    # 测试：生成Invoice
    print("\n[测试] 为Supplier交易生成Invoice:")
    
    test_transaction = {
        'id': 1,
        'customer_id': 1,
        'date': '2025-01-15',
        'description': '7sl KEDAI RUNCIT',
        'amount': 500.00,
        'is_supplier_transaction': True,
        'supplier_name': '7sl',
        'statement_month': '2025-01',
        'bank_name': 'Maybank',
        'card_last4': '1234'
    }
    
    invoice_id = generator.create_invoice_from_transaction(test_transaction)
    
    if invoice_id:
        print(f"✅ Invoice创建成功！ID: {invoice_id}")
        
        # 获取Invoice详情
        invoice = generator.get_invoice_by_id(invoice_id)
        print(f"\n📄 Invoice详情:")
        print(f"  Invoice编号: {invoice['invoice_number']}")
        print(f"  Supplier: {invoice['supplier_name']}")
        print(f"  金额: RM {invoice['amount']:.2f}")
        print(f"  1% Fee: RM {invoice['fee_amount']:.2f}")
        print(f"  总计: RM {invoice['total_amount']:.2f}")
        print(f"  文件路径: {invoice['file_path']}")
        
        # 检查HTML文件是否生成
        if os.path.exists(invoice['file_path']):
            print(f"\n✅ HTML文件已生成: {os.path.basename(invoice['file_path'])}")
        else:
            print(f"\n❌ HTML文件未找到")
    else:
        print("❌ Invoice创建失败")
    
    print("\n" + "=" * 80)
    print("✅ Supplier Invoice生成器测试完成！")
    print("=" * 80)
