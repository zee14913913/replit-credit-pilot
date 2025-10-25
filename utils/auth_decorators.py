"""
权限装饰器 - 控制用户访问权限
"""
from functools import wraps
from flask import session, redirect, url_for, flash, abort, request


def login_required(f):
    """要求用户登录 - 支持Admin和Customer两种登录"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Admin登录检查（有user_role=admin）
        if session.get('user_role') == 'admin':
            return f(*args, **kwargs)
        
        # Customer登录检查（有user_id）
        if 'user_id' not in session:
            flash('请先登录', 'warning')
            # 根据当前路由判断应该跳转到哪个登录页
            if session.get('user_role') is None:
                # 没有任何登录信息，跳转到客户登录
                return redirect(url_for('customer_login'))
            else:
                # 有登录信息但无效，跳转到对应的登录页
                return redirect(url_for('admin_login') if 'admin' in str(request.url) else url_for('customer_login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """要求管理员权限"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录', 'warning')
            return redirect(url_for('customer_login'))
        
        if session.get('user_role') != 'admin':
            flash('此功能需要管理员权限', 'error')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function


def customer_access_required(f):
    """
    要求客户访问权限
    - Admin可以访问任何客户的数据
    - Customer只能访问自己的数据
    
    路由必须包含customer_id参数
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录', 'warning')
            return redirect(url_for('customer_login'))
        
        # 获取路由中的customer_id
        customer_id = kwargs.get('customer_id')
        
        # Admin可以访问所有客户
        if session.get('user_role') == 'admin':
            return f(*args, **kwargs)
        
        # Customer只能访问自己的数据
        if session.get('user_role') == 'customer':
            # 从session获取关联的customer_id
            user_customer_id = session.get('customer_id')
            
            if customer_id and customer_id != user_customer_id:
                flash('您没有权限访问其他客户的数据', 'error')
                abort(403)
            
            return f(*args, **kwargs)
        
        # 其他情况拒绝访问
        flash('权限不足', 'error')
        abort(403)
    
    return decorated_function


def get_accessible_customers(user_id, role):
    """
    获取用户可以访问的客户列表
    - Admin: 返回所有客户
    - Customer: 只返回自己
    
    Returns:
        list: customer_id列表
    """
    from utils.database import get_db
    
    if role == 'admin':
        # 管理员可以访问所有客户
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM customers')
            return [row['id'] for row in cursor.fetchall()]
    
    elif role == 'customer':
        # 客户只能访问自己
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM customers WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            return [row['id']] if row else []
    
    return []
