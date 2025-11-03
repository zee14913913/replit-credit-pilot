from functools import wraps
from flask import session, jsonify
from sqlalchemy import select, and_
from accounting_app.db import SessionLocal
from accounting_app.models import User, Permission


def get_current_user():
    """
    获取当前登录用户
    """
    user_id = session.get('user_id')
    if not user_id:
        return None
    
    db = SessionLocal()
    try:
        stmt = select(User).where(User.id == user_id, User.is_active == True)
        result = db.execute(stmt)
        user = result.scalar_one_or_none()
        return user
    finally:
        db.close()


def has_permission(resource, action, user=None):
    """
    检查用户是否拥有指定资源的操作权限
    使用现有的Permission表（role+resource+action）
    
    Args:
        resource: 资源名称 (如 'bank_statements', 'reports', 'invoices')
        action: 操作类型 (如 'view', 'edit', 'delete', 'upload')
        user: 用户对象（可选，默认使用当前登录用户）
    """
    if not user:
        user = get_current_user()
    
    if not user:
        return False
    
    if user.role == 'admin':
        return True
    
    db = SessionLocal()
    try:
        stmt = select(Permission).where(
            and_(
                Permission.role == user.role,
                Permission.resource.in_([resource, '*']),
                Permission.action.in_([action, '*']),
                Permission.allowed == True
            )
        )
        result = db.execute(stmt)
        permission = result.scalar_one_or_none()
        return permission is not None
    finally:
        db.close()


def require_permission(resource, action):
    """
    权限检查装饰器
    用法: @require_permission('bank_statements', 'view')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            
            if not user:
                return jsonify({'error': '未登录', 'error_en': 'Not logged in'}), 401
            
            if not has_permission(resource, action, user):
                return jsonify({
                    'error': f'权限不足：需要 {resource}.{action} 权限',
                    'error_en': f'Permission denied: {resource}.{action} required'
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def require_role(*allowed_roles):
    """
    角色检查装饰器（更简单的权限控制）
    用法: @require_role('admin', 'accountant')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            
            if not user:
                return jsonify({'error': '未登录', 'error_en': 'Not logged in'}), 401
            
            if user.role not in allowed_roles:
                return jsonify({
                    'error': f'权限不足：需要角色 {", ".join(allowed_roles)}',
                    'error_en': f'Permission denied: roles {", ".join(allowed_roles)} required'
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def init_default_permissions():
    """
    初始化默认权限配置
    基于现有Permission表结构（role+resource+action）
    """
    
    default_permissions = [
        {'role': 'admin', 'resource': '*', 'action': '*', 'description': '管理员拥有所有权限'},
        
        {'role': 'accountant', 'resource': 'dashboard', 'action': '*', 'description': '会计师可以访问仪表板'},
        {'role': 'accountant', 'resource': 'reports', 'action': '*', 'description': '会计师可以查看和生成报表'},
        {'role': 'accountant', 'resource': 'bank_statements', 'action': '*', 'description': '会计师可以管理银行对账单'},
        {'role': 'accountant', 'resource': 'invoices', 'action': '*', 'description': '会计师可以管理发票'},
        {'role': 'accountant', 'resource': 'pos_data', 'action': '*', 'description': '会计师可以管理POS数据'},
        {'role': 'accountant', 'resource': 'exceptions', 'action': '*', 'description': '会计师可以处理异常'},
        {'role': 'accountant', 'resource': 'period_closing', 'action': 'close', 'description': '会计师可以关闭会计期间'},
        {'role': 'accountant', 'resource': 'auto_posting_rules', 'action': '*', 'description': '会计师可以管理自动记账规则'},
        
        {'role': 'data_entry', 'resource': 'dashboard', 'action': 'view', 'description': '数据录入员可以查看仪表板'},
        {'role': 'data_entry', 'resource': 'bank_statements', 'action': 'view', 'description': '数据录入员可以查看银行对账单'},
        {'role': 'data_entry', 'resource': 'bank_statements', 'action': 'upload', 'description': '数据录入员可以上传银行对账单'},
        {'role': 'data_entry', 'resource': 'invoices', 'action': 'view', 'description': '数据录入员可以查看发票'},
        {'role': 'data_entry', 'resource': 'invoices', 'action': 'upload', 'description': '数据录入员可以上传发票'},
        {'role': 'data_entry', 'resource': 'pos_data', 'action': 'view', 'description': '数据录入员可以查看POS数据'},
        {'role': 'data_entry', 'resource': 'pos_data', 'action': 'upload', 'description': '数据录入员可以上传POS数据'},
        {'role': 'data_entry', 'resource': 'exceptions', 'action': 'view', 'description': '数据录入员可以查看异常'},
        
        {'role': 'viewer', 'resource': 'dashboard', 'action': 'view', 'description': '查看者可以查看仪表板'},
        {'role': 'viewer', 'resource': 'reports', 'action': 'view', 'description': '查看者可以查看报表'},
        {'role': 'viewer', 'resource': 'reports', 'action': 'export', 'description': '查看者可以导出报表'},
        {'role': 'viewer', 'resource': 'bank_statements', 'action': 'view', 'description': '查看者可以查看银行对账单'},
        {'role': 'viewer', 'resource': 'invoices', 'action': 'view', 'description': '查看者可以查看发票'},
        {'role': 'viewer', 'resource': 'pos_data', 'action': 'view', 'description': '查看者可以查看POS数据'},
        
        {'role': 'loan_officer', 'resource': 'dashboard', 'action': 'view', 'description': '贷款专员可以查看仪表板'},
        {'role': 'loan_officer', 'resource': 'reports', 'action': 'view', 'description': '贷款专员可以查看报表'},
        {'role': 'loan_officer', 'resource': 'reports', 'action': 'export', 'description': '贷款专员可以导出报表'},
        {'role': 'loan_officer', 'resource': 'bank_statements', 'action': 'view', 'description': '贷款专员可以查看银行对账单'},
        {'role': 'loan_officer', 'resource': 'invoices', 'action': 'view', 'description': '贷款专员可以查看发票'},
    ]
    
    db = SessionLocal()
    try:
        existing_permissions = db.execute(
            select(Permission.role, Permission.resource, Permission.action)
        ).fetchall()
        existing_set = {(row[0], row[1], row[2]) for row in existing_permissions}
        
        count_added = 0
        for perm_data in default_permissions:
            perm_key = (perm_data['role'], perm_data['resource'], perm_data['action'])
            if perm_key not in existing_set:
                new_perm = Permission(
                    role=perm_data['role'],
                    resource=perm_data['resource'],
                    action=perm_data['action'],
                    allowed=True,
                    description=perm_data.get('description')
                )
                db.add(new_perm)
                count_added += 1
        
        db.commit()
        
        print("✅ RBAC权限系统初始化完成")
        print(f"   - 新增 {count_added} 个权限记录")
        print(f"   - 总计 {len(existing_set) + count_added} 个权限配置")
    finally:
        db.close()
