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
        """标准化工资单收入（返回月度DSR/DSRC）"""
        basic = structured_income.get("basic_salary", 0.0)
        allowance = structured_income.get("allowance", 0.0)
        gross = structured_income.get("gross_salary", 0.0)
        net = structured_income.get("net_salary", 0.0)
        
        fixed_income = basic
        variable_income = allowance
        
        best_estimate = gross if gross > 0 else (basic + allowance)
        annualized = best_estimate * 12
        
        dsr_income = basic
        dsrc_income = best_estimate
        
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
        """标准化税单收入（返回月度DSR/DSRC）"""
        annual = structured_income.get("annual_income", 0.0)
        
        monthly_estimate = annual / 12 if annual > 0 else 0.0
        
        fixed_income = monthly_estimate * 0.7
        variable_income = monthly_estimate * 0.3
        
        dsr_income = monthly_estimate
        dsrc_income = monthly_estimate
        
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
        """标准化EPF收入（返回月度DSR/DSRC）"""
        epf_contrib = structured_income.get("epf_contribution", 0.0)
        
        estimated_salary = epf_contrib / 0.11 if epf_contrib > 0 else 0.0
        
        fixed_income = estimated_salary
        variable_income = 0.0
        annualized = estimated_salary * 12
        
        dsr_income = estimated_salary
        dsrc_income = estimated_salary
        
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
        """标准化银行流水收入（返回月度DSR/DSRC）"""
        inflow = structured_income.get("bank_inflow", 0.0)
        
        fixed_income = 0.0
        variable_income = inflow
        annualized = inflow * 12
        
        bank_verified = inflow
        
        dsr_income = inflow * 0.8
        dsrc_income = inflow * 0.9
        
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
    def aggregate_customer_income(standardized_incomes_with_metadata: list) -> Dict:
        """
        聚合客户的多个收入来源，选择最佳估算
        保留每个文件的详细信息
        
        Args:
            standardized_incomes_with_metadata: 包含file_id, period和standardized_income的列表
            
        Returns:
            聚合后的最佳收入估算
        """
        if not standardized_incomes_with_metadata:
            return {
                "customer_id": None,
                "dsr_income": 0.0,
                "dsrc_income": 0.0,
                "best_source": None,
                "confidence": 0.0,
                "components": []
            }
        
        sources_priority = {
            "tax_return": 4,
            "salary_slip": 3,
            "epf": 2,
            "bank_inflow": 1
        }
        
        best_record = max(
            standardized_incomes_with_metadata,
            key=lambda x: (
                sources_priority.get(x.get("standardized_income", {}).get("source", ""), 0),
                x.get("standardized_income", {}).get("confidence", 0.0)
            )
        )
        
        components = []
        for item in standardized_incomes_with_metadata:
            std_income = item.get("standardized_income", {})
            components.append({
                "file_id": item.get("file_id"),
                "period": item.get("period"),
                "source": std_income.get("source"),
                "dsr_income": std_income.get("dsr_income", 0.0),
                "dsrc_income": std_income.get("dsrc_income", 0.0),
                "confidence": std_income.get("confidence", 0.0),
                "best_estimate": std_income.get("best_estimate_income", 0.0),
                "annualized_income": std_income.get("annualized_income", 0.0)
            })
        
        best_std_income = best_record.get("standardized_income", {})
        
        return {
            "dsr_income": best_std_income.get("dsr_income", 0.0),
            "dsrc_income": best_std_income.get("dsrc_income", 0.0),
            "best_source": best_std_income.get("source"),
            "confidence": best_std_income.get("confidence", 0.0),
            "components": components
        }
