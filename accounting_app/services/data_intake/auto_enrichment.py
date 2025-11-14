"""
Auto Enrichment - 自动数据增强层
统一入口，自动填充缺失的风控数据

功能：
- 自动检测并填充CCRIS bucket
- 自动检测并填充CTOS SME score
- 自动检测并填充Cashflow variance
- 自动检测并填充Employment stability
- 自动检测并填充Industry classification
"""
from typing import Dict, Optional
from .ccris_parser import CCRISParser
from .ctos_parser import CTOSParser
from .bank_statement_analyzer import BankStatementAnalyzer
from .employment_detector import EmploymentDetector
from .industry_classifier import IndustryClassifier
from .income_detector import IncomeDetector


class AutoEnrichment:
    """自动数据增强引擎"""
    
    @staticmethod
    def enrich_personal_loan_data(
        customer_id: int,
        db,
        provided_data: Dict
    ) -> Dict:
        """
        自动增强个人贷款数据
        
        Args:
            customer_id: 客户ID
            db: 数据库连接
            provided_data: 用户已提供的数据
                {
                    "ccris_bucket": Optional[int],
                    "age": Optional[int],
                    "employment_years": Optional[float],
                    "credit_score": Optional[int],
                    ...
                }
                
        Returns:
            完整的风控数据字典
        """
        enriched = provided_data.copy()
        
        # 1. CCRIS Bucket自动检测
        if "ccris_bucket" not in enriched or enriched["ccris_bucket"] is None:
            ccris_data = CCRISParser.auto_detect_ccris_bucket(customer_id, db)
            enriched["ccris_bucket"] = ccris_data["bucket"]
            enriched["_ccris_confidence"] = ccris_data["confidence"]
        
        # 2. Employment Years自动检测
        if "employment_years" not in enriched or enriched["employment_years"] is None:
            employment_data = EmploymentDetector.auto_detect_employment(customer_id, db)
            enriched["employment_years"] = employment_data["employment_years"]
            enriched["_employment_confidence"] = employment_data["confidence"]
        
        # 3. Credit Score默认值
        if "credit_score" not in enriched or enriched["credit_score"] is None:
            enriched["credit_score"] = 700  # 默认中等分数
            enriched["_credit_score_confidence"] = 0.50
        
        # 4. Age默认值
        if "age" not in enriched or enriched["age"] is None:
            enriched["age"] = 35  # 默认年龄
            enriched["_age_confidence"] = 0.50
        
        # 5. Income自动聚合
        if "income" not in enriched or enriched["income"] is None:
            income_data = IncomeDetector.aggregate_income_sources(customer_id, db)
            enriched["income"] = income_data["final_income"]
            enriched["_income_confidence"] = income_data["confidence"]
        
        return enriched
    
    @staticmethod
    def enrich_sme_loan_data(
        customer_id: int,
        db,
        provided_data: Dict
    ) -> Dict:
        """
        自动增强SME贷款数据
        
        Args:
            customer_id: 客户ID
            db: 数据库连接
            provided_data: 用户已提供的数据
                {
                    "ctos_sme_score": Optional[int],
                    "cashflow_variance": Optional[float],
                    "industry_sector": Optional[str],
                    "company_age_years": Optional[int],
                    ...
                }
                
        Returns:
            完整的风控数据字典
        """
        enriched = provided_data.copy()
        
        # 1. CTOS SME Score自动检测
        if "ctos_sme_score" not in enriched or enriched["ctos_sme_score"] is None:
            ctos_data = CTOSParser.auto_detect_ctos_sme_score(customer_id, db)
            enriched["ctos_sme_score"] = ctos_data["sme_score"]
            enriched["_ctos_confidence"] = ctos_data["confidence"]
        
        # 2. Cashflow Variance自动计算
        if "cashflow_variance" not in enriched or enriched["cashflow_variance"] is None:
            cashflow_data = BankStatementAnalyzer.auto_analyze_cashflow(customer_id, db)
            enriched["cashflow_variance"] = cashflow_data["variance"]
            enriched["_cashflow_confidence"] = cashflow_data["confidence"]
        
        # 3. Industry Sector自动分类
        if "industry_sector" not in enriched or enriched["industry_sector"] is None:
            industry_data = IndustryClassifier.auto_classify_industry(customer_id, db)
            enriched["industry_sector"] = industry_data["industry"]
            enriched["_industry_confidence"] = industry_data["confidence"]
        
        # 4. Company Age默认值
        if "company_age_years" not in enriched or enriched["company_age_years"] is None:
            enriched["company_age_years"] = 5  # 默认5年
            enriched["_company_age_confidence"] = 0.50
        
        # 5. Employee Count默认值
        if "employee_count" not in enriched or enriched["employee_count"] is None:
            enriched["employee_count"] = 10  # 默认10人
            enriched["_employee_count_confidence"] = 0.50
        
        # 6. Operating Income自动获取
        if "operating_income" not in enriched or enriched["operating_income"] is None:
            # TODO: 从business_loan_engine获取
            enriched["operating_income"] = 0.0
            enriched["_operating_income_confidence"] = 0.30
        
        return enriched
    
    @staticmethod
    def get_enrichment_summary(enriched_data: Dict) -> Dict:
        """
        生成数据增强摘要
        
        Returns:
            {
                "auto_filled_fields": List[str],
                "confidence_scores": Dict[str, float]
            }
        """
        auto_filled = []
        confidence_scores = {}
        
        for key, value in enriched_data.items():
            if key.startswith("_") and key.endswith("_confidence"):
                field_name = key.replace("_", "").replace("confidence", "")
                confidence_scores[field_name] = value
                
                if value < 0.70:  # 低置信度 = 自动填充
                    auto_filled.append(field_name)
        
        return {
            "auto_filled_fields": auto_filled,
            "confidence_scores": confidence_scores
        }
