"""
CTOS Parser - CTOS SME数据解析器
自动解析CTOS SME报告（Credit Tip-Off Service）

功能：
- 提取CTOS SME Score (0~999)
- 确定Risk Band (Excellent/Good/Fair/Poor/High Risk)
- 检测企业风险因子
"""
from typing import Dict, List, Optional
import re


class CTOSParser:
    """CTOS报告解析器"""
    
    # CTOS SME Score分段
    SCORE_BANDS = {
        "excellent": (750, 999),
        "good": (650, 749),
        "fair": (550, 649),
        "poor": (450, 549),
        "high_risk": (0, 449)
    }
    
    @staticmethod
    def parse_ctos_sme_score(document: Dict) -> Dict:
        """
        解析CTOS SME分数
        
        Args:
            document: CTOS文档数据
                {
                    "text": str,  # OCR文本
                    "score_section": Dict,  # 分数区域
                    "business_profile": Dict  # 企业资料
                }
                
        Returns:
            {
                "sme_score": int (0~999),
                "risk_band": str,
                "confidence": float,
                "flags": List[str]
            }
        """
        # 方法1: 从结构化数据提取
        score_section = document.get("score_section", {})
        if score_section and "sme_score" in score_section:
            sme_score = int(score_section["sme_score"])
            confidence = 0.95
        # 方法2: 从文本OCR提取
        else:
            text = document.get("text", "")
            sme_score = CTOSParser._extract_score_from_text(text)
            confidence = 0.70 if sme_score > 0 else 0.50
        
        # 确定risk band
        risk_band = CTOSParser._get_risk_band(sme_score)
        
        # 解析业务风险因子
        risk_factors = CTOSParser.parse_business_risk_factors(document)
        
        return {
            "sme_score": sme_score,
            "risk_band": risk_band,
            "confidence": confidence,
            "flags": risk_factors["flags"],
            "source": "ctos_report"
        }
    
    @staticmethod
    def _extract_score_from_text(text: str) -> int:
        """从OCR文本提取SME分数"""
        # 查找模式: "SME Score: 685" 或 "Score 685"
        patterns = [
            r"SME\s+Score[:\s]+(\d{3})",
            r"Score[:\s]+(\d{3})",
            r"评分[:\s]+(\d{3})"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        # 默认中等分数
        return 650
    
    @staticmethod
    def _get_risk_band(score: int) -> str:
        """根据分数确定risk band"""
        for band_name, (min_score, max_score) in CTOSParser.SCORE_BANDS.items():
            if min_score <= score <= max_score:
                return band_name.replace("_", " ").title()
        return "Fair"
    
    @staticmethod
    def parse_business_risk_factors(document: Dict) -> Dict:
        """
        解析企业风险因子
        
        Returns:
            {
                "flags": List[str],
                "legal_cases": int,
                "trade_references": str,
                "payment_trend": str
            }
        """
        flags = []
        
        text = document.get("text", "").lower()
        business_profile = document.get("business_profile", {})
        
        # 法律诉讼
        legal_cases = business_profile.get("legal_cases", 0)
        if legal_cases > 0:
            flags.append("legal_cases")
        
        # 支付趋势
        payment_trend = business_profile.get("payment_trend", "stable")
        if payment_trend == "declining":
            flags.append("declining_payments")
        elif payment_trend == "irregular":
            flags.append("irregular_payments")
        
        # 从文本检测
        if "winding up" in text or "liquidation" in text:
            flags.append("winding_up_risk")
        if "dishonoured" in text or "bounced" in text:
            flags.append("dishonoured_cheques")
        if "default" in text:
            flags.append("default_history")
        
        # Trade references
        trade_ref_count = business_profile.get("trade_references", 0)
        if trade_ref_count >= 5:
            trade_references = "good"
        elif trade_ref_count >= 2:
            trade_references = "fair"
        else:
            trade_references = "poor"
            flags.append("insufficient_trade_refs")
        
        return {
            "flags": list(set(flags)),
            "legal_cases": legal_cases,
            "trade_references": trade_references,
            "payment_trend": payment_trend
        }
    
    @staticmethod
    def auto_detect_ctos_sme_score(customer_id: int, db) -> Dict:
        """
        自动从系统中查找企业的CTOS数据
        
        Args:
            customer_id: 客户ID
            db: 数据库连接
            
        Returns:
            解析后的CTOS数据
        """
        # TODO: 从uploaded_documents表中查找CTOS文件
        # TODO: 调用OCR服务提取文本
        # TODO: 调用parse_ctos_sme_score解析
        
        # 当前返回默认值
        return {
            "sme_score": 650,
            "risk_band": "Good",
            "confidence": 0.50,
            "flags": [],
            "source": "auto_detected",
            "note": "Using default - no CTOS document found"
        }
