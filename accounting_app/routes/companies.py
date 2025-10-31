"""
公司管理路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..db import get_db
from ..models import Company
from ..schemas import CompanyCreate, CompanyResponse

router = APIRouter()


@router.post("/", response_model=CompanyResponse)
def create_company(company: CompanyCreate, db: Session = Depends(get_db)):
    """创建新公司"""
    # 检查company_code是否已存在
    existing = db.query(Company).filter(Company.company_code == company.company_code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Company code '{company.company_code}' already exists")
    
    db_company = Company(**company.dict())
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
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
