"""
Bank Statement Analyzer - 银行流水分析器
自动分析银行对账单，计算现金流波动率

功能：
- 分析月度现金流
- 计算Cashflow Variance
- 检测不规则模式
"""
from typing import Dict, List, Optional
import statistics


class BankStatementAnalyzer:
    """银行流水分析器"""
    
    @staticmethod
    def analyze_monthly_cashflow(transactions: List[Dict]) -> Dict:
        """
        分析月度现金流
        
        Args:
            transactions: 交易列表
                [
                    {"date": "2025-01", "type": "inflow", "amount": 50000},
                    {"date": "2025-01", "type": "outflow", "amount": 30000},
                    ...
                ]
                
        Returns:
            {
                "monthly_cashflow": List[Dict],
                "variance": float (0~1),
                "irregularities": List[str],
                "confidence": float
            }
        """
        if not transactions:
            return {
                "monthly_cashflow": [],
                "variance": 0.30,  # 默认中等波动
                "irregularities": [],
                "confidence": 0.30,
                "source": "no_data"
            }
        
        # 按月份聚合
        monthly_data = BankStatementAnalyzer._aggregate_by_month(transactions)
        
        # 计算variance
        variance = BankStatementAnalyzer.calculate_variance(monthly_data)
        
        # 检测不规则模式
        irregularities = BankStatementAnalyzer.detect_irregularities(monthly_data)
        
        return {
            "monthly_cashflow": monthly_data,
            "variance": variance,
            "irregularities": irregularities,
            "confidence": 0.85,
            "source": "bank_statement"
        }
    
    @staticmethod
    def _aggregate_by_month(transactions: List[Dict]) -> List[Dict]:
        """按月份聚合现金流"""
        monthly_map = {}
        
        for txn in transactions:
            month = txn.get("date", "")[:7]  # YYYY-MM
            txn_type = txn.get("type", "")
            amount = txn.get("amount", 0)
            
            if month not in monthly_map:
                monthly_map[month] = {"month": month, "inflow": 0, "outflow": 0, "net": 0}
            
            if txn_type == "inflow":
                monthly_map[month]["inflow"] += amount
            elif txn_type == "outflow":
                monthly_map[month]["outflow"] += amount
        
        # 计算净现金流
        for month_data in monthly_map.values():
            month_data["net"] = month_data["inflow"] - month_data["outflow"]
        
        return sorted(monthly_map.values(), key=lambda x: x["month"])
    
    @staticmethod
    def calculate_variance(monthly_cashflow: List[Dict]) -> float:
        """
        计算现金流波动率 (Coefficient of Variation)
        
        Variance = StdDev / Mean
        
        Returns:
            0~1的浮点数（0=完全稳定，1=极度波动）
        """
        if len(monthly_cashflow) < 2:
            return 0.30  # 默认中等
        
        net_flows = [m["net"] for m in monthly_cashflow]
        
        # 过滤负值（使用绝对值）
        abs_flows = [abs(f) for f in net_flows]
        
        if not abs_flows:
            return 0.30
        
        mean = statistics.mean(abs_flows)
        if mean == 0:
            return 1.0  # 完全波动
        
        try:
            stdev = statistics.stdev(abs_flows)
            variance = stdev / mean
            
            # 限制在0~1范围
            return min(1.0, max(0.0, variance))
        except:
            return 0.30
    
    @staticmethod
    def detect_irregularities(monthly_cashflow: List[Dict]) -> List[str]:
        """
        检测不规则模式
        
        Returns:
            ["negative_months", "sudden_spike", "declining_trend", ...]
        """
        irregularities = []
        
        if len(monthly_cashflow) < 3:
            return irregularities
        
        net_flows = [m["net"] for m in monthly_cashflow]
        
        # 1. 检测负现金流月份
        negative_count = sum(1 for f in net_flows if f < 0)
        if negative_count >= len(net_flows) * 0.3:  # 30%以上负现金流
            irregularities.append("frequent_negative_months")
        
        # 2. 检测突然激增
        for i in range(1, len(net_flows)):
            if net_flows[i] > net_flows[i-1] * 3:  # 3倍激增
                irregularities.append("sudden_spike")
                break
        
        # 3. 检测下降趋势
        if len(net_flows) >= 6:
            recent_avg = statistics.mean(net_flows[-3:])
            older_avg = statistics.mean(net_flows[:3])
            
            if recent_avg < older_avg * 0.7:  # 下降超过30%
                irregularities.append("declining_trend")
        
        # 4. 检测极端波动
        if len(net_flows) >= 4:
            try:
                stdev = statistics.stdev(net_flows)
                mean = statistics.mean(net_flows)
                if abs(mean) > 0 and stdev / abs(mean) > 0.8:
                    irregularities.append("extreme_volatility")
            except:
                pass
        
        return irregularities
    
    @staticmethod
    def auto_analyze_cashflow(customer_id: int, db) -> Dict:
        """
        自动从系统中查找客户的银行流水并分析
        
        Args:
            customer_id: 客户ID
            db: 数据库连接
            
        Returns:
            现金流分析结果
        """
        # TODO: 从transactions表中提取客户流水
        # TODO: 调用analyze_monthly_cashflow分析
        
        # 当前返回默认值
        return {
            "monthly_cashflow": [],
            "variance": 0.30,
            "irregularities": [],
            "confidence": 0.50,
            "source": "auto_detected",
            "note": "Using default - insufficient transaction data"
        }
