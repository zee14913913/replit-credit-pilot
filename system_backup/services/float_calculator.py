"""
Float Days Calculator - 免息期计算引擎
计算信用卡消费的免息天数，帮助客户最大化资金使用时间
"""

from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from typing import Dict, List, Optional
import calendar


class FloatDaysCalculator:
    """免息期计算器"""
    
    def calculate_float_days(self, purchase_date: date, 
                            cutoff_day: int, 
                            due_day: int) -> Dict:
        """
        计算单笔消费的免息天数
        
        Args:
            purchase_date: 消费日期
            cutoff_day: 账单日（每月1-31号）
            due_day: 到期日（每月1-31号）
        
        Returns:
            {
                'float_days': int,           # 免息天数
                'statement_date': date,      # 账单日期
                'due_date': date,            # 到期日期
                'billing_cycle': str         # 账单周期 YYYY-MM
            }
        """
        # Step 1: 确定消费属于哪个账单周期
        if purchase_date.day <= cutoff_day:
            # 消费在本月账单日之前 → 记入本月账单
            statement_month = purchase_date
        else:
            # 消费在本月账单日之后 → 记入下月账单
            statement_month = purchase_date + relativedelta(months=1)
        
        # Step 2: 计算账单日期
        try:
            statement_date = statement_month.replace(day=cutoff_day)
        except ValueError:
            # 处理2月、小月问题（如cutoff_day=31但2月没有31号）
            last_day = calendar.monthrange(statement_month.year, statement_month.month)[1]
            statement_date = statement_month.replace(day=min(cutoff_day, last_day))
        
        # Step 3: 计算到期日期
        # 假设到期日在账单日之后的同一个月或下个月
        try:
            due_date = statement_date.replace(day=due_day)
        except ValueError:
            last_day = calendar.monthrange(statement_date.year, statement_date.month)[1]
            due_date = statement_date.replace(day=min(due_day, last_day))
        
        # 如果到期日在账单日之前或同一天，推到下个月
        if due_date <= statement_date:
            due_date = due_date + relativedelta(months=1)
            try:
                due_date = due_date.replace(day=due_day)
            except ValueError:
                last_day = calendar.monthrange(due_date.year, due_date.month)[1]
                due_date = due_date.replace(day=min(due_day, last_day))
        
        # Step 4: 计算免息天数
        float_days = (due_date - purchase_date).days
        
        return {
            'float_days': float_days,
            'statement_date': statement_date,
            'due_date': due_date,
            'billing_cycle': statement_date.strftime('%Y-%m')
        }
    
    def find_optimal_purchase_window(self, cutoff_day: int, 
                                     due_day: int,
                                     target_month: str) -> Dict:
        """
        找出本月的最佳刷卡窗口（获得最长免息期）
        
        Args:
            cutoff_day: 账单日
            due_day: 到期日
            target_month: 目标月份 "YYYY-MM"
        
        Returns:
            {
                'best_window_start': date,   # 最佳窗口起始
                'best_window_end': date,     # 最佳窗口结束
                'max_float_days': int,       # 最大免息天数
                'worst_window_start': date,  # 最短窗口起始
                'min_float_days': int        # 最小免息天数
            }
        """
        year, month = map(int, target_month.split('-'))
        month_start = date(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        month_end = date(year, month, last_day)
        
        # 模拟整个月每一天的免息期
        float_days_map = {}
        for day in range(1, last_day + 1):
            test_date = date(year, month, day)
            result = self.calculate_float_days(test_date, cutoff_day, due_day)
            float_days_map[test_date] = result['float_days']
        
        # 找出最大和最小免息期
        max_float = max(float_days_map.values())
        min_float = min(float_days_map.values())
        
        # 找出对应的日期区间
        best_dates = [d for d, f in float_days_map.items() if f == max_float]
        worst_dates = [d for d, f in float_days_map.items() if f == min_float]
        
        return {
            'best_window_start': min(best_dates),
            'best_window_end': max(best_dates),
            'max_float_days': max_float,
            'worst_window_start': min(worst_dates),
            'min_float_days': min_float,
            'all_days_map': float_days_map  # 返回完整映射供前端使用
        }
    
    def compare_cards_float_days(self, cards: List[Dict], 
                                 purchase_date: date) -> List[Dict]:
        """
        比较多张卡在同一消费日期的免息天数
        
        Args:
            cards: 信用卡列表，每个包含 {id, bank_name, cutoff_day, due_day}
            purchase_date: 消费日期
        
        Returns:
            按免息天数降序排列的卡片列表
        """
        results = []
        
        for card in cards:
            if not card.get('cutoff_day') or not card.get('due_day'):
                # 跳过没有设置账单日/到期日的卡
                continue
            
            float_result = self.calculate_float_days(
                purchase_date,
                card['cutoff_day'],
                card['due_day']
            )
            
            results.append({
                'card_id': card['id'],
                'bank_name': card['bank_name'],
                'card_number_last4': card.get('card_number_last4'),
                'float_days': float_result['float_days'],
                'statement_date': float_result['statement_date'],
                'due_date': float_result['due_date'],
                'is_optimal': False  # 将在排序后标记
            })
        
        # 按免息天数降序排序
        results.sort(key=lambda x: x['float_days'], reverse=True)
        
        # 标记最优选择
        if results:
            results[0]['is_optimal'] = True
        
        return results
    
    def calculate_batch_float_days(self, card_id: int,
                                   cutoff_day: int,
                                   due_day: int,
                                   date_list: List[date]) -> Dict:
        """
        批量计算多个日期的免息天数
        
        Returns:
            {
                'card_id': int,
                'calculations': [
                    {
                        'purchase_date': date,
                        'float_days': int,
                        'statement_date': date,
                        'due_date': date
                    },
                    ...
                ]
            }
        """
        calculations = []
        
        for purchase_date in date_list:
            result = self.calculate_float_days(purchase_date, cutoff_day, due_day)
            calculations.append({
                'purchase_date': purchase_date,
                'float_days': result['float_days'],
                'statement_date': result['statement_date'],
                'due_date': result['due_date']
            })
        
        return {
            'card_id': card_id,
            'calculations': calculations
        }


# 便捷函数
def calculate_float_for_card(card: Dict, purchase_date: date) -> int:
    """快速计算单张卡的免息天数"""
    calculator = FloatDaysCalculator()
    result = calculator.calculate_float_days(
        purchase_date,
        card['cutoff_day'],
        card['due_day']
    )
    return result['float_days']


# 测试代码
if __name__ == "__main__":
    calc = FloatDaysCalculator()
    
    # 测试用例1: CIMB卡，账单日25号，到期日15号
    test_date = date(2025, 11, 6)
    result = calc.calculate_float_days(test_date, 25, 15)
    
    print("="*60)
    print("测试用例1: CIMB卡免息期计算")
    print("="*60)
    print(f"消费日期: {test_date}")
    print(f"账单日: 每月25号")
    print(f"到期日: 每月15号")
    print(f"\n结果:")
    print(f"  免息天数: {result['float_days']}天")
    print(f"  账单日期: {result['statement_date']}")
    print(f"  到期日期: {result['due_date']}")
    print(f"  账单周期: {result['billing_cycle']}")
    
    # 测试用例2: 找出本月最佳刷卡窗口
    print("\n" + "="*60)
    print("测试用例2: 2025年11月最佳刷卡窗口")
    print("="*60)
    window = calc.find_optimal_purchase_window(25, 15, "2025-11")
    print(f"最佳刷卡窗口: {window['best_window_start']} 至 {window['best_window_end']}")
    print(f"最大免息天数: {window['max_float_days']}天")
    print(f"最短免息天数: {window['min_float_days']}天")
    
    # 测试用例3: 比较多张卡
    print("\n" + "="*60)
    print("测试用例3: 比较多张卡在同一天的免息期")
    print("="*60)
    test_cards = [
        {'id': 1, 'bank_name': 'CIMB', 'cutoff_day': 25, 'due_day': 15},
        {'id': 2, 'bank_name': 'Maybank', 'cutoff_day': 5, 'due_day': 25},
        {'id': 3, 'bank_name': 'UOB', 'cutoff_day': 15, 'due_day': 5}
    ]
    comparison = calc.compare_cards_float_days(test_cards, date(2025, 11, 10))
    
    for i, card in enumerate(comparison, 1):
        optimal_mark = "⭐ 最优" if card['is_optimal'] else ""
        print(f"{i}. {card['bank_name']}: {card['float_days']}天 {optimal_mark}")
