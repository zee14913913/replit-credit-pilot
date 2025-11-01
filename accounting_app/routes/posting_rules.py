"""
Auto Posting Rules API路由
企业级规则引擎 - 表驱动化的自动记账规则管理
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
import logging
from datetime import datetime

from ..db import get_db
from ..models import AutoPostingRule
from ..schemas import (
    RuleCreate, RuleUpdate, RuleResponse, 
    RuleListResponse, RuleTestRequest, RuleTestResponse
)
from ..middleware.multi_tenant import get_current_company_id
from ..services.rule_engine import RuleEngine

router = APIRouter(prefix="/posting-rules", tags=["Auto Posting Rules"])
logger = logging.getLogger(__name__)


@router.get("/", response_model=RuleListResponse)
def list_rules(
    company_id: int = Depends(get_current_company_id),
    source_type: Optional[str] = Query(None, description="过滤source_type"),
    is_active: Optional[bool] = Query(None, description="过滤is_active"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
    db: Session = Depends(get_db)
):
    """
    获取记账规则列表（分页+过滤）
    
    ⚠️ 多租户隔离：company_id从get_current_company_id注入
    """
    # 构建查询
    query = db.query(AutoPostingRule).filter(
        AutoPostingRule.company_id == company_id
    )
    
    # 过滤条件
    if source_type:
        query = query.filter(AutoPostingRule.source_type == source_type)
    if is_active is not None:
        query = query.filter(AutoPostingRule.is_active == is_active)
    
    # 总数
    total = query.count()
    
    # 分页（按优先级排序）
    offset = (page - 1) * page_size
    rules = query.order_by(AutoPostingRule.priority.asc()).offset(offset).limit(page_size).all()
    
    return RuleListResponse(
        total=total,
        page=page,
        page_size=page_size,
        rules=[RuleResponse.from_orm(rule) for rule in rules]
    )


@router.get("/{rule_id}", response_model=RuleResponse)
def get_rule(
    rule_id: int,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db)
):
    """
    获取单个规则详情
    
    ⚠️ 多租户隔离：必须同时验证rule_id和company_id
    """
    rule = db.query(AutoPostingRule).filter(
        AutoPostingRule.id == rule_id,
        AutoPostingRule.company_id == company_id
    ).first()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    return RuleResponse.from_orm(rule)


@router.post("/", response_model=RuleResponse)
def create_rule(
    rule: RuleCreate,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db)
):
    """
    创建新的记账规则
    
    ⚠️ 多租户隔离：company_id从get_current_company_id注入，不接受用户输入
    """
    # 验证会计科目是否存在
    engine = RuleEngine(db, company_id)
    
    # 创建临时规则对象用于验证
    temp_rule = AutoPostingRule(
        company_id=company_id,
        debit_account_code=rule.debit_account_code,
        credit_account_code=rule.credit_account_code,
        **rule.dict(exclude={"debit_account_code", "credit_account_code"})
    )
    
    is_valid, error_msg = engine.validate_rule_accounts(temp_rule)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    # 创建规则
    rule_data = rule.dict()
    rule_data['company_id'] = company_id
    
    db_rule = AutoPostingRule(**rule_data)
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    
    # 清除缓存（确保新规则立即生效）
    engine.clear_cache()
    
    logger.info(f"✅ 规则创建成功: {db_rule.rule_name} (ID: {db_rule.id}) | Company: {company_id}")
    
    return RuleResponse.from_orm(db_rule)


@router.put("/{rule_id}", response_model=RuleResponse)
def update_rule(
    rule_id: int,
    rule: RuleUpdate,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db)
):
    """
    更新规则
    
    ⚠️ 多租户隔离：必须同时验证rule_id和company_id
    """
    # 查找规则（租户隔离）
    db_rule = db.query(AutoPostingRule).filter(
        AutoPostingRule.id == rule_id,
        AutoPostingRule.company_id == company_id
    ).first()
    
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    # 更新字段
    update_data = rule.dict(exclude_unset=True)
    
    # 如果更新了会计科目，需要验证
    if 'debit_account_code' in update_data or 'credit_account_code' in update_data:
        # 应用更新后的值进行验证
        for key, value in update_data.items():
            setattr(db_rule, key, value)
        
        engine = RuleEngine(db, company_id)
        is_valid, error_msg = engine.validate_rule_accounts(db_rule)
        if not is_valid:
            db.rollback()
            raise HTTPException(status_code=400, detail=error_msg)
    else:
        # 直接应用更新
        for key, value in update_data.items():
            setattr(db_rule, key, value)
    
    db_rule.updated_at = datetime.now()
    db.commit()
    db.refresh(db_rule)
    
    # 清除缓存（确保更新后的规则立即生效）
    engine = RuleEngine(db, company_id)
    engine.clear_cache()
    
    logger.info(f"✅ 规则更新成功: {db_rule.rule_name} (ID: {db_rule.id})")
    
    return RuleResponse.from_orm(db_rule)


@router.delete("/{rule_id}")
def delete_rule(
    rule_id: int,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db)
):
    """
    删除规则
    
    ⚠️ 多租户隔离：必须同时验证rule_id和company_id
    """
    db_rule = db.query(AutoPostingRule).filter(
        AutoPostingRule.id == rule_id,
        AutoPostingRule.company_id == company_id
    ).first()
    
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    rule_name = db_rule.rule_name
    db.delete(db_rule)
    db.commit()
    
    # 清除缓存（确保删除的规则不再被使用）
    engine = RuleEngine(db, company_id)
    engine.clear_cache()
    
    logger.info(f"✅ 规则删除成功: {rule_name} (ID: {rule_id})")
    
    return {"message": f"Rule '{rule_name}' deleted successfully"}


@router.post("/test", response_model=RuleTestResponse)
def test_rule_matching(
    test_request: RuleTestRequest,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db)
):
    """
    测试规则匹配
    
    用于验证交易描述能否匹配到规则
    """
    engine = RuleEngine(db, company_id)
    
    # 尝试匹配
    matched_rule = engine.match_transaction(
        test_request.description,
        test_request.source_type
    )
    
    if matched_rule:
        return RuleTestResponse(
            matched=True,
            rule=RuleResponse.from_orm(matched_rule),
            reason=f"匹配成功：规则'{matched_rule.rule_name}'（优先级：{matched_rule.priority}）"
        )
    else:
        return RuleTestResponse(
            matched=False,
            rule=None,
            reason="未找到匹配的规则"
        )
