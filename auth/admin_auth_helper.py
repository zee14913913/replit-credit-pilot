"""
Admin认证辅助模块
统一调用8000端口的FastAPI认证服务验证用户身份和权限
"""

import requests
import os
from functools import wraps
from flask import session, redirect, url_for, flash, request
import logging

logger = logging.getLogger(__name__)

# FastAPI后端地址
ACCOUNTING_API_BASE = os.environ.get('API_BASE_URL', 'http://localhost:8000')


def verify_user_with_accounting_api(session_token=None):
    """
    调用8000端口的/api/auth/me验证用户身份
    
    Returns:
        dict: {
            'success': bool,
            'user': {
                'id': int,
                'username': str,
                'role': str,  # admin, accountant, viewer
                'company_id': int
            }
        }
    """
    if not session_token:
        # 尝试从session获取
        session_token = session.get('session_token')
    
    if not session_token:
        return {'success': False, 'error': 'No session token found'}
    
    try:
        # 调用FastAPI的/api/auth/me
        response = requests.get(
            f'{ACCOUNTING_API_BASE}/api/auth/me',
            headers={'Authorization': f'Bearer {session_token}'},
            timeout=5
        )
        
        if response.status_code == 200:
            user_data = response.json()
            return {
                'success': True,
                'user': user_data
            }
        else:
            logger.warning(f"FastAPI认证失败: {response.status_code} - {response.text}")
            return {'success': False, 'error': f'Authentication failed: {response.status_code}'}
    
    except requests.RequestException as e:
        logger.error(f"FastAPI认证请求失败: {str(e)}")
        return {'success': False, 'error': f'Connection error: {str(e)}'}


def require_admin_or_accountant(f):
    """
    装饰器：要求admin或accountant角色才能访问
    调用8000端口的FastAPI认证服务验证
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 1. 检查session中是否有token
        session_token = session.get('session_token')
        
        if not session_token:
            flash('请先登录管理员账号', 'error')
            return redirect(url_for('admin_login'))
        
        # 2. 调用FastAPI验证
        result = verify_user_with_accounting_api(session_token)
        
        if not result['success']:
            flash('认证失败，请重新登录', 'error')
            session.clear()
            return redirect(url_for('admin_login'))
        
        # 3. 检查角色权限
        user = result['user']
        allowed_roles = ['admin', 'accountant']
        
        if user.get('role') not in allowed_roles:
            flash(f'权限不足：此页面仅限管理员和会计人员访问（当前角色：{user.get("role")}）', 'error')
            return redirect(url_for('index'))
        
        # 4. 权限通过，保存用户信息到session
        session['current_user'] = user
        session['user_id'] = user['id']
        session['user_role'] = user['role']
        session['company_id'] = user.get('company_id')
        
        # 5. 执行原函数
        return f(*args, **kwargs)
    
    return decorated_function


def require_admin_only(f):
    """
    装饰器：只允许admin角色访问
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_token = session.get('session_token')
        
        if not session_token:
            flash('请先登录管理员账号', 'error')
            return redirect(url_for('admin_login'))
        
        result = verify_user_with_accounting_api(session_token)
        
        if not result['success']:
            flash('认证失败，请重新登录', 'error')
            session.clear()
            return redirect(url_for('admin_login'))
        
        user = result['user']
        
        if user.get('role') != 'admin':
            flash(f'权限不足：此功能仅限超级管理员（当前角色：{user.get("role")}）', 'error')
            return redirect(url_for('admin_dashboard'))
        
        session['current_user'] = user
        session['user_id'] = user['id']
        session['user_role'] = user['role']
        session['company_id'] = user.get('company_id')
        
        return f(*args, **kwargs)
    
    return decorated_function


def get_current_user():
    """
    获取当前登录用户信息
    """
    return session.get('current_user')


def is_admin():
    """
    检查当前用户是否是admin
    """
    user = get_current_user()
    return user and user.get('role') == 'admin'


def is_admin_or_accountant():
    """
    检查当前用户是否是admin或accountant
    """
    user = get_current_user()
    return user and user.get('role') in ['admin', 'accountant']
