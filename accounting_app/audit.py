"""
审计日志系统
自动记录所有管理员操作和API调用
"""
from functools import wraps
from flask import request, session, g
from sqlalchemy import text
from accounting_app.db import SessionLocal
from accounting_app.models import AuditLog
from datetime import datetime
import json


def get_client_ip():
    """获取客户端IP地址"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr


def log_audit(
    action_type,
    entity_type=None,
    entity_id=None,
    description=None,
    reason=None,
    old_value=None,
    new_value=None,
    company_id=None
):
    """
    记录审计日志
    
    Args:
        action_type: 操作类型 (export, delete, rule_change, manual_entry, etc.)
        entity_type: 实体类型 (bank_statement, invoice, etc.)
        entity_id: 实体ID
        description: 操作描述
        reason: 操作原因
        old_value: 修改前的值（dict或任何可JSON序列化的对象）
        new_value: 修改后的值（dict或任何可JSON序列化的对象）
        company_id: 公司ID
    """
    db = SessionLocal()
    try:
        user_id = session.get('user_id')
        username = session.get('username') or session.get('email') or 'anonymous'
        
        if not company_id:
            company_id = session.get('company_id')
        
        audit_log = AuditLog(
            company_id=company_id,
            user_id=user_id,
            username=username,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description or f"{action_type} on {entity_type}",
            reason=reason,
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent'),
            request_method=request.method,
            request_path=request.path,
            old_value=old_value,
            new_value=new_value,
            created_at=datetime.utcnow()
        )
        
        db.add(audit_log)
        db.commit()
        
        return audit_log.id
        
    except Exception as e:
        print(f"审计日志记录失败: {str(e)}")
        db.rollback()
        return None
    finally:
        db.close()


def audit_log_decorator(action_type, entity_type=None, require_reason=False):
    """
    审计日志装饰器
    自动记录路由的操作
    
    用法:
        @audit_log_decorator('delete', 'bank_statement')
        def delete_bank_statement(statement_id):
            ...
    
    Args:
        action_type: 操作类型
        entity_type: 实体类型
        require_reason: 是否必须提供操作原因（手工改账等敏感操作必须）
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            json_data = request.get_json(silent=True)
            
            if require_reason:
                if not json_data or not json_data.get('reason'):
                    from flask import jsonify
                    return jsonify({
                        'error': '操作失败：必须提供操作原因',
                        'error_en': 'Operation failed: reason required'
                    }), 400
            
            result = f(*args, **kwargs)
            
            entity_id = kwargs.get('id') or kwargs.get('statement_id') or kwargs.get('invoice_id')
            reason = None
            old_value = None
            new_value = None
            
            if json_data:
                reason = json_data.get('reason')
                if require_reason:
                    old_value = getattr(g, 'audit_old_value', None)
                    new_value = json_data
            
            log_audit(
                action_type=action_type,
                entity_type=entity_type,
                entity_id=entity_id,
                reason=reason,
                old_value=old_value,
                new_value=new_value
            )
            
            return result
        
        return decorated_function
    return decorator


def audit_before_update(entity_obj):
    """
    在更新前记录旧值
    用法:
        old_statement = Statement.query.get(id)
        audit_before_update(old_statement)
        old_statement.amount = new_amount
        db.commit()
    """
    if not hasattr(g, 'audit_old_value'):
        g.audit_old_value = {}
    
    g.audit_old_value = {
        column.name: getattr(entity_obj, column.name)
        for column in entity_obj.__table__.columns
    }


class AuditMiddleware:
    """
    审计日志中间件
    自动记录所有管理员路由和敏感操作
    """
    
    SENSITIVE_PATHS = [
        '/admin/',
        '/api/v1/delete',
        '/api/v1/rules',
        '/api/v1/period_closing',
        '/api/v1/manual_entry',
        '/api/v1/config',
    ]
    
    AUTO_LOG_METHODS = ['POST', 'PUT', 'DELETE', 'PATCH']
    
    def __init__(self, app=None):
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化中间件"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
    
    def before_request(self):
        """请求前处理"""
        g.audit_start_time = datetime.utcnow()
        
    def after_request(self, response):
        """请求后处理：自动记录敏感操作"""
        
        if not self.should_log_request():
            return response
        
        try:
            action_type = self.get_action_type()
            entity_type = self.get_entity_type()
            
            description = f"{request.method} {request.path}"
            
            if response.status_code >= 200 and response.status_code < 300:
                description += " (成功 / Success)"
            else:
                description += f" (失败 / Failed: {response.status_code})"
            
            log_audit(
                action_type=action_type,
                entity_type=entity_type,
                description=description
            )
            
        except Exception as e:
            print(f"中间件审计日志记录失败: {str(e)}")
        
        return response
    
    def should_log_request(self):
        """判断是否需要记录此请求"""
        if request.path.startswith('/static/'):
            return False
        
        if request.method not in self.AUTO_LOG_METHODS:
            return False
        
        for sensitive_path in self.SENSITIVE_PATHS:
            if request.path.startswith(sensitive_path):
                return True
        
        return False
    
    def get_action_type(self):
        """根据请求路径和方法推断操作类型"""
        method = request.method
        path = request.path.lower()
        
        if 'delete' in path or method == 'DELETE':
            return 'delete'
        elif 'export' in path:
            return 'export'
        elif 'rule' in path:
            return 'rule_change'
        elif 'manual' in path or 'journal_entry' in path:
            return 'manual_entry'
        elif 'period' in path and 'clos' in path:
            return 'period_closing'
        elif 'config' in path:
            return 'config_change'
        elif method == 'POST':
            return 'create'
        elif method in ['PUT', 'PATCH']:
            return 'update'
        else:
            return 'api_call'
    
    def get_entity_type(self):
        """根据请求路径推断实体类型"""
        path = request.path.lower()
        
        if 'bank' in path or 'statement' in path:
            return 'bank_statement'
        elif 'invoice' in path:
            return 'invoice'
        elif 'pos' in path:
            return 'pos_transaction'
        elif 'rule' in path:
            return 'auto_posting_rule'
        elif 'journal' in path:
            return 'journal_entry'
        elif 'period' in path:
            return 'period_closing'
        elif 'config' in path:
            return 'system_config'
        elif 'user' in path:
            return 'user'
        elif 'company' in path:
            return 'company'
        else:
            return None


def init_audit_middleware(app):
    """
    初始化审计日志中间件
    在FastAPI main.py中调用
    """
    middleware = AuditMiddleware()
    middleware.init_app(app)
    print("✅ 审计日志中间件已初始化")
    return middleware
