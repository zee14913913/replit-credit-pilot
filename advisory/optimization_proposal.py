"""
优化建议对比系统
显示客户现状 vs 优化方案的对比结果
"""

from db.database import get_db
from datetime import datetime
import json

class OptimizationProposal:
    
    def generate_debt_optimization_proposal(self, customer_id):
        """
        生成债务优化建议（债务整合、余额转移）
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 获取客户所有信用卡债务
            cursor.execute('''
                SELECT 
                    cc.id,
                    cc.bank_name,
                    cc.card_type,
                    cc.interest_rate,
                    SUM(CASE WHEN sba.customer_balance > 0 THEN sba.customer_balance ELSE 0 END) as total_debt
                FROM credit_cards cc
                LEFT JOIN statements s ON cc.id = s.card_id
                LEFT JOIN statement_balance_analysis sba ON s.id = sba.statement_id
                WHERE cc.customer_id = ?
                GROUP BY cc.id
                HAVING total_debt > 0
                ORDER BY cc.interest_rate DESC
            ''', (customer_id,))
            
            cards = [dict(row) for row in cursor.fetchall()]
            
            if not cards:
                return None
            
            # 计算现状
            current_total_debt = sum(card['total_debt'] for card in cards)
            current_weighted_rate = sum(
                card['total_debt'] * card['interest_rate'] 
                for card in cards
            ) / current_total_debt if current_total_debt > 0 else 0
            
            current_monthly_interest = current_total_debt * (current_weighted_rate / 100 / 12)
            current_annual_interest = current_monthly_interest * 12
            
            # 模拟最优余额转移方案（实际应该从credit_card_products表查询）
            best_bt_card = {
                'bank_name': 'Maybank',
                'product_name': 'Balance Transfer Plus',
                'interest_rate': 6.88,
                'balance_transfer_fee': 2.0
            }
            
            if best_bt_card:
                new_rate = best_bt_card['interest_rate']
                bt_fee = best_bt_card['balance_transfer_fee']
                
                # 计算优化方案
                optimized_monthly_interest = current_total_debt * (new_rate / 100 / 12)
                optimized_annual_interest = optimized_monthly_interest * 12
                
                # 计算节省
                annual_savings = current_annual_interest - optimized_annual_interest - (current_total_debt * bt_fee / 100)
                monthly_savings = annual_savings / 12
                
                proposal = {
                    'proposal_type': 'debt_consolidation',
                    'customer_id': customer_id,
                    'current_situation': {
                        'total_debt': current_total_debt,
                        'num_cards': len(cards),
                        'weighted_interest_rate': current_weighted_rate,
                        'monthly_interest': current_monthly_interest,
                        'annual_interest_cost': current_annual_interest,
                        'card_details': cards
                    },
                    'optimized_solution': {
                        'recommended_product': f"{best_bt_card['bank_name']} - {best_bt_card['product_name']}",
                        'new_interest_rate': new_rate,
                        'balance_transfer_fee': bt_fee,
                        'monthly_interest': optimized_monthly_interest,
                        'annual_interest_cost': optimized_annual_interest
                    },
                    'savings': {
                        'annual_savings': annual_savings,
                        'monthly_savings': monthly_savings,
                        'savings_percentage': (annual_savings / current_annual_interest * 100) if current_annual_interest > 0 else 0,
                        'our_fee_50_percent': annual_savings * 0.5  # 50%分成
                    },
                    'comparison': {
                        'before': f"RM {current_annual_interest:.2f}/年",
                        'after': f"RM {optimized_annual_interest:.2f}/年",
                        'you_save': f"RM {annual_savings:.2f}/年",
                        'we_earn': f"RM {annual_savings * 0.5:.2f} (50%分成)"
                    }
                }
                
                # 保存建议到数据库
                cursor.execute('''
                    INSERT INTO financial_optimization_suggestions
                    (customer_id, optimization_type, suggestion_type, current_cost, optimized_cost, estimated_savings, suggestion_details, status,
                     current_monthly_payment, current_interest_rate, current_total_cost,
                     optimized_monthly_payment, optimized_interest_rate, optimized_total_cost,
                     monthly_savings, total_savings)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    customer_id,
                    'debt_consolidation',
                    'debt_consolidation',
                    current_annual_interest,
                    optimized_annual_interest,
                    annual_savings,
                    json.dumps(proposal),
                    0, current_weighted_rate, current_annual_interest,
                    0, new_rate, optimized_annual_interest,
                    monthly_savings, annual_savings
                ))
                
                proposal['suggestion_id'] = cursor.lastrowid
                conn.commit()
                
                return proposal
            
            return None
    
    def generate_credit_card_recommendation(self, customer_id):
        """
        生成信用卡推荐建议（基于消费习惯）
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 分析客户消费类别
            cursor.execute('''
                SELECT 
                    category,
                    SUM(ABS(amount)) as total_spent
                FROM transactions t
                JOIN statements s ON t.statement_id = s.id
                JOIN credit_cards cc ON s.card_id = cc.id
                WHERE cc.customer_id = ? 
                AND t.transaction_type = 'debit'
                AND t.belongs_to = 'customer'
                GROUP BY category
                ORDER BY total_spent DESC
                LIMIT 3
            ''', (customer_id,))
            
            top_categories = [dict(row) for row in cursor.fetchall()]
            
            if not top_categories:
                return None
            
            # 获取当前信用卡回扣率
            cursor.execute('''
                SELECT AVG(cashback_rate) as avg_cashback
                FROM credit_cards
                WHERE customer_id = ?
            ''', (customer_id,))
            
            current_cashback = cursor.fetchone()['avg_cashback'] or 0
            
            # 模拟最佳回扣卡（实际应该从credit_card_products表查询）
            best_card = {
                'bank_name': 'CIMB',
                'product_name': 'Preferred Mastercard',
                'cashback_rate': 5.0,
                'annual_fee': 150
            }
            
            if best_card and best_card['cashback_rate'] > current_cashback:
                
                # 计算年度总消费
                cursor.execute('''
                    SELECT SUM(ABS(amount)) as total_annual_spending
                    FROM transactions t
                    JOIN statements s ON t.statement_id = s.id
                    JOIN credit_cards cc ON s.card_id = cc.id
                    WHERE cc.customer_id = ?
                    AND t.transaction_type = 'debit'
                    AND t.belongs_to = 'customer'
                    AND t.transaction_date >= date('now', '-12 months')
                ''', (customer_id,))
                
                annual_spending = cursor.fetchone()['total_annual_spending'] or 0
                
                # 计算回扣对比
                current_cashback_amount = annual_spending * (current_cashback / 100)
                optimized_cashback_amount = annual_spending * (best_card['cashback_rate'] / 100)
                additional_cashback = optimized_cashback_amount - current_cashback_amount
                
                proposal = {
                    'proposal_type': 'credit_card_optimization',
                    'customer_id': customer_id,
                    'current_situation': {
                        'annual_spending': annual_spending,
                        'current_cashback_rate': current_cashback,
                        'current_cashback_amount': current_cashback_amount,
                        'top_spending_categories': top_categories
                    },
                    'optimized_solution': {
                        'recommended_card': f"{best_card['bank_name']} - {best_card['product_name']}",
                        'new_cashback_rate': best_card['cashback_rate'],
                        'optimized_cashback_amount': optimized_cashback_amount,
                        'annual_fee': best_card.get('annual_fee', 0)
                    },
                    'savings': {
                        'additional_annual_cashback': additional_cashback - best_card.get('annual_fee', 0),
                        'our_fee_50_percent': (additional_cashback - best_card.get('annual_fee', 0)) * 0.5
                    },
                    'comparison': {
                        'before': f"{current_cashback}% 回扣 = RM {current_cashback_amount:.2f}/年",
                        'after': f"{best_card['cashback_rate']}% 回扣 = RM {optimized_cashback_amount:.2f}/年",
                        'you_earn_extra': f"RM {additional_cashback:.2f}/年",
                        'we_earn': f"RM {(additional_cashback - best_card.get('annual_fee', 0)) * 0.5:.2f} (50%分成)"
                    }
                }
                
                # 保存建议
                net_savings = additional_cashback - best_card.get('annual_fee', 0)
                cursor.execute('''
                    INSERT INTO financial_optimization_suggestions
                    (customer_id, optimization_type, suggestion_type, current_cost, optimized_cost, estimated_savings, suggestion_details, status,
                     current_monthly_payment, current_interest_rate, current_total_cost,
                     optimized_monthly_payment, optimized_interest_rate, optimized_total_cost,
                     monthly_savings, total_savings)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    customer_id,
                    'credit_card_optimization',
                    'credit_card_optimization',
                    current_cashback_amount,
                    optimized_cashback_amount,
                    net_savings,
                    json.dumps(proposal),
                    0, 0, current_cashback_amount,
                    0, 0, optimized_cashback_amount,
                    net_savings / 12, net_savings
                ))
                
                proposal['suggestion_id'] = cursor.lastrowid
                conn.commit()
                
                return proposal
            
            return None
    
    def get_all_proposals(self, customer_id):
        """
        获取客户所有优化建议
        """
        proposals = []
        
        # 债务优化
        debt_proposal = self.generate_debt_optimization_proposal(customer_id)
        if debt_proposal:
            proposals.append(debt_proposal)
        
        # 信用卡优化
        card_proposal = self.generate_credit_card_recommendation(customer_id)
        if card_proposal:
            proposals.append(card_proposal)
        
        return proposals


# 便捷函数
def generate_proposals(customer_id):
    """生成所有优化建议"""
    optimizer = OptimizationProposal()
    return optimizer.get_all_proposals(customer_id)
