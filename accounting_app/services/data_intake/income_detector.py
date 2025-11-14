"""
Income Detector - 收入检测器
多源收入自动聚合

功能：
- 聚合薪资单、银行流水、EPF等多源收入
- 计算综合收入置信度
- 选择最可靠的收入来源
"""
from typing import Dict, List, Optional


class IncomeDetector:
    """收入检测器"""
    
    @staticmethod
    def aggregate_income_sources(customer_id: int, db) -> Dict:
        """
        聚合多源收入
        
        Returns:
            {
                "final_income": float,
                "best_source": str,
                "confidence": float,
                "sources": List[Dict]
            }
        """
        sources = []
        
        # 来源1: 薪资单
        salary_income = IncomeDetector._get_salary_income(customer_id, db)
        if salary_income:
            sources.append(salary_income)
        
        # 来源2: 银行流水
        bank_income = IncomeDetector._get_bank_income(customer_id, db)
        if bank_income:
            sources.append(bank_income)
        
        # 来源3: EPF Statement
        epf_income = IncomeDetector._get_epf_income(customer_id, db)
        if epf_income:
            sources.append(epf_income)
        
        # 来源4: Tax Return
        tax_income = IncomeDetector._get_tax_income(customer_id, db)
        if tax_income:
            sources.append(tax_income)
        
        # 选择最可靠的来源
        if sources:
            best_source = max(sources, key=lambda x: x["confidence"])
            final_income = best_source["amount"]
            best_source_name = best_source["source"]
            confidence = best_source["confidence"]
        else:
            final_income = 0.0
            best_source_name = "none"
            confidence = 0.0
        
        return {
            "final_income": final_income,
            "best_source": best_source_name,
            "confidence": confidence,
            "sources": sources
        }
    
    @staticmethod
    def _get_salary_income(customer_id: int, db) -> Optional[Dict]:
        """从薪资单提取收入（最高置信度）"""
        try:
            from ..income_service import IncomeService
            
            income_data = IncomeService.get_customer_income(db, customer_id, company_id=1)
            
            if income_data and income_data.get("dsr_income", 0) > 0:
                return {
                    "source": "salary_slip",
                    "amount": income_data["dsr_income"],
                    "confidence": 0.95
                }
        except:
            pass
        
        return None
    
    @staticmethod
    def _get_bank_income(customer_id: int, db) -> Optional[Dict]:
        """从银行流水提取收入（中等置信度）"""
        # TODO: 从transactions表计算平均月收入
        # TODO: 过滤掉非收入交易
        
        return None
    
    @staticmethod
    def _get_epf_income(customer_id: int, db) -> Optional[Dict]:
        """从EPF Statement提取收入（高置信度）"""
        # TODO: 从income_documents表提取EPF数据
        # TODO: 从EPF贡献反推薪资
        
        return None
    
    @staticmethod
    def _get_tax_income(customer_id: int, db) -> Optional[Dict]:
        """从Tax Return提取收入（中等置信度）"""
        # TODO: 从income_documents表提取税务申报数据
        
        return None
