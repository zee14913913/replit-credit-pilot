"""
分期付款追踪管理系统
Instalment Payment Tracking System

用途：
1. 记录客户的分期付款计划（金额、利率、期限、月供、商品）
2. 追踪每月分期付款记录
3. 生成分期付款报表
4. 计算总月供用于DSR分析
"""

from db.database import get_db
from datetime import datetime, timedelta
import json


class InstalmentTracker:
    """分期付款追踪器"""
    
    def create_instalment_plan(self, customer_id, card_id, plan_details):
        """
        创建新的分期付款计划
        
        参数:
        - customer_id: 客户ID
        - card_id: 信用卡ID
        - plan_details: {
            'product_name': 商品名称,
            'principal_amount': 分期本金,
            'interest_rate': 年利率(%),
            'tenure_months': 分期月数,
            'monthly_payment': 月供金额,
            'start_date': 开始日期,
            'merchant_name': 商家名称(可选)
          }
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 计算总支付金额和利息
            monthly_payment = plan_details['monthly_payment']
            tenure = plan_details['tenure_months']
            total_amount = monthly_payment * tenure
            total_interest = total_amount - plan_details['principal_amount']
            
            # 计算结束日期
            start_date = datetime.strptime(plan_details['start_date'], '%Y-%m-%d')
            end_date = start_date + timedelta(days=tenure * 30)
            
            # 插入分期计划
            cursor.execute('''
                INSERT INTO instalment_plans (
                    customer_id, card_id, product_name, merchant_name,
                    principal_amount, interest_rate, tenure_months,
                    monthly_payment, total_amount, total_interest,
                    start_date, end_date, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
            ''', (
                customer_id, card_id,
                plan_details['product_name'],
                plan_details.get('merchant_name', 'N/A'),
                plan_details['principal_amount'],
                plan_details['interest_rate'],
                tenure,
                monthly_payment,
                total_amount,
                total_interest,
                plan_details['start_date'],
                end_date.strftime('%Y-%m-%d')
            ))
            
            plan_id = cursor.lastrowid
            conn.commit()
            
            # 自动生成所有月供记录
            self._generate_payment_schedule(plan_id, plan_details)
            
            return plan_id
    
    def _generate_payment_schedule(self, plan_id, plan_details):
        """生成分期付款时间表"""
        with get_db() as conn:
            cursor = conn.cursor()
            
            start_date = datetime.strptime(plan_details['start_date'], '%Y-%m-%d')
            tenure = plan_details['tenure_months']
            monthly_payment = plan_details['monthly_payment']
            
            for month in range(1, tenure + 1):
                payment_date = start_date + timedelta(days=month * 30)
                
                cursor.execute('''
                    INSERT INTO instalment_payment_records (
                        plan_id, payment_number, scheduled_date,
                        scheduled_amount, status
                    ) VALUES (?, ?, ?, ?, 'pending')
                ''', (
                    plan_id, month,
                    payment_date.strftime('%Y-%m-%d'),
                    monthly_payment
                ))
            
            conn.commit()
    
    def record_monthly_payment(self, plan_id, payment_number, actual_date, actual_amount, transaction_id=None):
        """
        记录实际支付的月供
        
        参数:
        - plan_id: 分期计划ID
        - payment_number: 第几期
        - actual_date: 实际支付日期
        - actual_amount: 实际支付金额
        - transaction_id: 关联的交易记录ID(可选)
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE instalment_payment_records
                SET actual_date = ?,
                    actual_amount = ?,
                    transaction_id = ?,
                    status = 'paid',
                    paid_at = CURRENT_TIMESTAMP
                WHERE plan_id = ? AND payment_number = ?
            ''', (actual_date, actual_amount, transaction_id, plan_id, payment_number))
            
            conn.commit()
            
            # 检查是否所有分期都已支付完成
            self._check_plan_completion(plan_id)
    
    def _check_plan_completion(self, plan_id):
        """检查分期计划是否已完成"""
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 检查是否所有分期都已支付
            cursor.execute('''
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) as paid
                FROM instalment_payment_records
                WHERE plan_id = ?
            ''', (plan_id,))
            
            result = cursor.fetchone()
            
            if result['total'] == result['paid']:
                # 所有分期已支付完成
                cursor.execute('''
                    UPDATE instalment_plans
                    SET status = 'completed',
                        completed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (plan_id,))
                
                conn.commit()
    
    def get_customer_instalment_plans(self, customer_id):
        """获取客户所有分期计划"""
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    ip.*,
                    cc.bank_name,
                    cc.card_number_last4,
                    COUNT(ipr.id) as total_payments,
                    SUM(CASE WHEN ipr.status = 'paid' THEN 1 ELSE 0 END) as paid_payments
                FROM instalment_plans ip
                LEFT JOIN credit_cards cc ON ip.card_id = cc.id
                LEFT JOIN instalment_payment_records ipr ON ip.id = ipr.plan_id
                WHERE ip.customer_id = ?
                GROUP BY ip.id
                ORDER BY ip.start_date DESC
            ''', (customer_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_plan_payment_schedule(self, plan_id):
        """获取分期付款时间表"""
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT *
                FROM instalment_payment_records
                WHERE plan_id = ?
                ORDER BY payment_number
            ''', (plan_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_total_monthly_instalment(self, customer_id):
        """
        计算客户所有活跃分期的总月供
        用于DSR计算
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT COALESCE(SUM(monthly_payment), 0) as total_monthly_instalment
                FROM instalment_plans
                WHERE customer_id = ? AND status = 'active'
            ''', (customer_id,))
            
            result = cursor.fetchone()
            return result['total_monthly_instalment']
    
    def get_upcoming_payments(self, customer_id, days=30):
        """获取即将到期的分期付款（未来N天内）"""
        with get_db() as conn:
            cursor = conn.cursor()
            
            future_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
            
            cursor.execute('''
                SELECT 
                    ipr.*,
                    ip.product_name,
                    ip.monthly_payment,
                    cc.bank_name,
                    cc.card_number_last4
                FROM instalment_payment_records ipr
                JOIN instalment_plans ip ON ipr.plan_id = ip.id
                JOIN credit_cards cc ON ip.card_id = cc.id
                WHERE ip.customer_id = ?
                  AND ipr.status = 'pending'
                  AND ipr.scheduled_date <= ?
                ORDER BY ipr.scheduled_date
            ''', (customer_id, future_date))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def auto_detect_instalment_from_transaction(self, transaction_id):
        """
        从交易记录自动识别分期付款
        如果交易描述包含"INST"、"分期"等关键词
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 获取交易信息
            cursor.execute('''
                SELECT * FROM transactions WHERE id = ?
            ''', (transaction_id,))
            
            transaction = cursor.fetchone()
            if not transaction:
                return None
            
            description = transaction['description'].lower()
            
            # 检测分期关键词
            instalment_keywords = ['inst', 'instalment', 'installment', '分期', 'epp', 'ipp']
            
            is_instalment = any(keyword in description for keyword in instalment_keywords)
            
            if is_instalment:
                # 标记为分期交易
                cursor.execute('''
                    UPDATE transactions
                    SET transaction_subtype = 'instalment_payment'
                    WHERE id = ?
                ''', (transaction_id,))
                
                conn.commit()
                return True
            
            return False
    
    def get_instalment_summary(self, customer_id):
        """获取客户分期付款汇总"""
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 活跃分期总数
            cursor.execute('''
                SELECT COUNT(*) as active_plans,
                       COALESCE(SUM(monthly_payment), 0) as total_monthly,
                       COALESCE(SUM(principal_amount - (
                           SELECT COALESCE(SUM(actual_amount), 0)
                           FROM instalment_payment_records
                           WHERE plan_id = instalment_plans.id AND status = 'paid'
                       )), 0) as remaining_principal
                FROM instalment_plans
                WHERE customer_id = ? AND status = 'active'
            ''', (customer_id,))
            
            summary = dict(cursor.fetchone())
            
            # 即将到期的分期（7天内）
            cursor.execute('''
                SELECT COUNT(*) as upcoming_count
                FROM instalment_payment_records ipr
                JOIN instalment_plans ip ON ipr.plan_id = ip.id
                WHERE ip.customer_id = ?
                  AND ipr.status = 'pending'
                  AND ipr.scheduled_date <= date('now', '+7 days')
            ''', (customer_id,))
            
            summary['upcoming_payments'] = cursor.fetchone()['upcoming_count']
            
            return summary


# 工具函数
def create_instalment_plan(customer_id, card_id, plan_details):
    """创建分期付款计划"""
    tracker = InstalmentTracker()
    return tracker.create_instalment_plan(customer_id, card_id, plan_details)


def get_customer_instalments(customer_id):
    """获取客户所有分期计划"""
    tracker = InstalmentTracker()
    return tracker.get_customer_instalment_plans(customer_id)


def get_total_monthly_instalment(customer_id):
    """获取客户总月供（用于DSR计算）"""
    tracker = InstalmentTracker()
    return tracker.get_total_monthly_instalment(customer_id)
