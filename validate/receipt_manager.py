"""
付款收据管理服务
Manage payment receipts upload and storage
"""

from db.database import get_db
from datetime import datetime
import os
from pathlib import Path

class ReceiptManager:
    
    def __init__(self, upload_folder='static/uploads/receipts'):
        self.upload_folder = upload_folder
        Path(upload_folder).mkdir(parents=True, exist_ok=True)
    
    def upload_receipt(self, statement_id, card_id, customer_id, receipt_file, payment_amount, payment_date):
        """
        上传付款收据
        """
        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_extension = os.path.splitext(receipt_file.filename)[1]
        filename = f"receipt_{customer_id}_{statement_id}_{timestamp}{file_extension}"
        
        # 保存文件
        file_path = os.path.join(self.upload_folder, filename)
        receipt_file.save(file_path)
        
        # 保存到数据库
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO payment_receipts 
                (statement_id, card_id, customer_id, receipt_file_path, payment_amount, payment_date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (statement_id, card_id, customer_id, file_path, payment_amount, payment_date))
            
            receipt_id = cursor.lastrowid
            conn.commit()
            
            return {
                'receipt_id': receipt_id,
                'file_path': file_path,
                'filename': filename
            }
    
    def get_statement_receipts(self, statement_id):
        """
        获取账单的所有收据
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    pr.*,
                    cc.bank_name,
                    cc.card_type,
                    cc.last_four
                FROM payment_receipts pr
                JOIN credit_cards cc ON pr.card_id = cc.id
                WHERE pr.statement_id = ?
                ORDER BY pr.payment_date DESC
            ''', (statement_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_customer_receipts_for_tax(self, customer_id, month):
        """
        获取客户某月的所有收据（用于做账扣税）
        
        Args:
            customer_id: 客户ID
            month: 月份，格式 'YYYY-MM'
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    pr.*,
                    cc.bank_name,
                    cc.card_type,
                    s.statement_date,
                    s.due_date
                FROM payment_receipts pr
                JOIN credit_cards cc ON pr.card_id = cc.id
                JOIN statements s ON pr.statement_id = s.id
                WHERE pr.customer_id = ? 
                AND strftime('%Y-%m', pr.payment_date) = ?
                ORDER BY pr.payment_date
            ''', (customer_id, month))
            
            receipts = [dict(row) for row in cursor.fetchall()]
            
            # 计算总金额
            total_payments = sum(r['payment_amount'] for r in receipts)
            
            return {
                'receipts': receipts,
                'total_payments': total_payments,
                'receipt_count': len(receipts),
                'month': month
            }
    
    def mark_statement_paid(self, statement_id):
        """
        标记账单已付款（当收据上传后）
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 更新相关提醒为已付款
            cursor.execute('''
                UPDATE reminders 
                SET is_paid = 1
                WHERE statement_id = ?
            ''', (statement_id,))
            
            conn.commit()
            return True
    
    def get_monthly_tax_report(self, customer_id, month):
        """
        生成月度扣税报告
        """
        receipt_data = self.get_customer_receipts_for_tax(customer_id, month)
        
        # 获取客户信息
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
            customer = dict(cursor.fetchone())
        
        report = {
            'customer': customer,
            'month': month,
            'receipts': receipt_data['receipts'],
            'total_payments': receipt_data['total_payments'],
            'receipt_count': receipt_data['receipt_count'],
            'summary': f"客户 {customer['name']} 在 {month} 共上传 {receipt_data['receipt_count']} 张付款收据，总金额 RM {receipt_data['total_payments']:.2f}"
        }
        
        return report


def upload_payment_receipt(statement_id, card_id, customer_id, file, amount, date):
    """便捷函数：上传收据"""
    manager = ReceiptManager()
    return manager.upload_receipt(statement_id, card_id, customer_id, file, amount, date)

def get_receipts(statement_id):
    """便捷函数：获取收据"""
    manager = ReceiptManager()
    return manager.get_statement_receipts(statement_id)

def get_tax_report(customer_id, month):
    """便捷函数：获取扣税报告"""
    manager = ReceiptManager()
    return manager.get_monthly_tax_report(customer_id, month)
