"""
Flask RBAC Bridge
桥接Flask到FastAPI的RBAC权限系统

Phase 2-2 Task 3: Flask与FastAPI权限统一
- 提供Flask装饰器：require_flask_auth, require_flask_permission
- 查询PostgreSQL的users和permissions表
- 防御性审计日志写入
"""
from functools import wraps
from flask import session, redirect, url_for, flash, request, abort
import psycopg2
import os
import logging
import hashlib

logger = logging.getLogger(__name__)


def get_pg_connection():
    """获取PostgreSQL连接（FastAPI数据库）"""
    return psycopg2.connect(os.environ.get('DATABASE_URL'))


def verify_flask_user(username: str = None, password: str = None, user_id: int = None):
    """
    验证Flask用户身份（从PostgreSQL的users表）
    
    Args:
        username: 用户名（如果通过username验证）
        password: 密码（如果通过username验证）
        user_id: 用户ID（如果通过session验证）
    
    Returns:
        dict: {'success': bool, 'user': dict, 'error': str}
    """
    conn = None
    try:
        conn = get_pg_connection()
        cursor = conn.cursor()
        
        if user_id:
            # 通过user_id验证（session验证）
            cursor.execute("""
                SELECT id, username, password_hash, role, company_id, is_active
                FROM users
                WHERE id = %s AND is_active = TRUE
            """, (user_id,))
        else:
            # 通过username验证（登录验证）
            cursor.execute("""
                SELECT id, username, password_hash, role, company_id, is_active
                FROM users
                WHERE username = %s AND is_active = TRUE
            """, (username,))
        
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return {'success': False, 'user': None, 'error': '用户不存在或已禁用'}
        
        user_dict = {
            'id': user[0],
            'username': user[1],
            'password_hash': user[2],
            'role': user[3],
            'company_id': user[4],
            'is_active': user[5]
        }
        
        # 如果提供了密码，验证密码
        if password:
            import bcrypt
            if not bcrypt.checkpw(password.encode('utf-8'), user_dict['password_hash'].encode('utf-8')):
                return {'success': False, 'user': None, 'error': '密码错误'}
        
        return {'success': True, 'user': user_dict, 'error': None}
    
    except Exception as e:
        logger.error(f"Flask用户验证失败: {e}")
        return {'success': False, 'user': None, 'error': str(e)}


def check_flask_permission(user_id: int, resource: str, action: str):
    """
    检查Flask用户权限（从PostgreSQL的permissions表）
    
    Args:
        user_id: 用户ID
        resource: 资源名称（例如：export:journal_entries）
        action: 操作名称（例如：read）
    
    Returns:
        bool: True表示有权限，False表示无权限
    """
    try:
        conn = get_pg_connection()
        cursor = conn.cursor()
        
        # 先获取用户角色
        cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return False
        
        role = user[0]
        
        # 检查权限
        cursor.execute("""
            SELECT allowed
            FROM permissions
            WHERE role = %s AND resource = %s AND action = %s
        """, (role, resource, action))
        
        permission = cursor.fetchone()
        conn.close()
        
        if not permission:
            # 没有配置该权限，默认禁止
            return False
        
        return permission[0]  # allowed字段
    
    except Exception as e:
        logger.error(f"Flask权限检查失败: {e}")
        return False


def write_flask_audit_log(user_id: int, username: str, company_id: int, action_type: str, 
                          entity_type: str, description: str, success: bool, 
                          old_value: dict = None, new_value: dict = None) -> None:
    """
    写入Flask审计日志到PostgreSQL（防御性）
    
    Args:
        user_id: 用户ID
        username: 用户名
        company_id: 公司ID
        action_type: 操作类型（view, create, update, delete, export等）
        entity_type: 实体类型（customer, statement, transaction等）
        description: 操作描述
        success: 操作是否成功
        old_value: 旧值（JSON）
        new_value: 新值（JSON）
    """
    conn = None
    try:
        import json
        conn = get_pg_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO audit_logs (
                company_id, user_id, username, action_type, entity_type,
                description, old_value, new_value, success, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """, (
            company_id, user_id, username, action_type, entity_type,
            description, 
            json.dumps(old_value) if old_value else None,
            json.dumps(new_value) if new_value else None,
            success
        ))
        
        conn.commit()
        conn.close()
        logger.info(f"Flask审计日志写入成功: {action_type} {entity_type}")
    
    except Exception as e:
        logger.error(f"Flask审计日志写入失败: {e}")
        if conn:
            try:
                conn.rollback()
                conn.close()
            except:
                pass


def require_flask_auth(f):
    """
    Flask装饰器：要求用户登录
    
    用法：
        @app.route('/admin')
        @require_flask_auth
        def admin_page():
            user = session['flask_rbac_user']
            return f"Hello {user['username']}"
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 检查session中是否有flask_rbac_user_id
        user_id = session.get('flask_rbac_user_id')
        
        if not user_id:
            flash('请先登录', 'warning')
            return redirect(url_for('admin_login'))
        
        # 验证用户
        result = verify_flask_user(username=None, user_id=user_id)
        
        if not result['success']:
            session.clear()
            flash('会话已过期，请重新登录', 'warning')
            return redirect(url_for('admin_login'))
        
        # 将用户信息存入session供后续使用
        session['flask_rbac_user'] = result['user']
        
        return f(*args, **kwargs)
    
    return decorated_function


def require_flask_permission(resource: str, action: str = 'read'):
    """
    Flask装饰器：要求用户有特定权限
    
    用法：
        @app.route('/export/csv')
        @require_flask_permission('export:journal_entries', 'read')
        def export_csv():
            user = session['flask_rbac_user']
            return "Exporting..."
    
    Args:
        resource: 资源名称（例如：export:journal_entries）
        action: 操作名称（例如：read, write, delete）
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 首先检查是否登录
            user_id = session.get('flask_rbac_user_id')
            
            if not user_id:
                flash('请先登录', 'warning')
                return redirect(url_for('admin_login'))
            
            # 验证用户
            result = verify_flask_user(username=None, user_id=user_id)
            
            if not result['success']:
                session.clear()
                flash('会话已过期，请重新登录', 'warning')
                return redirect(url_for('admin_login'))
            
            user = result['user']
            
            # 检查权限
            has_permission = check_flask_permission(user['id'], resource, action)
            
            if not has_permission:
                # 写入审计日志（权限拒绝）
                write_flask_audit_log(
                    user_id=user['id'],
                    username=user['username'],
                    company_id=user['company_id'],
                    action_type='access_denied',
                    entity_type='permission',
                    description=f"权限拒绝: {resource} - {action}",
                    success=False,
                    new_value={'resource': resource, 'action': action, 'role': user['role']}
                )
                
                abort(403, description=f"权限不足：无法对 {resource} 执行 {action} 操作")
            
            # 将用户信息存入session供后续使用
            session['flask_rbac_user'] = user
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator
