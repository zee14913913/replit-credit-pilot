"""
Risk Validator - 风险验证器
评估信用卡使用方案的风险等级，并生成风险告知内容
"""

from datetime import date
from typing import Dict, List, Optional


class RiskValidator:
    """风险验证器"""
    
    # 风险阈值配置
    THRESHOLDS = {
        'utilization_high': 80.0,         # 使用率>80%为高风险
        'utilization_critical': 90.0,     # 使用率>90%为极高风险
        'total_debt_income_ratio': 3.0,   # 总欠款>月收入3倍为高风险
        'days_to_due_critical': 3,        # ≤3天到期为危急
        'min_emergency_buffer': 1000.0    # 最低应急缓冲（RM）
    }
    
    # 风险类型定义
    RISK_TYPES = {
        'high_utilization': '信用卡使用率过高',
        'insufficient_funds': '还款资金不足',
        'delayed_payment': '即将逾期',
        'over_leverage': '债务杠杆过高',
        'no_emergency_fund': '缺少应急资金',
        'multiple_cards_critical': '多张卡同时到期'
    }
    
    def __init__(self):
        pass
    
    def validate_card_usage(self, card: Dict, 
                           planned_amount: float,
                           customer_monthly_income: Optional[float] = None) -> Dict:
        """
        验证单张卡使用计划的风险
        
        Args:
            card: {
                'id': int,
                'bank_name': str,
                'credit_limit': float,
                'current_balance': float
            }
            planned_amount: 计划消费金额
            customer_monthly_income: 客户月收入（可选）
        
        Returns:
            {
                'card_id': int,
                'risk_level': str,  # low, medium, high, critical
                'risk_score': float,  # 0-100
                'risks': List[Dict],  # 识别出的风险列表
                'warnings': List[str],
                'requires_consent': bool
            }
        """
        risks = []
        warnings = []
        risk_score = 0
        
        credit_limit = card.get('credit_limit', 0)
        current_balance = card.get('current_balance', 0)
        
        if credit_limit <= 0:
            return {
                'card_id': card['id'],
                'risk_level': 'critical',
                'risk_score': 100,
                'risks': [{'type': 'invalid_card', 'description': '此卡额度为0或无效'}],
                'warnings': ['此卡无法使用'],
                'requires_consent': False
            }
        
        # 计算使用率
        available = credit_limit - current_balance
        utilization_after = ((current_balance + planned_amount) / credit_limit) * 100
        
        # 风险1：额度不足
        if available < planned_amount:
            risks.append({
                'type': 'insufficient_credit',
                'severity': 'critical',
                'description': f'可用额度不足：需要RM {planned_amount:.2f}，仅剩RM {available:.2f}',
                'impact': '交易可能被拒绝'
            })
            risk_score += 50
            warnings.append('❌ 额度不足，无法完成此交易')
        
        # 风险2：使用率过高
        elif utilization_after > self.THRESHOLDS['utilization_critical']:
            risks.append({
                'type': 'high_utilization',
                'severity': 'critical',
                'description': f'使用率将达{utilization_after:.1f}%（极高）',
                'impact': '可能严重影响信用评分，增加利息负担'
            })
            risk_score += 40
            warnings.append(f'⚠️ 使用率过高：{utilization_after:.1f}%')
        
        elif utilization_after > self.THRESHOLDS['utilization_high']:
            risks.append({
                'type': 'high_utilization',
                'severity': 'high',
                'description': f'使用率将达{utilization_after:.1f}%（较高）',
                'impact': '可能影响信用评分'
            })
            risk_score += 25
            warnings.append(f'⚠️ 使用率较高：{utilization_after:.1f}%')
        
        # 风险3：债务收入比过高（如果提供了月收入）
        if customer_monthly_income and customer_monthly_income > 0:
            total_debt = current_balance + planned_amount
            debt_income_ratio = total_debt / customer_monthly_income
            
            if debt_income_ratio > self.THRESHOLDS['total_debt_income_ratio']:
                risks.append({
                    'type': 'over_leverage',
                    'severity': 'high',
                    'description': f'总欠款达月收入{debt_income_ratio:.1f}倍',
                    'impact': '债务压力过大，还款能力堪忧'
                })
                risk_score += 30
                warnings.append(f'⚠️ 债务杠杆过高：{debt_income_ratio:.1f}倍月收入')
        
        # 确定风险等级
        if risk_score >= 50:
            risk_level = 'critical'
        elif risk_score >= 30:
            risk_level = 'high'
        elif risk_score >= 15:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        # 判断是否需要用户确认
        requires_consent = risk_level in ['critical', 'high']
        
        return {
            'card_id': card['id'],
            'bank_name': card['bank_name'],
            'risk_level': risk_level,
            'risk_score': min(risk_score, 100),
            'utilization_after': round(utilization_after, 2),
            'risks': risks,
            'warnings': warnings,
            'requires_consent': requires_consent
        }
    
    def validate_payment_plan(self, payment_plans: List[Dict], 
                             available_funds: float) -> Dict:
        """
        验证还款计划的风险
        
        Returns:
            {
                'risk_level': str,
                'risks': List[Dict],
                'warnings': List[str],
                'requires_consent': bool
            }
        """
        risks = []
        warnings = []
        risk_score = 0
        
        # 计算总最低还款
        total_minimum = sum(p.get('minimum_payment', 0) for p in payment_plans)
        
        # 风险1：资金不足以支付最低还款
        if available_funds < total_minimum:
            gap = total_minimum - available_funds
            risks.append({
                'type': 'insufficient_funds',
                'severity': 'critical',
                'description': f'资金不足：最低还款需RM {total_minimum:.2f}，仅有RM {available_funds:.2f}',
                'impact': f'缺口RM {gap:.2f}，将产生逾期罚金和利息'
            })
            risk_score += 50
            warnings.append(f'❌ 资金不足RM {gap:.2f}')
        
        # 风险2：即将逾期的卡
        critical_cards = [
            p for p in payment_plans 
            if p.get('days_to_due', 999) <= self.THRESHOLDS['days_to_due_critical']
        ]
        
        if critical_cards:
            risks.append({
                'type': 'delayed_payment',
                'severity': 'critical',
                'description': f'{len(critical_cards)}张卡将在3天内到期',
                'impact': '极有可能产生逾期记录，影响信用'
            })
            risk_score += 30
            warnings.append(f'🔴 {len(critical_cards)}张卡即将到期')
        
        # 风险3：多张卡同时到期
        urgent_cards = [
            p for p in payment_plans 
            if p.get('days_to_due', 999) <= 7
        ]
        
        if len(urgent_cards) >= 3:
            risks.append({
                'type': 'multiple_cards_critical',
                'severity': 'high',
                'description': f'{len(urgent_cards)}张卡将在一周内到期',
                'impact': '还款压力集中，需要提前准备资金'
            })
            risk_score += 20
            warnings.append(f'⚠️ {len(urgent_cards)}张卡即将到期')
        
        # 确定风险等级
        if risk_score >= 50:
            risk_level = 'critical'
        elif risk_score >= 30:
            risk_level = 'high'
        elif risk_score >= 15:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        return {
            'risk_level': risk_level,
            'risk_score': min(risk_score, 100),
            'risks': risks,
            'warnings': warnings,
            'requires_consent': risk_level in ['critical', 'high']
        }
    
    def generate_consent_text(self, risks: List[Dict], 
                             language: str = 'cn') -> Dict:
        """
        生成风险告知文本（中英双语）
        
        Returns:
            {
                'title': str,
                'content': str,
                'bullet_points': List[str],
                'disclaimer': str
            }
        """
        if language == 'cn':
            title = "⚠️ 风险告知"
            
            bullet_points = []
            for risk in risks:
                if risk['severity'] in ['critical', 'high']:
                    bullet_points.append(f"• {risk['description']} → {risk['impact']}")
            
            disclaimer = (
                "我已了解上述风险，并同意承担由此产生的所有后果。"
                "我理解信用卡使用不当可能导致利息、罚金及信用评分下降。"
            )
            
            content = (
                "您计划的操作存在以下风险：\n\n" +
                "\n".join(bullet_points) +
                "\n\n请仔细阅读并确认是否继续。"
            )
        
        else:  # English
            title = "⚠️ Risk Disclosure"
            
            bullet_points = []
            for risk in risks:
                if risk['severity'] in ['critical', 'high']:
                    bullet_points.append(f"• {risk['description']} → {risk['impact']}")
            
            disclaimer = (
                "I have read and understood the risks above, and agree to bear all consequences. "
                "I understand that improper credit card usage may result in interest charges, penalties, "
                "and negative impact on credit score."
            )
            
            content = (
                "Your planned action carries the following risks:\n\n" +
                "\n".join(bullet_points) +
                "\n\nPlease review carefully before proceeding."
            )
        
        return {
            'title': title,
            'content': content,
            'bullet_points': bullet_points,
            'disclaimer': disclaimer
        }
    
    def create_consent_record(self, customer_id: int,
                             plan_id: Optional[int],
                             risk_type: str,
                             risk_description: str,
                             consent_given: bool,
                             ip_address: Optional[str] = None,
                             user_agent: Optional[str] = None) -> Dict:
        """
        创建风险确认记录（待插入数据库）
        
        Returns:
            待插入risk_consents表的记录
        """
        from datetime import datetime
        
        return {
            'customer_id': customer_id,
            'plan_id': plan_id,
            'risk_type': risk_type,
            'risk_description': risk_description,
            'consent_given': 1 if consent_given else 0,
            'consent_timestamp': datetime.now() if consent_given else None,
            'ip_address': ip_address,
            'user_agent': user_agent
        }


# 测试代码
if __name__ == "__main__":
    validator = RiskValidator()
    
    # 测试用例1：高使用率风险
    print("="*80)
    print("测试用例1: 高使用率风险")
    print("="*80)
    
    test_card = {
        'id': 1,
        'bank_name': 'CIMB Visa',
        'credit_limit': 10000,
        'current_balance': 8500
    }
    
    result = validator.validate_card_usage(test_card, 1000, customer_monthly_income=5000)
    
    print(f"风险等级: {result['risk_level'].upper()}")
    print(f"风险评分: {result['risk_score']}/100")
    print(f"使用率: {result['utilization_after']:.1f}%")
    print(f"需要用户确认: {'是' if result['requires_consent'] else '否'}\n")
    
    print("识别风险：")
    for risk in result['risks']:
        print(f"  [{risk['severity'].upper()}] {risk['description']}")
        print(f"  → 影响: {risk['impact']}\n")
    
    # 测试用例2: 生成风险告知
    print("="*80)
    print("测试用例2: 生成风险告知文本")
    print("="*80)
    
    consent = validator.generate_consent_text(result['risks'])
    print(consent['title'])
    print("-" * 80)
    print(consent['content'])
    print("\n" + consent['disclaimer'])
