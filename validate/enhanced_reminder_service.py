"""
增强的提醒服务
Enhanced Reminder Service with:
- Statement date + 3 days reminder (提醒客户上传账单)
- Due date - 3 days reminder (提醒付款)
"""

from db.database import get_db
from datetime import datetime, timedelta
import schedule

class EnhancedReminderService:
    
    def create_statement_reminder(self, statement_id, card_id, customer_id, statement_date):
        """
        创建账单上传提醒（statement date + 3天）
        """
        # 计算提醒日期
        stmt_date = datetime.strptime(statement_date, '%Y-%m-%d')
        reminder_date = stmt_date + timedelta(days=3)
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO statement_reminders 
                (statement_id, card_id, customer_id, statement_date, reminder_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (statement_id, card_id, customer_id, statement_date, reminder_date.strftime('%Y-%m-%d')))
            
            conn.commit()
            return cursor.lastrowid
    
    def create_payment_reminder(self, statement_id, card_id, due_date, amount_due):
        """
        创建付款提醒（due date - 3天）
        """
        # 计算提醒日期
        due = datetime.strptime(due_date, '%Y-%m-%d')
        reminder_date = due - timedelta(days=3)
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 检查是否已存在
            cursor.execute('''
                SELECT id FROM reminders 
                WHERE statement_id = ?
            ''', (statement_id,))
            
            if cursor.fetchone():
                return None  # 已存在
            
            cursor.execute('''
                INSERT INTO reminders 
                (statement_id, reminder_date, is_sent, is_paid)
                VALUES (?, ?, 0, 0)
            ''', (statement_id, reminder_date.strftime('%Y-%m-%d')))
            
            conn.commit()
            return cursor.lastrowid
    
    def check_statement_upload_reminders(self):
        """
        检查并发送账单上传提醒
        """
        today = datetime.now().date()
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    sr.*,
                    c.name as customer_name,
                    c.email,
                    cc.bank_name,
                    cc.card_type,
                    cc.last_four
                FROM statement_reminders sr
                JOIN customers c ON sr.customer_id = c.id
                JOIN credit_cards cc ON sr.card_id = cc.id
                WHERE sr.reminder_date = ? 
                AND sr.is_sent = 0 
                AND sr.is_uploaded = 0
            ''', (today.strftime('%Y-%m-%d'),))
            
            reminders = cursor.fetchall()
            
            for reminder in reminders:
                self._send_statement_upload_reminder(reminder)
                
                # 标记为已发送
                cursor.execute('''
                    UPDATE statement_reminders 
                    SET is_sent = 1 
                    WHERE id = ?
                ''', (reminder['id'],))
            
            conn.commit()
            return len(reminders)
    
    def check_payment_reminders(self):
        """
        检查并发送付款提醒（due date - 3天）
        """
        today = datetime.now().date()
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    r.*,
                    s.due_date,
                    s.total_amount,
                    c.name as customer_name,
                    c.email,
                    cc.bank_name,
                    cc.card_type,
                    cc.last_four
                FROM reminders r
                JOIN statements s ON r.statement_id = s.id
                JOIN credit_cards cc ON s.card_id = cc.id
                JOIN customers cu ON cc.customer_id = cu.id
                JOIN customers c ON cu.id = c.id
                WHERE r.reminder_date = ? 
                AND r.is_sent = 0 
                AND r.is_paid = 0
            ''', (today.strftime('%Y-%m-%d'),))
            
            reminders = cursor.fetchall()
            
            for reminder in reminders:
                self._send_payment_reminder(reminder)
                
                # 标记为已发送
                cursor.execute('''
                    UPDATE reminders 
                    SET is_sent = 1 
                    WHERE id = ?
                ''', (reminder['id'],))
            
            conn.commit()
            return len(reminders)
    
    def _send_statement_upload_reminder(self, reminder):
        """
        发送账单上传提醒
        """
        message = f"""
        ╔════════════════════════════════════════════════════╗
        ║     📋 信用卡账单上传提醒 | STATEMENT UPLOAD      ║
        ╚════════════════════════════════════════════════════╝
        
        客户: {reminder['customer_name']}
        银行: {reminder['bank_name']}
        卡号: **** {reminder['last_four']}
        账单日期: {reminder['statement_date']}
        
        ⏰ 请记得上传本月的信用卡账单，以便我们为您分析并分类交易！
        
        📤 上传账单后，我们将为您：
        ✓ 自动分类消费和付款交易
        ✓ 计算供应商手续费
        ✓ 追踪信用卡积分
        ✓ 生成月度分析报告
        ✓ 提供优化建议
        
        ═══════════════════════════════════════════════════════
        """
        print(message)
        
        # TODO: 集成实际的邮件/SMS发送
        # email_service.send_email(reminder['email'], "账单上传提醒", message)
    
    def _send_payment_reminder(self, reminder):
        """
        发送付款提醒
        """
        message = f"""
        ╔════════════════════════════════════════════════════╗
        ║     💳 信用卡付款提醒 | PAYMENT REMINDER         ║
        ╚════════════════════════════════════════════════════╝
        
        客户: {reminder['customer_name']}
        银行: {reminder['bank_name']}
        卡号: **** {reminder['last_four']}
        
        应付金额: RM {reminder['total_amount']:.2f}
        到期日期: {reminder['due_date']}
        
        ⚠️ 距离到期日还有3天！请尽快安排付款以避免：
        • 高额罚款和利息
        • 信用评分下降
        • 影响DSR和未来贷款批准
        
        📤 付款后请上传收据，我们会为您记录并用于扣税准备。
        
        ═══════════════════════════════════════════════════════
        """
        print(message)
        
        # TODO: 集成实际的邮件/SMS发送
        # email_service.send_email(reminder['email'], "付款提醒", message)
    
    def mark_statement_uploaded(self, statement_id):
        """
        标记账单已上传
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE statement_reminders 
                SET is_uploaded = 1 
                WHERE statement_id = ?
            ''', (statement_id,))
            
            conn.commit()
            return True
    
    def get_pending_statement_reminders(self, customer_id=None):
        """
        获取待处理的账单上传提醒
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            if customer_id:
                cursor.execute('''
                    SELECT 
                        sr.*,
                        c.name as customer_name,
                        cc.bank_name,
                        cc.card_type,
                        cc.last_four
                    FROM statement_reminders sr
                    JOIN customers c ON sr.customer_id = c.id
                    JOIN credit_cards cc ON sr.card_id = cc.id
                    WHERE sr.customer_id = ? AND sr.is_uploaded = 0
                    ORDER BY sr.reminder_date
                ''', (customer_id,))
            else:
                cursor.execute('''
                    SELECT 
                        sr.*,
                        c.name as customer_name,
                        cc.bank_name,
                        cc.card_type,
                        cc.last_four
                    FROM statement_reminders sr
                    JOIN customers c ON sr.customer_id = c.id
                    JOIN credit_cards cc ON sr.card_id = cc.id
                    WHERE sr.is_uploaded = 0
                    ORDER BY sr.reminder_date
                ''')
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_pending_payment_reminders(self, customer_id=None):
        """
        获取待处理的付款提醒
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            if customer_id:
                cursor.execute('''
                    SELECT 
                        r.*,
                        s.due_date,
                        s.total_amount,
                        c.name as customer_name,
                        cc.bank_name,
                        cc.card_type,
                        cc.last_four
                    FROM reminders r
                    JOIN statements s ON r.statement_id = s.id
                    JOIN credit_cards cc ON s.card_id = cc.id
                    JOIN customers c ON cc.customer_id = c.id
                    WHERE c.id = ? AND r.is_paid = 0
                    ORDER BY s.due_date
                ''', (customer_id,))
            else:
                cursor.execute('''
                    SELECT 
                        r.*,
                        s.due_date,
                        s.total_amount,
                        c.name as customer_name,
                        cc.bank_name,
                        cc.card_type,
                        cc.last_four
                    FROM reminders r
                    JOIN statements s ON r.statement_id = s.id
                    JOIN credit_cards cc ON s.card_id = cc.id
                    JOIN customers c ON cc.customer_id = c.id
                    WHERE r.is_paid = 0
                    ORDER BY s.due_date
                ''')
            
            return [dict(row) for row in cursor.fetchall()]


# 便捷函数
def create_upload_reminder(statement_id, card_id, customer_id, statement_date):
    service = EnhancedReminderService()
    return service.create_statement_reminder(statement_id, card_id, customer_id, statement_date)

def create_pay_reminder(statement_id, card_id, due_date, amount):
    service = EnhancedReminderService()
    return service.create_payment_reminder(statement_id, card_id, due_date, amount)

def check_all_reminders():
    service = EnhancedReminderService()
    upload_count = service.check_statement_upload_reminders()
    payment_count = service.check_payment_reminders()
    return {'upload_reminders': upload_count, 'payment_reminders': payment_count}
