"""
Phase 1-3: 文件索引API路由
Flask→FastAPI文件索引同步
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from typing import List, Optional

from ..db import get_db
from ..models import FileIndex
from ..services.file_index_service import FileIndexService
from ..schemas.file_index_schemas import (
    FileIndexCreate,
    FileIndexResponse,
    FileIndexUpdate,
    FileIndexList,
    RecycleBinResponse,
    FlaskToFastAPIFileSync
)

router = APIRouter(prefix="/api/file-index", tags=["File Index"])


def get_current_company_id(x_company_id: Optional[int] = Header(None)) -> int:
    """从HTTP Header获取公司ID"""
    if x_company_id is None:
        raise HTTPException(status_code=400, detail="缺少X-Company-Id header")
    return x_company_id


@router.post("/", response_model=FileIndexResponse, summary="创建文件索引")
def create_file_index(
    data: FileIndexCreate,
    db: Session = Depends(get_db),
    company_id: int = Depends(get_current_company_id)
):
    """
    创建文件索引记录
    
    注意：如果没有related_entity_id，该文件会被视为孤儿文件
    """
    # 确保company_id一致
    if data.company_id != company_id:
        raise HTTPException(status_code=403, detail="公司ID不匹配")
    
    service = FileIndexService(db)
    
    try:
        # 转换date为datetime
        transaction_dt = None
        if data.transaction_date:
            from datetime import datetime
            transaction_dt = datetime.combine(data.transaction_date, datetime.min.time())
        
        file_index = service.create_file_index(
            company_id=data.company_id,
            file_category=data.file_category,
            file_type=data.file_type,
            filename=data.filename,
            file_path=data.file_path,
            module=data.module,
            raw_document_id=data.raw_document_id,  # Phase 1-3修复：强制字段
            related_entity_type=data.related_entity_type,
            related_entity_id=data.related_entity_id,
            file_size_kb=data.file_size_kb,
            file_extension=data.file_extension,
            mime_type=data.mime_type,
            period=data.period,
            transaction_date=transaction_dt,
            upload_by=data.upload_by,
            description=data.description,
            tags=data.tags
        )
        return file_index
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/flask-sync", response_model=FileIndexResponse, summary="Flask→FastAPI文件索引同步")
def flask_to_fastapi_sync(
    data: FlaskToFastAPIFileSync,
    db: Session = Depends(get_db)
):
    """
    Flask上传完成后，将文件索引同步到FastAPI
    
    关键规则：
    - Flask必须把company_id/customer_id识别结果一并传给FastAPI
    - 不能只传文件路径
    - 如果无法识别公司/客户，Flask应先进upload_staging
    """
    service = FileIndexService(db)
    
    try:
        # Phase 1-3修复：强制传递raw_document_id，防止绕过1:1封存
        file_index = service.create_file_index(
            company_id=data.company_id,
            file_category=data.file_category,
            file_type=data.file_type,
            filename=data.filename,
            file_path=data.file_path,
            module=data.module,
            raw_document_id=data.raw_document_id,  # 强制字段
            file_size_kb=data.file_size_kb,
            period=data.period,
            upload_by=data.upload_by,
            related_entity_type='customer_id' if data.customer_id else None,
            related_entity_id=data.customer_id
        )
        return file_index
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=FileIndexList, summary="查询文件列表")
def list_files(
    module: Optional[str] = Query(None, description="模块过滤"),
    file_category: Optional[str] = Query(None, description="分类过滤"),
    status: str = Query('active', description="状态过滤"),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    company_id: int = Depends(get_current_company_id)
):
    """
    查询文件列表（支持分页和过滤）
    """
    service = FileIndexService(db)
    items = service.list_files(
        company_id=company_id,
        module=module,
        file_category=file_category,
        status=status,
        limit=limit,
        offset=offset
    )
    
    # 转换为响应模型
    response_items = [FileIndexResponse.from_orm(item) for item in items]
    
    return FileIndexList(total=len(response_items), items=response_items)


@router.get("/{file_id}", response_model=FileIndexResponse, summary="获取文件索引详情")
def get_file_index(
    file_id: int,
    db: Session = Depends(get_db),
    company_id: int = Depends(get_current_company_id)
):
    """
    获取文件索引详情
    """
    service = FileIndexService(db)
    file_index = service.get_file_index(file_id)
    
    if not file_index:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 验证权限
    if file_index.company_id != company_id:
        raise HTTPException(status_code=403, detail="无权访问此文件")
    
    return file_index


@router.patch("/{file_id}", response_model=FileIndexResponse, summary="更新文件索引")
def update_file_index(
    file_id: int,
    data: FileIndexUpdate,
    db: Session = Depends(get_db),
    company_id: int = Depends(get_current_company_id)
):
    """
    更新文件索引（描述、标签、关联实体）
    """
    service = FileIndexService(db)
    file_index = service.get_file_index(file_id)
    
    if not file_index:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 验证权限
    if file_index.company_id != company_id:
        raise HTTPException(status_code=403, detail="无权访问此文件")
    
    # 更新字段
    if data.description is not None:
        file_index.description = data.description  # type: ignore
    if data.tags is not None:
        file_index.tags = data.tags  # type: ignore
    if data.related_entity_type is not None:
        file_index.related_entity_type = data.related_entity_type  # type: ignore
    if data.related_entity_id is not None:
        file_index.related_entity_id = data.related_entity_id  # type: ignore
    
    db.commit()
    db.refresh(file_index)
    
    return file_index


@router.delete("/{file_id}", summary="软删除文件")
def soft_delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    company_id: int = Depends(get_current_company_id)
):
    """
    软删除文件（标记为deleted，移入回收站）
    """
    service = FileIndexService(db)
    file_index = service.get_file_index(file_id)
    
    if not file_index:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 验证权限
    if file_index.company_id != company_id:
        raise HTTPException(status_code=403, detail="无权访问此文件")
    
    success = service.soft_delete(file_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="删除失败")
    
    return {"message": "文件已移入回收站", "file_id": file_id}


@router.post("/{file_id}/archive", summary="归档文件")
def archive_file(
    file_id: int,
    db: Session = Depends(get_db),
    company_id: int = Depends(get_current_company_id)
):
    """
    归档文件（标记为archived）
    """
    service = FileIndexService(db)
    file_index = service.get_file_index(file_id)
    
    if not file_index:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 验证权限
    if file_index.company_id != company_id:
        raise HTTPException(status_code=403, detail="无权访问此文件")
    
    success = service.archive(file_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="归档失败")
    
    return {"message": "文件已归档", "file_id": file_id}


@router.post("/{file_id}/restore", response_model=FileIndexResponse, summary="恢复文件")
def restore_file(
    file_id: int,
    db: Session = Depends(get_db),
    company_id: int = Depends(get_current_company_id)
):
    """
    从回收站恢复文件
    """
    service = FileIndexService(db)
    
    # 注意：这里不能用get_file_index，因为它只返回active状态的文件
    file_index = db.query(FileIndex).filter(FileIndex.id == file_id).first()
    
    if not file_index or file_index.company_id != company_id:
        raise HTTPException(status_code=404, detail="文件不存在或无权访问")
    
    success = service.restore(file_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="恢复失败")
    
    # 重新获取
    restored_file = service.get_file_index(file_id)
    return restored_file


@router.get("/recyclebin/list", response_model=RecycleBinResponse, summary="查看回收站")
def get_recyclebin(
    db: Session = Depends(get_db),
    company_id: int = Depends(get_current_company_id)
):
    """
    获取回收站文件列表（deleted状态的文件）
    """
    service = FileIndexService(db)
    items = service.get_recyclebin(company_id)
    
    # 转换为响应模型
    response_items = [FileIndexResponse.from_orm(item) for item in items]
    
    return RecycleBinResponse(total=len(response_items), items=response_items)


@router.get("/orphans/list", response_model=FileIndexList, summary="查询孤儿文件")
def get_orphan_files(
    db: Session = Depends(get_db),
    company_id: int = Depends(get_current_company_id)
):
    """
    查询孤儿文件（没有related_entity_id的文件）
    """
    service = FileIndexService(db)
    items = service.find_orphan_files(company_id)
    
    # 转换为响应模型
    response_items = [FileIndexResponse.from_orm(item) for item in items]
    
    return FileIndexList(total=len(response_items), items=response_items)


@router.post("/{file_id}/link", summary="关联文件到业务实体")
def link_file_to_entity(
    file_id: int,
    related_entity_type: str = Query(..., description="实体类型"),
    related_entity_id: int = Query(..., description="实体ID"),
    db: Session = Depends(get_db),
    company_id: int = Depends(get_current_company_id)
):
    """
    将孤儿文件关联到业务实体
    """
    service = FileIndexService(db)
    file_index = service.get_file_index(file_id)
    
    if not file_index:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 验证权限
    if file_index.company_id != company_id:
        raise HTTPException(status_code=403, detail="无权访问此文件")
    
    success = service.link_to_entity(file_id, related_entity_type, related_entity_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="关联失败")
    
    return {"message": "文件已关联到业务实体", "file_id": file_id, "entity_type": related_entity_type, "entity_id": related_entity_id}
