"""
多租户隔离中间件
确保所有查询都自动注入 company_id 过滤条件
"""
from fastapi import Request, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class CompanyContext:
    """公司上下文 - 存储当前请求的company_id"""
    
    def __init__(self):
        self.company_id: Optional[int] = None
        self.company_code: Optional[str] = None


# 全局上下文（在请求范围内使用）
_company_context = CompanyContext()


def get_company_id_from_request(request: Request) -> Optional[int]:
    """
    从请求中提取company_id
    
    优先级:
    1. Header: X-Company-ID
    2. Query参数: company_id
    3. Path参数: company_id
    4. 默认公司ID: 1
    """
    # 从Header获取
    company_id = request.headers.get('X-Company-ID')
    if company_id:
        try:
            return int(company_id)
        except ValueError:
            logger.warning(f"无效的X-Company-ID header: {company_id}")
    
    # 从Query参数获取
    company_id = request.query_params.get('company_id')
    if company_id:
        try:
            return int(company_id)
        except ValueError:
            logger.warning(f"无效的company_id参数: {company_id}")
    
    # 从Path参数获取（需要在路由中定义）
    if hasattr(request, 'path_params') and 'company_id' in request.path_params:
        try:
            return int(request.path_params['company_id'])
        except ValueError:
            logger.warning(f"无效的path company_id: {request.path_params['company_id']}")
    
    # 默认返回公司ID 1（开发环境）
    # 生产环境应该强制要求company_id
    logger.warning("未找到company_id，使用默认值1")
    return 1


async def company_id_middleware(request: Request, call_next):
    """
    中间件: 自动注入company_id到请求上下文
    """
    company_id = get_company_id_from_request(request)
    
    # 设置到全局上下文
    _company_context.company_id = company_id
    
    # 添加到request state
    request.state.company_id = company_id
    
    logger.debug(f"请求 {request.url.path} 使用 company_id={company_id}")
    
    response = await call_next(request)
    return response


def get_current_company_id(request: Request) -> int:
    """
    依赖注入: 获取当前公司ID
    
    使用方法:
    @router.get("/")
    def my_endpoint(company_id: int = Depends(get_current_company_id), db: Session = Depends(get_db)):
        # 现在company_id会自动注入
        results = db.query(Model).filter(Model.company_id == company_id).all()
    """
    if hasattr(request.state, 'company_id'):
        return request.state.company_id
    
    # 如果中间件未设置，尝试手动获取
    company_id = get_company_id_from_request(request)
    if company_id is None:
        raise HTTPException(
            status_code=400,
            detail="缺少company_id参数。请在Header中提供X-Company-ID或在URL中添加company_id参数"
        )
    
    return company_id


def validate_company_access(company_id: int, db: Session) -> bool:
    """
    验证公司访问权限
    
    在生产环境中，这里应该检查:
    1. 公司是否存在
    2. 用户是否有权限访问该公司
    3. 公司状态是否激活
    """
    from ..models import Company
    
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        logger.error(f"公司ID {company_id} 不存在")
        return False
    
    # 可以添加更多权限检查
    # if not user_has_permission(current_user, company):
    #     return False
    
    return True


class MultiTenantQuery:
    """
    多租户查询助手
    自动添加company_id过滤条件
    """
    
    @staticmethod
    def filter_by_company(query, model, company_id: int):
        """
        为查询添加company_id过滤
        
        使用示例:
        query = db.query(BankStatement)
        query = MultiTenantQuery.filter_by_company(query, BankStatement, company_id)
        """
        if hasattr(model, 'company_id'):
            return query.filter(model.company_id == company_id)
        else:
            logger.warning(f"模型 {model.__name__} 没有 company_id 字段")
            return query
    
    @staticmethod
    def get_all(db: Session, model, company_id: int, **filters):
        """
        获取所有记录（自动过滤company_id）
        
        使用示例:
        statements = MultiTenantQuery.get_all(
            db, BankStatement, company_id,
            statement_month='2025-01'
        )
        """
        query = db.query(model).filter(model.company_id == company_id)
        
        for key, value in filters.items():
            if hasattr(model, key):
                query = query.filter(getattr(model, key) == value)
        
        return query.all()
    
    @staticmethod
    def get_by_id(db: Session, model, entity_id: int, company_id: int):
        """
        根据ID获取记录（自动验证company_id）
        
        使用示例:
        statement = MultiTenantQuery.get_by_id(
            db, BankStatement, statement_id, company_id
        )
        """
        entity = db.query(model).filter(
            model.id == entity_id,
            model.company_id == company_id
        ).first()
        
        if not entity:
            raise HTTPException(
                status_code=404,
                detail=f"{model.__name__} ID {entity_id} 不存在或无权访问"
            )
        
        return entity
    
    @staticmethod
    def create(db: Session, model, company_id: int, **data):
        """
        创建记录（自动设置company_id）
        
        使用示例:
        new_statement = MultiTenantQuery.create(
            db, BankStatement, company_id,
            bank_name='Maybank',
            account_number='123456'
        )
        """
        data['company_id'] = company_id
        entity = model(**data)
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity


# ========== 使用示例 ==========

"""
在 FastAPI 应用中使用:

# 1. 注册中间件
from accounting_app.middleware.multi_tenant import company_id_middleware
app.middleware("http")(company_id_middleware)

# 2. 在路由中使用依赖注入
from accounting_app.middleware.multi_tenant import get_current_company_id

@router.get("/bank-statements")
def get_statements(
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db)
):
    # company_id 自动注入
    statements = db.query(BankStatement).filter(
        BankStatement.company_id == company_id
    ).all()
    return statements

# 3. 使用查询助手
from accounting_app.middleware.multi_tenant import MultiTenantQuery

@router.get("/bank-statements/{statement_id}")
def get_statement(
    statement_id: int,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db)
):
    # 自动验证company_id
    statement = MultiTenantQuery.get_by_id(db, BankStatement, statement_id, company_id)
    return statement
"""
