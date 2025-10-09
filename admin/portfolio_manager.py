"""
INFINITE GZ Portfolio Management System
管理员核心运营工具 - 监控所有客户的50/50咨询服务workflow

Core Business Functions:
1. Track all client advisory workflows (proposal → consultation → contract → payment → fee)
2. Calculate actual savings vs INFINITE GZ revenue (50/50 split)
3. Monitor supplier fee revenue (7 suppliers @ 1% fee)
4. Identify risk clients (overdue, over-limit, high DSR)
5. Portfolio-level financial analytics
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect('db/smart_loan_manager.db')
    conn.row_factory = sqlite3.Row
    return conn

class PortfolioManager:
    """管理员Portfolio管理器"""
    
    def __init__(self):
        self.conn = get_db_connection()
    
    def get_portfolio_overview(self) -> Dict[str, Any]:
        """获取Portfolio总览"""
        cursor = self.conn.cursor()
        
        # 1. 总客户数
        cursor.execute("SELECT COUNT(*) as total FROM customers")
        total_customers = cursor.fetchone()['total']
        
        # 2. 活跃客户（有statement的）
        cursor.execute("""
            SELECT COUNT(DISTINCT cc.customer_id) as active
            FROM statements s
            JOIN credit_cards cc ON s.card_id = cc.id
            WHERE s.statement_date >= date('now', '-3 months')
        """)
        active_customers = cursor.fetchone()['active']
        
        # 3. 待处理consultation requests
        cursor.execute("""
            SELECT COUNT(*) as pending
            FROM consultation_requests
            WHERE status = 'pending'
        """)
        pending_consultations = cursor.fetchone()['pending']
        
        # 4. 活跃contracts
        cursor.execute("""
            SELECT COUNT(*) as active
            FROM service_contracts
            WHERE status = 'active'
        """)
        active_contracts = cursor.fetchone()['active']
        
        # 5. 总节省金额（所有成功的优化）
        cursor.execute("""
            SELECT COALESCE(SUM(actual_savings_achieved), 0) as total_savings
            FROM success_fee_calculations
            WHERE fee_paid = 1
        """)
        total_savings = cursor.fetchone()['total_savings']
        
        # 6. INFINITE GZ总收入（50%分成）
        cursor.execute("""
            SELECT COALESCE(SUM(our_fee_50_percent), 0) as total_revenue
            FROM success_fee_calculations
            WHERE fee_paid = 1
        """)
        gz_revenue_from_advisory = cursor.fetchone()['total_revenue']
        
        # 7. Supplier费用收入（1% from 7 suppliers）
        cursor.execute("""
            SELECT COALESCE(SUM(t.amount * 0.01), 0) as supplier_revenue
            FROM transactions t
            WHERE t.description IN (
                'AEON', 'AEON CO', 'AEON MALL',
                'COURTS', 'COURTS MAMMOTH',
                'SENHENG', 'SENQ',
                'HARVEY NORMAN',
                'LAZADA', 'SHOPEE',
                'GRAB', 'FOODPANDA'
            )
        """)
        supplier_revenue = cursor.fetchone()['supplier_revenue']
        
        # 8. 总收入（advisory + supplier）
        total_revenue = gz_revenue_from_advisory + supplier_revenue
        
        # 9. 风险客户（透支 or 逾期）
        cursor.execute("""
            SELECT COUNT(DISTINCT cc.customer_id) as risk_count
            FROM credit_cards cc
            LEFT JOIN (
                SELECT s.card_id, SUM(t.amount) as total_balance
                FROM transactions t
                JOIN statements s ON t.statement_id = s.id
                GROUP BY s.card_id
            ) bal ON cc.id = bal.card_id
            WHERE COALESCE(bal.total_balance, 0) > cc.credit_limit
        """)
        risk_customers = cursor.fetchone()['risk_count']
        
        return {
            'total_customers': total_customers,
            'active_customers': active_customers,
            'pending_consultations': pending_consultations,
            'active_contracts': active_contracts,
            'total_savings_all_clients': round(total_savings, 2),
            'gz_revenue_advisory': round(gz_revenue_from_advisory, 2),
            'gz_revenue_supplier': round(supplier_revenue, 2),
            'gz_total_revenue': round(total_revenue, 2),
            'risk_customers': risk_customers
        }
    
    def get_all_clients_portfolio(self) -> List[Dict[str, Any]]:
        """获取所有客户的Portfolio详情"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                c.id,
                c.name,
                c.email,
                c.phone,
                c.monthly_income,
                COUNT(DISTINCT s.id) as statement_count,
                MAX(s.statement_date) as last_statement_date,
                COUNT(DISTINCT cc.id) as credit_card_count,
                COALESCE(SUM(t.amount), 0) as total_balance
            FROM customers c
            LEFT JOIN credit_cards cc ON c.id = cc.customer_id
            LEFT JOIN statements s ON cc.id = s.card_id
            LEFT JOIN transactions t ON s.id = t.statement_id
            GROUP BY c.id
            ORDER BY c.id
        """)
        
        clients = []
        for row in cursor.fetchall():
            customer_id = row['id']
            
            # 获取workflow状态
            workflow_stage = self._get_workflow_stage(customer_id)
            
            # 获取财务指标
            metrics = self._get_client_metrics(customer_id)
            
            clients.append({
                'id': customer_id,
                'name': row['name'],
                'email': row['email'],
                'phone': row['phone'],
                'monthly_income': row['monthly_income'],
                'statement_count': row['statement_count'],
                'last_statement_date': row['last_statement_date'],
                'credit_card_count': row['credit_card_count'],
                'total_balance': round(row['total_balance'], 2),
                'workflow_stage': workflow_stage,
                'metrics': metrics
            })
        
        return clients
    
    def _get_workflow_stage(self, customer_id: int) -> Dict[str, Any]:
        """获取客户advisory workflow阶段"""
        cursor = self.conn.cursor()
        
        # 检查是否有active contract
        cursor.execute("""
            SELECT COUNT(*) as count FROM service_contracts
            WHERE customer_id = ? AND status = 'active'
        """, (customer_id,))
        active_contracts = cursor.fetchone()['count']
        
        if active_contracts > 0:
            # Stage 5: Active Contract - Payment on Behalf
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM payment_on_behalf_records p
                JOIN service_contracts sc ON p.contract_id = sc.id
                WHERE sc.customer_id = ?
            """, (customer_id,))
            payment_count = cursor.fetchone()['count']
            
            return {
                'stage': 5,
                'stage_name': 'Active - Payment on Behalf',
                'stage_detail': f'{payment_count} payments made',
                'status': 'success'
            }
        
        # 检查是否有signed contract（待激活）
        cursor.execute("""
            SELECT COUNT(*) as count FROM service_contracts
            WHERE customer_id = ? AND status = 'signed'
        """, (customer_id,))
        signed_contracts = cursor.fetchone()['count']
        
        if signed_contracts > 0:
            return {
                'stage': 4,
                'stage_name': 'Contract Signed - Pending Activation',
                'stage_detail': 'Waiting for service to begin',
                'status': 'warning'
            }
        
        # 检查是否有consultation已完成
        cursor.execute("""
            SELECT COUNT(*) as count FROM consultation_requests
            WHERE customer_id = ? AND status = 'completed'
        """, (customer_id,))
        completed_consultations = cursor.fetchone()['count']
        
        if completed_consultations > 0:
            return {
                'stage': 3,
                'stage_name': 'Consultation Completed - Awaiting Contract',
                'stage_detail': 'Ready to sign contract',
                'status': 'info'
            }
        
        # 检查是否有pending consultation
        cursor.execute("""
            SELECT COUNT(*) as count FROM consultation_requests
            WHERE customer_id = ? AND status IN ('pending', 'scheduled')
        """, (customer_id,))
        pending_consultations = cursor.fetchone()['count']
        
        if pending_consultations > 0:
            return {
                'stage': 2,
                'stage_name': 'Consultation Requested',
                'stage_detail': 'Awaiting appointment',
                'status': 'warning'
            }
        
        # 检查是否有optimization proposal
        cursor.execute("""
            SELECT COUNT(*) as count FROM financial_optimization_suggestions
            WHERE customer_id = ? AND status = 'proposed'
        """, (customer_id,))
        proposals = cursor.fetchone()['count']
        
        if proposals > 0:
            return {
                'stage': 1,
                'stage_name': 'Proposal Sent',
                'stage_detail': f'{proposals} optimization proposals',
                'status': 'info'
            }
        
        # 没有任何workflow
        return {
            'stage': 0,
            'stage_name': 'No Advisory Service',
            'stage_detail': 'Regular customer only',
            'status': 'secondary'
        }
    
    def _get_client_metrics(self, customer_id: int) -> Dict[str, Any]:
        """获取客户财务指标"""
        cursor = self.conn.cursor()
        
        # 1. 总节省金额
        cursor.execute("""
            SELECT COALESCE(SUM(actual_savings_achieved), 0) as total_savings
            FROM success_fee_calculations
            WHERE customer_id = ? AND fee_paid = 1
        """, (customer_id,))
        total_savings = cursor.fetchone()['total_savings']
        
        # 2. INFINITE GZ收入（50%）
        cursor.execute("""
            SELECT COALESCE(SUM(our_fee_50_percent), 0) as gz_revenue
            FROM success_fee_calculations
            WHERE customer_id = ? AND fee_paid = 1
        """, (customer_id,))
        gz_revenue = cursor.fetchone()['gz_revenue']
        
        # 3. 客户保留金额（50%）
        customer_keeps = total_savings - gz_revenue
        
        # 4. DSR计算
        cursor.execute("""
            SELECT monthly_income FROM customers WHERE id = ?
        """, (customer_id,))
        monthly_income = cursor.fetchone()['monthly_income'] or 0
        
        # 获取月度债务还款
        cursor.execute("""
            SELECT COALESCE(SUM(t.amount), 0) as monthly_debt
            FROM transactions t
            JOIN statements s ON t.statement_id = s.id
            JOIN credit_cards cc ON s.card_id = cc.id
            WHERE cc.customer_id = ?
            AND t.description LIKE '%PAYMENT%'
            AND t.transaction_date >= date('now', '-1 month')
        """, (customer_id,))
        monthly_debt = cursor.fetchone()['monthly_debt']
        
        dsr = (monthly_debt / monthly_income * 100) if monthly_income > 0 else 0
        
        # 5. 风险状态
        risk_status = 'safe'
        if dsr > 70:
            risk_status = 'high_dsr'
        
        # 检查透支
        cursor.execute("""
            SELECT COUNT(*) as overdrawn
            FROM credit_cards cc
            LEFT JOIN (
                SELECT s.card_id, SUM(t.amount) as balance
                FROM transactions t
                JOIN statements s ON t.statement_id = s.id
                GROUP BY s.card_id
            ) bal ON cc.id = bal.card_id
            WHERE cc.customer_id = ?
            AND COALESCE(bal.balance, 0) > cc.credit_limit
        """, (customer_id,))
        
        if cursor.fetchone()['overdrawn'] > 0:
            risk_status = 'overdrawn'
        
        return {
            'total_savings': round(total_savings, 2),
            'gz_revenue': round(gz_revenue, 2),
            'customer_keeps': round(customer_keeps, 2),
            'dsr': round(dsr, 1),
            'risk_status': risk_status
        }
    
    def get_client_detail(self, customer_id: int) -> Dict[str, Any]:
        """获取单个客户完整详情"""
        cursor = self.conn.cursor()
        
        # 基本信息
        cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
        customer = dict(cursor.fetchone())
        
        # Workflow详情
        workflow = self._get_workflow_detail(customer_id)
        
        # 财务指标
        metrics = self._get_client_metrics(customer_id)
        
        # 所有credit cards
        cursor.execute("""
            SELECT 
                cc.*,
                COALESCE(SUM(t.amount), 0) as current_balance,
                ROUND(COALESCE(SUM(t.amount), 0) / cc.credit_limit * 100, 1) as utilization
            FROM credit_cards cc
            LEFT JOIN statements s ON cc.id = s.card_id
            LEFT JOIN transactions t ON s.id = t.statement_id
            WHERE cc.customer_id = ?
            GROUP BY cc.id
        """, (customer_id,))
        credit_cards = [dict(row) for row in cursor.fetchall()]
        
        return {
            'customer': customer,
            'workflow': workflow,
            'metrics': metrics,
            'credit_cards': credit_cards
        }
    
    def _get_workflow_detail(self, customer_id: int) -> Dict[str, Any]:
        """获取完整workflow详情"""
        cursor = self.conn.cursor()
        
        # 1. Optimization Proposals
        cursor.execute("""
            SELECT * FROM financial_optimization_suggestions
            WHERE customer_id = ?
            ORDER BY created_at DESC
        """, (customer_id,))
        proposals = [dict(row) for row in cursor.fetchall()]
        
        # 2. Consultation Requests
        cursor.execute("""
            SELECT * FROM consultation_requests
            WHERE customer_id = ?
            ORDER BY created_at DESC
        """, (customer_id,))
        consultations = [dict(row) for row in cursor.fetchall()]
        
        # 3. Service Contracts
        cursor.execute("""
            SELECT * FROM service_contracts
            WHERE customer_id = ?
            ORDER BY created_at DESC
        """, (customer_id,))
        contracts = [dict(row) for row in cursor.fetchall()]
        
        # 4. Payment on Behalf Records
        cursor.execute("""
            SELECT p.* FROM payment_on_behalf_records p
            JOIN service_contracts sc ON p.contract_id = sc.id
            WHERE sc.customer_id = ?
            ORDER BY p.payment_date DESC
        """, (customer_id,))
        payments = [dict(row) for row in cursor.fetchall()]
        
        # 5. Success Fee Calculations
        cursor.execute("""
            SELECT * FROM success_fee_calculations
            WHERE customer_id = ?
            ORDER BY calculation_date DESC
        """, (customer_id,))
        fee_calculations = [dict(row) for row in cursor.fetchall()]
        
        return {
            'proposals': proposals,
            'consultations': consultations,
            'contracts': contracts,
            'payments': payments,
            'fee_calculations': fee_calculations
        }
    
    def get_revenue_breakdown(self) -> Dict[str, Any]:
        """获取收入明细分析"""
        cursor = self.conn.cursor()
        
        # 1. Advisory服务收入（按月）
        cursor.execute("""
            SELECT 
                strftime('%Y-%m', calculation_date) as month,
                COUNT(*) as client_count,
                SUM(actual_savings_achieved) as total_savings,
                SUM(our_fee_50_percent) as gz_revenue
            FROM success_fee_calculations
            WHERE fee_paid = 1
            AND calculation_date >= date('now', '-12 months')
            GROUP BY month
            ORDER BY month DESC
        """)
        advisory_revenue = [dict(row) for row in cursor.fetchall()]
        
        # 2. Supplier费用收入（按月）
        cursor.execute("""
            SELECT 
                strftime('%Y-%m', t.transaction_date) as month,
                COUNT(*) as transaction_count,
                SUM(t.amount) as total_spending,
                SUM(t.amount * 0.01) as gz_commission
            FROM transactions t
            WHERE t.description IN (
                'AEON', 'AEON CO', 'AEON MALL',
                'COURTS', 'COURTS MAMMOTH',
                'SENHENG', 'SENQ',
                'HARVEY NORMAN',
                'LAZADA', 'SHOPEE',
                'GRAB', 'FOODPANDA'
            )
            AND t.transaction_date >= date('now', '-12 months')
            GROUP BY month
            ORDER BY month DESC
        """)
        supplier_revenue = [dict(row) for row in cursor.fetchall()]
        
        # 3. 按供应商分类
        cursor.execute("""
            SELECT 
                t.description as supplier,
                COUNT(*) as transaction_count,
                SUM(t.amount) as total_spending,
                SUM(t.amount * 0.01) as gz_commission
            FROM transactions t
            WHERE t.description IN (
                'AEON', 'AEON CO', 'AEON MALL',
                'COURTS', 'COURTS MAMMOTH',
                'SENHENG', 'SENQ',
                'HARVEY NORMAN',
                'LAZADA', 'SHOPEE',
                'GRAB', 'FOODPANDA'
            )
            AND t.transaction_date >= date('now', '-12 months')
            GROUP BY supplier
            ORDER BY gz_commission DESC
        """)
        by_supplier = [dict(row) for row in cursor.fetchall()]
        
        return {
            'advisory_revenue_monthly': advisory_revenue,
            'supplier_revenue_monthly': supplier_revenue,
            'revenue_by_supplier': by_supplier
        }
    
    def get_risk_clients(self) -> List[Dict[str, Any]]:
        """获取风险客户列表"""
        cursor = self.conn.cursor()
        
        risk_clients = []
        
        # 1. 透支客户
        cursor.execute("""
            SELECT 
                c.id,
                c.name,
                c.email,
                cc.bank_name,
                cc.card_number_last4,
                cc.credit_limit,
                COALESCE(SUM(t.amount), 0) as current_balance,
                COALESCE(SUM(t.amount), 0) - cc.credit_limit as overdrawn_amount
            FROM customers c
            JOIN credit_cards cc ON c.id = cc.customer_id
            LEFT JOIN statements s ON cc.id = s.card_id
            LEFT JOIN transactions t ON s.id = t.statement_id
            GROUP BY c.id, cc.id
            HAVING current_balance > cc.credit_limit
        """)
        
        for row in cursor.fetchall():
            card_display = f"{row['bank_name']} ****{row['card_number_last4']}"
            risk_clients.append({
                'customer_id': row['id'],
                'name': row['name'],
                'email': row['email'],
                'risk_type': 'Overdrawn',
                'severity': 'critical',
                'detail': f"{card_display}: RM {row['overdrawn_amount']:.2f} over limit",
                'action_required': 'Contact for immediate payment'
            })
        
        # 2. 高DSR客户（>70%）
        cursor.execute("""
            SELECT 
                c.id,
                c.name,
                c.email,
                c.monthly_income,
                COALESCE(SUM(CASE WHEN t.description LIKE '%PAYMENT%' THEN t.amount ELSE 0 END), 0) as monthly_debt
            FROM customers c
            LEFT JOIN credit_cards cc ON c.id = cc.customer_id
            LEFT JOIN statements s ON cc.id = s.card_id
            LEFT JOIN transactions t ON s.id = t.statement_id
            WHERE t.transaction_date >= date('now', '-1 month')
            GROUP BY c.id
            HAVING (monthly_debt / monthly_income * 100) > 70
        """)
        
        for row in cursor.fetchall():
            dsr = (row['monthly_debt'] / row['monthly_income'] * 100) if row['monthly_income'] > 0 else 0
            risk_clients.append({
                'customer_id': row['id'],
                'name': row['name'],
                'email': row['email'],
                'risk_type': 'High DSR',
                'severity': 'warning',
                'detail': f"DSR: {dsr:.1f}% (monthly debt RM {row['monthly_debt']:.2f})",
                'action_required': 'Recommend debt consolidation'
            })
        
        # 3. 即将逾期（7天内到期）
        cursor.execute("""
            SELECT 
                c.id,
                c.name,
                c.email,
                r.due_date,
                r.amount_due,
                r.card_id
            FROM customers c
            JOIN credit_cards cc ON c.id = cc.customer_id
            JOIN repayment_reminders r ON cc.id = r.card_id
            WHERE r.due_date <= date('now', '+7 days')
            AND r.due_date >= date('now')
            AND r.is_paid = 0
            ORDER BY r.due_date ASC
        """)
        
        for row in cursor.fetchall():
            days_until_due = (datetime.strptime(row['due_date'], '%Y-%m-%d') - datetime.now()).days
            severity = 'critical' if days_until_due <= 3 else 'warning'
            
            risk_clients.append({
                'customer_id': row['id'],
                'name': row['name'],
                'email': row['email'],
                'risk_type': 'Payment Due Soon',
                'severity': severity,
                'detail': f"RM {row['amount_due']:.2f} due in {days_until_due} days",
                'action_required': 'Send payment reminder'
            })
        
        return risk_clients
    
    def __del__(self):
        """关闭数据库连接"""
        if hasattr(self, 'conn'):
            self.conn.close()
