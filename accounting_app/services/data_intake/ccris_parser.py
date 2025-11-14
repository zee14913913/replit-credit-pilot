"""
CCRIS Parser - CCRIS数据解析器
自动解析Bank Negara Malaysia CCRIS报告

功能：
- 提取CCRIS Bucket (0~3+)
- 计算Behavior Score
- 检测特殊标记 (rescheduled, delinquent, legal action)
"""
from typing import Dict, List, Optional
import re


class CCRISParser:
    """CCRIS报告解析器"""
    
    @staticmethod
    def parse_ccris_bucket(raw_data: Dict) -> Dict:
        """
        解析CCRIS bucket（最高逾期等级）
        
        Args:
            raw_data: CCRIS原始数据
                {
                    "text": str,  # OCR文本或PDF提取文本
                    "facilities": List[Dict],  # 贷款设施列表
                    "payment_history": List[Dict]  # 还款历史
                }
                
        Returns:
            {
                "bucket": int (0~3),
                "behavior_score": int (0~100),
                "special_flags": List[str],
                "confidence": float
            }
        """
        # 从设施列表中提取bucket
        facilities = raw_data.get("facilities", [])
        payment_history = raw_data.get("payment_history", [])
        text = raw_data.get("text", "")
        
        # 方法1: 从结构化数据提取
        if facilities:
            bucket = CCRISParser._extract_bucket_from_facilities(facilities)
            confidence = 0.95
        # 方法2: 从文本OCR提取
        elif text:
            bucket = CCRISParser._extract_bucket_from_text(text)
            confidence = 0.75
        else:
            # 默认bucket 0 (最佳)
            bucket = 0
            confidence = 0.50
        
        # 计算behavior score
        behavior_score = CCRISParser.calculate_behavior_score(raw_data)
        
        # 检测特殊标记
        special_flags = CCRISParser.detect_special_flags(raw_data)
        
        return {
            "bucket": bucket,
            "behavior_score": behavior_score,
            "special_flags": special_flags,
            "confidence": confidence,
            "source": "ccris_report"
        }
    
    @staticmethod
    def _extract_bucket_from_facilities(facilities: List[Dict]) -> int:
        """从设施列表提取最高bucket"""
        max_bucket = 0
        
        for facility in facilities:
            # 查找特殊账户代码
            special_code = facility.get("special_account_code", "0")
            
            # 映射Bank Negara特殊代码到bucket
            # 0 = 正常
            # 1 = 1-30天逾期
            # 2 = 31-60天逾期
            # 3 = 61-90天逾期
            # 4+ = 90天以上逾期
            if special_code in ["0", "00"]:
                bucket = 0
            elif special_code in ["1", "01"]:
                bucket = 1
            elif special_code in ["2", "02"]:
                bucket = 2
            else:
                bucket = 3
            
            max_bucket = max(max_bucket, bucket)
        
        return min(max_bucket, 3)  # 最高3
    
    @staticmethod
    def _extract_bucket_from_text(text: str) -> int:
        """从OCR文本提取bucket（模糊匹配）"""
        text_lower = text.lower()
        
        # 查找关键词
        if "rescheduled" in text_lower or "restructured" in text_lower:
            return 3
        elif "delinquent" in text_lower or "overdue" in text_lower:
            return 2
        elif "late payment" in text_lower or "延迟" in text_lower:
            return 1
        else:
            return 0
    
    @staticmethod
    def calculate_behavior_score(raw_data: Dict) -> int:
        """
        计算CCRIS行为分数 (0~100)
        
        基于：
        - 还款记录准时性
        - 信贷使用率
        - 账户数量
        """
        payment_history = raw_data.get("payment_history", [])
        facilities = raw_data.get("facilities", [])
        
        # 基础分数
        base_score = 100
        
        # 还款历史扣分
        if payment_history:
            late_payments = sum(1 for p in payment_history if p.get("status") == "late")
            total_payments = len(payment_history)
            
            if total_payments > 0:
                late_ratio = late_payments / total_payments
                payment_penalty = int(late_ratio * 40)  # 最多扣40分
            else:
                payment_penalty = 0
        else:
            payment_penalty = 0
        
        # 信贷使用率扣分
        if facilities:
            total_limit = sum(f.get("approved_limit", 0) for f in facilities)
            total_outstanding = sum(f.get("outstanding_balance", 0) for f in facilities)
            
            if total_limit > 0:
                utilization_ratio = total_outstanding / total_limit
                if utilization_ratio > 0.9:
                    utilization_penalty = 20
                elif utilization_ratio > 0.7:
                    utilization_penalty = 10
                elif utilization_ratio > 0.5:
                    utilization_penalty = 5
                else:
                    utilization_penalty = 0
            else:
                utilization_penalty = 0
        else:
            utilization_penalty = 0
        
        # 账户数量调整
        account_count = len(facilities)
        if account_count > 10:
            account_penalty = 10
        elif account_count > 5:
            account_penalty = 5
        else:
            account_penalty = 0
        
        final_score = base_score - payment_penalty - utilization_penalty - account_penalty
        return max(0, min(100, final_score))
    
    @staticmethod
    def detect_special_flags(raw_data: Dict) -> List[str]:
        """
        检测特殊标记
        
        Returns:
            ["rescheduled", "delinquent", "legal_action", "bankruptcy", ...]
        """
        flags = []
        
        facilities = raw_data.get("facilities", [])
        text = raw_data.get("text", "").lower()
        
        # 从设施状态检测
        for facility in facilities:
            status = facility.get("status", "").lower()
            
            if "rescheduled" in status or "restructured" in status:
                flags.append("rescheduled")
            if "delinquent" in status:
                flags.append("delinquent")
            if "legal" in status:
                flags.append("legal_action")
            if "write" in status and "off" in status:
                flags.append("written_off")
        
        # 从文本检测
        if "bankruptcy" in text or "bankrap" in text:
            flags.append("bankruptcy")
        if "litigation" in text or "suit" in text:
            flags.append("legal_action")
        if "default" in text:
            flags.append("default")
        
        return list(set(flags))  # 去重
    
    @staticmethod
    def auto_detect_ccris_bucket(customer_id: int, db) -> Dict:
        """
        自动从系统中查找客户的CCRIS数据
        
        Args:
            customer_id: 客户ID
            db: 数据库连接
            
        Returns:
            解析后的CCRIS数据
        """
        # TODO: 从uploaded_documents表中查找CCRIS文件
        # TODO: 调用OCR服务提取文本
        # TODO: 调用parse_ccris_bucket解析
        
        # 当前返回默认值
        return {
            "bucket": 0,
            "behavior_score": 85,
            "special_flags": [],
            "confidence": 0.50,
            "source": "auto_detected",
            "note": "Using default - no CCRIS document found"
        }
