"""
企业级导出模板管理 - Templates API
表驱动化CSV导出格式配置
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
import logging
from datetime import datetime

from ..db import get_db
from ..models import ExportTemplate
from ..schemas import (
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    TemplateListResponse,
    TemplateTestRequest,
    TemplateTestResponse
)
from ..services.template_engine import TemplateEngine
from ..middleware.multi_tenant import get_current_company_id

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/export-templates/", response_model=TemplateListResponse)
def list_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    software_name: Optional[str] = None,
    export_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db)
):
    """
    获取导出模板列表（分页+过滤）
    
    - **skip**: 跳过记录数
    - **limit**: 返回记录数
    - **software_name**: 过滤软件名称
    - **export_type**: 过滤导出类型
    - **is_active**: 过滤启用状态
    - **search**: 搜索template_name或description
    """
    query = db.query(ExportTemplate).filter(
        ExportTemplate.company_id == company_id
    )
    
    # 过滤条件
    if software_name:
        query = query.filter(ExportTemplate.software_name == software_name)
    if export_type:
        query = query.filter(ExportTemplate.export_type == export_type)
    if is_active is not None:
        query = query.filter(ExportTemplate.is_active == is_active)
    if search:
        query = query.filter(
            (ExportTemplate.template_name.ilike(f"%{search}%")) |
            (ExportTemplate.description.ilike(f"%{search}%"))
        )
    
    total = query.count()
    templates = query.offset(skip).limit(limit).all()
    
    return TemplateListResponse(
        total=total,
        skip=skip,
        limit=limit,
        templates=[TemplateResponse.from_orm(t) for t in templates]
    )


@router.get("/export-templates/{template_id}", response_model=TemplateResponse)
def get_template(
    template_id: int,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db)
):
    """获取单个模板详情"""
    template = db.query(ExportTemplate).filter(
        ExportTemplate.id == template_id,
        ExportTemplate.company_id == company_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return TemplateResponse.from_orm(template)


@router.post("/export-templates/", response_model=TemplateResponse)
def create_template(
    template: TemplateCreate,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db)
):
    """
    创建导出模板
    
    - 自动注入company_id（租户隔离）
    - 验证模板配置有效性
    - CRUD后清除缓存
    """
    engine = TemplateEngine(db, company_id)
    
    # 创建临时对象用于验证
    temp_template = ExportTemplate(**template.dict(), company_id=company_id)
    
    # 验证模板配置
    is_valid, error_msg = engine.validate_template(temp_template)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    # 创建模板
    template_data = template.dict()
    template_data['company_id'] = company_id
    
    db_template = ExportTemplate(**template_data)
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    
    # 清除缓存
    engine.clear_cache()
    
    logger.info(f"✅ 模板创建成功: {db_template.template_name} (ID: {db_template.id}) | Company: {company_id}")
    
    return TemplateResponse.from_orm(db_template)


@router.put("/export-templates/{template_id}", response_model=TemplateResponse)
def update_template(
    template_id: int,
    template: TemplateUpdate,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db)
):
    """
    更新导出模板
    
    - 双重过滤（template_id + company_id）
    - 验证更新后的模板配置
    - 更新后清除缓存
    """
    db_template = db.query(ExportTemplate).filter(
        ExportTemplate.id == template_id,
        ExportTemplate.company_id == company_id
    ).first()
    
    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # 更新字段
    update_data = template.dict(exclude_unset=True)
    
    # 如果更新了column_mappings，需要验证
    if 'column_mappings' in update_data:
        # 临时应用更新进行验证
        for key, value in update_data.items():
            setattr(db_template, key, value)
        
        engine = TemplateEngine(db, company_id)
        is_valid, error_msg = engine.validate_template(db_template)
        if not is_valid:
            db.rollback()
            raise HTTPException(status_code=400, detail=error_msg)
    else:
        # 直接应用更新
        for key, value in update_data.items():
            setattr(db_template, key, value)
    
    db_template.updated_at = datetime.now()
    db.commit()
    db.refresh(db_template)
    
    # 清除缓存
    engine = TemplateEngine(db, company_id)
    engine.clear_cache()
    
    logger.info(f"✅ 模板更新成功: {db_template.template_name} (ID: {db_template.id})")
    
    return TemplateResponse.from_orm(db_template)


@router.delete("/export-templates/{template_id}")
def delete_template(
    template_id: int,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db)
):
    """删除导出模板"""
    db_template = db.query(ExportTemplate).filter(
        ExportTemplate.id == template_id,
        ExportTemplate.company_id == company_id
    ).first()
    
    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    template_name = db_template.template_name
    db.delete(db_template)
    db.commit()
    
    # 清除缓存
    engine = TemplateEngine(db, company_id)
    engine.clear_cache()
    
    logger.info(f"✅ 模板删除成功: {template_name} (ID: {template_id})")
    
    return {"message": f"Template '{template_name}' deleted successfully"}


@router.post("/export-templates/test", response_model=TemplateTestResponse)
def test_template(
    request: TemplateTestRequest,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db)
):
    """
    测试模板导出
    
    - 使用样本数据测试模板
    - 返回CSV预览
    """
    template = db.query(ExportTemplate).filter(
        ExportTemplate.id == request.template_id,
        ExportTemplate.company_id == company_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    engine = TemplateEngine(db, company_id)
    
    # 测试模板
    success, csv_preview, error = engine.test_template(
        template,
        request.sample_data,
        request.preview_rows
    )
    
    if not success:
        return TemplateTestResponse(
            success=False,
            preview_csv="",
            row_count=0,
            column_count=0,
            errors=[error]
        )
    
    # 计算行列数
    lines = csv_preview.strip().split('\n')
    row_count = len(lines) - (1 if template.include_header else 0)
    column_count = len(template.column_mappings)
    
    return TemplateTestResponse(
        success=True,
        preview_csv=csv_preview,
        row_count=row_count,
        column_count=column_count,
        errors=None
    )
