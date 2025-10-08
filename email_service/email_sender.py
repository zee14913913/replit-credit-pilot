"""
Email Notification Service
Send email notifications for uploads, reminders, and alerts
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime
from db.database import get_db

class EmailService:
    """Service for sending email notifications"""
    
    def __init__(self, smtp_host: str = 'smtp.gmail.com', smtp_port: int = 587,
                 smtp_user: Optional[str] = None, smtp_password: Optional[str] = None):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.enabled = bool(smtp_user and smtp_password)
    
    def send_email(self, to_email: str, subject: str, body_html: str, 
                   customer_id: Optional[int] = None, email_type: str = 'general') -> bool:
        """Send an email and log it"""
        
        if not self.enabled:
            print(f"Email service not configured. Would send: {subject} to {to_email}")
            self._log_email(customer_id, to_email, subject, email_type, 'skipped', 
                           'SMTP not configured')
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.smtp_user
            msg['To'] = to_email
            msg['Subject'] = subject
            
            html_part = MIMEText(body_html, 'html')
            msg.attach(html_part)
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            self._log_email(customer_id, to_email, subject, email_type, 'sent')
            return True
            
        except Exception as e:
            error_msg = str(e)
            print(f"Email send error: {error_msg}")
            self._log_email(customer_id, to_email, subject, email_type, 'failed', error_msg)
            return False
    
    def send_upload_notification(self, customer_email: str, customer_name: str, 
                                 validation_result: str, transaction_count: int,
                                 customer_id: int) -> bool:
        """Send notification after statement upload"""
        
        if validation_result == 'PASSED':
            status_color = '#1FAA59'
            status_text = 'Successfully Verified'
            message = f'{transaction_count} transactions were extracted and verified with 100% accuracy.'
        elif validation_result == 'WARNING':
            status_color = '#F59E0B'
            status_text = 'Needs Review'
            message = f'{transaction_count} transactions extracted. Please review for accuracy.'
        else:
            status_color = '#DC2626'
            status_text = 'Verification Failed'
            message = 'Statement could not be verified. Please check and re-upload.'
        
        html = f'''
        <html>
        <body style="font-family: Inter, sans-serif; background: #F8FAFC; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <div style="background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%); padding: 30px; text-align: center;">
                    <h1 style="color: #F5E6C8; margin: 0; font-family: 'Playfair Display', serif;">
                        Smart Credit & Loan Manager
                    </h1>
                </div>
                <div style="padding: 30px;">
                    <h2 style="color: #0F172A; margin-top: 0;">Hi {customer_name},</h2>
                    <p style="color: #475569; font-size: 16px; line-height: 1.6;">
                        Your credit card statement has been processed.
                    </p>
                    <div style="background: {status_color}15; border-left: 4px solid {status_color}; padding: 15px; margin: 20px 0; border-radius: 4px;">
                        <p style="margin: 0; color: {status_color}; font-weight: 600;">
                            Status: {status_text}
                        </p>
                        <p style="margin: 10px 0 0 0; color: #475569;">
                            {message}
                        </p>
                    </div>
                    <p style="color: #475569;">
                        <a href="#" style="color: #1FAA59; text-decoration: none; font-weight: 600;">
                            View Dashboard →
                        </a>
                    </p>
                </div>
                <div style="background: #F8FAFC; padding: 20px; text-align: center; color: #94A3B8; font-size: 12px;">
                    © 2025 Smart Credit & Loan Manager
                </div>
            </div>
        </body>
        </html>
        '''
        
        return self.send_email(customer_email, 'Statement Processed', html, customer_id, 'upload')
    
    def send_reminder_notification(self, customer_email: str, customer_name: str,
                                   bank_name: str, amount: float, due_date: str,
                                   customer_id: int) -> bool:
        """Send payment reminder"""
        
        html = f'''
        <html>
        <body style="font-family: Inter, sans-serif; background: #F8FAFC; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <div style="background: #F59E0B; padding: 30px; text-align: center;">
                    <h1 style="color: white; margin: 0;">Payment Reminder</h1>
                </div>
                <div style="padding: 30px;">
                    <h2 style="color: #0F172A;">Hi {customer_name},</h2>
                    <p style="color: #475569; font-size: 16px;">
                        Your {bank_name} credit card payment is due soon.
                    </p>
                    <div style="background: #FEF3C7; border: 2px solid #F59E0B; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <p style="margin: 0; font-size: 14px; color: #92400E;">Amount Due:</p>
                        <p style="margin: 5px 0; font-size: 32px; font-weight: 700; color: #F59E0B;">
                            RM {amount:,.2f}
                        </p>
                        <p style="margin: 10px 0 0 0; color: #92400E;">Due Date: {due_date}</p>
                    </div>
                    <p style="color: #475569;">
                        Please ensure payment is made before the due date to avoid late fees.
                    </p>
                </div>
            </div>
        </body>
        </html>
        '''
        
        return self.send_email(customer_email, f'Payment Reminder - {bank_name}', 
                             html, customer_id, 'reminder')
    
    def send_budget_alert(self, customer_email: str, customer_name: str,
                         category: str, spent: float, limit: float, utilization: float,
                         customer_id: int) -> bool:
        """Send budget alert notification"""
        
        status = 'exceeded' if utilization >= 100 else 'approaching'
        color = '#DC2626' if utilization >= 100 else '#F59E0B'
        
        html = f'''
        <html>
        <body style="font-family: Inter, sans-serif; background: #F8FAFC; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px;">
                <div style="background: {color}; padding: 30px; text-align: center;">
                    <h1 style="color: white; margin: 0;">Budget Alert</h1>
                </div>
                <div style="padding: 30px;">
                    <h2 style="color: #0F172A;">Hi {customer_name},</h2>
                    <p style="color: #475569;">
                        Your <strong>{category}</strong> spending is {status} the budget limit.
                    </p>
                    <div style="background: {color}15; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <p style="margin: 0; color: {color}; font-size: 24px; font-weight: 700;">
                            {utilization:.0f}% Used
                        </p>
                        <p style="margin: 10px 0 0 0; color: #475569;">
                            Spent: RM {spent:,.2f} / RM {limit:,.2f}
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        '''
        
        return self.send_email(customer_email, f'Budget Alert: {category}', 
                             html, customer_id, 'budget_alert')
    
    def _log_email(self, customer_id: Optional[int], email_to: str, subject: str,
                   email_type: str, status: str, error_message: Optional[str] = None):
        """Log email sending attempt"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO email_log 
                (customer_id, email_to, email_subject, email_type, status, error_message, sent_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (customer_id, email_to, subject, email_type, status, error_message,
                  datetime.now() if status == 'sent' else None))
            conn.commit()
    
    def get_notification_preferences(self, customer_id: int) -> dict:
        """Get customer notification preferences"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM notification_preferences WHERE customer_id = ?
            ''', (customer_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            
            # Create default preferences
            cursor.execute('''
                INSERT INTO notification_preferences (customer_id)
                VALUES (?)
            ''', (customer_id,))
            conn.commit()
            return {
                'email_enabled': 1,
                'upload_notifications': 1,
                'reminder_notifications': 1,
                'budget_alerts': 1,
                'anomaly_alerts': 1
            }
