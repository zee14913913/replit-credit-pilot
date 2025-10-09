"""
咨询预约系统
客户接受建议后预约见面/通话
"""

from db.database import get_db
from datetime import datetime
import json

class ConsultationBooking:
    
    def create_consultation_request(self, customer_id, suggestion_id, preferred_method='meeting', preferred_date=None, notes=None):
        """
        创建咨询预约请求
        
        Args:
            customer_id: 客户ID
            suggestion_id: 优化建议ID
            preferred_method: 'meeting'(见面) 或 'call'(通话)
            preferred_date: 客户偏好的日期时间
            notes: 客户备注
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 获取建议详情
            cursor.execute('''
                SELECT * FROM financial_optimization_suggestions
                WHERE id = ? AND customer_id = ?
            ''', (suggestion_id, customer_id))
            
            suggestion = cursor.fetchone()
            if not suggestion:
                return None
            
            suggestion = dict(suggestion)
            
            # 创建咨询请求
            cursor.execute('''
                INSERT INTO consultation_requests
                (customer_id, suggestion_id, preferred_contact_method, preferred_date, customer_notes, status)
                VALUES (?, ?, ?, ?, ?, 'pending')
            ''', (
                customer_id,
                suggestion_id,
                preferred_method,
                preferred_date or datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                notes
            ))
            
            request_id = cursor.lastrowid
            
            # 更新建议状态为"客户感兴趣"
            cursor.execute('''
                UPDATE financial_optimization_suggestions
                SET status = 'consultation_requested'
                WHERE id = ?
            ''', (suggestion_id,))
            
            conn.commit()
            
            return {
                'request_id': request_id,
                'customer_id': customer_id,
                'suggestion': suggestion,
                'preferred_method': preferred_method,
                'preferred_date': preferred_date,
                'status': 'pending',
                'message': f"咨询预约已提交！我们会尽快与您联系安排{'见面' if preferred_method == 'meeting' else '通话'}。"
            }
    
    def get_pending_consultations(self):
        """
        获取所有待处理的咨询请求
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    cr.*,
                    c.name as customer_name,
                    c.email,
                    c.phone,
                    fos.suggestion_type,
                    fos.estimated_savings,
                    fos.suggestion_details
                FROM consultation_requests cr
                JOIN customers c ON cr.customer_id = c.id
                JOIN financial_optimization_suggestions fos ON cr.suggestion_id = fos.id
                WHERE cr.status = 'pending'
                ORDER BY cr.created_at DESC
            ''')
            
            return [dict(row) for row in cursor.fetchall()]
    
    def confirm_consultation(self, request_id, confirmed_date, meeting_location=None):
        """
        确认咨询安排
        
        Args:
            request_id: 咨询请求ID
            confirmed_date: 确认的日期时间
            meeting_location: 见面地点（如果是见面）
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE consultation_requests
                SET status = 'confirmed',
                    confirmed_date = ?,
                    meeting_location = ?
                WHERE id = ?
            ''', (confirmed_date, meeting_location, request_id))
            
            conn.commit()
            
            return {
                'request_id': request_id,
                'status': 'confirmed',
                'confirmed_date': confirmed_date,
                'meeting_location': meeting_location
            }
    
    def complete_consultation(self, request_id, outcome_notes, proceed_with_service=False):
        """
        完成咨询（谈话后）
        
        Args:
            request_id: 咨询请求ID
            outcome_notes: 咨询结果备注
            proceed_with_service: 客户是否决定继续服务
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE consultation_requests
                SET status = 'completed',
                    outcome_notes = ?,
                    proceed_with_service = ?
                WHERE id = ?
            ''', (outcome_notes, 1 if proceed_with_service else 0, request_id))
            
            # 如果客户决定继续，更新建议状态
            if proceed_with_service:
                cursor.execute('''
                    UPDATE financial_optimization_suggestions
                    SET status = 'contract_pending'
                    WHERE id = (SELECT suggestion_id FROM consultation_requests WHERE id = ?)
                ''', (request_id,))
            
            conn.commit()
            
            return {
                'request_id': request_id,
                'status': 'completed',
                'proceed_with_service': proceed_with_service
            }
    
    def get_customer_consultations(self, customer_id):
        """
        获取客户的所有咨询记录
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    cr.*,
                    fos.suggestion_type,
                    fos.estimated_savings
                FROM consultation_requests cr
                JOIN financial_optimization_suggestions fos ON cr.suggestion_id = fos.id
                WHERE cr.customer_id = ?
                ORDER BY cr.created_at DESC
            ''', (customer_id,))
            
            return [dict(row) for row in cursor.fetchall()]


# 便捷函数
def book_consultation(customer_id, suggestion_id, method='meeting', date=None, notes=None):
    """创建咨询预约"""
    booking = ConsultationBooking()
    return booking.create_consultation_request(customer_id, suggestion_id, method, date, notes)

def get_pending_requests():
    """获取待处理的咨询请求"""
    booking = ConsultationBooking()
    return booking.get_pending_consultations()
