"""
Industry Classifier - 行业分类器
基于BNM标准13行业分类

功能：
- 从公司名称/SSM代码/业务描述自动分类
- 映射到BNM风险表
"""
from typing import Dict, Optional
import re


class IndustryClassifier:
    """行业分类器（BNM标准）"""
    
    # BNM标准13行业分类
    INDUSTRY_KEYWORDS = {
        "professional_services": [
            "consultant", "consulting", "advisory", "legal", "accounting",
            "audit", "law firm", "professional", "services"
        ],
        "healthcare": [
            "clinic", "hospital", "medical", "dental", "healthcare",
            "pharmacy", "doctor", "health"
        ],
        "education": [
            "education", "school", "training", "university", "college",
            "tuition", "learning", "academy"
        ],
        "trading": [
            "trading", "import", "export", "distribution", "wholesale",
            "trader", "supply"
        ],
        "retail": [
            "retail", "shop", "store", "mart", "boutique", "outlet",
            "supermarket", "minimart"
        ],
        "fnb": [
            "restaurant", "cafe", "food", "beverage", "catering",
            "bakery", "kitchen", "dining", "f&b", "fnb"
        ],
        "manufacturing": [
            "manufacturing", "factory", "production", "industrial",
            "maker", "assembly", "plant"
        ],
        "construction": [
            "construction", "builder", "contractor", "building",
            "civil", "developer", "engineering"
        ],
        "property_development": [
            "property", "real estate", "developer", "development",
            "realty", "land"
        ],
        "agriculture": [
            "agriculture", "farming", "plantation", "agro", "livestock",
            "fishery", "aquaculture"
        ],
        "tourism_hospitality": [
            "hotel", "resort", "tourism", "travel", "hospitality",
            "inn", "lodge", "vacation"
        ],
        "logistics": [
            "logistics", "transport", "delivery", "courier", "shipping",
            "freight", "haulage", "cargo"
        ],
        "oil_gas": [
            "oil", "gas", "petroleum", "energy", "fuel", "oilfield"
        ]
    }
    
    @staticmethod
    def classify_industry(
        company_name: str = "",
        ssm_code: str = "",
        description: str = ""
    ) -> Dict:
        """
        分类行业
        
        Args:
            company_name: 公司名称
            ssm_code: SSM注册代码
            description: 业务描述
            
        Returns:
            {
                "industry": str,
                "risk_level": str,
                "risk_score": int,
                "confidence": float
            }
        """
        # 合并所有文本
        combined_text = f"{company_name} {description}".lower()
        
        # 方法1: 基于关键词匹配
        matched_industry, confidence = IndustryClassifier._match_by_keywords(combined_text)
        
        # 方法2: 基于SSM代码（如果可用）
        if ssm_code:
            ssm_industry = IndustryClassifier._match_by_ssm_code(ssm_code)
            if ssm_industry:
                matched_industry = ssm_industry
                confidence = 0.95
        
        # 映射到风险表
        risk_info = IndustryClassifier.map_to_risk_table(matched_industry)
        
        return {
            "industry": matched_industry,
            "risk_level": risk_info["risk_level"],
            "risk_score": risk_info["risk_score"],
            "confidence": confidence,
            "source": "auto_classified"
        }
    
    @staticmethod
    def _match_by_keywords(text: str) -> tuple:
        """基于关键词匹配行业"""
        best_match = "trading"  # 默认
        best_score = 0
        
        for industry, keywords in IndustryClassifier.INDUSTRY_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                if keyword in text:
                    score += 1
            
            if score > best_score:
                best_score = score
                best_match = industry
        
        # 计算置信度
        if best_score >= 3:
            confidence = 0.90
        elif best_score >= 2:
            confidence = 0.75
        elif best_score >= 1:
            confidence = 0.60
        else:
            confidence = 0.40
        
        return best_match, confidence
    
    @staticmethod
    def _match_by_ssm_code(ssm_code: str) -> Optional[str]:
        """基于SSM代码匹配（MSIC 2008标准）"""
        # 简化版SSM代码映射
        ssm_map = {
            "46": "trading",
            "47": "retail",
            "56": "fnb",
            "10": "manufacturing",
            "41": "construction",
            "68": "property_development",
            "01": "agriculture",
            "55": "tourism_hospitality"
        }
        
        # 提取前两位数字
        code_prefix = re.findall(r"\d{2}", ssm_code)
        if code_prefix:
            return ssm_map.get(code_prefix[0])
        
        return None
    
    @staticmethod
    def map_to_risk_table(industry: str) -> Dict:
        """
        映射到BNM风险表
        
        Returns:
            {
                "risk_level": str,
                "risk_score": int
            }
        """
        # 低风险 (1-3)
        low_risk = ["professional_services", "healthcare", "education"]
        
        # 中风险 (4-6)
        medium_risk = ["trading", "retail", "fnb", "manufacturing", "logistics"]
        
        # 高风险 (7-10)
        high_risk = ["construction", "property_development", "agriculture", "tourism_hospitality", "oil_gas"]
        
        if industry in low_risk:
            return {"risk_level": "Low", "risk_score": 2}
        elif industry in medium_risk:
            return {"risk_level": "Medium", "risk_score": 5}
        elif industry in high_risk:
            return {"risk_level": "High", "risk_score": 8}
        else:
            return {"risk_level": "Medium", "risk_score": 5}
    
    @staticmethod
    def auto_classify_industry(customer_id: int, db) -> Dict:
        """
        自动从系统中查找客户的公司信息并分类
        
        Args:
            customer_id: 客户ID
            db: 数据库连接
            
        Returns:
            行业分类结果
        """
        # TODO: 从customers表中提取公司名称和描述
        # TODO: 调用classify_industry分类
        
        # 当前返回默认值
        return {
            "industry": "trading",
            "risk_level": "Medium",
            "risk_score": 5,
            "confidence": 0.50,
            "source": "auto_detected",
            "note": "Using default - insufficient company data"
        }
