"""
Income Standardizer - 收入标准化模型
用于将多源收入数据标准化为统一收入模型，支持DSR/DSRC计算
"""
from typing import Dict, Optional


class IncomeStandardizer:
    """
    收入标准化器
    将 structured_income 转换为银行认可的标准化收入模型
    """
    
    @staticmethod
    def standardize(
        structured_income: Dict,
        document_type: str,
        confidence: float = 0.0
    ) -> Dict:
        """
        标准化收入数据
        
        Args:
            structured_income: IncomeParser 解析的结构化收入
            document_type: 文件类型 (salary_slip/tax_return/epf/bank_inflow)
            confidence: OCR置信度
            
        Returns:
            标准化收入模型
        """
        
        result = {
            "fixed_income": 0.0,
            "variable_income": 0.0,
            "annualized_income": 0.0,
            "bank_verified_income": 0.0,
            "best_estimate_income": 0.0,
            "dsr_income": 0.0,
            "dsrc_income": 0.0,
            "confidence": 0.0,
            "source": document_type,
            "components": {}
        }
        
        if document_type == "salary_slip":
            result = IncomeStandardizer._standardize_salary_slip(
                structured_income, confidence
            )
        elif document_type == "tax_return":
            result = IncomeStandardizer._standardize_tax_return(
                structured_income, confidence
            )
        elif document_type == "epf":
            result = IncomeStandardizer._standardize_epf(
                structured_income, confidence
            )
        elif document_type == "bank_inflow":
            result = IncomeStandardizer._standardize_bank_inflow(
                structured_income, confidence
            )
        
        result["source"] = document_type
        return result
    
    @staticmethod
    def _standardize_salary_slip(structured_income: Dict, confidence: float) -> Dict:
        """标准化工资单收入"""
        basic = structured_income.get("basic_salary", 0.0)
        allowance = structured_income.get("allowance", 0.0)
        gross = structured_income.get("gross_salary", 0.0)
        net = structured_income.get("net_salary", 0.0)
        
        fixed_income = basic
        variable_income = allowance
        
        best_estimate = gross if gross > 0 else (basic + allowance)
        annualized = best_estimate * 12
        
        dsr_income = basic * 12
        dsrc_income = best_estimate * 12
        
        income_confidence = confidence * 0.95
        
        return {
            "fixed_income": fixed_income,
            "variable_income": variable_income,
            "annualized_income": annualized,
            "bank_verified_income": 0.0,
            "best_estimate_income": best_estimate,
            "dsr_income": dsr_income,
            "dsrc_income": dsrc_income,
            "confidence": income_confidence,
            "source": "salary_slip",
            "components": {
                "basic_salary": basic,
                "allowance": allowance,
                "gross_salary": gross,
                "net_salary": net
            }
        }
    
    @staticmethod
    def _standardize_tax_return(structured_income: Dict, confidence: float) -> Dict:
        """标准化税单收入"""
        annual = structured_income.get("annual_income", 0.0)
        
        monthly_estimate = annual / 12 if annual > 0 else 0.0
        
        fixed_income = monthly_estimate * 0.7
        variable_income = monthly_estimate * 0.3
        
        dsr_income = annual
        dsrc_income = annual
        
        income_confidence = confidence * 0.98
        
        return {
            "fixed_income": fixed_income,
            "variable_income": variable_income,
            "annualized_income": annual,
            "bank_verified_income": 0.0,
            "best_estimate_income": monthly_estimate,
            "dsr_income": dsr_income,
            "dsrc_income": dsrc_income,
            "confidence": income_confidence,
            "source": "tax_return",
            "components": {
                "annual_income": annual,
                "monthly_estimate": monthly_estimate
            }
        }
    
    @staticmethod
    def _standardize_epf(structured_income: Dict, confidence: float) -> Dict:
        """标准化EPF收入"""
        epf_contrib = structured_income.get("epf_contribution", 0.0)
        
        estimated_salary = epf_contrib / 0.11 if epf_contrib > 0 else 0.0
        
        fixed_income = estimated_salary
        variable_income = 0.0
        annualized = estimated_salary * 12
        
        dsr_income = annualized
        dsrc_income = annualized
        
        income_confidence = confidence * 0.85
        
        return {
            "fixed_income": fixed_income,
            "variable_income": variable_income,
            "annualized_income": annualized,
            "bank_verified_income": 0.0,
            "best_estimate_income": estimated_salary,
            "dsr_income": dsr_income,
            "dsrc_income": dsrc_income,
            "confidence": income_confidence,
            "source": "epf",
            "components": {
                "epf_contribution": epf_contrib,
                "estimated_salary": estimated_salary
            }
        }
    
    @staticmethod
    def _standardize_bank_inflow(structured_income: Dict, confidence: float) -> Dict:
        """标准化银行流水收入"""
        inflow = structured_income.get("bank_inflow", 0.0)
        
        fixed_income = 0.0
        variable_income = inflow
        annualized = inflow * 12
        
        bank_verified = inflow
        
        dsr_income = annualized * 0.8
        dsrc_income = annualized * 0.9
        
        income_confidence = confidence * 0.75
        
        return {
            "fixed_income": fixed_income,
            "variable_income": variable_income,
            "annualized_income": annualized,
            "bank_verified_income": bank_verified,
            "best_estimate_income": inflow,
            "dsr_income": dsr_income,
            "dsrc_income": dsrc_income,
            "confidence": income_confidence,
            "source": "bank_inflow",
            "components": {
                "bank_inflow": inflow,
                "monthly_average": inflow
            }
        }
    
    @staticmethod
    def aggregate_customer_income(standardized_incomes: list) -> Dict:
        """
        聚合客户的多个收入来源，选择最佳估算
        
        Args:
            standardized_incomes: 多个标准化收入记录列表
            
        Returns:
            聚合后的最佳收入估算
        """
        if not standardized_incomes:
            return {
                "customer_id": None,
                "dsr_income": 0.0,
                "dsrc_income": 0.0,
                "best_source": None,
                "confidence": 0.0,
                "components": {}
            }
        
        sources_priority = {
            "tax_return": 4,
            "salary_slip": 3,
            "epf": 2,
            "bank_inflow": 1
        }
        
        best_record = max(
            standardized_incomes,
            key=lambda x: (
                sources_priority.get(x.get("source", ""), 0),
                x.get("confidence", 0.0)
            )
        )
        
        components = {}
        for record in standardized_incomes:
            source = record.get("source", "unknown")
            components[source] = {
                "dsr_income": record.get("dsr_income", 0.0),
                "dsrc_income": record.get("dsrc_income", 0.0),
                "confidence": record.get("confidence", 0.0),
                "best_estimate": record.get("best_estimate_income", 0.0)
            }
        
        return {
            "dsr_income": best_record.get("dsr_income", 0.0),
            "dsrc_income": best_record.get("dsrc_income", 0.0),
            "best_source": best_record.get("source"),
            "confidence": best_record.get("confidence", 0.0),
            "components": components
        }
