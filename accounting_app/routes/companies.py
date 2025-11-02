"""
公司管理路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging

from ..db import get_db
from ..models import Company
from ..schemas import CompanyCreate, CompanyResponse
from ..services.coa_initializer import init_default_coa

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=CompanyResponse)
def create_company(company: CompanyCreate, db: Session = Depends(get_db)):
    """
    创建新公司
    
    自动初始化马来西亚标准会计科目表（Malaysia SME default template）：
    - 1001 银行存款 (asset)
    - 1101 应收账款 (asset)
    - 1201 存货 (asset)
    - 2001 应付账款 (liability)
    - 2101 银行短期贷款 (liability)
    - 3001 实收资本 (equity)
    - 3101 留存收益 (equity)
    - 4001 销售收入 (income)
    - 5001 管理费用 (expense)
    - 5101 薪资 (expense)
    - 6001 SST Payable (liability)
    """
    # 检查company_code是否已存在
    existing = db.query(Company).filter(Company.company_code == company.company_code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Company code '{company.company_code}' already exists")
    
    # 创建公司
    db_company = Company(**company.dict())
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    
    # 自动初始化默认会计科目
    try:
        coa_count = init_default_coa(db, db_company.id)
        logger.info(f"✅ 公司 {db_company.company_code} 创建成功，自动初始化 {coa_count} 个默认会计科目")
    except Exception as e:
        logger.error(f"⚠️ 公司创建成功，但会计科目初始化失败: {str(e)}")
        # 不影响公司创建的成功，只记录警告
    
    return db_company


@router.get("/", response_model=List[CompanyResponse])
def list_companies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """获取所有公司列表"""
    companies = db.query(Company).filter(Company.status == 'active').offset(skip).limit(limit).all()
    return companies


@router.get("/{company_id}", response_model=CompanyResponse)
def get_company(company_id: int, db: Session = Depends(get_db)):
    """获取单个公司详情"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company
