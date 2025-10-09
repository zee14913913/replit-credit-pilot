"""
代付流程管理
签合同后才能开始代付
"""

from db.database import get_db
from datetime import datetime
import json
import sqlite3

class PaymentOnBehalf:
    
    def can_start_payment_service(self, contract_id):
        """
        检查是否可以开始代付服务
        只有双方签字的合同才能开始
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    sc.*,
                    c.name as customer_name,
                    fos.suggestion_type
                FROM service_contracts sc
                JOIN customers c ON sc.customer_id = c.id
                JOIN financial_optimization_suggestions fos ON sc.suggestion_id = fos.id
                WHERE sc.id = ?
            ''', (contract_id,))
            
            contract = cursor.fetchone()
            
            if not contract:
                return {'can_start': False, 'reason': '合同不存在'}
            
            contract = dict(contract)
            
            if not contract['customer_signed']:
                return {'can_start': False, 'reason': '客户尚未签字'}
            
            if not contract['company_signed']:
                return {'can_start': False, 'reason': '公司尚未签字'}
            
            if contract['status'] != 'active':
                return {'can_start': False, 'reason': '合同状态异常'}
            
            return {
                'can_start': True,
                'contract': contract,
                'message': '合同已生效，可以开始代付服务'
            }
    
    def record_payment_on_behalf(self, contract_id, card_id, amount, payment_type, notes=None):
        """
        记录代付交易
        
        Args:
            contract_id: 合同ID
            card_id: 信用卡ID
            amount: 代付金额
            payment_type: 'bill_payment'(账单代付) 或 'balance_transfer'(余额转移)
            notes: 备注
        """
        # 检查是否可以代付
        check_result = self.can_start_payment_service(contract_id)
        
        if not check_result['can_start']:
            return {'success': False, 'reason': check_result['reason']}
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 记录代付
            cursor.execute('''
                INSERT INTO payment_on_behalf_records
                (contract_id, card_id, amount, payment_type, payment_date, notes, status)
                VALUES (?, ?, ?, ?, ?, ?, 'completed')
            ''', (
                contract_id,
                card_id,
                amount,
                payment_type,
                datetime.now().strftime('%Y-%m-%d'),
                notes
            ))
            
            payment_id = cursor.lastrowid
            
            # 更新合同的实际代付总额
            cursor.execute('''
                UPDATE service_contracts
                SET actual_payment_amount = COALESCE(actual_payment_amount, 0) + ?
                WHERE id = ?
            ''', (amount, contract_id))
            
            conn.commit()
            
            return {
                'success': True,
                'payment_id': payment_id,
                'amount': amount,
                'message': f'代付成功：RM {amount:.2f}'
            }
    
    def get_contract_payment_history(self, contract_id):
        """
        获取合同的代付历史
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    pob.*,
                    cc.bank_name,
                    cc.card_type
                FROM payment_on_behalf_records pob
                LEFT JOIN credit_cards cc ON pob.card_id = cc.id
                WHERE pob.contract_id = ?
                ORDER BY pob.payment_date DESC
            ''', (contract_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def calculate_actual_profit_share(self, contract_id):
        """
        计算实际利润分成
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 获取合同信息
            cursor.execute('''
                SELECT * FROM service_contracts WHERE id = ?
            ''', (contract_id,))
            
            contract = dict(cursor.fetchone())
            
            # 获取实际节省/赚取金额
            cursor.execute('''
                SELECT 
                    fos.suggestion_type,
                    fos.estimated_savings,
                    fos.suggestion_details
                FROM financial_optimization_suggestions fos
                WHERE fos.id = ?
            ''', (contract['suggestion_id'],))
            
            suggestion = dict(cursor.fetchone())
            
            # 计算实际节省（这里简化处理，实际应该根据具体业务逻辑计算）
            estimated_savings = contract['total_savings']
            actual_savings = estimated_savings  # 实际应该根据执行结果计算
            
            # 50%分成
            our_actual_fee = actual_savings * 0.5
            customer_gets = actual_savings * 0.5
            
            # 更新success_fee_calculations表  
            cursor.execute('''
                INSERT OR REPLACE INTO success_fee_calculations
                (customer_id, optimization_id, actual_savings_achieved, total_customer_benefit, calculated_fee,
                 suggestion_id, estimated_savings, actual_savings, our_fee_50_percent, 
                 customer_profit, fee_paid, calculation_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
            ''', (
                contract['customer_id'],
                contract['suggestion_id'],  # optimization_id
                actual_savings,  # actual_savings_achieved  
                customer_gets,  # total_customer_benefit
                our_actual_fee,  # calculated_fee
                contract['suggestion_id'],
                estimated_savings,
                actual_savings,
                our_actual_fee,
                customer_gets,
                datetime.now().strftime('%Y-%m-%d')
            ))
            
            conn.commit()
            
            return {
                'estimated_savings': estimated_savings,
                'actual_savings': actual_savings,
                'our_fee': our_actual_fee,
                'customer_gets': customer_gets,
                'breakdown': {
                    'total_saved_or_earned': f"RM {actual_savings:.2f}",
                    'infinite_gz_fee_50%': f"RM {our_actual_fee:.2f}",
                    'customer_keeps_50%': f"RM {customer_gets:.2f}"
                }
            }
    
    def record_fee_payment(self, contract_id, payment_method='bank_transfer', transaction_ref=None):
        """
        记录客户支付的50%服务费
        """
        profit_share = self.calculate_actual_profit_share(contract_id)
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 更新费用支付状态
            cursor.execute('''
                UPDATE success_fee_calculations
                SET fee_paid = 1,
                    payment_method = ?,
                    payment_reference = ?,
                    payment_date = ?
                WHERE suggestion_id = (SELECT suggestion_id FROM service_contracts WHERE id = ?)
            ''', (
                payment_method,
                transaction_ref,
                datetime.now().strftime('%Y-%m-%d'),
                contract_id
            ))
            
            # 更新合同状态为已完成
            cursor.execute('''
                UPDATE service_contracts
                SET status = 'completed'
                WHERE id = ?
            ''', (contract_id,))
            
            # 更新建议状态为已完成
            cursor.execute('''
                UPDATE financial_optimization_suggestions
                SET status = 'completed'
                WHERE id = (SELECT suggestion_id FROM service_contracts WHERE id = ?)
            ''', (contract_id,))
            
            conn.commit()
            
            return {
                'success': True,
                'our_fee_received': profit_share['our_fee'],
                'customer_profit': profit_share['customer_gets'],
                'message': f"服务费已收到：RM {profit_share['our_fee']:.2f}。客户保留：RM {profit_share['customer_gets']:.2f}"
            }
    
    def get_service_summary(self, contract_id):
        """
        获取服务完整摘要
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    sc.*,
                    c.name as customer_name,
                    fos.suggestion_type,
                    fos.estimated_savings,
                    sfc.actual_savings,
                    sfc.our_fee_50_percent,
                    sfc.customer_profit,
                    sfc.fee_paid
                FROM service_contracts sc
                JOIN customers c ON sc.customer_id = c.id
                JOIN financial_optimization_suggestions fos ON sc.suggestion_id = fos.id
                LEFT JOIN success_fee_calculations sfc ON fos.id = sfc.suggestion_id
                WHERE sc.id = ?
            ''', (contract_id,))
            
            summary = dict(cursor.fetchone())
            
            # 获取代付记录
            payments = self.get_contract_payment_history(contract_id)
            
            return {
                'contract': summary,
                'payment_history': payments,
                'financial_summary': {
                    'estimated_savings': summary.get('estimated_savings', 0),
                    'actual_savings': summary.get('actual_savings', 0),
                    'our_fee': summary.get('our_fee_50_percent', 0),
                    'customer_profit': summary.get('customer_profit', 0),
                    'fee_paid': bool(summary.get('fee_paid', 0))
                }
            }


# 便捷函数
def check_can_start_service(contract_id):
    """检查是否可以开始服务"""
    service = PaymentOnBehalf()
    return service.can_start_payment_service(contract_id)

def record_payment(contract_id, card_id, amount, payment_type='bill_payment', notes=None):
    """记录代付"""
    service = PaymentOnBehalf()
    return service.record_payment_on_behalf(contract_id, card_id, amount, payment_type, notes)

def calculate_profit(contract_id):
    """计算利润分成"""
    service = PaymentOnBehalf()
    return service.calculate_actual_profit_share(contract_id)

def record_fee(contract_id, method='bank_transfer', ref=None):
    """记录费用支付"""
    service = PaymentOnBehalf()
    return service.record_fee_payment(contract_id, method, ref)
