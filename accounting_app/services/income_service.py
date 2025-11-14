"""
Income Service - 统一收入查询服务
用于系统内部调用，获取客户的标准化收入数据
"""
from typing import Dict, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from ..models import FileIndex, Customer


class IncomeService:
    """
    统一收入查询服务
    从 standardized income 数据中获取客户收入信息
    """
    
    @staticmethod
    def get_customer_income(db: Session, customer_id: int, company_id: int = 1) -> Optional[Dict]:
        """
        获取客户的标准化收入数据
        
        Args:
            db: 数据库会话
            customer_id: 客户ID
            company_id: 公司ID（默认1）
            
        Returns:
            包含 dsr_income, dsrc_income, best_source, confidence, timestamp 的字典
            如果未找到收入数据，返回 None
        """
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return None
        
        files = db.query(FileIndex).filter(
            FileIndex.company_id == company_id,
            FileIndex.module == 'income',
            FileIndex.is_active == True
        ).order_by(FileIndex.upload_date.desc()).all()
        
        standardized_incomes_with_metadata = []
        latest_timestamp = None
        
        for file in files:
            metadata = file.metadata or {}
            if metadata.get('customer_id') == customer_id:
                standardized_income = metadata.get('standardized_income')
                if standardized_income:
                    standardized_incomes_with_metadata.append({
                        "file_id": file.id,
                        "period": file.period,
                        "standardized_income": standardized_income,
                        "upload_date": file.upload_date
                    })
                    
                    if latest_timestamp is None or (file.upload_date and file.upload_date > latest_timestamp):
                        latest_timestamp = file.upload_date
        
        if not standardized_incomes_with_metadata:
            return None
        
        from ..services.income_standardizer import IncomeStandardizer
        aggregated = IncomeStandardizer.aggregate_customer_income(standardized_incomes_with_metadata)
        
        return {
            "customer_id": customer_id,
            "customer_name": customer.name,
            "dsr_income": aggregated.get("dsr_income", 0.0),
            "dsrc_income": aggregated.get("dsrc_income", 0.0),
            "best_source": aggregated.get("best_source"),
            "confidence": aggregated.get("confidence", 0.0),
            "timestamp": latest_timestamp.isoformat() if latest_timestamp else None,
            "components": aggregated.get("components", [])
        }
    
    @staticmethod
    def has_income_data(db: Session, customer_id: int, company_id: int = 1) -> bool:
        """
        检查客户是否有收入数据
        
        Args:
            db: 数据库会话
            customer_id: 客户ID
            company_id: 公司ID
            
        Returns:
            True 如果有收入数据，否则 False
        """
        income_data = IncomeService.get_customer_income(db, customer_id, company_id)
        return income_data is not None and income_data.get("dsr_income", 0.0) > 0
