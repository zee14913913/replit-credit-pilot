"""
Card Optimizer - 排卡优化引擎
基于免息期、可用额度、使用率等多维度评分，为客户推荐最优刷卡方案
"""

from datetime import date
from typing import Dict, List, Optional
from services.float_calculator import FloatDaysCalculator


class CardOptimizer:
    """排卡优先级评分引擎"""
    
    # 默认评分权重
    WEIGHTS = {
        'float_days': 2.0,              # 免息期权重（最重要）
        'available_credit': 1.0,         # 可用额度权重
        'low_utilization_bonus': 0.5,    # 低使用率奖励
        'risk_penalty': 3.0              # 高风险惩罚
    }
    
    # 风险阈值
    RISK_THRESHOLDS = {
        'utilization_high': 80.0,        # 使用率>80%为高风险
        'utilization_critical': 90.0,    # 使用率>90%为极高风险
        'min_available_buffer': 500.0    # 最小可用余额缓冲（RM）
    }
    
    def __init__(self, weights: Optional[Dict] = None):
        """初始化优化器，可自定义权重"""
        if weights:
            self.WEIGHTS.update(weights)
        self.float_calc = FloatDaysCalculator()
    
    def calculate_card_score(self, card: Dict, 
                            purchase_date: date,
                            expected_amount: float) -> Dict:
        """
        计算单张卡的优先级评分
        
        Args:
            card: {
                'id': int,
                'bank_name': str,
                'credit_limit': float,
                'current_balance': float,
                'cutoff_day': int,
                'due_day': int,
                'card_number_last4': str (optional)
            }
            purchase_date: 计划消费日期
            expected_amount: 预计消费金额
        
        Returns:
            {
                'card_id': int,
                'score': float,
                'float_days': int,
                'utilization_after': float,
                'risk_level': str,
                'recommendation': str,
                'is_recommended': bool
            }
        """
        # 验证必要字段
        if not card.get('cutoff_day') or not card.get('due_day'):
            return {
                'card_id': card['id'],
                'score': 0,
                'error': '此卡未设置账单日/到期日，无法计算',
                'is_recommended': False
            }
        
        # 1. 计算免息期
        float_result = self.float_calc.calculate_float_days(
            purchase_date, 
            card['cutoff_day'], 
            card['due_day']
        )
        float_days = float_result['float_days']
        
        # 2. 计算可用额度比例
        credit_limit = card.get('credit_limit', 0)
        current_balance = card.get('current_balance', 0)
        
        if credit_limit <= 0:
            return {
                'card_id': card['id'],
                'score': 0,
                'error': '此卡额度为0，无法使用',
                'is_recommended': False
            }
        
        available_credit = credit_limit - current_balance
        available_ratio = (available_credit / credit_limit) * 100
        
        # 3. 计算消费后使用率
        utilization_after = ((current_balance + expected_amount) / credit_limit) * 100
        
        # 4. 风险评估
        risk_level, risk_penalty = self._assess_risk(
            utilization_after, 
            available_credit, 
            expected_amount
        )
        
        # 5. 计算总分
        score = (
            self.WEIGHTS['float_days'] * float_days +
            self.WEIGHTS['available_credit'] * available_ratio +
            self.WEIGHTS['low_utilization_bonus'] * (100 - utilization_after) -
            self.WEIGHTS['risk_penalty'] * risk_penalty
        )
        
        # 6. 生成推荐说明
        recommendation = self._generate_recommendation(
            float_days, utilization_after, risk_level, available_credit, expected_amount
        )
        
        return {
            'card_id': card['id'],
            'bank_name': card['bank_name'],
            'card_number_last4': card.get('card_number_last4'),
            'score': round(score, 2),
            'float_days': float_days,
            'utilization_current': round((current_balance / credit_limit) * 100, 2),
            'utilization_after': round(utilization_after, 2),
            'available_credit': round(available_credit, 2),
            'risk_level': risk_level,
            'recommendation': recommendation,
            'is_recommended': risk_level != 'critical',
            'statement_date': float_result['statement_date'],
            'due_date': float_result['due_date']
        }
    
    def _assess_risk(self, utilization: float, 
                     available: float, 
                     amount: float) -> tuple:
        """
        风险评估
        
        Returns:
            (risk_level, risk_penalty)
            - risk_level: 'low', 'medium', 'high', 'critical'
            - risk_penalty: 0-20的惩罚分数
        """
        # 极高风险：额度不足
        if available < amount:
            return ('critical', 20.0)
        
        # 极高风险：使用率>90%
        if utilization > self.RISK_THRESHOLDS['utilization_critical']:
            return ('critical', 15.0)
        
        # 高风险：使用率>80%
        if utilization > self.RISK_THRESHOLDS['utilization_high']:
            return ('high', 10.0)
        
        # 中风险：剩余额度<缓冲金额
        if available - amount < self.RISK_THRESHOLDS['min_available_buffer']:
            return ('medium', 5.0)
        
        # 低风险
        return ('low', 0.0)
    
    def _generate_recommendation(self, float_days: int, 
                                utilization: float, 
                                risk: str,
                                available: float,
                                amount: float) -> str:
        """生成推荐说明"""
        # 极高风险警告
        if risk == 'critical':
            if available < amount:
                return f"❌ 不推荐：可用额度不足（需要RM {amount:.2f}，仅剩RM {available:.2f}）"
            else:
                return f"❌ 不推荐：使用率过高（{utilization:.1f}%），可能影响信用评分"
        
        # 高风险警告
        if risk == 'high':
            return f"⚠️ 谨慎使用：使用率将达{utilization:.1f}%，建议先还款后使用"
        
        # 根据免息期评级
        if float_days >= 50:
            return f"✅ 强烈推荐：{float_days}天免息期，资金周转时间长"
        elif float_days >= 40:
            return f"✓ 推荐：{float_days}天免息期，较为理想"
        elif float_days >= 30:
            return f"○ 可用：{float_days}天免息期，一般"
        else:
            return f"△ 免息期较短：仅{float_days}天"
    
    def optimize_for_customer(self, cards: List[Dict], 
                             purchase_date: date,
                             total_amount: float) -> Dict:
        """
        为客户优化排卡方案
        
        Args:
            cards: 客户所有信用卡列表
            purchase_date: 计划消费日期
            total_amount: 总消费金额
        
        Returns:
            {
                'recommended_cards': List[Dict],  # 按优先级排序
                'total_available': float,
                'is_sufficient': bool,
                'warnings': List[str]
            }
        """
        if not cards:
            return {
                'recommended_cards': [],
                'total_available': 0,
                'is_sufficient': False,
                'warnings': ['客户没有任何信用卡']
            }
        
        # 计算所有卡的评分
        scored_cards = []
        total_available = 0
        warnings = []
        
        for card in cards:
            score_result = self.calculate_card_score(card, purchase_date, total_amount)
            
            if 'error' in score_result:
                warnings.append(f"{card['bank_name']}: {score_result['error']}")
            else:
                scored_cards.append(score_result)
                total_available += score_result['available_credit']
        
        # 按评分排序
        scored_cards.sort(key=lambda x: x['score'], reverse=True)
        
        # 标记优先级
        for i, card in enumerate(scored_cards, 1):
            card['priority_rank'] = i
        
        # 检查总额度是否足够
        is_sufficient = total_available >= total_amount
        
        if not is_sufficient:
            warnings.append(
                f"⚠️ 总可用额度不足：需要RM {total_amount:.2f}，仅剩RM {total_available:.2f}"
            )
        
        return {
            'recommended_cards': scored_cards,
            'total_available': round(total_available, 2),
            'is_sufficient': is_sufficient,
            'warnings': warnings
        }
    
    def suggest_optimal_window(self, card: Dict, 
                              target_month: str) -> Dict:
        """
        为单张卡建议本月最佳刷卡窗口
        
        Returns:
            {
                'card_id': int,
                'best_window': {
                    'start': date,
                    'end': date,
                    'max_float_days': int
                },
                'calendar_heatmap': Dict[date, int]  # 每天的免息天数
            }
        """
        window = self.float_calc.find_optimal_purchase_window(
            card['cutoff_day'],
            card['due_day'],
            target_month
        )
        
        return {
            'card_id': card['id'],
            'bank_name': card['bank_name'],
            'best_window': {
                'start': window['best_window_start'],
                'end': window['best_window_end'],
                'max_float_days': window['max_float_days']
            },
            'worst_window': {
                'start': window['worst_window_start'],
                'min_float_days': window['min_float_days']
            },
            'calendar_heatmap': window['all_days_map']
        }


# 测试代码
if __name__ == "__main__":
    optimizer = CardOptimizer()
    
    # 测试用例：客户有3张卡
    test_cards = [
        {
            'id': 1,
            'bank_name': 'CIMB Visa Signature',
            'credit_limit': 10000,
            'current_balance': 4500,
            'cutoff_day': 25,
            'due_day': 15,
            'card_number_last4': '1234'
        },
        {
            'id': 2,
            'bank_name': 'Maybank Platinum',
            'credit_limit': 8000,
            'current_balance': 6500,
            'cutoff_day': 5,
            'due_day': 25,
            'card_number_last4': '5678'
        },
        {
            'id': 3,
            'bank_name': 'UOB One Card',
            'credit_limit': 12000,
            'current_balance': 2000,
            'cutoff_day': 15,
            'due_day': 5,
            'card_number_last4': '9012'
        }
    ]
    
    test_date = date(2025, 11, 10)
    test_amount = 5000
    
    print("="*80)
    print("智能排卡优化测试")
    print("="*80)
    print(f"消费日期: {test_date}")
    print(f"消费金额: RM {test_amount:,.2f}\n")
    
    result = optimizer.optimize_for_customer(test_cards, test_date, test_amount)
    
    print(f"总可用额度: RM {result['total_available']:,.2f}")
    print(f"额度是否充足: {'✅ 是' if result['is_sufficient'] else '❌ 否'}\n")
    
    print("推荐卡片排序：")
    print("-" * 80)
    for card in result['recommended_cards']:
        print(f"\n{card['priority_rank']}. {card['bank_name']} (*{card['card_number_last4']})")
        print(f"   评分: {card['score']:.2f} 分")
        print(f"   免息期: {card['float_days']}天")
        print(f"   使用率: {card['utilization_current']:.1f}% → {card['utilization_after']:.1f}%")
        print(f"   可用额度: RM {card['available_credit']:,.2f}")
        print(f"   风险等级: {card['risk_level']}")
        print(f"   建议: {card['recommendation']}")
    
    if result['warnings']:
        print("\n⚠️ 警告：")
        for warning in result['warnings']:
            print(f"  - {warning}")
