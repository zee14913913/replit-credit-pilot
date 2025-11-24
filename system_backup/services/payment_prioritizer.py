"""
Payment Prioritizer - 还款优先级引擎
根据到期日、利率、余额等因素，为客户制定最优还款计划
"""

from datetime import date, timedelta
from typing import Dict, List, Optional


class PaymentPrioritizer:
    """还款优先级引擎"""
    
    # 紧迫程度阈值
    URGENCY_THRESHOLDS = {
        'critical': 3,    # ≤3天为危急
        'urgent': 7,      # ≤7天为紧急
        'normal': 14,     # ≤14天为正常
        'low': 30         # >30天为低优先级
    }
    
    def __init__(self):
        pass
    
    def prioritize_payments(self, cards: List[Dict], 
                           available_funds: float,
                           target_date: Optional[date] = None) -> Dict:
        """
        计算还款优先级
        
        Args:
            cards: 所有信用卡数据，每个包含：
                {
                    'id': int,
                    'bank_name': str,
                    'current_balance': float,
                    'next_due_date': date,
                    'interest_rate': float (optional, default 18.0),
                    'min_payment_rate': float (optional, default 5.0)
                }
            available_funds: 可用还款资金
            target_date: 目标日期（默认为今天）
        
        Returns:
            {
                'payment_plans': List[Dict],  # 按优先级排序的还款计划
                'total_minimum': float,
                'total_recommended': float,
                'funding_gap': float,
                'warnings': List[str]
            }
        """
        if target_date is None:
            target_date = date.today()
        
        payment_plans = []
        total_minimum = 0
        total_recommended = 0
        warnings = []
        
        for card in cards:
            if card.get('current_balance', 0) <= 0:
                continue  # 跳过无余额的卡
            
            # 计算到期紧迫性（距离到期日天数）
            due_date = card.get('next_due_date')
            if not due_date:
                warnings.append(f"{card['bank_name']}: 未设置到期日")
                continue
            
            if isinstance(due_date, str):
                due_date = date.fromisoformat(due_date)
            
            days_to_due = (due_date - target_date).days
            
            # 计算最低还款额（默认5%）
            min_payment_rate = card.get('min_payment_rate', 5.0) / 100
            min_payment = card['current_balance'] * min_payment_rate
            
            # 计算建议还款额
            recommended_payment = self._calculate_recommended_payment(
                card, available_funds, min_payment
            )
            
            # 优先级评分（越高越优先）
            priority_score = self._calculate_priority_score(
                card, days_to_due
            )
            
            # 紧迫程度
            urgency_level = self._get_urgency_level(days_to_due)
            
            payment_plans.append({
                'card_id': card['id'],
                'bank_name': card['bank_name'],
                'current_balance': card['current_balance'],
                'due_date': due_date,
                'days_to_due': days_to_due,
                'minimum_payment': round(min_payment, 2),
                'recommended_payment': round(recommended_payment, 2),
                'priority_score': round(priority_score, 2),
                'urgency_level': urgency_level,
                'interest_rate': card.get('interest_rate', 18.0),
                'funding_source': 'self'  # 默认自有资金
            })
            
            total_minimum += min_payment
            total_recommended += recommended_payment
        
        # 按优先级排序
        payment_plans.sort(key=lambda x: x['priority_score'], reverse=True)
        
        # 标记优先级顺序
        for i, plan in enumerate(payment_plans, 1):
            plan['priority_order'] = i
        
        # 计算资金缺口
        funding_gap = total_minimum - available_funds
        
        if funding_gap > 0:
            warnings.append(
                f"⚠️ 资金不足：最低还款需RM {total_minimum:.2f}，仅有RM {available_funds:.2f}，缺口RM {funding_gap:.2f}"
            )
        
        # 检查紧急到期的卡
        critical_cards = [p for p in payment_plans if p['urgency_level'] == 'critical']
        if critical_cards:
            warnings.append(
                f"🔴 紧急：{len(critical_cards)}张卡将在3天内到期"
            )
        
        return {
            'payment_plans': payment_plans,
            'total_minimum': round(total_minimum, 2),
            'total_recommended': round(total_recommended, 2),
            'funding_gap': round(max(funding_gap, 0), 2),
            'warnings': warnings
        }
    
    def _calculate_priority_score(self, card: Dict, days_to_due: int) -> float:
        """
        计算还款优先级评分
        
        评分规则：
        - 越快到期，分数越高
        - 高利率优先
        - 高余额优先
        """
        # 1. 时间紧迫性（权重最高）
        if days_to_due <= 0:
            time_score = 200  # 已逾期，极高优先级
        elif days_to_due <= 3:
            time_score = 100
        elif days_to_due <= 7:
            time_score = 50
        elif days_to_due <= 14:
            time_score = 25
        else:
            time_score = max(0, 30 - days_to_due)  # 越远越低
        
        # 2. 利率因素（权重次高）
        interest_rate = card.get('interest_rate', 18.0)
        interest_score = interest_rate * 2  # 高利率优先
        
        # 3. 余额因素（权重最低）
        balance_score = card['current_balance'] / 1000  # 高余额优先
        
        # 综合评分
        total_score = time_score + interest_score + balance_score
        
        return total_score
    
    def _calculate_recommended_payment(self, card: Dict, 
                                      available: float,
                                      min_payment: float) -> float:
        """
        计算建议还款额
        
        策略：
        - 如果可用资金充足，建议全额还款
        - 否则，建议还款30%余额（高于最低还款）
        - 至少保证最低还款额
        """
        balance = card['current_balance']
        
        # 策略1：全额还款
        if available >= balance:
            return balance
        
        # 策略2：30%余额
        recommended = balance * 0.30
        
        # 策略3：至少最低还款
        if available < min_payment:
            return min_payment  # 即使资金不足也返回最低还款（会触发警告）
        
        return max(recommended, min_payment)
    
    def _get_urgency_level(self, days: int) -> str:
        """紧迫程度分级"""
        if days <= 0:
            return 'overdue'  # 已逾期
        elif days <= self.URGENCY_THRESHOLDS['critical']:
            return 'critical'
        elif days <= self.URGENCY_THRESHOLDS['urgent']:
            return 'urgent'
        elif days <= self.URGENCY_THRESHOLDS['normal']:
            return 'normal'
        else:
            return 'low'
    
    def allocate_funds(self, payment_plans: List[Dict], 
                      available_funds: float) -> Dict:
        """
        智能分配可用资金到各张卡
        
        策略：
        1. 优先保证所有卡的最低还款
        2. 剩余资金按优先级分配
        """
        # 深拷贝计划避免修改原数据
        plans = [p.copy() for p in payment_plans]
        remaining_funds = available_funds
        allocations = []
        
        # Phase 1: 保证所有卡的最低还款
        for plan in plans:
            min_pay = plan['minimum_payment']
            if remaining_funds >= min_pay:
                plan['allocated_amount'] = min_pay
                remaining_funds -= min_pay
            else:
                plan['allocated_amount'] = remaining_funds
                remaining_funds = 0
                break
        
        # Phase 2: 剩余资金按优先级分配
        for plan in plans:
            if remaining_funds <= 0:
                break
            
            current_allocated = plan.get('allocated_amount', 0)
            max_needed = plan['current_balance'] - current_allocated
            
            if max_needed > 0:
                additional = min(remaining_funds, max_needed)
                plan['allocated_amount'] = current_allocated + additional
                remaining_funds -= additional
        
        # 生成分配结果
        for plan in plans:
            allocation = plan.get('allocated_amount', 0)
            allocations.append({
                'card_id': plan['card_id'],
                'bank_name': plan['bank_name'],
                'allocated_amount': round(allocation, 2),
                'is_minimum_met': allocation >= plan['minimum_payment'],
                'is_full_payment': allocation >= plan['current_balance']
            })
        
        return {
            'allocations': allocations,
            'total_allocated': round(available_funds - remaining_funds, 2),
            'remaining_funds': round(remaining_funds, 2)
        }


# 测试代码
if __name__ == "__main__":
    prioritizer = PaymentPrioritizer()
    
    # 测试用例
    test_cards = [
        {
            'id': 1,
            'bank_name': 'UOB One Card',
            'current_balance': 2500,
            'next_due_date': date.today() + timedelta(days=3),
            'interest_rate': 18.0,
            'min_payment_rate': 5.0
        },
        {
            'id': 2,
            'bank_name': 'Maybank Platinum',
            'current_balance': 5000,
            'next_due_date': date.today() + timedelta(days=15),
            'interest_rate': 15.0,
            'min_payment_rate': 5.0
        },
        {
            'id': 3,
            'bank_name': 'CIMB Visa',
            'current_balance': 3000,
            'next_due_date': date.today() + timedelta(days=7),
            'interest_rate': 20.0,
            'min_payment_rate': 5.0
        }
    ]
    
    available_funds = 1500
    
    print("="*80)
    print("还款优先级测试")
    print("="*80)
    print(f"可用资金: RM {available_funds:,.2f}\n")
    
    result = prioritizer.prioritize_payments(test_cards, available_funds)
    
    print(f"最低还款总额: RM {result['total_minimum']:,.2f}")
    print(f"建议还款总额: RM {result['total_recommended']:,.2f}")
    print(f"资金缺口: RM {result['funding_gap']:,.2f}\n")
    
    print("还款计划（按优先级排序）：")
    print("-" * 80)
    
    for plan in result['payment_plans']:
        urgency_emoji = {
            'critical': '🔴',
            'urgent': '🟠',
            'normal': '🟡',
            'low': '🟢'
        }.get(plan['urgency_level'], '')
        
        print(f"\n{plan['priority_order']}. {urgency_emoji} {plan['bank_name']}")
        print(f"   余额: RM {plan['current_balance']:,.2f}")
        print(f"   到期: {plan['due_date']} ({plan['days_to_due']}天后)")
        print(f"   最低还款: RM {plan['minimum_payment']:,.2f}")
        print(f"   建议还款: RM {plan['recommended_payment']:,.2f}")
        print(f"   利率: {plan['interest_rate']:.1f}%")
        print(f"   优先级评分: {plan['priority_score']:.2f}")
    
    if result['warnings']:
        print("\n⚠️ 警告：")
        for warning in result['warnings']:
            print(f"  {warning}")
    
    # 测试资金分配
    print("\n" + "="*80)
    print("智能资金分配测试")
    print("="*80)
    allocation = prioritizer.allocate_funds(result['payment_plans'], available_funds)
    
    for alloc in allocation['allocations']:
        status = "✅" if alloc['is_minimum_met'] else "❌"
        full = "（全额）" if alloc['is_full_payment'] else ""
        print(f"{status} {alloc['bank_name']}: RM {alloc['allocated_amount']:,.2f} {full}")
    
    print(f"\n总分配: RM {allocation['total_allocated']:,.2f}")
    print(f"剩余资金: RM {allocation['remaining_funds']:,.2f}")
