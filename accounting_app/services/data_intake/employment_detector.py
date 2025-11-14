"""
Employment Detector - 就业稳定性检测器
自动检测就业年限和稳定性

功能：
- 从薪资单/EPF记录检测工作年限
- 检测跳槽模式
- 评估就业稳定性
"""
from typing import Dict, List, Optional
from datetime import datetime
from dateutil.relativedelta import relativedelta


class EmploymentDetector:
    """就业稳定性检测器"""
    
    @staticmethod
    def detect_employment_years(documents: List[Dict]) -> Dict:
        """
        检测就业年限
        
        Args:
            documents: 薪资单或EPF记录
                [
                    {
                        "type": "pay_slip" | "epf_statement",
                        "date": "2025-01",
                        "employer": "Company ABC"
                    },
                    ...
                ]
                
        Returns:
            {
                "employment_years": float,
                "stability_score": int (0~100),
                "risk_flag": str,
                "confidence": float
            }
        """
        if not documents:
            return {
                "employment_years": 3.0,  # 默认3年
                "stability_score": 70,
                "risk_flag": "unknown",
                "confidence": 0.30,
                "source": "no_data"
            }
        
        # 检测跳槽模式
        job_changes = EmploymentDetector.detect_job_changes(documents)
        
        # 计算当前雇主的工作年限
        current_employment_years = EmploymentDetector._calculate_current_tenure(documents)
        
        # 评估稳定性
        stability_result = EmploymentDetector.evaluate_stability(
            employment_years=current_employment_years,
            job_changes=job_changes
        )
        
        return {
            "employment_years": current_employment_years,
            "stability_score": stability_result["stability_score"],
            "risk_flag": stability_result["risk_flag"],
            "job_changes_detected": job_changes["change_count"],
            "confidence": 0.85,
            "source": "pay_slip_analysis"
        }
    
    @staticmethod
    def _calculate_current_tenure(documents: List[Dict]) -> float:
        """计算当前雇主的工作年限"""
        if not documents:
            return 3.0
        
        # 按日期排序
        sorted_docs = sorted(documents, key=lambda x: x.get("date", ""), reverse=True)
        
        # 获取当前雇主
        current_employer = sorted_docs[0].get("employer", "")
        
        # 找到当前雇主的最早记录
        earliest_date = None
        latest_date = None
        
        for doc in sorted_docs:
            if doc.get("employer") == current_employer:
                doc_date = doc.get("date", "")
                if doc_date:
                    if earliest_date is None or doc_date < earliest_date:
                        earliest_date = doc_date
                    if latest_date is None or doc_date > latest_date:
                        latest_date = doc_date
        
        if earliest_date and latest_date:
            try:
                start = datetime.strptime(earliest_date, "%Y-%m")
                end = datetime.strptime(latest_date, "%Y-%m")
                delta = relativedelta(end, start)
                years = delta.years + delta.months / 12.0
                return round(years, 1)
            except:
                return 3.0
        
        return 3.0
    
    @staticmethod
    def detect_job_changes(documents: List[Dict]) -> Dict:
        """
        检测跳槽模式
        
        Returns:
            {
                "change_count": int,
                "pattern": "stable" | "moderate" | "frequent",
                "employers": List[str]
            }
        """
        if not documents:
            return {"change_count": 0, "pattern": "unknown", "employers": []}
        
        # 提取所有雇主
        employers = []
        for doc in documents:
            employer = doc.get("employer", "")
            if employer and employer not in employers:
                employers.append(employer)
        
        change_count = len(employers) - 1 if len(employers) > 0 else 0
        
        # 确定模式
        if change_count == 0:
            pattern = "stable"
        elif change_count <= 2:
            pattern = "moderate"
        else:
            pattern = "frequent"
        
        return {
            "change_count": change_count,
            "pattern": pattern,
            "employers": employers
        }
    
    @staticmethod
    def evaluate_stability(employment_years: float, job_changes: Dict) -> Dict:
        """
        评估就业稳定性
        
        Returns:
            {
                "stability_score": int (0~100),
                "risk_flag": str
            }
        """
        base_score = 100
        
        # 工作年限扣分
        if employment_years >= 5:
            years_penalty = 0
        elif employment_years >= 2:
            years_penalty = 10
        elif employment_years >= 1:
            years_penalty = 20
        else:
            years_penalty = 30
        
        # 跳槽频率扣分
        change_count = job_changes.get("change_count", 0)
        if change_count == 0:
            change_penalty = 0
        elif change_count <= 2:
            change_penalty = 10
        elif change_count <= 4:
            change_penalty = 20
        else:
            change_penalty = 30
        
        stability_score = base_score - years_penalty - change_penalty
        stability_score = max(0, min(100, stability_score))
        
        # 确定风险标记
        if stability_score >= 80:
            risk_flag = "stable"
        elif stability_score >= 60:
            risk_flag = "moderate"
        elif stability_score >= 40:
            risk_flag = "unstable"
        else:
            risk_flag = "high-risk"
        
        return {
            "stability_score": stability_score,
            "risk_flag": risk_flag
        }
    
    @staticmethod
    def auto_detect_employment(customer_id: int, db) -> Dict:
        """
        自动从系统中查找客户的就业文档并分析
        
        Args:
            customer_id: 客户ID
            db: 数据库连接
            
        Returns:
            就业稳定性分析结果
        """
        # TODO: 从income_documents表中提取薪资单
        # TODO: 调用detect_employment_years分析
        
        # 当前返回默认值
        return {
            "employment_years": 3.0,
            "stability_score": 70,
            "risk_flag": "moderate",
            "job_changes_detected": 1,
            "confidence": 0.50,
            "source": "auto_detected",
            "note": "Using default - no employment documents found"
        }
