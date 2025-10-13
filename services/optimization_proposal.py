"""
Optimization Proposal Service
智能优化方案生成与对比展示

核心功能：
1. 分析客户当前财务状况
2. 生成优化方案
3. 清晰对比：现状 vs 方案（省钱金额）
4. 自动化获客：吸引客户点击「申请方案」
"""

from typing import Dict, List
import json


class OptimizationProposal:
    """优化方案生成器"""
    
    def __init__(self):
        self.proposal_types = {
            'debt_consolidation': '债务整合贷款',
            'balance_transfer': '余额转移',
            'credit_card_optimization': '信用卡优化',
            'cashback_maximization': '现金返现最大化',
            'rewards_optimization': '积分奖励优化'
        }
    
    def analyze_customer_status(self, customer_data):
        """
        分析客户当前状况
        
        Args:
            customer_data: 包含所有信用卡和交易数据
            
        Returns:
            dict: 当前状况分析结果
        """
        total_debt = sum(card.get('current_balance', 0) for card in customer_data.get('cards', []))
        total_credit_limit = sum(card.get('credit_limit', 0) for card in customer_data.get('cards', []))
        monthly_spending = customer_data.get('monthly_spending', 0)
        monthly_income = customer_data.get('monthly_income', 0)
        
        # 计算平均利率
        total_interest_paid = 0
        cards_with_balance = [c for c in customer_data.get('cards', []) if c.get('current_balance', 0) > 0]
        avg_interest_rate = 18.0  # 马来西亚信用卡平均利率
        
        # 计算月度利息成本
        monthly_interest_cost = (total_debt * avg_interest_rate / 100) / 12
        
        # 计算DSR (Debt Service Ratio)
        monthly_payment = total_debt * 0.05  # 假设最低还款5%
        dsr = (monthly_payment / monthly_income * 100) if monthly_income > 0 else 0
        
        return {
            'total_debt': total_debt,
            'total_credit_limit': total_credit_limit,
            'utilization_rate': (total_debt / total_credit_limit * 100) if total_credit_limit > 0 else 0,
            'monthly_spending': monthly_spending,
            'monthly_income': monthly_income,
            'avg_interest_rate': avg_interest_rate,
            'monthly_interest_cost': monthly_interest_cost,
            'annual_interest_cost': monthly_interest_cost * 12,
            'dsr': dsr,
            'num_cards': len(customer_data.get('cards', [])),
            'cards_with_balance': len(cards_with_balance)
        }
    
    def generate_debt_consolidation_proposal(self, current_status):
        """
        生成债务整合方案
        
        核心：将多张信用卡债务合并到低利率个人贷款
        """
        total_debt = current_status['total_debt']
        current_interest = current_status['avg_interest_rate']
        
        # 个人贷款利率通常比信用卡低（6-8%）
        proposed_interest_rate = 6.0
        
        # 计算节省
        current_monthly_interest = (total_debt * current_interest / 100) / 12
        proposed_monthly_interest = (total_debt * proposed_interest_rate / 100) / 12
        monthly_savings = current_monthly_interest - proposed_monthly_interest
        annual_savings = monthly_savings * 12
        
        return {
            'type': 'debt_consolidation',
            'title': '债务整合贷款方案',
            'description': '将所有信用卡债务合并到低利率个人贷款',
            'current': {
                'total_debt': total_debt,
                'interest_rate': current_interest,
                'monthly_interest': current_monthly_interest,
                'annual_cost': current_monthly_interest * 12
            },
            'proposed': {
                'total_debt': total_debt,
                'interest_rate': proposed_interest_rate,
                'monthly_interest': proposed_monthly_interest,
                'annual_cost': proposed_monthly_interest * 12
            },
            'savings': {
                'monthly': monthly_savings,
                'annual': annual_savings,
                'percentage': ((current_interest - proposed_interest_rate) / current_interest * 100)
            }
        }
    
    def generate_balance_transfer_proposal(self, current_status):
        """
        生成余额转移方案
        
        核心：转移到0%利率促销信用卡（6-12个月）
        """
        total_debt = current_status['total_debt']
        current_monthly_interest = current_status['monthly_interest_cost']
        
        # 0%利率促销期（假设12个月）
        promo_months = 12
        monthly_savings = current_monthly_interest
        promo_period_savings = monthly_savings * promo_months
        
        # 小额手续费（通常3-5%）
        transfer_fee_rate = 3.0
        transfer_fee = total_debt * (transfer_fee_rate / 100)
        
        net_savings = promo_period_savings - transfer_fee
        
        return {
            'type': 'balance_transfer',
            'title': '余额转移0%利率方案',
            'description': f'转移到促销0%利率信用卡（{promo_months}个月）',
            'current': {
                'monthly_interest': current_monthly_interest,
                'promo_period_cost': current_monthly_interest * promo_months
            },
            'proposed': {
                'monthly_interest': 0,
                'promo_period_cost': transfer_fee,
                'transfer_fee': transfer_fee,
                'promo_months': promo_months
            },
            'savings': {
                'gross_savings': promo_period_savings,
                'transfer_fee': transfer_fee,
                'net_savings': net_savings,
                'monthly_equivalent': net_savings / promo_months
            }
        }
    
    def generate_cashback_optimization_proposal(self, current_status):
        """
        生成现金返现优化方案
        
        核心：推荐最佳现金返现信用卡，最大化返现收益
        """
        monthly_spending = current_status['monthly_spending']
        
        # 当前情况（假设无返现或低返现1%）
        current_cashback_rate = 1.0
        current_monthly_cashback = monthly_spending * (current_cashback_rate / 100)
        
        # 优化方案：使用高返现卡（3-5%分类返现）
        # 假设消费分布：餐饮30%（5%返现）、加油20%（5%返现）、其他50%（1%返现）
        proposed_cashback = (
            (monthly_spending * 0.30 * 0.05) +  # 餐饮5%
            (monthly_spending * 0.20 * 0.05) +  # 加油5%
            (monthly_spending * 0.50 * 0.01)    # 其他1%
        )
        
        monthly_increase = proposed_cashback - current_monthly_cashback
        annual_increase = monthly_increase * 12
        
        return {
            'type': 'cashback_optimization',
            'title': '现金返现最大化方案',
            'description': '使用分类返现信用卡最大化返现收益',
            'current': {
                'cashback_rate': current_cashback_rate,
                'monthly_cashback': current_monthly_cashback,
                'annual_cashback': current_monthly_cashback * 12
            },
            'proposed': {
                'avg_cashback_rate': (proposed_cashback / monthly_spending * 100),
                'monthly_cashback': proposed_cashback,
                'annual_cashback': proposed_cashback * 12,
                'breakdown': {
                    'dining_5pct': monthly_spending * 0.30 * 0.05,
                    'petrol_5pct': monthly_spending * 0.20 * 0.05,
                    'others_1pct': monthly_spending * 0.50 * 0.01
                }
            },
            'earnings': {
                'monthly_increase': monthly_increase,
                'annual_increase': annual_increase,
                'percentage_increase': ((proposed_cashback - current_monthly_cashback) / current_monthly_cashback * 100) if current_monthly_cashback > 0 else 0
            }
        }
    
    def generate_comprehensive_proposal(self, customer_data):
        """
        生成综合优化方案
        
        分析客户情况，生成所有适用的优化建议
        
        Returns:
            dict: 包含所有方案和总体节省/收益
        """
        current_status = self.analyze_customer_status(customer_data)
        
        proposals = []
        total_monthly_benefit = 0
        total_annual_benefit = 0
        
        # 1. 如果有债务，生成债务整合方案
        if current_status['total_debt'] > 5000:
            debt_proposal = self.generate_debt_consolidation_proposal(current_status)
            proposals.append(debt_proposal)
            total_monthly_benefit += debt_proposal['savings']['monthly']
            total_annual_benefit += debt_proposal['savings']['annual']
        
        # 2. 如果有高余额，生成余额转移方案
        if current_status['total_debt'] > 3000:
            balance_proposal = self.generate_balance_transfer_proposal(current_status)
            proposals.append(balance_proposal)
            # 余额转移节省（仅计入促销期平均）
            total_monthly_benefit += balance_proposal['savings']['monthly_equivalent']
        
        # 3. 如果有消费，生成现金返现优化方案
        if current_status['monthly_spending'] > 1000:
            cashback_proposal = self.generate_cashback_optimization_proposal(current_status)
            proposals.append(cashback_proposal)
            total_monthly_benefit += cashback_proposal['earnings']['monthly_increase']
            total_annual_benefit += cashback_proposal['earnings']['annual_increase']
        
        # 计算50/50利润分成
        advisor_monthly_fee = total_monthly_benefit * 0.5
        advisor_annual_fee = total_annual_benefit * 0.5
        customer_net_monthly_benefit = total_monthly_benefit * 0.5
        customer_net_annual_benefit = total_annual_benefit * 0.5
        
        return {
            'customer_name': customer_data.get('name', 'Unknown'),
            'analysis_date': customer_data.get('date', ''),
            'current_status': current_status,
            'proposals': proposals,
            'total_benefit': {
                'gross_monthly': total_monthly_benefit,
                'gross_annual': total_annual_benefit,
                'customer_net_monthly': customer_net_monthly_benefit,
                'customer_net_annual': customer_net_annual_benefit,
                'advisor_monthly_fee': advisor_monthly_fee,
                'advisor_annual_fee': advisor_annual_fee
            },
            'num_proposals': len(proposals),
            'estimated_implementation_time': '2-4 weeks'
        }
    
    def format_proposal_comparison(self, proposal):
        """
        格式化方案对比展示
        生成清晰的对比数据，用于前端展示
        
        Returns:
            dict: 格式化的对比数据
        """
        comparison = {
            'title': '💰 财务优化方案对比',
            'subtitle': f'为 {proposal["customer_name"]} 量身定制',
            'summary': {
                'total_monthly_saving': proposal['total_benefit']['gross_monthly'],
                'total_annual_saving': proposal['total_benefit']['gross_annual'],
                'customer_net_monthly': proposal['total_benefit']['customer_net_monthly'],
                'customer_net_annual': proposal['total_benefit']['customer_net_annual']
            },
            'proposals_detail': proposal['proposals'],
            'profit_sharing': {
                'model': '零风险50/50利润分成',
                'description': '只在实际节省/收益后收费',
                'customer_keeps': '50%',
                'advisor_fee': '50%',
                'customer_monthly_net': proposal['total_benefit']['customer_net_monthly'],
                'advisor_monthly_fee': proposal['total_benefit']['advisor_monthly_fee']
            },
            'cta': {
                'primary': '申请了解完整优化方案',
                'secondary': '查看详细计算过程',
                'urgency': f'立即行动，每月可净赚 RM {proposal["total_benefit"]["customer_net_monthly"]:.2f}'
            }
        }
        
        return comparison


# 示例用法
if __name__ == "__main__":
    optimizer = OptimizationProposal()
    
    # 示例客户数据
    sample_customer = {
        'name': 'cheok jun yoon',
        'monthly_income': 6000,
        'monthly_spending': 3500,
        'cards': [
            {'bank_name': 'Maybank', 'current_balance': 8000, 'credit_limit': 15000},
            {'bank_name': 'CIMB', 'current_balance': 5000, 'credit_limit': 10000},
            {'bank_name': 'Public Bank', 'current_balance': 3000, 'credit_limit': 8000}
        ]
    }
    
    # 生成方案
    proposal = optimizer.generate_comprehensive_proposal(sample_customer)
    comparison = optimizer.format_proposal_comparison(proposal)
    
    print(json.dumps(comparison, indent=2, ensure_ascii=False))
