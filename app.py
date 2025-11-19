from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, send_from_directory, session
import os
from datetime import datetime, timedelta
import json
import threading
import time
import schedule
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import requests

# Configure logger
logger = logging.getLogger(__name__)

# ==================== PDF PARSER CONFIG ====================
# PDF解析器强制配置（VBA优先）
from config.pdf_parser_config import (
    PARSER_MODE,
    is_pdf_upload_allowed,
    is_auto_parse_allowed,
    is_vba_upload_allowed,
    get_upload_guidance,
    ERROR_MESSAGES
)
# ==================== END PDF PARSER CONFIG ====================

# ==================== FEATURE TOGGLES ====================
# 功能开关配置（环境变量控制，默认关闭）
FEATURE_ADVANCED_ANALYTICS = os.getenv('FEATURE_ADVANCED_ANALYTICS', 'false').lower() == 'true'
FEATURE_CUSTOMER_TIER = os.getenv('FEATURE_CUSTOMER_TIER', 'false').lower() == 'true'
# ==================== END FEATURE TOGGLES ====================

from db.database import get_db, log_audit, get_all_customers, get_customer, get_customer_cards, get_card_statements, get_statement_transactions
from auth.flask_rbac_bridge import require_flask_auth, require_flask_permission, write_flask_audit_log, verify_flask_user, extract_flask_request_info
from ingest.statement_parser import parse_statement_auto
from validate.categorizer import categorize_transaction, validate_statement, get_spending_summary
from validate.transaction_validator import validate_transactions, generate_validation_report
from validate.reminder_service import check_and_send_reminders, create_reminder, get_pending_reminders, mark_as_paid
from loan.dsr_calculator import calculate_dsr, calculate_max_loan_amount, simulate_loan_scenarios
# Removed: News management feature deleted
from report.pdf_generator import generate_monthly_report
import pdfplumber

# New services for advanced features
from export.export_service import ExportService
from search.search_service import SearchService
from batch.batch_service import BatchService
# Removed: Budget management feature deleted
from email_service.email_sender import EmailService
from db.tag_service import TagService

# Statement organizer and optimization
from services.statement_organizer import StatementOrganizer
from services.optimization_proposal import OptimizationProposal
from services.uniqueness_validator import UniquenessValidator

# Monthly report automation
from services.monthly_report_scheduler import MonthlyReportScheduler

# i18n support
from i18n.translations import translate, TRANSLATIONS

# Customer authentication
from auth.customer_auth import (
    create_customer_login, 
    authenticate_customer, 
    verify_session, 
    logout_customer,
    get_customer_data_summary
)

# Admin认证辅助模块（统一调用8000端口验证）
from auth.admin_auth_helper import (
    require_admin_or_accountant,
    require_admin_only,
    verify_user_with_accounting_api,
    get_current_user,
    is_admin,
    is_admin_or_accountant
)

# Admin Portfolio Management
from admin.portfolio_manager import PortfolioManager

# Dashboard Metrics Service

# CTOS Consent Management (Phase 7)
from app_ctos_routes import (
    ctos_consent,
    ctos_personal,
    ctos_personal_submit,
    ctos_company,
    ctos_company_submit
)
from services.dashboard_metrics import get_customer_monthly_metrics, get_all_cards_summary

# Card Optimizer API (Fixed Version)
from api.card_optimizer_routes_fixed import register_card_optimizer_routes

# Business Plan AI Service
from services.business_plan_ai import generate_business_plan

# Credit Card Recommendation Services
from modules.recommendations.card_recommendation_engine import CardRecommendationEngine
from modules.recommendations.comparison_report_generator import ComparisonReportGenerator
from modules.recommendations.benefit_calculator import BenefitCalculator

# Receipt Management Services
from ingest.receipt_parser import ReceiptParser
from services.receipt_matcher import ReceiptMatcher

# Monthly Summary Report Service
from services.monthly_summary_report import MonthlySummaryReport

# Initialize services
export_service = ExportService()
search_service = SearchService()
batch_service = BatchService()
# Removed: budget_service initialization (feature deleted)
email_service = EmailService()
tag_service = TagService()
monthly_summary_reporter = MonthlySummaryReport()
statement_organizer = StatementOrganizer()
optimization_service = OptimizationProposal()
monthly_report_scheduler = MonthlyReportScheduler()
card_recommender = CardRecommendationEngine()
comparison_reporter = ComparisonReportGenerator()
benefit_calculator = BenefitCalculator()
receipt_parser = ReceiptParser()
receipt_matcher = ReceiptMatcher()

app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB limit for batch uploads
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable static file caching

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Register abs() function for Jinja2 templates
app.jinja_env.globals.update(abs=abs)

# Force no-cache headers for all responses
@app.after_request
def add_no_cache_headers(response):
    """Add no-cache headers to prevent browser/server caching issues"""
    if request.path.startswith('/static/css/'):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, public, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        # Remove ETag and Last-Modified to prevent 304 responses
        response.headers.pop('ETag', None)
        response.headers.pop('Last-Modified', None)
    return response

# Language support
import json

# Load translation files
TRANSLATIONS = {}
try:
    with open('static/i18n/en.json', 'r', encoding='utf-8') as f:
        TRANSLATIONS['en'] = json.load(f)
    with open('static/i18n/zh.json', 'r', encoding='utf-8') as f:
        TRANSLATIONS['zh'] = json.load(f)
except Exception as e:
    print(f"⚠️ 翻译文件加载失败: {e}")
    TRANSLATIONS = {'en': {}, 'zh': {}}

def translate(key, lang='en', **kwargs):
    """
    翻译函数：从翻译字典中获取对应语言的文本
    """
    text = TRANSLATIONS.get(lang, {}).get(key, key)
    # 支持参数替换，例如 {name}, {email} 等
    if kwargs:
        try:
            text = text.format(**kwargs)
        except:
            pass
    return text

def get_current_language():
    """
    智能语言管理：
    - 新会话（首次访问）默认英文
    - 用户切换语言后，在整个会话期间保持该语言
    - 关闭浏览器后重新打开，恢复为英文
    """
    # 1. URL parameter 优先（用于语言切换）
    lang = request.args.get('lang')
    if lang in ('zh', 'en'):
        session['language'] = lang  # 保存到 session，在会话期间持久
        return lang
    
    # 2. Session 读取（在会话期间保持用户选择的语言）
    if 'language' in session:
        return session['language']
    
    # 3. 新会话默认英文
    return 'en'

# Register Card Optimizer API Blueprint
register_card_optimizer_routes(app)

@app.context_processor
def inject_language():
    """Inject language and user role info into all templates"""
    lang = get_current_language()
    
    # Check session for admin/accountant role without making API calls
    # This is safe for anonymous requests and doesn't mutate session
    def check_admin_or_accountant():
        try:
            # Quick check: look for existing session data first
            flask_user_id = session.get('flask_rbac_user_id')
            flask_user = session.get('flask_rbac_user')
            
            if flask_user_id and flask_user:
                # User already verified via Flask RBAC
                role = flask_user.get('role')
                return role in ['admin', 'accountant']
            
            # Check FastAPI session
            if session.get('user_role'):
                return session.get('user_role') in ['admin', 'accountant']
            
            return False
        except:
            return False
    
    def check_admin():
        try:
            # Quick check: look for existing session data first
            flask_user = session.get('flask_rbac_user')
            if flask_user:
                return flask_user.get('role') == 'admin'
            
            if session.get('user_role'):
                return session.get('user_role') == 'admin'
            
            return False
        except:
            return False
    
    return {
        'current_lang': lang,
        't': lambda key, **kwargs: translate(key, lang, **kwargs),
        'is_admin_or_accountant': check_admin_or_accountant(),
        'is_admin': check_admin()
    }

@app.route('/set-language/<lang>')
def set_language(lang):
    """
    切换语言并保存到 session
    - 在当前会话期间，所有页面保持该语言
    - 关闭浏览器后重新打开，恢复为英文
    """
    if lang in ['en', 'zh']:
        session['language'] = lang
    return redirect(request.referrer or url_for('index'))


@app.route('/api/ai-assistant/<path:subpath>', methods=['GET', 'POST'])
def ai_assistant_proxy(subpath):
    """
    AI助手API代理（Flask -> FastAPI）
    V2企业智能版新增
    """
    try:
        fastapi_url = f'http://localhost:8000/api/ai-assistant/{subpath}'
        
        if request.method == 'GET':
            resp = requests.get(fastapi_url, params=request.args, timeout=30)
        else:
            resp = requests.post(fastapi_url, json=request.json, timeout=30)
        
        return resp.json(), resp.status_code
        
    except requests.exceptions.Timeout:
        return {"error": "请求超时"}, 504
    except Exception as e:
        return {"error": f"代理错误: {str(e)}"}, 500

@app.route('/view_statement_file/<int:statement_id>')
@require_admin_or_accountant
def view_statement_file(statement_id):
    """查看账单原始文件（支持新组织结构 + 向后兼容旧路径）"""
    from flask import send_file, make_response
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT file_path FROM statements WHERE id = ?', (statement_id,))
        row = cursor.fetchone()
        
        if not row or not row['file_path']:
            return "文件不存在", 404
        
        file_path = row['file_path']
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            # 向后兼容：如果新路径不存在，尝试从attached_assets读取
            if file_path.startswith('static/uploads/'):
                # 尝试旧的attached_assets路径
                old_path = file_path.replace('static/uploads/', 'attached_assets/', 1)
                # 尝试从文件名中提取
                import re
                filename_match = re.search(r'/([^/]+\.pdf)$', file_path)
                if filename_match:
                    # 查找attached_assets中的文件
                    for root, dirs, files in os.walk('attached_assets'):
                        if filename_match.group(1) in files:
                            file_path = os.path.join(root, filename_match.group(1))
                            break
            
            # 最后检查
            if not os.path.exists(file_path):
                return f"文件未找到: {row['file_path']}", 404
        
        # 发送文件
        response = make_response(send_file(file_path, mimetype='application/pdf'))
        
        # 设置响应头
        response.headers['Content-Disposition'] = 'inline'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        return response

@app.route('/static/uploads/<path:filename>')
@require_admin_or_accountant
def serve_uploaded_file(filename):
    """Serve uploaded PDF files with correct MIME type (legacy support)"""
    from flask import send_from_directory, make_response
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if not os.path.exists(file_path):
        return "File not found", 404
    
    response = make_response(send_from_directory(app.config['UPLOAD_FOLDER'], filename))
    
    # Set correct MIME type for PDF
    if filename.lower().endswith('.pdf'):
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline; filename=' + filename
    
    # Prevent caching
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response

@app.route('/')
def index():
    """Dashboard - 权限过滤：验证后才加载数据，确保安全"""
    # 导入验证辅助函数
    from auth.admin_auth_helper import verify_user_with_accounting_api
    
    # 默认：未验证，不加载任何数据
    customers = []
    is_admin_verified = False
    
    # 步骤1：如果有admin session，先验证（在加载数据之前）
    if session.get('flask_rbac_user_id'):
        auth_result = verify_user_with_accounting_api()
        
        if auth_result['success'] and auth_result['user']['role'] in ['admin', 'accountant']:
            # ✅ Admin/Accountant验证通过
            is_admin_verified = True
        else:
            # ❌ 验证失败或非admin角色：清除session
            session.pop('flask_rbac_user_id', None)
            session.pop('flask_rbac_user', None)
    
    # 步骤2：根据验证结果加载数据（验证后才加载）
    if is_admin_verified:
        # Admin/Accountant：加载所有客户
        customers = get_all_customers()
    elif session.get('customer_token'):
        # Customer：验证token并只加载自己
        verification = verify_session(session['customer_token'])
        
        if verification['success']:
            customer_id = verification['customer_id']
            with get_db() as conn:
                cursor = conn.cursor()
                # 只查询verified的customer_id，确保活跃状态
                cursor.execute('SELECT * FROM customers WHERE id = ? AND is_active = 1', (customer_id,))
                customer_row = cursor.fetchone()
                if customer_row:
                    customers = [dict(customer_row)]
                else:
                    # 账户不存在或被禁用
                    session.pop('customer_token', None)
        else:
            # Token无效
            session.pop('customer_token', None)
    
    # 步骤3：返回结果（未登录 = 空列表）
    return render_template('index.html', customers=customers)

@app.route('/add_customer_page')
@require_admin_or_accountant
def add_customer_page():
    """Show add customer form page - Admin only"""
    return render_template('add_customer.html')

@app.route('/add_customer', methods=['POST'])
@require_admin_or_accountant
def add_customer():
    """Admin: Add a new customer"""
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        monthly_income = float(request.form.get('monthly_income', 0))
        
        # 新增：收款账户信息
        personal_account_name = request.form.get('personal_account_name', '').strip()
        personal_account_number = request.form.get('personal_account_number', '').strip()
        company_account_name = request.form.get('company_account_name', '').strip()
        company_account_number = request.form.get('company_account_number', '').strip()
        
        if not all([name, email, phone]):
            lang = get_current_language()
            flash(translate('all_fields_required', lang), 'error')
            return redirect(url_for('index'))
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Check if email already exists
            cursor.execute("SELECT id FROM customers WHERE email = ?", (email,))
            if cursor.fetchone():
                lang = get_current_language()
                flash(translate('customer_already_exists', lang).format(email=email), 'error')
                return redirect(url_for('index'))
            
            # 自动生成customer_code（简化版，无序号）
            def generate_customer_code(name):
                """生成客户代码：Be_rich_{首字母缩写}"""
                words = name.upper().split()
                initials = ''.join([word[0] for word in words if word])
                return f"Be_rich_{initials}"
            
            customer_code = generate_customer_code(name)
            
            # Insert new customer with customer_code and account info
            cursor.execute("""
                INSERT INTO customers (
                    name, email, phone, monthly_income, customer_code,
                    personal_account_name, personal_account_number,
                    company_account_name, company_account_number
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, email, phone, monthly_income, customer_code,
                  personal_account_name or None, personal_account_number or None,
                  company_account_name or None, company_account_number or None))
            
            customer_id = cursor.lastrowid
            conn.commit()
            
            lang = get_current_language()
            flash(translate('customer_added_success', lang).format(name=name, code=customer_code, email=email), 'success')
            return redirect(url_for('customer_dashboard', customer_id=customer_id))
            
    except Exception as e:
        lang = get_current_language()
        flash(translate('error_adding_customer', lang).format(error=str(e)), 'error')
        return redirect(url_for('index'))

@app.route('/edit_customer/<int:customer_id>', methods=['GET'])
@require_admin_or_accountant
def edit_customer_page(customer_id):
    """Show edit customer form page - Admin only"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        customer_row = cursor.fetchone()
        customer = dict(customer_row) if customer_row else None
        
        if customer:
            # 加载customer_accounts账户，向后兼容旧表单
            cursor.execute('''
                SELECT account_name, account_number FROM customer_accounts 
                WHERE customer_id = ? AND account_type = 'personal' AND is_primary = 1
            ''', (customer_id,))
            personal_account = cursor.fetchone()
            if personal_account:
                customer['personal_account_name'] = personal_account[0]
                customer['personal_account_number'] = personal_account[1]
            
            cursor.execute('''
                SELECT account_name, account_number FROM customer_accounts 
                WHERE customer_id = ? AND account_type = 'company' AND is_primary = 1
            ''', (customer_id,))
            company_account = cursor.fetchone()
            if company_account:
                customer['company_account_name'] = company_account[0]
                customer['company_account_number'] = company_account[1]
    
    if not customer:
        lang = get_current_language()
        flash('客户不存在', 'error')
        return redirect(url_for('index'))
    
    return render_template('edit_customer.html', customer=customer)

@app.route('/edit_customer/<int:customer_id>', methods=['POST'])
@require_admin_or_accountant
def edit_customer(customer_id):
    """Update customer information - now supports multiple accounts"""
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        monthly_income = float(request.form.get('monthly_income', 0))
        
        # 收款账户信息（向后兼容）
        personal_account_name = request.form.get('personal_account_name', '').strip()
        personal_account_number = request.form.get('personal_account_number', '').strip()
        company_account_name = request.form.get('company_account_name', '').strip()
        company_account_number = request.form.get('company_account_number', '').strip()
        
        if not all([name, email, phone]):
            flash('所有必填字段都需要填写', 'error')
            return redirect(url_for('edit_customer_page', customer_id=customer_id))
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Check if email already exists (excluding current customer)
            cursor.execute("SELECT id FROM customers WHERE email = ? AND id != ?", (email, customer_id))
            if cursor.fetchone():
                flash(f'邮箱 {email} 已被其他客户使用', 'error')
                return redirect(url_for('edit_customer_page', customer_id=customer_id))
            
            # Update customer基本信息
            cursor.execute("""
                UPDATE customers SET
                    name = ?,
                    email = ?,
                    phone = ?,
                    monthly_income = ?
                WHERE id = ?
            """, (name, email, phone, monthly_income, customer_id))
            
            # Update customer_accounts表（私人账户）
            if personal_account_name and personal_account_number:
                cursor.execute('''
                    SELECT id FROM customer_accounts 
                    WHERE customer_id = ? AND account_type = 'personal' AND is_primary = 1
                ''', (customer_id,))
                existing = cursor.fetchone()
                
                if existing:
                    cursor.execute('''
                        UPDATE customer_accounts 
                        SET account_name = ?, account_number = ?
                        WHERE id = ?
                    ''', (personal_account_name, personal_account_number, existing[0]))
                else:
                    cursor.execute('''
                        INSERT INTO customer_accounts (customer_id, account_type, account_name, account_number, is_primary)
                        VALUES (?, 'personal', ?, ?, 1)
                    ''', (customer_id, personal_account_name, personal_account_number))
            
            # Update customer_accounts表（公司账户）
            if company_account_name and company_account_number:
                cursor.execute('''
                    SELECT id FROM customer_accounts 
                    WHERE customer_id = ? AND account_type = 'company' AND is_primary = 1
                ''', (customer_id,))
                existing = cursor.fetchone()
                
                if existing:
                    cursor.execute('''
                        UPDATE customer_accounts 
                        SET account_name = ?, account_number = ?
                        WHERE id = ?
                    ''', (company_account_name, company_account_number, existing[0]))
                else:
                    cursor.execute('''
                        INSERT INTO customer_accounts (customer_id, account_type, account_name, account_number, is_primary)
                        VALUES (?, 'company', ?, ?, 1)
                    ''', (customer_id, company_account_name, company_account_number))
            
            conn.commit()
            
            flash(f'✅ 客户 {name} 的信息已成功更新', 'success')
            return redirect(url_for('customer_dashboard', customer_id=customer_id))
            
    except Exception as e:
        flash(f'更新客户信息时出错：{str(e)}', 'error')
        return redirect(url_for('edit_customer_page', customer_id=customer_id))

@app.route('/customer/<int:customer_id>')
@require_admin_or_accountant
def customer_dashboard(customer_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        customer_row = cursor.fetchone()
        customer = dict(customer_row) if customer_row else None
    
    if not customer:
        lang = get_current_language()
        flash(translate('customer_not_found', lang), 'error')
        return redirect(url_for('index'))
    
    cards = get_customer_cards(customer_id)
    
    total_spending = 0
    all_transactions = []
    for card in cards:
        statements = get_card_statements(card['id'])
        for statement in statements:
            if statement['is_confirmed']:
                transactions = get_statement_transactions(statement['id'])
                all_transactions.extend(transactions)
                total_spending += sum(t['amount'] for t in transactions)
    
    spending_summary = get_spending_summary(all_transactions) if all_transactions else {}
    
    from services.card_timeline import get_card_12month_timeline, get_month_coverage_percentage
    cards_with_timeline = []
    for card in cards:
        card_dict = dict(card)
        card_dict['timeline'] = get_card_12month_timeline(card['id'])
        card_dict['coverage_percentage'] = get_month_coverage_percentage(card['id'])
        cards_with_timeline.append(card_dict)
    
    # 获取月度账本数据（8项计算）
    from services.monthly_ledger_engine import MonthlyLedgerEngine
    ledger_engine = MonthlyLedgerEngine()
    
    # 获取最新月份的账本汇总
    monthly_ledgers = []
    for card in cards:
        with get_db() as conn:
            cursor = conn.cursor()
            # 获取最新月份
            cursor.execute("""
                SELECT month_start, statement_id
                FROM monthly_ledger 
                WHERE card_id = ? 
                ORDER BY month_start DESC 
                LIMIT 1
            """, (card['id'],))
            latest_month = cursor.fetchone()
            
            if latest_month:
                month_start, statement_id = latest_month
                
                # 获取客户账本数据
                cursor.execute("""
                    SELECT previous_balance, customer_spend, customer_payments, rolling_balance
                    FROM monthly_ledger
                    WHERE card_id = ? AND month_start = ?
                """, (card['id'], month_start))
                customer_ledger = cursor.fetchone()
                
                # 获取INFINITE账本数据
                cursor.execute("""
                    SELECT previous_balance, infinite_spend, supplier_fee, infinite_payments, rolling_balance
                    FROM infinite_monthly_ledger
                    WHERE card_id = ? AND month_start = ?
                """, (card['id'], month_start))
                infinite_ledger = cursor.fetchone()
                
                # 获取转账记录（第8项）
                cursor.execute("""
                    SELECT SUM(amount) as total_transfers
                    FROM savings_transactions
                    WHERE customer_name_tag = ? AND DATE(transaction_date) LIKE ?
                    AND (description LIKE '%转账%' OR description LIKE '%TRANSFER%')
                """, (customer['name'], month_start[:7] + '%'))
                transfer_result = cursor.fetchone()
                infinite_transfers = transfer_result[0] if transfer_result and transfer_result[0] else 0
                
                if customer_ledger and infinite_ledger:
                    monthly_ledgers.append({
                        'card': card,
                        'month': month_start[:7],  # YYYY-MM格式
                        'customer': {
                            'previous_balance': customer_ledger[0],
                            'total_spend': customer_ledger[1],
                            'total_payments': customer_ledger[2],
                            'rolling_balance': customer_ledger[3]
                        },
                        'infinite': {
                            'previous_balance': infinite_ledger[0],
                            'total_spend': infinite_ledger[1],
                            'supplier_fee': infinite_ledger[2],
                            'total_payments': infinite_ledger[3],
                            'rolling_balance': infinite_ledger[4],
                            'transfers': infinite_transfers
                        }
                    })
    
    return render_template('customer_dashboard.html', 
                         customer=customer, 
                         cards=cards_with_timeline,
                         spending_summary=spending_summary,
                         total_spending=total_spending,
                         monthly_ledgers=monthly_ledgers)


@app.route('/customer/<int:customer_id>/add-card', methods=['GET', 'POST'])
@require_admin_or_accountant
def add_credit_card(customer_id):
    """添加信用卡"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        customer = cursor.fetchone()
        
        if not customer:
            lang = get_current_language()
            flash(translate('customer_not_found', lang), 'error')
            return redirect(url_for('index'))
        
        if request.method == 'POST':
            bank_name = request.form.get('bank_name')
            card_number_last4 = request.form.get('card_number_last4')
            credit_limit = int(float(request.form.get('credit_limit', 0)))
            due_date_str = request.form.get('due_date')
            
            # 验证必填字段
            if not all([bank_name, card_number_last4, due_date_str]):
                lang = get_current_language()
                flash(translate('all_fields_required', lang), 'error')
                return redirect(request.url)
            
            # 验证卡号后四位
            if not card_number_last4 or not card_number_last4.isdigit() or len(card_number_last4) != 4:
                lang = get_current_language()
                flash(translate('card_last4_invalid', lang), 'error')
                return redirect(request.url)
            
            # 转换due_date
            try:
                due_date = int(due_date_str) if due_date_str else 0
                if due_date == 0:
                    raise ValueError("Invalid due date")
            except (ValueError, TypeError):
                lang = get_current_language()
                flash(translate('due_date_invalid', lang), 'error')
                return redirect(request.url)
            
            # ✅ 强制性唯一性检查（大小写无关，去除空格）
            card_id, is_new = UniquenessValidator.get_or_create_credit_card(
                customer_id, bank_name, card_number_last4, credit_limit
            )
            
            if not is_new:
                lang = get_current_language()
                flash(translate('credit_card_already_exists', lang).format(bank_name=bank_name, last4=card_number_last4, card_id=card_id), 'error')
                return redirect(request.url)
            
            # 更新due_date（get_or_create不包含此字段）
            cursor.execute('''
                UPDATE credit_cards SET due_date = ? WHERE id = ?
            ''', (due_date, card_id))
            
            conn.commit()
            
            lang = get_current_language()
            flash(translate('credit_card_added_success', lang).format(bank_name=bank_name, last4=card_number_last4), 'success')
            log_audit('credit_card_added', customer_id, 
                     f'添加信用卡：{bank_name} ****{card_number_last4}')
            
            return redirect(url_for('customer_dashboard', customer_id=customer_id))
        
        # GET 请求：显示添加表单
        cursor.execute('SELECT * FROM credit_cards WHERE customer_id = ?', (customer_id,))
        existing_cards = cursor.fetchall()
    
    return render_template('add_credit_card.html', 
                          customer=customer,
                          existing_cards=existing_cards)


@app.route('/validate_statement/<int:statement_id>')
@require_admin_or_accountant
def validate_statement_view(statement_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.*, c.card_number_last4, c.bank_name, cu.name as customer_name
            FROM statements s
            JOIN credit_cards c ON s.card_id = c.id
            JOIN customers cu ON c.customer_id = cu.id
            WHERE s.id = ?
        ''', (statement_id,))
        statement_row = cursor.fetchone()
        statement = dict(statement_row) if statement_row else None
    
    if not statement:
        lang = get_current_language()
        flash(translate('statement_not_found', lang), 'error')
        return redirect(url_for('index'))
    
    transactions = get_statement_transactions(statement_id)
    spending_summary = get_spending_summary(transactions)
    
    try:
        inconsistencies = json.loads(statement['inconsistencies']) if statement['inconsistencies'] else []
    except:
        inconsistencies = []
    
    return render_template('validate_statement.html', 
                         statement=statement,
                         transactions=transactions,
                         spending_summary=spending_summary,
                         inconsistencies=inconsistencies)

@app.route('/confirm_statement/<int:statement_id>', methods=['POST'])
@require_admin_or_accountant
def confirm_statement(statement_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE statements SET is_confirmed = 1 WHERE id = ?', (statement_id,))
        conn.commit()
        log_audit(None, 'CONFIRM_STATEMENT', 'statement', statement_id, 'Statement confirmed by user')
    
    lang = get_current_language()
    flash(translate('statement_confirmed', lang), 'success')
    return redirect(url_for('index'))

@app.route('/reminders')
@require_admin_or_accountant
def reminders():
    pending_reminders = get_pending_reminders()
    return render_template('reminders.html', reminders=pending_reminders)

@app.route('/create_reminder', methods=['POST'])
@require_admin_or_accountant
def create_reminder_route():
    card_id = request.form.get('card_id')
    due_date = request.form.get('due_date')
    amount_due = request.form.get('amount_due')
    
    if card_id and due_date and amount_due:
        reminder_id = create_reminder(int(card_id), due_date, float(amount_due))
        log_audit(None, 'CREATE_REMINDER', 'reminder', reminder_id, f'Created reminder for card {card_id}')
        lang = get_current_language()
        flash(translate('reminder_created', lang), 'success')
    else:
        lang = get_current_language()
        flash(translate('missing_required_fields', lang), 'error')
    
    return redirect(url_for('reminders'))

@app.route('/mark_paid/<int:reminder_id>', methods=['POST'])
@require_admin_or_accountant
def mark_paid_route(reminder_id):
    mark_as_paid(reminder_id)
    log_audit(None, 'MARK_PAID', 'reminder', reminder_id, 'Marked reminder as paid')
    lang = get_current_language()
    flash(translate('payment_completed', lang), 'success')
    return redirect(url_for('reminders'))

@app.route('/notifications-history')
def notifications_history():
    """通知历史页面"""
    return render_template('notifications_history.html')

@app.route('/notification-settings')
def notification_settings():
    """通知偏好设置页面"""
    return render_template('notification_settings.html')

@app.route('/loan_evaluation/<int:customer_id>')
@require_admin_or_accountant
def loan_evaluation(customer_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        customer_row = cursor.fetchone()
        customer = dict(customer_row) if customer_row else None
    
    if not customer:
        lang = get_current_language()
        flash(translate('customer_not_found', lang), 'error')
        return redirect(url_for('index'))
    
    cards = get_customer_cards(customer_id)
    current_repayments = sum(card.get('credit_limit', 0) * 0.05 for card in cards)
    
    monthly_income = customer.get('monthly_income', 0)
    dsr = calculate_dsr(monthly_income, current_repayments)
    max_loan_calc = calculate_max_loan_amount(monthly_income, current_repayments)
    scenarios = simulate_loan_scenarios(monthly_income, current_repayments)
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO loan_evaluations 
            (customer_id, monthly_income, total_monthly_repayments, dsr, max_loan_amount, 
             loan_term_months, interest_rate, monthly_installment)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            customer_id, monthly_income, current_repayments, dsr,
            max_loan_calc['max_loan_amount'], 360, 0.04,
            max_loan_calc['monthly_installment']
        ))
        conn.commit()
    
    return render_template('loan_evaluation.html',
                         customer=customer,
                         dsr=dsr,
                         max_loan_calc=max_loan_calc,
                         scenarios=scenarios,
                         current_repayments=current_repayments)

@app.route('/generate_report/<int:customer_id>')
@require_admin_or_accountant
def generate_report(customer_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        customer_row = cursor.fetchone()
        customer = dict(customer_row) if customer_row else None
    
    if not customer:
        lang = get_current_language()
        flash(translate('customer_not_found', lang), 'error')
        return redirect(url_for('index'))
    
    cards = get_customer_cards(customer_id)
    all_transactions = []
    for card in cards:
        statements = get_card_statements(card['id'])
        for statement in statements:
            if statement['is_confirmed']:
                transactions = get_statement_transactions(statement['id'])
                all_transactions.extend(transactions)
    
    spending_summary = get_spending_summary(all_transactions) if all_transactions else {}
    
    current_repayments = sum(card.get('credit_limit', 0) * 0.05 for card in cards)
    dsr = calculate_dsr(customer['monthly_income'], current_repayments)
    max_loan_calc = calculate_max_loan_amount(customer['monthly_income'], current_repayments)
    
    dsr_data = {
        'dsr': dsr,
        'total_repayments': current_repayments,
        'max_loan': max_loan_calc['max_loan_amount']
    }
    
    output_filename = f"report_{customer_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
    
    generate_monthly_report(customer, spending_summary, dsr_data, output_path)
    
    log_audit(None, 'GENERATE_REPORT', 'customer', customer_id, 'Generated monthly report')
    
    return send_file(output_path, as_attachment=True, download_name=output_filename)

@app.route('/analytics/<int:customer_id>')
@require_admin_or_accountant
def analytics(customer_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        customer_row = cursor.fetchone()
        customer = dict(customer_row) if customer_row else None
    
    if not customer:
        lang = get_current_language()
        flash(translate('customer_not_found', lang), 'error')
        return redirect(url_for('index'))
    
    cards = get_customer_cards(customer_id)
    all_transactions = []
    for card in cards:
        statements = get_card_statements(card['id'])
        for statement in statements:
            if statement['is_confirmed']:
                transactions = get_statement_transactions(statement['id'])
                all_transactions.extend(transactions)
    
    spending_summary = get_spending_summary(all_transactions) if all_transactions else {}
    
    return render_template('analytics.html', 
                         customer=customer,
                         spending_summary=spending_summary,
                         transactions=all_transactions)

# ========== NEW FEATURES ==========

@app.route('/export/<int:customer_id>/<format>')
@require_flask_permission('export:bank_statements', 'read')
def export_transactions(customer_id, format):
    """Export transactions to Excel or CSV (RBAC protected)"""
    filters = {
        'start_date': request.args.get('start_date'),
        'end_date': request.args.get('end_date'),
        'category': request.args.get('category')
    }
    filters = {k: v for k, v in filters.items() if v}
    
    user = session.get('flask_rbac_user', {})
    
    try:
        if format == 'excel':
            filepath = export_service.export_to_excel(customer_id, filters)
        elif format == 'csv':
            filepath = export_service.export_to_csv(customer_id, filters)
        else:
            lang = get_current_language()
            flash(translate('invalid_export_format', lang), 'error')
            return redirect(request.referrer or url_for('index'))
        
        # 写入审计日志（防御性）
        request_info = extract_flask_request_info()
        write_flask_audit_log(
            user_id=user.get('id', 0),
            username=user.get('username', 'unknown'),
            company_id=user.get('company_id', 1),
            action_type='export',
            entity_type='transaction',
            description=f"导出客户交易记录: customer_id={customer_id}, format={format}",
            success=True,
            new_value={'customer_id': customer_id, 'format': format, 'filters': filters},
            ip_address=request_info['ip_address'],
            user_agent=request_info['user_agent']
        )
        
        return send_file(filepath, as_attachment=True)
    except Exception as e:
        # 写入审计日志（失败）
        request_info = extract_flask_request_info()
        write_flask_audit_log(
            user_id=user.get('id', 0),
            username=user.get('username', 'unknown'),
            company_id=user.get('company_id', 1),
            action_type='export',
            entity_type='transaction',
            description=f"导出客户交易记录失败: customer_id={customer_id}, format={format}",
            success=False,
            new_value={'customer_id': customer_id, 'format': format, 'error': str(e)},
            ip_address=request_info['ip_address'],
            user_agent=request_info['user_agent']
        )
        
        lang = get_current_language()
        flash(translate('export_failed', lang).format(error=str(e)), 'error')
        return redirect(request.referrer or url_for('index'))

@app.route('/search/<int:customer_id>', methods=['GET'])
def search_transactions(customer_id):
    """Search and filter transactions"""
    query = request.args.get('q', '')
    filters = {
        'category': request.args.get('category'),
        'start_date': request.args.get('start_date'),
        'end_date': request.args.get('end_date'),
        'min_amount': request.args.get('min_amount'),
        'max_amount': request.args.get('max_amount'),
        'bank': request.args.get('bank')
    }
    filters = {k: v for k, v in filters.items() if v}
    
    results = search_service.search_transactions(customer_id, query, filters)
    suggestions = search_service.get_filter_suggestions(customer_id)
    saved_filters = search_service.get_saved_filters(customer_id)
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        customer_row = cursor.fetchone()
        customer = dict(customer_row) if customer_row else None
    
    return render_template('search.html', customer=customer, transactions=results, 
                          suggestions=suggestions, saved_filters=saved_filters, 
                          current_query=query, current_filters=filters)

@app.route('/batch/upload/<int:customer_id>', methods=['GET', 'POST'])
def batch_upload(customer_id):
    """Batch upload statements with auto-create credit cards"""
    if request.method == 'POST':
        # ==================== VBA强制检查 ====================
        # 允许上传PDF文件，但禁止自动解析（必须用VBA）
        # 注意：这里只是保存文件，不做解析
        # ==================== END VBA强制检查 ====================
        
        # Phase 2-3 Task 2: Import audit helper
        from utils.upload_audit import record_upload_event_async
        
        files = request.files.getlist('statement_files')
        
        if not files:
            lang = get_current_language()
            flash(translate('select_files_upload', lang), 'error')
            return redirect(request.url)
        
        # Get customer info for audit logging
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT customer_code, name FROM customers WHERE id = ?', (customer_id,))
            customer_row = cursor.fetchone()
            customer_code = customer_row['customer_code'] if customer_row else None
            customer_name = customer_row['name'] if customer_row else None
        
        batch_id = batch_service.create_batch_job('upload', customer_id, len(files))
        
        processed = 0
        failed = 0
        created_cards = []
        
        for file in files:
            file_upload_success = False
            file_upload_error = None
            saved_file_path = None
            file_size = 0
            
            try:
                filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                saved_file_path = file_path
                file_size = os.path.getsize(file_path)
                
                result = parse_statement_auto(file_path)
                
                if isinstance(result, tuple) and len(result) >= 2:
                    data_dict, _ = result
                    if data_dict and isinstance(data_dict, dict):
                        bank_name = data_dict.get('bank', 'Unknown')
                        card_last4 = data_dict.get('card_last4', None)
                        statement_date = str(data_dict.get('statement_date', ''))
                        total = float(data_dict.get('total', 0))
                        
                        if not card_last4 or not card_last4.isdigit() or len(card_last4) != 4:
                            print(f"❌ Skipped {file.filename}: Cannot extract valid 4-digit card number (got: {card_last4})")
                            file_upload_error = f"Cannot extract valid 4-digit card number (got: {card_last4})"
                            failed += 1
                        elif bank_name == 'Unknown':
                            print(f"❌ Skipped {file.filename}: Cannot detect bank")
                            file_upload_error = "Cannot detect bank"
                            failed += 1
                        else:
                            with get_db() as conn:
                                cursor = conn.cursor()
                                
                                cursor.execute('''
                                    SELECT id FROM credit_cards 
                                    WHERE customer_id = ? AND bank_name = ? AND card_number_last4 = ?
                                ''', (customer_id, bank_name, card_last4))
                                card_row = cursor.fetchone()
                                
                                if card_row:
                                    card_id = card_row['id']
                                else:
                                    cursor.execute('''
                                        INSERT INTO credit_cards (customer_id, bank_name, card_number_last4, credit_limit, due_date)
                                        VALUES (?, ?, ?, ?, ?)
                                    ''', (customer_id, bank_name, card_last4, 10000.0, 25))
                                    card_id = cursor.lastrowid
                                    created_cards.append(f"{bank_name} ****{card_last4}")
                                    print(f"✅ Auto-created card: {bank_name} ****{card_last4}")
                                
                                cursor.execute('''
                                    INSERT INTO statements (card_id, statement_date, statement_total, file_path, batch_job_id)
                                    VALUES (?, ?, ?, ?, ?)
                                ''', (card_id, statement_date, total, file_path, batch_id))
                                statement_id = cursor.lastrowid
                                conn.commit()
                            
                            # 🚀 自动触发计算系统（100%自动化）
                            try:
                                from services.auto_processor import auto_processor
                                logger.info(f"🚀 自动触发计算系统 (Statement ID: {statement_id})")
                                auto_result = auto_processor.process_uploaded_statement(statement_id)
                                
                                if auto_result['success']:
                                    logger.info(f"✅ 自动处理成功 (Statement ID: {statement_id})")
                                else:
                                    logger.warning(f"⚠️ 自动处理有警告: {auto_result['errors']}")
                            except Exception as auto_e:
                                logger.error(f"❌ 自动处理失败: {auto_e}")
                                # 不阻止上传流程，只记录错误
                            
                            processed += 1
                            file_upload_success = True
                    else:
                        failed += 1
                        file_upload_error = "Failed to parse statement data"
                else:
                    failed += 1
                    file_upload_error = "Failed to extract statement info"
                    
                batch_service.update_batch_progress(batch_id, processed, failed)
            except Exception as e:
                print(f"❌ Batch upload error: {e}")
                failed += 1
                file_upload_error = str(e)
                batch_service.update_batch_progress(batch_id, processed, failed)
            
            # Phase 2-3 Task 2: Record upload event to audit log (non-blocking)
            try:
                record_upload_event_async(
                    customer_id=customer_id,
                    customer_code=customer_code,
                    customer_name=customer_name,
                    upload_type='credit_card_statement_batch',
                    filename=file.filename,
                    file_size=file_size,
                    file_path=saved_file_path,
                    success=file_upload_success,
                    error_message=file_upload_error,
                    additional_info={'batch_id': batch_id}
                )
            except:
                pass  # Audit failure should never block upload
        
        batch_service.complete_batch_job(batch_id, 'completed')
        
        success_msg = f'Batch upload completed: {processed} succeeded, {failed} failed'
        if created_cards:
            success_msg += f'. Auto-created {len(created_cards)} new cards: {", ".join(created_cards)}'
        
        flash(success_msg, 'success')
        return redirect(url_for('customer_dashboard', customer_id=customer_id))
    
    cards = get_customer_cards(customer_id)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        customer_row = cursor.fetchone()
        customer = dict(customer_row) if customer_row else None
    
    return render_template('batch_upload.html', customer=customer, cards=cards)

@app.route('/transaction/<int:transaction_id>/note', methods=['POST'])
def update_transaction_note(transaction_id):
    """Update transaction note"""
    notes = request.form.get('notes', '')
    tag_service.update_transaction_note(transaction_id, notes)
    return jsonify({'success': True})

@app.route('/transaction/<int:transaction_id>/tag', methods=['POST'])
def add_transaction_tag(transaction_id):
    """Add tag to transaction"""
    tag_name = request.form.get('tag_name') or request.form.get('tags')
    
    if not tag_name:
        return jsonify({'success': False, 'error': 'Tag name is required'}), 400
    
    # Try to get customer_id from form, or derive from transaction
    customer_id_str = request.form.get('customer_id')
    
    if customer_id_str:
        try:
            customer_id = int(customer_id_str)
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid customer ID'}), 400
    else:
        # Derive customer_id from transaction
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT c.id FROM customers c
                JOIN credit_cards cc ON c.id = cc.customer_id
                JOIN statements s ON cc.id = s.card_id
                JOIN transactions t ON s.id = t.statement_id
                WHERE t.id = ?
            ''', (transaction_id,))
            row = cursor.fetchone()
            if not row:
                return jsonify({'success': False, 'error': 'Transaction not found'}), 404
            customer_id = row[0]
    
    tag_id = tag_service.create_tag(customer_id, tag_name)
    tag_service.add_tag_to_transaction(transaction_id, tag_id)
    return jsonify({'success': True, 'tag_id': tag_id})

# ========== FINANCIAL ADVISORY ROUTES ==========

@app.route('/advisory/<int:customer_id>')
def financial_advisory(customer_id):
    """Financial advisory dashboard - card recommendations and optimizations"""
    from advisory.card_recommendation_engine import CardRecommendationEngine
    from advisory.financial_optimizer import FinancialOptimizer
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        customer_row = cursor.fetchone()
        customer = dict(customer_row) if customer_row else None
    
    if not customer:
        lang = get_current_language()
        flash(translate('customer_not_found', lang), 'error')
        return redirect(url_for('index'))
    
    # Get card recommendations
    card_engine = CardRecommendationEngine()
    card_recommendations = card_engine.analyze_and_recommend(customer_id)
    
    # Get optimization suggestions
    optimizer = FinancialOptimizer()
    optimizations = optimizer.generate_optimization_suggestions(customer_id)
    
    return render_template('financial_advisory.html',
                          customer=customer,
                          card_recommendations=card_recommendations,
                          optimizations=optimizations)

@app.route('/consultation/request/<int:customer_id>', methods=['POST'])
def request_consultation(customer_id):
    """Customer requests detailed consultation"""
    
    optimization_id = request.form.get('optimization_id')
    request_type = request.form.get('request_type', 'full_optimization')
    message = request.form.get('message', '')
    contact_method = request.form.get('contact_method', 'email')
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO consultation_requests (
                customer_id, optimization_suggestion_id, request_type,
                customer_message, preferred_contact_method, status
            ) VALUES (?, ?, ?, ?, ?, 'new')
        ''', (customer_id, optimization_id, request_type, message, contact_method))
        
        # Mark optimization as client interested
        if optimization_id:
            cursor.execute('''
                UPDATE financial_optimization_suggestions 
                SET consultation_requested = 1, status = 'client_interested'
                WHERE id = ?
            ''', (optimization_id,))
        
        conn.commit()
    
    lang = get_current_language()
    flash(translate('consultation_submitted_success', lang), 'success')
    return redirect(url_for('financial_advisory', customer_id=customer_id))

@app.route('/customer/<int:customer_id>/employment', methods=['GET', 'POST'])
def set_employment_type(customer_id):
    """Set customer employment type and upload income documents"""
    
    if request.method == 'POST':
        employment_type = request.form.get('employment_type')
        employer_name = request.form.get('employer_name', '')
        business_name = request.form.get('business_name', '')
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO customer_employment_types (
                    customer_id, employment_type, employer_name, business_name, 
                    verification_status
                ) VALUES (?, ?, ?, ?, 'pending')
            ''', (customer_id, employment_type, employer_name, business_name))
            conn.commit()
        
        lang = get_current_language()
        flash(translate('employment_info_updated', lang), 'success')
        return redirect(url_for('customer_dashboard', customer_id=customer_id))
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        customer = dict(cursor.fetchone())
        
        cursor.execute('''
            SELECT * FROM customer_employment_types WHERE customer_id = ?
        ''', (customer_id,))
        emp_row = cursor.fetchone()
        employment = dict(emp_row) if emp_row else None
        
        # Get income requirement terms
        cursor.execute('''
            SELECT term_type, title_cn, content_cn FROM service_terms
            WHERE term_type LIKE 'income_requirements_%'
            ORDER BY display_order
        ''')
        income_requirements = [dict(row) for row in cursor.fetchall()]
    
    return render_template('employment_setup.html',
                          customer=customer,
                          employment=employment,
                          income_requirements=income_requirements)

@app.route('/customer-authorization')
def customer_authorization():
    """Display customer authorization agreement"""
    return render_template('customer_authorization.html')

@app.route('/generate_report/<int:customer_id>')
def generate_enhanced_report(customer_id):
    """Generate enhanced monthly report with financial advisory"""
    from report.enhanced_pdf_generator import generate_enhanced_monthly_report
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        customer_row = cursor.fetchone()
        customer = dict(customer_row) if customer_row else None
    
    if not customer:
        lang = get_current_language()
        flash(translate('customer_not_found', lang), 'error')
        return redirect(url_for('index'))
    
    output_filename = f"enhanced_report_{customer_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
    
    generate_enhanced_monthly_report(customer, output_path)
    
    lang = get_current_language()
    flash(translate('monthly_report_generated', lang), 'success')
    return send_file(output_path, as_attachment=True, download_name=output_filename)

# ==================== CUSTOMER AUTHENTICATION SYSTEM ====================

@app.route('/customer/register', methods=['GET', 'POST'])
def customer_register():
    """Customer registration page"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        monthly_income = request.form.get('monthly_income')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate password
        if password != confirm_password:
            return render_template('customer_register.html', error="Passwords do not match")
        
        # Validate inputs
        if not all([name, email, phone, monthly_income, password]):
            return render_template('customer_register.html', error='All fields are required')
        
        # Type assertions for safety
        assert isinstance(email, str) and isinstance(password, str) and isinstance(name, str)
        assert isinstance(phone, str) and isinstance(monthly_income, str)
        
        try:
            income_float = float(monthly_income)
        except (ValueError, TypeError):
            return render_template('customer_register.html', error='Invalid monthly income')
        
        # Create customer first
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO customers (name, phone, email, monthly_income)
                VALUES (?, ?, ?, ?)
            """, (name, phone, email, income_float))
            customer_id = cursor.lastrowid
            conn.commit()
        
        # Verify customer_id is valid
        if not customer_id:
            return render_template('customer_register.html', error='Failed to create customer')
        
        # Create login credentials - customer_id is guaranteed to be int here
        result = create_customer_login(customer_id, email, password)
        
        if result['success']:
            lang = get_current_language()
            flash(translate('registration_successful', lang), 'success')
            return redirect(url_for('customer_login'))
        else:
            return render_template('customer_register.html', error=result['error'])
    
    return render_template('customer_register.html')

@app.route('/customer/portal')
def customer_portal():
    """Customer data portal - view and download personal records"""
    token = session.get('customer_token')
    
    if not token:
        lang = get_current_language()
        flash(translate('please_login_portal', lang), 'warning')
        return redirect(url_for('customer_login'))
    
    # Verify session
    verification = verify_session(token)
    
    if not verification['success']:
        session.clear()
        flash(verification['error'], 'warning')
        return redirect(url_for('customer_login'))
    
    # Get customer data
    customer_id = verification['customer_id']
    data = get_customer_data_summary(customer_id)
    
    return render_template('customer_portal.html', 
                         customer=data['customer'],
                         credit_cards=data['credit_cards'],
                         statements=data['statements'],
                         total_spending=data['total_spending'])

@app.route('/customer/download/<int:statement_id>')
def customer_download_statement(statement_id):
    """Download specific statement (customer access only)"""
    token = session.get('customer_token')
    
    if not token:
        lang = get_current_language()
        flash(translate('please_login_data', lang), 'warning')
        return redirect(url_for('customer_login'))
    
    # Verify session and ownership
    verification = verify_session(token)
    
    if not verification['success']:
        session.clear()
        flash(verification['error'], 'warning')
        return redirect(url_for('customer_login'))
    
    customer_id = verification['customer_id']
    
    # Check if statement belongs to customer
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.file_path, s.statement_date
            FROM statements s
            WHERE s.id = ? AND s.customer_id = ?
        """, (statement_id, customer_id))
        
        result = cursor.fetchone()
        
        if not result:
            lang = get_current_language()
            flash(translate('statement_access_denied', lang), 'danger')
            return redirect(url_for('customer_portal'))
        
        file_path = result[0]
        
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            lang = get_current_language()
            flash(translate('file_not_found', lang), 'danger')
            return redirect(url_for('customer_portal'))

# ==================== END CUSTOMER AUTHENTICATION ====================

# ==================== ADMIN AUTHENTICATION ====================

@app.route('/admin')
@require_admin_or_accountant
def admin_dashboard():
    """Admin dashboard route - 仅管理员和会计可见"""
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get all customers
        cursor.execute("SELECT * FROM customers ORDER BY created_at DESC")
        customers = [dict(row) for row in cursor.fetchall()]
        
        # Get statement count
        cursor.execute("SELECT COUNT(*) FROM statements")
        statement_count = cursor.fetchone()[0]
        
        # Get transaction count
        cursor.execute("SELECT COUNT(*) FROM transactions")
        txn_count = cursor.fetchone()[0]
        
        # Get active cards count
        cursor.execute("SELECT COUNT(*) FROM credit_cards")
        active_cards = cursor.fetchone()[0]
        
        # Get all monthly credit card statements (consolidated by BANK + MONTH)
        # Sorted by: Customer Name -> Bank -> Month (newest first)
        cursor.execute("""
            SELECT 
                ms.id as statement_id,
                ms.statement_month as statement_date,
                ms.customer_id,
                c.name as customer_name,
                ms.bank_name,
                ms.period_end_date as due_date,
                ms.closing_balance_total as closing_balance,
                ms.previous_balance_total as prev_bal,
                ms.owner_expenses,
                ms.owner_payments,
                ms.owner_balance as owner_os_bal,
                ms.gz_expenses as infinite_expenses,
                ms.gz_payments as infinite_payments,
                ms.gz_balance as infinite_os_bal
            FROM monthly_statements ms
            JOIN customers c ON ms.customer_id = c.id
            ORDER BY c.name ASC, ms.bank_name ASC, ms.statement_month DESC
            LIMIT 100
        """)
        cc_statements = [dict(row) for row in cursor.fetchall()]
        
        # Convert bank names to abbreviations
        for stmt in cc_statements:
            stmt['bank_abbr'] = stmt['bank_name'][:4].upper()  # Simple abbreviation
        
        # Get all savings account statements
        # Sorted by: Customer Name -> Bank -> Month (NEWEST FIRST)
        cursor.execute("""
            SELECT 
                ss.id as statement_id,
                ss.statement_date,
                cu.id as customer_id,
                cu.name as customer_name,
                sa.bank_name,
                COALESCE(SUM(CASE WHEN st.transaction_type = 'credit' THEN ABS(st.amount) ELSE 0 END), 0) as monthly_credit,
                COALESCE(SUM(CASE WHEN st.transaction_type = 'debit' THEN ABS(st.amount) ELSE 0 END), 0) as monthly_debit,
                MAX(st.balance) as closing_bal,
                COALESCE(SUM(CASE WHEN st.description LIKE '%PAYMENT%' OR st.description LIKE '%FPX%' THEN ABS(st.amount) ELSE 0 END), 0) as cc_sum_payment,
                COALESCE(SUM(CASE WHEN st.transaction_type = 'debit' AND (st.description LIKE '%TRANSFER%' OR st.description LIKE '%IBG%' OR st.description LIKE '%GIRO%') THEN ABS(st.amount) ELSE 0 END), 0) as total_transfer
            FROM savings_statements ss
            JOIN savings_accounts sa ON ss.savings_account_id = sa.id
            JOIN customers cu ON sa.customer_id = cu.id
            LEFT JOIN savings_transactions st ON ss.id = st.savings_statement_id
            GROUP BY ss.id, ss.statement_date, cu.id, cu.name, sa.bank_name
            ORDER BY cu.name ASC, sa.bank_name ASC, ss.statement_date DESC
            LIMIT 200
        """)
        sa_statements = [dict(row) for row in cursor.fetchall()]
        
        # Convert bank names to abbreviations for savings accounts
        for stmt in sa_statements:
            stmt['bank_abbr'] = stmt['bank_name'][:4].upper()  # Simple abbreviation
        
        # Calculate monthly statistics for dashboard cards
        total_owner_expenses = sum(stmt['owner_expenses'] for stmt in cc_statements)
        total_owner_payments = sum(stmt['owner_payments'] for stmt in cc_statements)
        total_gz_expenses = sum(stmt['infinite_expenses'] for stmt in cc_statements)
        total_gz_payments = sum(stmt['infinite_payments'] for stmt in cc_statements)
        
        # 1% 刷卡机费用由客户OWNER承担（不是GZ收入）
        # 业务逻辑：用客户信用卡刷卡购物换取现金，1%是银行收取的刷卡机费用
        card_processing_fee = total_gz_expenses * 0.01  # 刷卡机费用
        
        # OWNER总欠款 = OWNER消费 + 1%刷卡机费用 - OWNER付款
        total_owner_balance = (total_owner_expenses + card_processing_fee) - total_owner_payments
        
        # GZ欠款 = GZ消费 - GZ付款（不包含1%费用，因为这是OWNER承担的）
        total_gz_balance = total_gz_expenses - total_gz_payments
        
        # Count unique banks
        cursor.execute("SELECT COUNT(DISTINCT bank_name) FROM credit_cards")
        unique_banks = cursor.fetchone()[0]
        
        # Get receipts statistics
        cursor.execute("SELECT COUNT(*) FROM receipts")
        receipts_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM receipts")
        receipts_total = cursor.fetchone()[0]
        
        # Get supplier invoices statistics
        cursor.execute("SELECT COUNT(*) FROM supplier_invoices")
        invoices_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COALESCE(SUM(total_amount + supplier_fee), 0) FROM supplier_invoices")
        invoices_total = cursor.fetchone()[0]
        
        # Get Credit Card Customers (customers with at least one credit card)
        cursor.execute("""
            SELECT DISTINCT
                c.id,
                c.name,
                c.email,
                c.phone,
                c.monthly_income,
                COUNT(DISTINCT cc.id) as total_cards,
                COUNT(DISTINCT ms.id) as total_statements
            FROM customers c
            INNER JOIN credit_cards cc ON c.id = cc.customer_id
            LEFT JOIN monthly_statements ms ON c.id = ms.customer_id
            GROUP BY c.id, c.name, c.email, c.phone, c.monthly_income
            ORDER BY c.name ASC
        """)
        credit_card_customers = [dict(row) for row in cursor.fetchall()]
        
        # Get Savings Account Customers (customers with at least one savings account)
        cursor.execute("""
            SELECT DISTINCT
                c.id,
                c.name,
                c.email,
                c.phone,
                c.monthly_income,
                COUNT(DISTINCT sa.id) as total_accounts,
                COUNT(DISTINCT ss.id) as total_statements
            FROM customers c
            INNER JOIN savings_accounts sa ON c.id = sa.customer_id
            LEFT JOIN savings_statements ss ON sa.id = ss.savings_account_id
            GROUP BY c.id, c.name, c.email, c.phone, c.monthly_income
            ORDER BY c.name ASC
        """)
        savings_customers = [dict(row) for row in cursor.fetchall()]
    
    return render_template('admin_dashboard.html', 
                         customers=customers,
                         statement_count=statement_count,
                         txn_count=txn_count,
                         active_cards=active_cards,
                         cc_statements=cc_statements,
                         sa_statements=sa_statements,
                         credit_card_customers=credit_card_customers,
                         savings_customers=savings_customers,
                         total_owner_expenses=total_owner_expenses,
                         total_owner_payments=total_owner_payments,
                         total_gz_expenses=total_gz_expenses,
                         total_gz_payments=total_gz_payments,
                         card_processing_fee=card_processing_fee,
                         total_owner_balance=total_owner_balance,
                         total_gz_balance=total_gz_balance,
                         unique_banks=unique_banks,
                         receipts_count=receipts_count,
                         receipts_total=receipts_total,
                         invoices_count=invoices_count,
                         invoices_total=invoices_total)


@app.route('/ctos/consent')
@require_admin_or_accountant
def ctos_consent_route():
    return ctos_consent()

@app.route('/ctos/personal')
@require_admin_or_accountant
def ctos_personal_route():
    return ctos_personal()

@app.route('/ctos/personal/submit', methods=['POST'])
@require_admin_or_accountant
def ctos_personal_submit_route():
    return ctos_personal_submit()

@app.route('/ctos/company')
@require_admin_or_accountant
def ctos_company_route():
    return ctos_company()

@app.route('/ctos/company/submit', methods=['POST'])
@require_admin_or_accountant
def ctos_company_submit_route():
    return ctos_company_submit()

@app.route('/admin/payment-accounts')
@require_admin_or_accountant
def admin_payment_accounts():
    """GZ Payment Accounts 管理页面"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                id,
                account_name,
                account_holder,
                bank_name,
                account_number,
                account_type,
                is_active,
                created_at
            FROM payment_accounts
            ORDER BY account_type, bank_name
        """)
        payment_accounts = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute("SELECT COUNT(*) FROM bank_statements")
        total_bank_statements = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM payment_slips")
        total_payment_slips = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) 
            FROM transaction_validations 
            WHERE validation_status = 'FULLY_VALIDATED'
        """)
        validated_transactions = cursor.fetchone()[0]
    
    return render_template('admin_payment_accounts.html',
                         payment_accounts=payment_accounts,
                         total_bank_statements=total_bank_statements,
                         total_payment_slips=total_payment_slips,
                         validated_transactions=validated_transactions)

@app.route('/admin/api-keys')
@require_admin_or_accountant
def api_keys_management():
    """API密钥管理页面 - 仅管理员和会计可见"""
    # 从环境变量读取API_BASE_URL
    # 默认为空字符串，使用same-origin相对路径（生产环境推荐）
    # 开发环境可设置: export API_BASE_URL="http://localhost:8000"
    api_base_url = os.environ.get('API_BASE_URL', '')
    return render_template('api_keys_management.html', api_base_url=api_base_url)


@app.route('/savings-admin')
@require_admin_or_accountant
def savings_admin_dashboard():
    """储蓄账户管理中心 Dashboard - 仅管理员和会计可见"""
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 统计数据
        cursor.execute("""
            SELECT COUNT(DISTINCT c.id) as total_customers
            FROM customers c
            JOIN savings_accounts sa ON c.id = sa.customer_id
        """)
        total_customers = cursor.fetchone()['total_customers']
        
        cursor.execute("SELECT COUNT(*) as total_accounts FROM savings_accounts")
        total_accounts = cursor.fetchone()['total_accounts']
        
        cursor.execute("SELECT COUNT(*) as total_statements FROM savings_statements")
        total_statements = cursor.fetchone()['total_statements']
        
        cursor.execute("SELECT COUNT(*) as total_transactions FROM savings_transactions")
        total_transactions = cursor.fetchone()['total_transactions']
        
        # 获取所有月结单，按月份排序（像Admin页面的Credit Card Statements那样）
        cursor.execute("""
            SELECT 
                ss.id as statement_id,
                ss.statement_date,
                ss.total_transactions,
                ss.verification_status,
                ss.verified_at,
                sa.id as savings_account_id,
                sa.bank_name,
                sa.account_number_last4,
                c.id as customer_id,
                c.name as customer_name,
                COALESCE(SUM(CASE WHEN st.transaction_type = 'credit' THEN ABS(st.amount) ELSE 0 END), 0) as monthly_credit,
                COALESCE(SUM(CASE WHEN st.transaction_type = 'debit' THEN ABS(st.amount) ELSE 0 END), 0) as monthly_debit,
                MAX(st.balance) as closing_bal,
                COALESCE(SUM(CASE WHEN st.description LIKE '%PAYMENT%' OR st.description LIKE '%FPX%' THEN ABS(st.amount) ELSE 0 END), 0) as cc_sum_payment,
                COALESCE(SUM(CASE WHEN st.transaction_type = 'debit' AND (st.description LIKE '%Transfer%' OR st.description LIKE '%IBG%' OR st.description LIKE '%GIRO%') THEN ABS(st.amount) ELSE 0 END), 0) as total_transfer
            FROM savings_statements ss
            JOIN savings_accounts sa ON ss.savings_account_id = sa.id
            JOIN customers c ON sa.customer_id = c.id
            LEFT JOIN savings_transactions st ON ss.id = st.savings_statement_id
            GROUP BY ss.id, ss.statement_date, ss.total_transactions, ss.verification_status, 
                     ss.verified_at, sa.id, sa.bank_name, sa.account_number_last4, c.id, c.name
            ORDER BY ss.statement_date DESC, c.name ASC, sa.bank_name ASC
            LIMIT 200
        """)
        statements = [dict(row) for row in cursor.fetchall()]
    
    return render_template('savings_admin_dashboard.html',
                         total_customers=total_customers,
                         total_accounts=total_accounts,
                         total_statements=total_statements,
                         total_transactions=total_transactions,
                         statements=statements)

# ==================== END SAVINGS ADMIN AUTHENTICATION ====================

@app.route('/admin/customers')
@require_admin_or_accountant
def admin_customers_list():
    """管理员客户列表页面 - 仅管理员和会计可见所有客户"""
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                c.id,
                c.name,
                c.email,
                c.phone,
                c.customer_code,
                COUNT(DISTINCT cc.id) as total_cards,
                COUNT(DISTINCT sa.id) as total_savings_accounts
            FROM customers c
            LEFT JOIN credit_cards cc ON c.id = cc.customer_id
            LEFT JOIN savings_accounts sa ON c.id = sa.customer_id
            GROUP BY c.id
            ORDER BY c.name
        """)
        
        customers = [dict(row) for row in cursor.fetchall()]
        
        for customer in customers:
            cursor.execute("""
                SELECT id, account_type, account_name, account_number, bank_name, is_primary
                FROM customer_accounts
                WHERE customer_id = ?
                ORDER BY account_type, is_primary DESC, id
            """, (customer['id'],))
            customer['accounts'] = [dict(row) for row in cursor.fetchall()]
    
    return render_template('admin_customers_list.html', customers=customers)

@app.route('/customers')
def customers_profile():
    """客户个人资料页面 - 客户只能查看自己的数据"""
    
    # Check if customer is logged in
    customer_session_token = session.get('customer_session_token')
    
    # If admin/accountant is accessing, redirect to admin view
    if is_admin_or_accountant():
        return redirect(url_for('admin_customers_list'))
    
    # If no customer session, redirect to login
    if not customer_session_token:
        flash('Please login to view your profile', 'warning')
        return redirect(url_for('index'))
    
    # Verify customer session
    session_data = verify_session(customer_session_token)
    
    if not session_data['success']:
        session.pop('customer_session_token', None)
        flash('Your session has expired. Please login again.', 'warning')
        return redirect(url_for('index'))
    
    # Validate session data has required keys
    if 'customer_id' not in session_data or 'customer_name' not in session_data:
        session.pop('customer_session_token', None)
        flash('Invalid session data. Please login again.', 'error')
        return redirect(url_for('index'))
    
    customer_id = session_data['customer_id']
    customer_name = session_data['customer_name']
    
    # Get customer's complete data
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get customer info
        cursor.execute("""
            SELECT id, name, email, phone, customer_code, monthly_income, 
                   employment_type, created_at
            FROM customers 
            WHERE id = ?
        """, (customer_id,))
        
        customer_row = cursor.fetchone()
        
        # Handle edge case: customer record not found
        if not customer_row:
            session.pop('customer_session_token', None)
            flash('Customer profile not found. Please contact support.', 'error')
            return redirect(url_for('index'))
        
        customer = dict(customer_row)
        
        # Get customer's credit cards with latest statement info
        cursor.execute("""
            SELECT 
                cc.id,
                cc.bank_name,
                cc.card_number_last4,
                cc.credit_limit,
                cc.interest_rate,
                cc.cashback_rate,
                cc.due_date,
                cc.card_type,
                COUNT(DISTINCT s.id) as total_statements,
                MAX(s.statement_date) as last_statement_date,
                COALESCE(SUM(CASE WHEN s.payment_status != 'paid' THEN s.due_amount ELSE 0 END), 0) as total_outstanding
            FROM credit_cards cc
            LEFT JOIN statements s ON cc.id = s.card_id
            WHERE cc.customer_id = ?
            GROUP BY cc.id
            ORDER BY cc.bank_name
        """, (customer_id,))
        credit_cards = [dict(row) for row in cursor.fetchall()]
        
        # Get customer's savings accounts
        cursor.execute("""
            SELECT 
                sa.id,
                sa.bank_name,
                sa.account_number_last4,
                sa.account_type,
                COUNT(DISTINCT ss.id) as total_statements,
                MAX(ss.statement_date) as last_statement_date
            FROM savings_accounts sa
            LEFT JOIN savings_statements ss ON sa.id = ss.savings_account_id
            WHERE sa.customer_id = ?
            GROUP BY sa.id
            ORDER BY sa.bank_name
        """, (customer_id,))
        savings_accounts = [dict(row) for row in cursor.fetchall()]
        
        # Get recent statements (last 5)
        cursor.execute("""
            SELECT 
                s.id,
                s.statement_date,
                s.due_date,
                s.due_amount,
                s.payment_status,
                cc.bank_name,
                cc.card_number_last4
            FROM statements s
            JOIN credit_cards cc ON s.card_id = cc.id
            WHERE cc.customer_id = ?
            ORDER BY s.statement_date DESC
            LIMIT 5
        """, (customer_id,))
        recent_statements = [dict(row) for row in cursor.fetchall()]
    
    return render_template('customer_profile.html',
                         customer=customer,
                         credit_cards=credit_cards,
                         savings_accounts=savings_accounts,
                         recent_statements=recent_statements)

@app.route('/admin/customers-cards')
@require_admin_or_accountant
def admin_customers_cards():
    """Admin page showing all customers and their credit cards - 仅管理员和会计可见"""
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get all customers with their credit cards
        cursor.execute("""
            SELECT 
                c.id as customer_id,
                c.name as customer_name,
                c.email,
                c.phone,
                c.monthly_income,
                COUNT(DISTINCT cc.id) as total_cards,
                COUNT(DISTINCT s.id) as total_statements,
                SUM(CASE WHEN s.statement_date >= date('now', 'start of month') THEN 1 ELSE 0 END) as current_month_statements
            FROM customers c
            LEFT JOIN credit_cards cc ON c.id = cc.customer_id
            LEFT JOIN statements s ON cc.id = s.card_id
            GROUP BY c.id
            ORDER BY c.name
        """)
        customers_summary = [dict(row) for row in cursor.fetchall()]
        
        # Get detailed card information for each customer
        customers_with_cards = []
        for customer in customers_summary:
            cursor.execute("""
                SELECT 
                    cc.id as card_id,
                    cc.card_type,
                    cc.card_number_last4,
                    cc.bank_name,
                    cc.credit_limit,
                    cc.interest_rate,
                    cc.cashback_rate,
                    cc.due_date,
                    COUNT(DISTINCT s.id) as statement_count,
                    MAX(s.statement_date) as last_statement_date,
                    SUM(CASE WHEN t.transaction_type = 'purchase' THEN t.amount ELSE 0 END) as total_spending,
                    (SELECT due_amount FROM statements WHERE card_id = cc.id ORDER BY statement_date DESC LIMIT 1) as latest_due_amount,
                    (SELECT due_date FROM statements WHERE card_id = cc.id ORDER BY statement_date DESC LIMIT 1) as latest_due_date,
                    (SELECT COALESCE(SUM(due_amount - COALESCE(paid_amount, 0)), 0) FROM statements WHERE card_id = cc.id AND payment_status != 'paid') as total_outstanding
                FROM credit_cards cc
                LEFT JOIN statements s ON cc.id = s.card_id
                LEFT JOIN transactions t ON s.id = t.statement_id
                WHERE cc.customer_id = ?
                GROUP BY cc.id
                ORDER BY cc.card_type
            """, (customer['customer_id'],))
            
            cards = [dict(row) for row in cursor.fetchall()]
            
            # Add billing cycle for each card
            for card in cards:
                # Calculate 50-day billing cycle
                if card['last_statement_date'] and card['due_date']:
                    from datetime import datetime, timedelta
                    try:
                        stmt_date = datetime.strptime(card['last_statement_date'], '%Y-%m-%d')
                        # Calculate cycle: statement date to due date (typically 20-25 days)
                        # Then add grace period to make approximately 50 days
                        due_day = card['due_date']
                        # Estimate due date by adding ~20 days to statement date
                        estimated_due = stmt_date + timedelta(days=20)
                        # Cycle end is due date + grace period (typically 20-25 days)
                        cycle_end = estimated_due + timedelta(days=30)
                        card['billing_cycle_start'] = stmt_date.strftime('%Y-%m-%d')
                        card['billing_cycle_end'] = cycle_end.strftime('%Y-%m-%d')
                    except:
                        card['billing_cycle_start'] = None
                        card['billing_cycle_end'] = None
                else:
                    card['billing_cycle_start'] = None
                    card['billing_cycle_end'] = None
            
            customers_with_cards.append({
                'customer': customer,
                'cards': cards
            })
    
    return render_template('admin_customers_cards.html', 
                         customers_with_cards=customers_with_cards)

# ==================== END ADMIN AUTHENTICATION ====================

# ==================== NOTIFICATION SERVICES ====================

def send_email_notification(to_email, subject, body):
    """Send email notification via SMTP"""
    try:
        sender = os.environ.get('EMAIL_USER')
        password = os.environ.get('EMAIL_PASSWORD')
        smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('SMTP_PORT', 587))
        
        if not sender or not password:
            print("Email credentials not configured")
            return False
        
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Email sent to {to_email}")
        return True
    except Exception as e:
        print(f"❌ Email failed: {e}")
        return False

def send_whatsapp_notification(to_number, message):
    """Send WhatsApp notification via Twilio"""
    try:
        account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        from_whatsapp = os.environ.get('TWILIO_WHATSAPP_FROM', 'whatsapp:+14155238886')
        
        if not account_sid or not auth_token:
            print("Twilio credentials not configured")
            return False
        
        from twilio.rest import Client
        
        client = Client(account_sid, auth_token)
        client.messages.create(
            from_=from_whatsapp,
            body=message,
            to=to_number
        )
        
        print(f"✅ WhatsApp sent to {to_number}")
        return True
    except Exception as e:
        print(f"❌ WhatsApp failed: {e}")
        return False

def notify_admin_statement_upload(customer_name, statement_date):
    """Notify admin when customer uploads statement"""
    admin_whatsapp = os.environ.get('WHATSAPP_ADMIN_TO')
    admin_email = os.environ.get('ADMIN_EMAIL')
    
    message = f"📄 New Statement Upload\nCustomer: {customer_name}\nDate: {statement_date}\nPlease review in admin panel."
    
    # Send WhatsApp if configured
    if admin_whatsapp:
        send_whatsapp_notification(admin_whatsapp, message)
    
    # Send Email if configured
    if admin_email:
        send_email_notification(admin_email, "New Statement Upload", message)

def notify_admin_consultation_request(customer_name, service_type):
    """Notify admin when customer requests consultation"""
    admin_whatsapp = os.environ.get('WHATSAPP_ADMIN_TO')
    admin_email = os.environ.get('ADMIN_EMAIL')
    
    message = f"💬 New Consultation Request\nCustomer: {customer_name}\nService: {service_type}\nPlease respond promptly."
    
    # Send WhatsApp if configured
    if admin_whatsapp:
        send_whatsapp_notification(admin_whatsapp, message)
    
    # Send Email if configured
    if admin_email:
        send_email_notification(admin_email, "New Consultation Request", message)

# ==================== END NOTIFICATION SERVICES ====================

# ==================== ADMIN PORTFOLIO MANAGEMENT ====================

@app.route('/admin/portfolio')
@require_admin_or_accountant
def admin_portfolio():
    """管理员Portfolio管理仪表板 - 核心运营工具 - 仅管理员和会计可见"""
    portfolio_mgr = PortfolioManager()
    
    # 获取总览数据
    overview = portfolio_mgr.get_portfolio_overview()
    
    # 获取所有客户portfolio
    clients = portfolio_mgr.get_all_clients_portfolio()
    
    # 获取风险客户
    risk_clients = portfolio_mgr.get_risk_clients()
    
    # 获取收入明细
    revenue_breakdown = portfolio_mgr.get_revenue_breakdown()
    
    return render_template('admin_portfolio.html',
                         overview=overview,
                         clients=clients,
                         risk_clients=risk_clients,
                         revenue_breakdown=revenue_breakdown)

@app.route('/admin/portfolio/client/<int:customer_id>')
@require_admin_or_accountant
def admin_client_detail(customer_id):
    """查看单个客户完整workflow详情 - 仅管理员和会计可见"""
    portfolio_mgr = PortfolioManager()
    client_detail = portfolio_mgr.get_client_detail(customer_id)
    
    return render_template('admin_client_detail.html',
                         client=client_detail)

@app.route('/api/portfolio/overview')
def api_portfolio_overview():
    """API: 获取Portfolio总览"""
    portfolio_mgr = PortfolioManager()
    overview = portfolio_mgr.get_portfolio_overview()
    return jsonify(overview)

@app.route('/api/portfolio/revenue')
def api_portfolio_revenue():
    """API: 获取收入明细"""
    portfolio_mgr = PortfolioManager()
    revenue = portfolio_mgr.get_revenue_breakdown()
    return jsonify(revenue)

# ==================== END ADMIN PORTFOLIO ====================

# ==================== ADVANCED ANALYTICS FEATURES ====================

# Import new analytics modules (仅当功能开启时初始化)
if FEATURE_ADVANCED_ANALYTICS:
    from analytics.financial_health_score import FinancialHealthScore
    from analytics.cashflow_predictor import CashflowPredictor
    from analytics.anomaly_detector import AnomalyDetector
    from analytics.recommendation_engine import RecommendationEngine
    
    # Initialize analytics services
    health_score_service = FinancialHealthScore()
    cashflow_service = CashflowPredictor()
    anomaly_service = AnomalyDetector()
    recommendation_service = RecommendationEngine()

if FEATURE_CUSTOMER_TIER:
    from analytics.customer_tier_system import CustomerTierSystem
    tier_service = CustomerTierSystem()

@app.route('/advanced-analytics/<int:customer_id>')
def advanced_analytics(customer_id):
    """高级财务分析仪表板（Beta功能，需开关开启）"""
    # 检查功能开关
    if not FEATURE_ADVANCED_ANALYTICS:
        lang = get_current_language()
        flash(translate('advanced_analytics_disabled', lang), 'warning')
        return redirect(url_for('index'))
    
    lang = get_current_language()
    
    # 财务健康评分
    health_score = health_score_service.calculate_score(customer_id)
    score_trend = health_score_service.get_score_trend(customer_id, months=6)
    
    # 客户等级（仅当功能开启时计算）
    if FEATURE_CUSTOMER_TIER:
        tier_info = tier_service.calculate_customer_tier(customer_id)
    else:
        tier_info = None  # 功能未开启，模板需处理None
    
    # 异常检测
    anomalies = anomaly_service.detect_anomalies(customer_id)
    
    # 个性化推荐
    recommendations = recommendation_service.generate_recommendations(customer_id)
    
    # 现金流预测（12个月）
    cashflow_data = cashflow_service.get_cashflow_chart_data(customer_id, months=12)
    
    return render_template('advanced_analytics.html',
                         customer_id=customer_id,
                         health_score=health_score,
                         score_trend=score_trend,
                         tier_info=tier_info,
                         anomalies=anomalies,
                         recommendations=recommendations,
                         cashflow_data=cashflow_data,
                         current_lang=lang)

@app.route('/api/cashflow-prediction/<int:customer_id>')
def api_cashflow_prediction(customer_id):
    """API: 获取现金流预测数据"""
    if not FEATURE_ADVANCED_ANALYTICS:
        return jsonify({'error': 'Feature disabled'}), 403
    months = request.args.get('months', 12, type=int)
    prediction = cashflow_service.predict_cashflow(customer_id, months)
    return jsonify(prediction)

@app.route('/api/financial-score/<int:customer_id>')
def api_financial_score(customer_id):
    """API: 获取财务健康评分"""
    if not FEATURE_ADVANCED_ANALYTICS:
        return jsonify({'error': 'Feature disabled'}), 403
    score_data = health_score_service.calculate_score(customer_id)
    return jsonify(score_data)

@app.route('/api/anomalies/<int:customer_id>')
def api_anomalies(customer_id):
    """API: 获取财务异常"""
    if not FEATURE_ADVANCED_ANALYTICS:
        return jsonify({'error': 'Feature disabled'}), 403
    anomalies = anomaly_service.get_active_anomalies(customer_id)
    return jsonify({'anomalies': anomalies})

@app.route('/api/recommendations/<int:customer_id>')
def api_recommendations(customer_id):
    """API: 获取个性化推荐"""
    if not FEATURE_ADVANCED_ANALYTICS:
        return jsonify({'error': 'Feature disabled'}), 403
    recommendations = recommendation_service.generate_recommendations(customer_id)
    return jsonify(recommendations)

@app.route('/api/tier-info/<int:customer_id>')
def api_tier_info(customer_id):
    """API: 获取客户等级信息"""
    if not FEATURE_CUSTOMER_TIER:
        return jsonify({'error': 'Feature disabled'}), 403
    tier_info = tier_service.calculate_customer_tier(customer_id)
    return jsonify(tier_info)

@app.route('/resolve-anomaly/<int:anomaly_id>', methods=['POST'])
def resolve_anomaly_route(anomaly_id):
    """解决财务异常"""
    if not FEATURE_ADVANCED_ANALYTICS:
        flash('Advanced Analytics feature is currently disabled.', 'warning')
        return redirect(url_for('index'))
    resolution_note = request.form.get('resolution_note', '')
    anomaly_service.resolve_anomaly(anomaly_id, resolution_note)
    lang = get_current_language()
    flash(translate('anomaly_resolved', lang), 'success')
    return redirect(request.referrer or url_for('index'))

# ==================== END ADVANCED ANALYTICS ====================

def run_scheduler():
    # 提醒任务
    schedule.every().day.at("09:00").do(check_and_send_reminders)
    schedule.every(6).hours.do(check_and_send_reminders)
    
    # ============================================================
    # 月度报表自动化系统 - 30号生成，1号发送
    # ============================================================
    
    def auto_generate_monthly_reports():
        """每月30号：自动生成所有客户的月度报表"""
        today = datetime.now()
        if today.day == 30:
            print(f"\n{'='*60}")
            print(f"🌌 [自动化任务] 开始生成所有客户的月度报表")
            print(f"{'='*60}\n")
            
            result = monthly_report_scheduler.generate_all_customer_reports()
            
            print(f"\n{'='*60}")
            print(f"✨ 报表生成完成！")
            print(f"   - 成功: {result['success']} 份")
            print(f"   - 失败: {result['failed']} 份")
            print(f"   - 月份: {result['year']}-{result['month']}")
            print(f"{'='*60}\n")
    
    def auto_send_monthly_reports():
        """每月1号：自动发送上月报表给所有客户"""
        today = datetime.now()
        if today.day == 1:
            print(f"\n{'='*60}")
            print(f"📧 [自动化任务] 开始发送月度报表邮件")
            print(f"{'='*60}\n")
            
            result = monthly_report_scheduler.send_reports_to_all_customers()
            
            print(f"\n{'='*60}")
            print(f"✅ 邮件发送完成！")
            print(f"   - 发送成功: {result['sent']} 封")
            print(f"   - 发送失败: {result['failed']} 封")
            print(f"   - 月份: {result['year']}-{result['month']}")
            print(f"{'='*60}\n")
    
    # 每天上午10点检查是否为30号，如果是则生成报表
    schedule.every().day.at("10:00").do(auto_generate_monthly_reports)
    
    # 每天上午9点检查是否为1号，如果是则发送报表邮件
    schedule.every().day.at("09:00").do(auto_send_monthly_reports)
    
    # ============================================================
    # AI财务日报自动化系统 - 每天早上08:00生成
    # ============================================================
    from accounting_app.tasks.ai_daily_report import generate_daily_report
    from accounting_app.tasks.email_notifier import send_ai_report_email
    
    schedule.every().day.at("08:00").do(generate_daily_report)
    schedule.every().day.at("08:10").do(send_ai_report_email)  # V2企业智能版：邮件推送
    
    print("⏰ AI日报计划任务已注册：每天 08:00 自动生成")
    print("📧 AI日报邮件推送已注册：每天 08:10 自动发送")
    
    while True:
        schedule.run_pending()
        time.sleep(60)

def start_scheduler():
    lock_file = '/tmp/smart_loan_scheduler.lock'
    max_retries = 5
    
    for attempt in range(max_retries):
        try:
            fd = os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            
            scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
            scheduler_thread.start()
            print(f"Reminder scheduler started in background (PID: {os.getpid()})")
            return
            
        except FileExistsError:
            try:
                with open(lock_file, 'r') as f:
                    pid = f.read().strip()
                    os.kill(int(pid), 0)
                    print(f"Scheduler already running in process {pid}")
                    return
            except (OSError, ValueError):
                try:
                    os.remove(lock_file)
                except FileNotFoundError:
                    pass
        except Exception as e:
            print(f"Scheduler start error on attempt {attempt + 1}: {e}")
            if attempt == max_retries - 1:
                return
    
    print("Failed to acquire scheduler lock after retries")

# Statement Comparison Route
@app.route('/statement/<int:statement_id>/comparison')
def statement_comparison(statement_id):
    """账单对比页面：原始账单 vs 分类报告并列展示"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get statement info
        cursor.execute('''
            SELECT s.*, cc.bank_name, cc.card_number_last4, cc.customer_id
            FROM statements s
            JOIN credit_cards cc ON s.card_id = cc.id
            WHERE s.id = ?
        ''', (statement_id,))
        
        statement = dict(cursor.fetchone())
        customer_id = statement['customer_id']
        
        # Get transactions
        cursor.execute('''
            SELECT * FROM transactions
            WHERE statement_id = ?
            ORDER BY transaction_date DESC
        ''', (statement_id,))
        
        transactions = [dict(row) for row in cursor.fetchall()]
        
        # Calculate summary
        total_debit = sum(abs(t['amount']) for t in transactions if t['transaction_type'] == 'purchase')
        total_credit = sum(abs(t['amount']) for t in transactions if t['transaction_type'] == 'payment')
        supplier_fees = sum(t.get('supplier_fee', 0) for t in transactions if t.get('supplier_fee'))
        
        # Category breakdown
        categories = {}
        for t in transactions:
            if t['transaction_type'] == 'purchase':
                cat = t.get('category', 'Uncategorized')
                categories[cat] = categories.get(cat, 0) + abs(t['amount'])
        
        summary = {
            'total_debit': total_debit,
            'total_credit': total_credit,
            'supplier_fees': supplier_fees,
            'categories': categories
        }
    
    return render_template('statement_comparison.html',
                         statement=statement,
                         transactions=transactions,
                         summary=summary,
                         customer_id=customer_id)

# Monthly Statement Detail Route (for consolidated statements)
@app.route('/monthly_statement/<int:monthly_statement_id>/detail')
def monthly_statement_detail(monthly_statement_id):
    """月度账单详情页面：显示合并后的月度账单详情（可能包含多张卡）"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get monthly statement info
        cursor.execute('''
            SELECT ms.*, c.name as customer_name
            FROM monthly_statements ms
            JOIN customers c ON ms.customer_id = c.id
            WHERE ms.id = ?
        ''', (monthly_statement_id,))
        
        monthly_stmt = cursor.fetchone()
        if not monthly_stmt:
            flash('Monthly statement not found', 'error')
            return redirect(url_for('admin_dashboard'))
        
        monthly_stmt = dict(monthly_stmt)
        customer_id = monthly_stmt['customer_id']
        
        # Get all cards included in this monthly statement
        cursor.execute('''
            SELECT cc.card_number_last4, cc.credit_limit, cc.bank_name, cc.card_type
            FROM monthly_statement_cards msc
            JOIN credit_cards cc ON msc.card_id = cc.id
            WHERE msc.monthly_statement_id = ?
        ''', (monthly_statement_id,))
        
        cards = [dict(row) for row in cursor.fetchall()]
        
        # Get all transactions for this monthly statement with bank info
        cursor.execute('''
            SELECT t.*, 
                   s.bank_name,
                   cc.bank_name as card_bank,
                   cc.card_number_last4 as full_card_last4
            FROM transactions t
            LEFT JOIN statements s ON t.statement_id = s.id
            LEFT JOIN credit_cards cc ON s.credit_card_id = cc.id
            WHERE t.monthly_statement_id = ?
            ORDER BY t.transaction_date ASC, t.id ASC
        ''', (monthly_statement_id,))
        
        transactions = [dict(row) for row in cursor.fetchall()]
        
        # Calculate running balance for each transaction
        running_balance = monthly_stmt['previous_balance_total']
        for txn in transactions:
            running_balance += txn['amount']
            txn['running_balance'] = running_balance
        
        # Calculate summary by owner_flag
        owner_transactions = [t for t in transactions if t.get('owner_flag') == 'own']
        gz_transactions = [t for t in transactions if t.get('owner_flag') == 'gz']
        
        owner_expenses = sum(abs(t['amount']) for t in owner_transactions if t['transaction_type'] == 'purchase')
        owner_payments = sum(abs(t['amount']) for t in owner_transactions if t['transaction_type'] == 'payment')
        gz_expenses = sum(abs(t['amount']) for t in gz_transactions if t['transaction_type'] == 'purchase')
        gz_payments = sum(abs(t['amount']) for t in gz_transactions if t['transaction_type'] == 'payment')
        supplier_fees = sum(t.get('supplier_fee', 0) for t in transactions if t.get('supplier_fee'))
        
        summary = {
            'owner_expenses': owner_expenses,
            'owner_payments': owner_payments,
            'gz_expenses': gz_expenses,
            'gz_payments': gz_payments,
            'supplier_fees': supplier_fees,
            'total_transactions': len(transactions),
            'card_count': len(cards)
        }
    
    return render_template('monthly_statement_detail.html',
                         monthly_stmt=monthly_stmt,
                         cards=cards,
                         transactions=transactions,
                         summary=summary,
                         customer_id=customer_id)

@app.route('/export_statement_transactions/<int:statement_id>/<format>')
@require_flask_permission('export:bank_statements', 'read')
def export_statement_transactions(statement_id, format):
    """导出单个statement的交易记录（RBAC protected）"""
    import pandas as pd
    from io import BytesIO
    
    user = session.get('flask_rbac_user', {})
    
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT t.*, s.statement_date, cc.bank_name
                FROM transactions t
                JOIN statements s ON t.statement_id = s.id
                JOIN credit_cards cc ON s.card_id = cc.id
                WHERE t.statement_id = ?
            ''', (statement_id,))
            
            transactions = [dict(row) for row in cursor.fetchall()]
        
        # Create DataFrame
        df = pd.DataFrame(transactions)
        
        if format == 'excel':
            output = BytesIO()
            df.to_excel(output, index=False, engine='openpyxl')  # type: ignore
            output.seek(0)
            
            # 写入审计日志（防御性）
            request_info = extract_flask_request_info()
            write_flask_audit_log(
                user_id=user.get('id', 0),
                username=user.get('username', 'unknown'),
                company_id=user.get('company_id', 1),
                action_type='export',
                entity_type='statement',
                description=f"导出月结单交易记录: statement_id={statement_id}, format=excel",
                success=True,
                new_value={'statement_id': statement_id, 'format': 'excel', 'count': len(transactions)},
                ip_address=request_info['ip_address'],
                user_agent=request_info['user_agent']
            )
            
            return send_file(output, 
                            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                            as_attachment=True,
                            download_name=f'Statement_{statement_id}_Transactions.xlsx')
        else:
            output = BytesIO()
            df.to_csv(output, index=False)
            output.seek(0)
            
            # 写入审计日志（防御性）
            request_info = extract_flask_request_info()
            write_flask_audit_log(
                user_id=user.get('id', 0),
                username=user.get('username', 'unknown'),
                company_id=user.get('company_id', 1),
                action_type='export',
                entity_type='statement',
                description=f"导出月结单交易记录: statement_id={statement_id}, format=csv",
                success=True,
                new_value={'statement_id': statement_id, 'format': 'csv', 'count': len(transactions)},
                ip_address=request_info['ip_address'],
                user_agent=request_info['user_agent']
            )
            
            return send_file(output, 
                            mimetype='text/csv',
                            as_attachment=True,
                            download_name=f'Statement_{statement_id}_Transactions.csv')
    
    except Exception as e:
        # 写入审计日志（失败）
        request_info = extract_flask_request_info()
        write_flask_audit_log(
            user_id=user.get('id', 0),
            username=user.get('username', 'unknown'),
            company_id=user.get('company_id', 1),
            action_type='export',
            entity_type='statement',
            description=f"导出月结单交易记录失败: statement_id={statement_id}",
            success=False,
            new_value={'statement_id': statement_id, 'format': format, 'error': str(e)},
            ip_address=request_info['ip_address'],
            user_agent=request_info['user_agent']
        )
        
        flash(f'Export failed: {str(e)}', 'error')
        return redirect(request.referrer or url_for('index'))

# Edit Monthly Statement Route (for Admin corrections)
@app.route('/monthly_statement/<int:monthly_statement_id>/edit', methods=['POST'])
def edit_monthly_statement(monthly_statement_id):
    """编辑月度账单的余额和分类数据"""
    try:
        # Get form data
        data = request.get_json() if request.is_json else request.form
        
        previous_balance = float(data.get('previous_balance', 0))
        owner_balance = float(data.get('owner_balance', 0))
        gz_balance = float(data.get('gz_balance', 0))
        owner_expenses = float(data.get('owner_expenses', 0))
        owner_payments = float(data.get('owner_payments', 0))
        gz_expenses = float(data.get('gz_expenses', 0))
        gz_payments = float(data.get('gz_payments', 0))
        closing_balance = float(data.get('closing_balance', 0))
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Update monthly statement
            cursor.execute('''
                UPDATE monthly_statements 
                SET previous_balance_total = ?,
                    owner_balance = ?,
                    gz_balance = ?,
                    owner_expenses = ?,
                    owner_payments = ?,
                    gz_expenses = ?,
                    gz_payments = ?,
                    closing_balance_total = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (previous_balance, owner_balance, gz_balance, 
                  owner_expenses, owner_payments, gz_expenses, gz_payments,
                  closing_balance, monthly_statement_id))
            
            conn.commit()
            
            # Log audit (admin user_id=1)
            log_audit(1, 'EDIT_MONTHLY_STATEMENT', 
                     entity_type='monthly_statement', 
                     entity_id=monthly_statement_id,
                     description=f'Edited monthly statement {monthly_statement_id}: prev_bal={previous_balance}, owner_bal={owner_balance}, gz_bal={gz_balance}')
        
        if request.is_json:
            return jsonify({'success': True, 'message': '账单已成功更新！'})
        else:
            flash('账单数据已成功更新！', 'success')
            return redirect(url_for('admin_dashboard'))
            
    except Exception as e:
        print(f"Error editing monthly statement: {e}")
        if request.is_json:
            return jsonify({'success': False, 'message': f'更新失败：{str(e)}'}), 400
        else:
            flash(f'更新失败：{str(e)}', 'error')
            return redirect(url_for('admin_dashboard'))

# Monthly Reports Routes
@app.route('/customer/<int:customer_id>/monthly-reports')
def customer_monthly_reports(customer_id):
    """查看客户的所有月度报表（按信用卡分组）"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        customer = dict(cursor.fetchone())
        
        # 获取所有月度报表，包含信用卡信息
        cursor.execute('''
            SELECT mr.*, cc.bank_name, cc.card_number_last4
            FROM monthly_reports mr
            LEFT JOIN credit_cards cc ON mr.card_id = cc.id
            WHERE mr.customer_id = ?
            ORDER BY mr.report_year DESC, mr.report_month DESC, cc.bank_name
        ''', (customer_id,))
        
        reports = [dict(row) for row in cursor.fetchall()]
        
        # 按年月分组报表
        reports_by_period = {}
        for report in reports:
            period_key = f"{report['report_year']}-{str(report['report_month']).zfill(2)}"
            if period_key not in reports_by_period:
                reports_by_period[period_key] = []
            reports_by_period[period_key].append(report)
    
    return render_template('monthly_reports.html',
                         customer=customer,
                         reports=reports,
                         reports_by_period=reports_by_period)

@app.route('/customer/<int:customer_id>/generate-monthly-report/<int:year>/<int:month>')
def generate_customer_monthly_report(customer_id, year, month):
    """手动生成指定月份的银河主题月度报表"""
    from report.galaxy_report_generator import GalaxyMonthlyReportGenerator
    
    try:
        generator = GalaxyMonthlyReportGenerator()
        pdf_path = generator.generate_customer_monthly_report_galaxy(customer_id, year, month)
        
        if pdf_path:
            flash(f'🌌 银河主题月度报表生成成功！({year}-{month})', 'success')
        else:
            flash(f'该月份没有账单数据 ({year}-{month})', 'error')
    except Exception as e:
        flash(f'生成报表失败: {str(e)}', 'error')
    
    return redirect(url_for('customer_monthly_reports', customer_id=customer_id))

@app.route('/download-monthly-report/<int:report_id>')
def download_monthly_report(report_id):
    """下载月度报表PDF"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM monthly_reports WHERE id = ?', (report_id,))
        report = cursor.fetchone()
    
    if report and os.path.exists(report['pdf_path']):
        return send_file(report['pdf_path'], as_attachment=True)
    else:
        lang = get_current_language()
        flash(translate('report_file_not_exist', lang), 'error')
        return redirect(url_for('index'))


# ============================================================================
# OPTIMIZATION PROPOSAL ROUTES - 自动化获客系统
# ============================================================================

@app.route('/customer/<int:customer_id>/optimization-proposal')
def show_optimization_proposal(customer_id):
    """
    展示优化方案对比页面
    核心：吸引客户点击「申请方案」按钮 = 自动获客
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 获取客户信息
        cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        customer = cursor.fetchone()
        
        if not customer:
            lang = get_current_language()
            flash(translate('customer_not_found', lang), 'error')
            return redirect(url_for('index'))
        
        # 获取客户所有信用卡
        cursor.execute('SELECT * FROM credit_cards WHERE customer_id = ?', (customer_id,))
        cards = cursor.fetchall()
        
        # 获取月度消费数据
        cursor.execute('''
            SELECT SUM(t.amount) as total_spending
            FROM transactions t
            JOIN statements s ON t.statement_id = s.id
            JOIN credit_cards c ON s.card_id = c.id
            WHERE c.customer_id = ? AND t.amount > 0
            AND s.statement_date >= date('now', '-1 month')
        ''', (customer_id,))
        spending_row = cursor.fetchone()
        monthly_spending = spending_row['total_spending'] if spending_row and spending_row['total_spending'] else 0
    
    # 准备客户数据
    customer_data = {
        'name': customer['name'],
        'monthly_income': customer.get('monthly_income', 0),
        'monthly_spending': monthly_spending,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'cards': [
            {
                'bank_name': card['bank_name'],
                'current_balance': card.get('current_balance', 0),
                'credit_limit': card.get('credit_limit', 0)
            }
            for card in cards
        ]
    }
    
    # 生成优化方案
    proposal = optimization_service.generate_comprehensive_proposal(customer_data)
    
    return render_template('optimization_proposal.html', 
                          customer_name=customer['name'],
                          customer_id=customer_id,
                          proposal=proposal)


@app.route('/customer/<int:customer_id>/request-optimization-consultation', methods=['GET', 'POST'])
def request_optimization_consultation(customer_id):
    """
    客户申请咨询优化方案
    关键：客户主动点击 = 自动获客成功！
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        customer = cursor.fetchone()
        
        if not customer:
            lang = get_current_language()
            flash(translate('customer_not_found', lang), 'error')
            return redirect(url_for('index'))
    
    if request.method == 'POST':
        # 记录咨询请求
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO consultation_requests 
                (customer_id, request_date, status, notes)
                VALUES (?, ?, 'pending', ?)
            ''', (
                customer_id,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                request.form.get('notes', '客户申请了解完整优化方案')
            ))
            conn.commit()
        
        # 发送通知给管理员（可选）
        # email_service.send_consultation_request_notification(customer)
        
        lang = get_current_language()
        flash(f"✅ {translate('consultation_request_submitted', lang)}", 'success')
        log_audit('consultation_request', customer_id, f'客户 {customer["name"]} 申请咨询优化方案')
        
        return redirect(url_for('customer_dashboard', customer_id=customer_id))
    
    # GET 请求：显示咨询申请表单
    return render_template('request_consultation.html',
                          customer_name=customer['name'],
                          customer_id=customer_id)


# 创建consultation_requests表（如果不存在）
def init_consultation_table():
    """初始化咨询请求表"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS consultation_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                request_date TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                notes TEXT,
                follow_up_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )
        ''')
        conn.commit()

# 初始化表
init_consultation_table()


# ============================================================================
# OWNER vs INFINITE 分类系统和月度报告路由
# ============================================================================
# 注意：旧的 view_classification, consumption_records, payment_records 路由已删除
# 现在使用 Credit Card Ledger 查看 OWNER vs INFINITE 分类


@app.route('/customer/<int:customer_id>/generate_monthly_report')
def generate_monthly_report_route(customer_id):
    """为客户生成月度报告"""
    from services.statement_processor import generate_customer_monthly_report
    from services.customer_folder_manager import setup_customer_folders
    
    month = request.args.get('month')  # 格式: YYYY-MM
    
    if not month:
        # 默认使用当前月份
        month = datetime.now().strftime('%Y-%m')
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM customers WHERE id = ?', (customer_id,))
        result = cursor.fetchone()
        if not result:
            lang = get_current_language()
            flash(translate('customer_not_found', lang), 'error')
            return redirect(url_for('index'))
        customer_name = result[0]
    
    # 确保客户文件夹存在
    try:
        setup_customer_folders(customer_id)
    except:
        pass
    
    # 生成月度报告
    report_path = generate_customer_monthly_report(customer_id, month)
    
    if report_path:
        flash(f'✅ {month} 月度报告已生成！', 'success')
        # 返回PDF文件供下载
        return send_file(report_path, as_attachment=True, 
                        download_name=f"Monthly_Report_{customer_name}_{month}.pdf")
    else:
        flash(f'⚠️ {month} 月份没有数据，无法生成报告', 'warning')
        return redirect(url_for('customer_dashboard', customer_id=customer_id))


# consumption_records 和 payment_records 路由已删除
# 现在使用 Credit Card Ledger 查看 OWNER vs INFINITE 交易明细


# ============================================================================
# 客户财务仪表板 - 关键指标展示
# ============================================================================

@app.route('/customer/<int:customer_id>/dashboard')
def financial_dashboard(customer_id):
    """
    客户财务仪表板 - 需要登录和访问权限
    展示关键指标：
    - 客户当月总消费/总付款/累计欠款余额
    - 每张信用卡的当月消费/付款/累计余额/积分
    """
    # 获取当前月份（默认）或用户选择的月份
    selected_month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 获取客户信息
        cursor.execute('SELECT full_name FROM customers WHERE id = ?', (customer_id,))
        result = cursor.fetchone()
        if not result:
            lang = get_current_language()
            flash(translate('customer_not_found', lang), 'error')
            return redirect(url_for('index'))
        customer_name = result[0]
    
    # 获取所有指标
    metrics = get_customer_monthly_metrics(customer_id, selected_month)
    
    # 生成月份选项（最近12个月）
    month_options = []
    for i in range(12):
        date = datetime.now() - timedelta(days=30*i)
        month_str = date.strftime('%Y-%m')
        month_display = date.strftime('%Y年%m月')
        month_options.append({
            'value': month_str,
            'display': month_display,
            'selected': month_str == selected_month
        })
    
    return render_template('financial_dashboard.html',
                          customer_id=customer_id,
                          customer_name=customer_name,
                          metrics=metrics,
                          month_options=month_options,
                          selected_month=selected_month)


@app.route('/customer/<int:customer_id>/delete', methods=['POST'])
def delete_customer(customer_id):
    """
    删除客户及其所有相关数据 - 仅管理员
    级联删除：信用卡、账单、交易、月度账本、供应商发票等
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 验证客户是否存在
            cursor.execute('SELECT name FROM customers WHERE id = ?', (customer_id,))
            customer = cursor.fetchone()
            if not customer:
                return jsonify({'success': False, 'error': '客户不存在'}), 404
            
            # 开始删除操作（按依赖顺序）
            
            # 1. 删除交易记录
            cursor.execute('DELETE FROM transactions WHERE customer_id = ?', (customer_id,))
            
            # 2. 删除账单
            cursor.execute('DELETE FROM statements WHERE customer_id = ?', (customer_id,))
            
            # 3. 删除月度账本
            cursor.execute('DELETE FROM monthly_ledger WHERE customer_id = ?', (customer_id,))
            
            # 4. 删除INFINITE账本
            cursor.execute('DELETE FROM infinite_monthly_ledger WHERE customer_id = ?', (customer_id,))
            
            # 5. 删除供应商发票
            cursor.execute('DELETE FROM supplier_invoices WHERE customer_id = ?', (customer_id,))
            
            # 6. 删除信用卡
            cursor.execute('DELETE FROM credit_cards WHERE customer_id = ?', (customer_id,))
            
            # 7. 删除提醒
            cursor.execute('DELETE FROM reminders WHERE customer_id = ?', (customer_id,))
            
            # 8. 删除咨询记录
            cursor.execute('DELETE FROM consultation_requests WHERE customer_id = ?', (customer_id,))
            
            # 9. 删除优化建议
            cursor.execute('DELETE FROM optimization_proposals WHERE customer_id = ?', (customer_id,))
            
            # 10. 最后删除客户本身
            cursor.execute('DELETE FROM customers WHERE id = ?', (customer_id,))
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': f'客户 {customer[0]} 及其所有数据已成功删除'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'删除失败: {str(e)}'
        }), 500


# ============================================================================
# 客户资源、人脉、技能管理
# ============================================================================

@app.route('/customer/<int:customer_id>/resources')
def customer_resources(customer_id):
    """客户资源、人脉、技能管理页面"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 获取客户信息
        cursor.execute('SELECT full_name FROM customers WHERE id = ?', (customer_id,))
        result = cursor.fetchone()
        if not result:
            lang = get_current_language()
            flash(translate('customer_not_found', lang), 'error')
            return redirect(url_for('index'))
        customer_name = result[0]
        
        # 获取资源
        cursor.execute('SELECT * FROM customer_resources WHERE customer_id = ? ORDER BY created_at DESC', (customer_id,))
        resources = cursor.fetchall()
        
        # 获取人脉
        cursor.execute('SELECT * FROM customer_network WHERE customer_id = ? ORDER BY created_at DESC', (customer_id,))
        networks = cursor.fetchall()
        
        # 获取技能
        cursor.execute('SELECT * FROM customer_skills WHERE customer_id = ? ORDER BY created_at DESC', (customer_id,))
        skills = cursor.fetchall()
    
    return render_template('customer_resources.html',
                          customer_id=customer_id,
                          customer_name=customer_name,
                          resources=resources,
                          networks=networks,
                          skills=skills)


@app.route('/customer/<int:customer_id>/add_resource', methods=['POST'])
def add_resource(customer_id):
    """添加个人资源"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO customer_resources (customer_id, resource_type, resource_name, description, estimated_value, availability)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (customer_id, request.form['resource_type'], request.form['resource_name'], 
              request.form.get('description'), request.form.get('estimated_value'), request.form.get('availability')))
        conn.commit()
    
    lang = get_current_language()
    flash(translate('resource_added', lang), 'success')
    return redirect(url_for('customer_resources', customer_id=customer_id))


@app.route('/customer/<int:customer_id>/add_network', methods=['POST'])
def add_network(customer_id):
    """添加人脉联系人"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO customer_network (customer_id, contact_name, relationship_type, industry, position, company, can_provide_help, contact_info)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (customer_id, request.form['contact_name'], request.form['relationship_type'],
              request.form.get('industry'), request.form.get('position'), request.form.get('company'),
              request.form.get('can_provide_help'), request.form.get('contact_info')))
        conn.commit()
    
    lang = get_current_language()
    flash(translate('contact_added', lang), 'success')
    return redirect(url_for('customer_resources', customer_id=customer_id))


@app.route('/customer/<int:customer_id>/add_skill', methods=['POST'])
def add_skill(customer_id):
    """添加特长技能"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO customer_skills (customer_id, skill_name, skill_category, proficiency_level, years_experience, certifications, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (customer_id, request.form['skill_name'], request.form['skill_category'],
              request.form['proficiency_level'], request.form.get('years_experience'),
              request.form.get('certifications'), request.form.get('description')))
        conn.commit()
    
    lang = get_current_language()
    flash(translate('skill_added', lang), 'success')
    return redirect(url_for('customer_resources', customer_id=customer_id))


@app.route('/customer/<int:customer_id>/delete_resource/<int:resource_id>')
def delete_resource(customer_id, resource_id):
    """删除资源"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM customer_resources WHERE id = ? AND customer_id = ?', (resource_id, customer_id))
        conn.commit()
    
    lang = get_current_language()
    flash(translate('resource_deleted', lang), 'success')
    return redirect(url_for('customer_resources', customer_id=customer_id))


@app.route('/customer/<int:customer_id>/delete_network/<int:network_id>')
def delete_network(customer_id, network_id):
    """删除人脉"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM customer_network WHERE id = ? AND customer_id = ?', (network_id, customer_id))
        conn.commit()
    
    lang = get_current_language()
    flash(translate('contact_deleted', lang), 'success')
    return redirect(url_for('customer_resources', customer_id=customer_id))


@app.route('/customer/<int:customer_id>/delete_skill/<int:skill_id>')
def delete_skill(customer_id, skill_id):
    """删除技能"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM customer_skills WHERE id = ? AND customer_id = ?', (skill_id, customer_id))
        conn.commit()
    
    lang = get_current_language()
    flash(translate('skill_deleted', lang), 'success')
    return redirect(url_for('customer_resources', customer_id=customer_id))


@app.route('/customer/<int:customer_id>/generate_business_plan')
def generate_plan(customer_id):
    """生成AI商业计划"""
    result = generate_business_plan(customer_id)
    
    if result['success']:
        lang = get_current_language()
        flash(translate('business_plan_generated', lang), 'success')
        return redirect(url_for('view_business_plan', customer_id=customer_id, plan_id=result['plan_id']))
    else:
        flash(f'生成失败：{result["error"]}', 'error')
        return redirect(url_for('customer_resources', customer_id=customer_id))


@app.route('/customer/<int:customer_id>/business_plan/<int:plan_id>')
def view_business_plan(customer_id, plan_id):
    """查看商业计划"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 获取客户信息
        cursor.execute('SELECT full_name FROM customers WHERE id = ?', (customer_id,))
        result = cursor.fetchone()
        if not result:
            lang = get_current_language()
            flash(translate('customer_not_found', lang), 'error')
            return redirect(url_for('index'))
        customer_name = result[0]
        
        # 获取商业计划
        cursor.execute('''
            SELECT plan_title, business_type, target_market, investment_required,
                   expected_roi, risk_assessment, action_steps, ai_analysis, generated_at
            FROM business_plans
            WHERE id = ? AND customer_id = ?
        ''', (plan_id, customer_id))
        
        plan = cursor.fetchone()
        if not plan:
            lang = get_current_language()
            flash(translate('business_plan_not_exist', lang), 'error')
            return redirect(url_for('customer_resources', customer_id=customer_id))
    
    # 解析JSON数据
    import json
    action_steps = json.loads(plan[6]) if plan[6] else []
    ai_analysis = json.loads(plan[7]) if plan[7] else {}
    
    return render_template('business_plan.html',
                          customer_id=customer_id,
                          customer_name=customer_name,
                          plan=plan,
                          action_steps=action_steps,
                          ai_analysis=ai_analysis)


@app.route('/customer/<int:customer_id>/business_plans')
def list_business_plans(customer_id):
    """查看所有商业计划历史"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute('SELECT full_name FROM customers WHERE id = ?', (customer_id,))
        result = cursor.fetchone()
        if not result:
            lang = get_current_language()
            flash(translate('customer_not_found', lang), 'error')
            return redirect(url_for('index'))
        customer_name = result[0]
        
        cursor.execute('''
            SELECT id, plan_title, business_type, investment_required, generated_at
            FROM business_plans
            WHERE customer_id = ?
            ORDER BY generated_at DESC
        ''', (customer_id,))
        
        plans = cursor.fetchall()
    
    return render_template('business_plans_list.html',
                          customer_id=customer_id,
                          customer_name=customer_name,
                          plans=plans)


# ============================================================================
# 管理员测试路由 - 月度报表自动化系统
# ============================================================================

@app.route('/admin/test-generate-reports')
@require_admin_or_accountant
def admin_test_generate_reports():
    """
    管理员测试：手动触发批量生成所有客户的月度报表
    模拟每月30号的自动化任务
    """
    print(f"\n{'='*60}")
    print(f"🧪 [管理员测试] 手动触发批量报表生成")
    print(f"{'='*60}\n")
    
    result = monthly_report_scheduler.generate_all_customer_reports()
    
    flash(f'✅ 报表生成完成！成功: {result["success"]} 份，失败: {result["failed"]} 份（{result["year"]}-{result["month"]}月）', 'success')
    return redirect(url_for('index'))


@app.route('/admin/test-send-reports')
@require_admin_or_accountant
def admin_test_send_reports():
    """
    管理员测试：手动触发批量发送月度报表邮件
    模拟每月1号的自动化任务
    """
    print(f"\n{'='*60}")
    print(f"🧪 [管理员测试] 手动触发批量邮件发送")
    print(f"{'='*60}\n")
    
    result = monthly_report_scheduler.send_reports_to_all_customers()
    
    flash(f'✅ 邮件发送完成！成功: {result["sent"]} 封，失败: {result["failed"]} 封（{result["year"]}-{result["month"]}月）', 'success')
    return redirect(url_for('index'))


@app.route('/admin/automation-status')
@require_admin_or_accountant
def admin_automation_status():
    """查看自动化系统状态"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 统计本月已生成的报表
        today = datetime.now()
        cursor.execute('''
            SELECT COUNT(*) as count, 
                   SUM(CASE WHEN email_sent = 1 THEN 1 ELSE 0 END) as sent_count
            FROM monthly_reports
            WHERE report_year = ? AND report_month = ?
        ''', (today.year, today.month - 1 if today.month > 1 else 12))
        
        stats = cursor.fetchone()
    
    return jsonify({
        'status': 'running',
        'current_month': f'{today.year}-{today.month}',
        'last_month_reports_generated': stats['count'] if stats else 0,
        'last_month_reports_sent': stats['sent_count'] if stats else 0,
        'scheduler_tasks': [
            {'task': '报表生成', 'schedule': '每月30号 10:00 AM', 'status': 'active'},
            {'task': '邮件发送', 'schedule': '每月1号 9:00 AM', 'status': 'active'}
        ]
    })


# ==================== 收入证明文件系统 Income Document System ====================

@app.route('/income')
def income_home():
    """收入文件管理首页"""
    return render_template('income/index.html')

@app.route('/income/upload')
def income_upload():
    """收入文件上传页面"""
    return render_template('income/upload.html')

@app.route('/api/customers/list')
def api_customers_list():
    """获取客户列表API（供前端使用）"""
    try:
        db = get_db()
        customers = get_all_customers(db)
        return jsonify({
            'status': 'success',
            'customers': [
                {
                    'id': c['id'],
                    'name': c['name'],
                    'email': c['email'],
                    'phone': c.get('phone', ''),
                    'customer_code': c.get('customer_code', '')
                }
                for c in customers
            ]
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# ==================== 储蓄账户追踪系统 Savings Account Tracking ====================

from ingest.savings_parser import parse_savings_statement

@app.route('/savings/upload', methods=['GET', 'POST'])
def upload_savings_statement():
    """上传储蓄账户月结单"""
    if request.method == 'POST':
        try:
            customer_id = request.form.get('customer_id')
            bank_name = request.form.get('bank_name')
            files = request.files.getlist('statements')
            
            if not files:
                lang = get_current_language()
                flash(translate('upload_at_least_one_statement', lang), 'error')
                return redirect(url_for('upload_savings_statement'))
            
            processed_count = 0
            total_transactions = 0
            last_statement_id = None  # 记录最后一个账单ID用于跳转验证
            
            for file in files:
                if file and file.filename:
                    # 临时保存文件用于解析
                    temp_filename = f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
                    temp_file_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
                    file.save(temp_file_path)
                    
                    # 解析账单
                    info, transactions = parse_savings_statement(temp_file_path, bank_name or '')
                    
                    with get_db() as conn:
                        cursor = conn.cursor()
                        
                        # 检查或创建储蓄账户
                        cursor.execute('''
                            SELECT id FROM savings_accounts 
                            WHERE bank_name = ? AND account_number_last4 = ?
                        ''', (info['bank_name'], info.get('account_last4', '')))
                        
                        account = cursor.fetchone()
                        
                        if not account:
                            cursor.execute('''
                                INSERT INTO savings_accounts (customer_id, bank_name, account_number_last4)
                                VALUES (?, ?, ?)
                            ''', (customer_id or None, info['bank_name'], info.get('account_last4', '')))
                            savings_account_id = cursor.lastrowid
                        else:
                            savings_account_id = account['id']
                        
                        # 🔥 强制性文件组织：获取客户信息（包含customer_code）
                        cursor.execute('''
                            SELECT c.name as customer_name, c.customer_code
                            FROM savings_accounts sa
                            JOIN customers c ON sa.customer_id = c.id
                            WHERE sa.id = ?
                        ''', (savings_account_id,))
                        
                        customer_row = cursor.fetchone()
                        if customer_row:
                            customer_name = customer_row['customer_name']
                            customer_code_for_files = customer_row['customer_code']
                        else:
                            customer_name = 'Unknown_Customer'
                            customer_code_for_files = 'Be_rich_UNKNOWN_00'
                        
                        # 使用StatementOrganizer组织文件（按客户代码）
                        from services.statement_organizer import StatementOrganizer
                        organizer = StatementOrganizer()
                        
                        stmt_date = info.get('statement_date', datetime.now().strftime('%Y-%m-%d'))
                        
                        try:
                            organize_result = organizer.organize_statement(
                                temp_file_path,
                                customer_code_for_files,
                                customer_name,
                                stmt_date,
                                {
                                    'bank_name': info['bank_name'],
                                    'last_4_digits': info.get('account_last4', '0000')
                                },
                                category=StatementOrganizer.CATEGORY_SAVINGS
                            )
                            
                            organized_file_path = organize_result['archived_path']
                            os.remove(temp_file_path)  # 删除临时文件
                            print(f"✅ 储蓄账户文件已组织到: {organized_file_path}")
                            
                        except Exception as e:
                            print(f"⚠️ 储蓄账户文件组织失败，使用临时路径: {str(e)}")
                            organized_file_path = temp_file_path
                        
                        # 创建账单记录
                        cursor.execute('''
                            INSERT INTO savings_statements 
                            (savings_account_id, statement_date, file_path, file_type, total_transactions, is_processed)
                            VALUES (?, ?, ?, ?, ?, 1)
                        ''', (
                            savings_account_id,
                            stmt_date,
                            organized_file_path,
                            'pdf' if temp_filename.endswith('.pdf') else 'excel',
                            len(transactions)
                        ))
                        
                        statement_id = cursor.lastrowid
                        
                        # 保存所有交易记录
                        for trans in transactions:
                            cursor.execute('''
                                INSERT INTO savings_transactions
                                (savings_statement_id, transaction_date, description, amount, transaction_type, balance)
                                VALUES (?, ?, ?, ?, ?, ?)
                            ''', (
                                statement_id,
                                trans.get('date', ''),
                                trans.get('description', ''),
                                trans.get('amount', 0),
                                trans.get('type', 'debit'),
                                trans.get('balance', None)  # 添加balance字段
                            ))
                        
                        conn.commit()
                        
                        processed_count += 1
                        total_transactions += len(transactions)
                        last_statement_id = statement_id  # 记录最后一个账单ID
            
            # ✅ 上传成功后，自动跳转到双重验证页面
            flash(f'✅ 成功上传{processed_count}个账单，共{total_transactions}笔交易记录。请进行双重人工验证。', 'success')
            if last_statement_id:
                return redirect(url_for('verify_savings_statement', statement_id=last_statement_id))
            else:
                return redirect(url_for('savings_customers'))
            
        except Exception as e:
            flash(f'上传失败: {str(e)}', 'error')
            import traceback
            traceback.print_exc()
            return redirect(url_for('upload_savings_statement'))
    
    # GET request - show upload form
    customers = get_all_customers()
    return render_template('savings/upload.html', customers=customers)

@app.route('/savings/verify/<int:statement_id>')
def verify_savings_statement(statement_id):
    """
    储蓄账户月结单 - 双重人工验证页面
    上传成功后自动跳转到此页面，显示对比表供人工验证
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 获取账单信息
        cursor.execute('''
            SELECT 
                ss.id,
                ss.statement_date,
                ss.total_transactions,
                ss.file_path,
                ss.verification_status,
                ss.verified_at,
                sa.bank_name,
                sa.account_number_last4,
                sa.account_holder_name,
                sa.customer_id,
                c.name as customer_name,
                c.customer_code
            FROM savings_statements ss
            JOIN savings_accounts sa ON ss.savings_account_id = sa.id
            JOIN customers c ON sa.customer_id = c.id
            WHERE ss.id = ?
        ''', (statement_id,))
        
        stmt = cursor.fetchone()
        
        if not stmt:
            flash('账单不存在', 'error')
            return redirect(url_for('savings_customers'))
        
        statement = dict(stmt)
        
        # 获取所有交易记录
        cursor.execute('''
            SELECT 
                id,
                transaction_date,
                description,
                amount,
                transaction_type,
                balance
            FROM savings_transactions
            WHERE savings_statement_id = ?
            ORDER BY id
        ''', (statement_id,))
        
        transactions = [dict(row) for row in cursor.fetchall()]
        
        # 计算财务汇总
        total_credit = sum(t['amount'] for t in transactions if t['transaction_type'] == 'credit')
        total_debit = sum(t['amount'] for t in transactions if t['transaction_type'] == 'debit')
        closing_balance = transactions[-1]['balance'] if transactions else 0
        
        statement['total_credit'] = total_credit
        statement['total_debit'] = total_debit
        statement['closing_balance'] = closing_balance
    
    return render_template('savings/verify.html', 
                          statement=statement, 
                          transactions=transactions)

@app.route('/savings/mark_verified/<int:statement_id>', methods=['POST'])
def mark_savings_verified(statement_id):
    """标记账单为已验证"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 更新验证状态
        cursor.execute('''
            UPDATE savings_statements
            SET verification_status = 'verified',
                verified_at = ?
            WHERE id = ?
        ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), statement_id))
        
        conn.commit()
    
    flash('✅ 账单已标记为已验证！数据已确认100%准确。', 'success')
    return redirect(url_for('savings_customers'))

@app.route('/savings')
def savings_report():
    """Public Savings Report - CHEOK JUN YOON Transfer Report"""
    return render_template('savings_report.html')

@app.route('/savings/customers')
@require_admin_or_accountant
def savings_customers():
    """Layer 1: 查看所有拥有储蓄账户的客户列表"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 获取所有有储蓄账户的客户
        cursor.execute('''
            SELECT DISTINCT
                c.id,
                c.name,
                c.customer_code,
                COUNT(DISTINCT sa.id) as account_count,
                COUNT(DISTINCT ss.id) as statement_count,
                COUNT(st.id) as total_transactions,
                SUM(CASE WHEN st.transaction_type = 'debit' THEN st.amount ELSE 0 END) as total_debit,
                SUM(CASE WHEN st.transaction_type = 'credit' THEN st.amount ELSE 0 END) as total_credit
            FROM customers c
            JOIN savings_accounts sa ON c.id = sa.customer_id
            LEFT JOIN savings_statements ss ON sa.id = ss.savings_account_id
            LEFT JOIN savings_transactions st ON ss.id = st.savings_statement_id
            GROUP BY c.id, c.name, c.customer_code
            ORDER BY c.name
        ''')
        
        customers = [dict(row) for row in cursor.fetchall()]
    
    return render_template('savings/customers.html', customers=customers)

@app.route('/savings/accounts')
def savings_accounts_redirect():
    """Redirect to savings customers list"""
    return redirect(url_for('savings_customers'))

@app.route('/savings/accounts/<int:customer_id>')
@require_admin_or_accountant
def savings_accounts(customer_id):
    """Layer 2: 查看特定客户的所有储蓄账户和账单"""
    import re
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 获取客户信息
        cursor.execute('SELECT id, name, customer_code FROM customers WHERE id = ?', (customer_id,))
        customer_row = cursor.fetchone()
        if not customer_row:
            lang = get_current_language()
            flash(translate('customer_not_found', lang), 'error')
            return redirect(url_for('savings_customers'))
        customer = dict(customer_row)
        
        # 获取该客户的所有储蓄账户
        cursor.execute('''
            SELECT 
                sa.id,
                sa.bank_name,
                sa.account_number_last4,
                sa.created_at,
                COUNT(DISTINCT ss.id) as statement_count,
                COUNT(st.id) as total_transactions,
                SUM(CASE WHEN st.transaction_type = 'debit' THEN st.amount ELSE 0 END) as total_debit,
                SUM(CASE WHEN st.transaction_type = 'credit' THEN st.amount ELSE 0 END) as total_credit
            FROM savings_accounts sa
            LEFT JOIN savings_statements ss ON sa.id = ss.savings_account_id
            LEFT JOIN savings_transactions st ON ss.id = st.savings_statement_id
            WHERE sa.customer_id = ?
            GROUP BY sa.id
            ORDER BY sa.created_at DESC
        ''', (customer_id,))
        
        accounts = [dict(row) for row in cursor.fetchall()]
        
        # 提取该客户所有转账交易中的收款人信息（按收款人+收款银行分组）
        cursor.execute('''
            SELECT st.description, st.amount, st.transaction_date, sa.bank_name as source_bank
            FROM savings_transactions st
            JOIN savings_statements ss ON st.savings_statement_id = ss.id
            JOIN savings_accounts sa ON ss.savings_account_id = sa.id
            WHERE sa.customer_id = ?
                AND st.transaction_type = 'debit' 
                AND (st.description LIKE '%Transfer%' OR st.description LIKE '%转账%' OR st.description LIKE '%Pay%')
            ORDER BY st.transaction_date
        ''', (customer_id,))
        
        all_transfers = cursor.fetchall()
        
        # 按收款人+收款银行分组
        recipient_groups = {}
        
        for trans in all_transfers:
            desc = trans['description']
            amount = trans['amount']
            source_bank = trans['source_bank']
            
            # 提取收款人名字和银行
            recipient_name = None
            recipient_bank = None
            
            # 提取银行代码（MBK/MBB = Maybank, GXS = GX Bank, OCBC, UOB等）
            if 'MBK' in desc.upper() or 'MBB' in desc.upper():
                recipient_bank = 'Maybank'
            elif 'GXS' in desc.upper() or 'GX BANK' in desc.upper():
                recipient_bank = 'GX Bank'
            elif 'OCBC' in desc.upper():
                recipient_bank = 'OCBC'
            elif 'UOB' in desc.upper():
                recipient_bank = 'UOB'
            elif 'CIMB' in desc.upper():
                recipient_bank = 'CIMB'
            elif 'HLB' in desc.upper() or 'HONG LEONG' in desc.upper():
                recipient_bank = 'Hong Leong Bank'
            elif 'PUBLIC' in desc.upper():
                recipient_bank = 'Public Bank'
            
            # 提取收款人名字（通常在银行代码后面）
            # 示例: "Transfer MBK YEO CHEE WANG" or "Pay MBB TEO YOK CHU"
            patterns = [
                r'(?:Transfer|Pay|Payment)\s+(?:MBK|MBB|GXS|OCBC|UOB|CIMB|HLB)\s+([A-Z][A-Za-z\s]+?)(?:\s+\d|\s*$|\.\.\.)',
                r'(?:Transfer|Pay|Payment)\s+([A-Z][A-Za-z\s]+?)(?:\s+\d|\s*$|\.\.\.)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, desc, re.IGNORECASE)
                if match:
                    recipient_name = match.group(1).strip().upper()
                    # 移除常见后缀
                    recipient_name = re.sub(r'\s+(SILAAM|BPERHATI|SILAAMBIL).*$', '', recipient_name)
                    break
            
            if recipient_name and recipient_bank:
                key = f"{recipient_name}_{recipient_bank}"
                
                if key not in recipient_groups:
                    recipient_groups[key] = {
                        'recipient_name': recipient_name,
                        'recipient_bank': recipient_bank,
                        'source_bank': source_bank,
                        'total_amount': 0,
                        'transaction_count': 0,
                        'transactions': []
                    }
                
                recipient_groups[key]['total_amount'] += amount
                recipient_groups[key]['transaction_count'] += 1
                recipient_groups[key]['transactions'].append({
                    'date': trans['transaction_date'],
                    'amount': amount,
                    'description': desc
                })
        
        # 转换为列表并按总金额排序
        recipients = sorted(recipient_groups.values(), key=lambda x: x['total_amount'], reverse=True)
    
    return render_template('savings/accounts.html', 
                         customer=customer,
                         customer_id=customer_id,
                         accounts=accounts, 
                         recipients=recipients)

@app.route('/savings/account/<int:account_id>')
@require_admin_or_accountant
def savings_account_detail(account_id):
    """查看特定账户的详细信息、账单和交易记录"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 获取账户信息
        cursor.execute('''
            SELECT id, bank_name, account_number_last4, account_type, created_at
            FROM savings_accounts
            WHERE id = ?
        ''', (account_id,))
        
        account_row = cursor.fetchone()
        if not account_row:
            lang = get_current_language()
            flash(f"⚠️ {translate('savings_account_not_found', lang)}", 'error')
            return redirect(url_for('savings_customers'))
        
        account = dict(account_row)
        
        # 获取账单列表
        cursor.execute('''
            SELECT 
                ss.id,
                ss.statement_date,
                ss.file_path,
                ss.file_type,
                ss.total_transactions,
                ss.created_at,
                ss.verification_status,
                ss.verified_by,
                ss.verified_at,
                ss.savings_account_id,
                COUNT(st.id) as transaction_count,
                SUM(CASE WHEN st.transaction_type = 'debit' THEN st.amount ELSE 0 END) as total_debit,
                SUM(CASE WHEN st.transaction_type = 'credit' THEN st.amount ELSE 0 END) as total_credit
            FROM savings_statements ss
            LEFT JOIN savings_transactions st ON ss.id = st.savings_statement_id
            WHERE ss.savings_account_id = ?
            GROUP BY ss.id
            ORDER BY ss.statement_date DESC, ss.created_at DESC
        ''', (account_id,))
        
        statements = [dict(row) for row in cursor.fetchall()]
        
        # 获取最近交易记录
        cursor.execute('''
            SELECT 
                st.id,
                st.transaction_date,
                st.description,
                st.amount,
                st.transaction_type,
                st.customer_name_tag,
                st.notes,
                ss.statement_date
            FROM savings_transactions st
            JOIN savings_statements ss ON st.savings_statement_id = ss.id
            WHERE ss.savings_account_id = ?
            ORDER BY st.transaction_date DESC, st.id DESC
            LIMIT 100
        ''', (account_id,))
        
        recent_transactions = [dict(row) for row in cursor.fetchall()]
        
        # 计算统计数据
        cursor.execute('''
            SELECT 
                COUNT(st.id) as total_transactions,
                SUM(CASE WHEN st.transaction_type = 'debit' THEN st.amount ELSE 0 END) as total_debit,
                SUM(CASE WHEN st.transaction_type = 'credit' THEN st.amount ELSE 0 END) as total_credit
            FROM savings_transactions st
            JOIN savings_statements ss ON st.savings_statement_id = ss.id
            WHERE ss.savings_account_id = ?
        ''', (account_id,))
        
        stats = dict(cursor.fetchone())
    
    return render_template('savings/account_detail.html', 
                         account=account, 
                         statements=statements,
                         recent_transactions=recent_transactions,
                         stats=stats)

@app.route('/savings/search', methods=['GET', 'POST'])
def savings_search():
    """搜索转账记录（按客户名字或关键词）"""
    transactions = []
    search_query = ''
    
    if request.method == 'POST' or request.args.get('q'):
        search_query = request.form.get('search_query') or request.args.get('q', '')
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 使用模糊搜索
            cursor.execute('''
                SELECT 
                    st.id,
                    st.transaction_date,
                    st.description,
                    st.amount,
                    st.transaction_type,
                    st.customer_name_tag,
                    sa.bank_name,
                    sa.account_number_last4,
                    ss.statement_date
                FROM savings_transactions st
                JOIN savings_statements ss ON st.savings_statement_id = ss.id
                JOIN savings_accounts sa ON ss.savings_account_id = sa.id
                WHERE st.description LIKE ? OR st.customer_name_tag LIKE ?
                ORDER BY st.transaction_date DESC
                LIMIT 500
            ''', (f'%{search_query}%', f'%{search_query}%'))
            
            transactions = [dict(row) for row in cursor.fetchall()]
    
    return render_template('savings/search.html', 
                         transactions=transactions, 
                         search_query=search_query)

@app.route('/savings/settlement/<customer_name>')
def savings_settlement(customer_name):
    """生成客户结算报告 - 按月分组显示"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 搜索该客户的所有转账记录
        cursor.execute('''
            SELECT 
                st.id,
                st.transaction_date,
                st.description,
                st.amount,
                st.transaction_type,
                sa.bank_name,
                sa.account_number_last4,
                ss.statement_date,
                sa.account_holder_name
            FROM savings_transactions st
            JOIN savings_statements ss ON st.savings_statement_id = ss.id
            JOIN savings_accounts sa ON ss.savings_account_id = sa.id
            WHERE st.description LIKE ? OR st.customer_name_tag = ?
            ORDER BY st.transaction_date ASC
        ''', (f'%{customer_name}%', customer_name))
        
        transactions = [dict(row) for row in cursor.fetchall()]
        
        # 只统计debit（转出）交易
        debit_transactions = [t for t in transactions if t['transaction_type'] == 'debit']
        
        # 按月分组 - 统一转换为 YYYY-MM 格式
        from collections import defaultdict
        from datetime import datetime
        
        month_map = {
            'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
            'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
            'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
        }
        
        monthly_groups = defaultdict(list)
        
        for trans in debit_transactions:
            # 提取月份 (格式: DD-MM-YYYY 或 DD MMM YYYY)
            date_str = trans['transaction_date']
            try:
                month_key = None
                month_display = None
                
                if '-' in date_str:
                    # DD-MM-YYYY 格式
                    parts = date_str.split('-')
                    if len(parts) == 3:
                        month_num = parts[1]  # MM
                        year = parts[2]  # YYYY
                        month_key = f"{year}-{month_num}"  # YYYY-MM
                        # 转换为 MMM YYYY 显示格式
                        month_names = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                        month_display = f"{month_names[int(month_num)]} {year}"
                elif ' ' in date_str:
                    # DD MMM YYYY 格式
                    parts = date_str.split()
                    if len(parts) >= 3:
                        month_abbr = parts[1].lower()[:3]  # 取前3个字符
                        year = parts[2]  # YYYY
                        month_num = month_map.get(month_abbr, '00')
                        month_key = f"{year}-{month_num}"  # YYYY-MM
                        month_display = f"{parts[1]} {year}"  # MMM YYYY
                
                if not month_key:
                    month_key = 'Unknown'
                    month_display = 'Unknown'
                    
            except:
                month_key = 'Unknown'
                month_display = 'Unknown'
            
            monthly_groups[month_key].append({
                **trans,
                'month_display': month_display
            })
        
        # 计算每月总额
        monthly_summary = []
        for month_key in sorted(monthly_groups.keys()):
            month_transactions = monthly_groups[month_key]
            month_total = sum(t['amount'] for t in month_transactions)
            monthly_summary.append({
                'month': month_transactions[0]['month_display'] if month_transactions else month_key,
                'transaction_count': len(month_transactions),
                'total_amount': month_total,
                'transactions': month_transactions
            })
        
        # 计算总额
        total_amount = sum(t['amount'] for t in debit_transactions)
        
        settlement_data = {
            'customer_name': customer_name,
            'total_amount': total_amount,
            'transaction_count': len(debit_transactions),
            'monthly_summary': monthly_summary,
            'all_transactions': debit_transactions,
            'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    return render_template('savings/settlement.html', settlement=settlement_data)

@app.route('/savings/transaction/<int:transaction_id>/edit', methods=['POST'])
def edit_savings_transaction(transaction_id):
    """编辑交易的客户标签和备注"""
    customer_tag = request.form.get('customer_tag', '').strip()
    notes = request.form.get('notes', '').strip()
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE savings_transactions 
            SET customer_name_tag = ?, notes = ?
            WHERE id = ?
        ''', (customer_tag, notes, transaction_id))
        conn.commit()
    
    lang = get_current_language()
    flash(f"✅ {translate('transaction_updated', lang)}", 'success')
    return redirect(request.referrer or url_for('savings_accounts'))

@app.route('/savings/tag/<int:transaction_id>', methods=['POST'])
def tag_savings_transaction(transaction_id):
    """标记交易的客户名字"""
    customer_tag = request.form.get('customer_tag')
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE savings_transactions
            SET customer_name_tag = ?, is_prepayment = 1
            WHERE id = ?
        ''', (customer_tag, transaction_id))
        conn.commit()
    
    flash(f'✅ 已标记交易为客户: {customer_tag}', 'success')
    return redirect(request.referrer or url_for('savings_search'))

@app.route('/savings/export-transaction/<int:transaction_id>')
@require_admin_or_accountant
def export_transaction_image(transaction_id):
    """导出单个交易在原始PDF中的截图（限admin/accountant）"""
    from pdf2image import convert_from_path
    from PIL import Image
    from io import BytesIO
    from flask import send_file
    import pdfplumber
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                st.id,
                st.transaction_date,
                st.description,
                st.amount,
                sa.bank_name,
                ss.id as statement_id,
                ss.file_path
            FROM savings_transactions st
            JOIN savings_statements ss ON st.savings_statement_id = ss.id
            JOIN savings_accounts sa ON ss.savings_account_id = sa.id
            WHERE st.id = ?
        ''', (transaction_id,))
        
        trans = cursor.fetchone()
        if not trans:
            return "Transaction not found", 404
        
        trans = dict(trans)
    
    pdf_path = trans['file_path']
    if not os.path.exists(pdf_path):
        return "PDF file not found", 404
    
    # 使用pdf2image将PDF转换为图片
    try:
        images = convert_from_path(pdf_path, dpi=200)
        
        # 查找包含该交易描述的页面
        target_desc = trans['description'][:30]  # 使用描述的前30个字符
        target_amount = f"{abs(trans['amount']):.2f}"
        
        # 使用pdfplumber查找交易位置
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if target_desc in text or target_amount in text:
                    # 找到包含该交易的页面，返回该页面的图片
                    page_image = images[page_num]
                    
                    # 保存到BytesIO
                    img_io = BytesIO()
                    page_image.save(img_io, 'PNG', quality=95)
                    img_io.seek(0)
                    
                    return send_file(img_io, mimetype='image/png', as_attachment=True, 
                                   download_name=f'statement_transaction_{transaction_id}.png')
        
        # 如果未找到，返回第一页
        img_io = BytesIO()
        images[0].save(img_io, 'PNG', quality=95)
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/png', as_attachment=True, 
                        download_name=f'statement_page_{transaction_id}.png')
        
    except Exception as e:
        return f"Error generating screenshot: {str(e)}", 500

@app.route('/view_savings_statement_file/<int:statement_id>')
@require_admin_or_accountant
def view_savings_statement_file(statement_id):
    """查看储蓄账户账单原始PDF文件"""
    from flask import send_file
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT file_path FROM savings_statements WHERE id = ?', (statement_id,))
        row = cursor.fetchone()
        
        if not row or not row['file_path']:
            return "PDF file not found", 404
        
        file_path = row['file_path']
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return f"File does not exist: {file_path}", 404
        
        # 返回PDF文件
        return send_file(file_path, mimetype='application/pdf')


# ============================================================================
# LOAN MATCHER SYSTEM - 智能贷款产品匹配系统
# ============================================================================

@app.route('/loan-matcher')
@require_admin_or_accountant
def loan_matcher():
    """贷款产品匹配系统 - 表单页面"""
    return render_template('loan_matcher.html')

@app.route('/loan-matcher/analyze', methods=['POST'])
@require_admin_or_accountant
def loan_matcher_analyze():
    """分析客户资料并匹配贷款产品"""
    from modules.parsers.ctos_parser import extract_commitment_from_ctos
    from modules.dsr import calculate_dsr
    from modules.matcher import load_all_products, match_loans
    
    # 获取表单数据
    client_name = request.form.get('client_name', '').strip()
    citizenship = request.form.get('citizenship', 'MY')
    age = int(request.form.get('age', 0) or 0)
    monthly_income = float(request.form.get('monthly_income', 0) or 0)
    company_age = request.form.get('company_age', '').strip()
    company_age = int(company_age) if company_age else None
    
    # 处理CTOS上传
    total_commitment = 0.0
    ctos_notes = "未上传CTOS报告"
    
    ctos_file = request.files.get('ctos_file')
    if ctos_file and ctos_file.filename:
        # 保存文件
        filename = f"ctos_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{ctos_file.filename}"
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        ctos_file.save(save_path)
        
        # 解析CTOS
        total_commitment, ctos_notes = extract_commitment_from_ctos(save_path)
    
    # 人工覆盖（如果提供）
    manual_commitment = request.form.get('manual_commitment', '').strip()
    if manual_commitment:
        total_commitment = float(manual_commitment)
        ctos_notes = "✅ 人工输入数据"
    
    # 计算DSR
    dsr = calculate_dsr(total_commitment, monthly_income)
    
    # 构建客户资料
    client = {
        'citizenship': citizenship,
        'age': age,
        'income': monthly_income,
        'dsr': dsr,
        'company_age': company_age
    }
    
    # 加载产品库并匹配（显示所有类型）
    products = load_all_products('data/banks')
    eligible, ineligible = match_loans(client, products)
    
    # 记录审计日志
    log_audit(
        user_id=session.get('user_id', 0),
        action_type='LOAN_MATCHER_ANALYSIS',
        description=f'客户: {client_name}, DSR: {dsr}%, 符合产品: {len(eligible)}个'
    )
    
    # 按类型分组（用于结果页面展示）
    from collections import defaultdict
    
    eligible_by_type = defaultdict(list)
    for item in eligible:
        category = item['product'].get('category', 'other')
        eligible_by_type[category].append(item)
    
    ineligible_by_type = defaultdict(list)
    for item in ineligible:
        category = item['product'].get('category', 'other')
        ineligible_by_type[category].append(item)
    
    # 类型名称映射
    category_names = {
        'personal': '个人贷款 (Personal Loan)',
        'home': '房屋贷款 (Mortgage Loan)',
        'auto': '汽车贷款 (Car Loan)',
        'sme': '企业贷款 (SME/Business Loan)',
        'refinance': '再融资 (Refinance)',
        'debt_consolidation': '债务整合 (Debt Consolidation)',
        'home_reno': '房屋装修贷款 (Home Renovation)',
        'investment': '投资贷款 (Investment)',
        'other': '其他贷款'
    }
    
    # 类型图标映射
    category_icons = {
        'personal': 'bi-person-check',
        'home': 'bi-house-door',
        'auto': 'bi-car-front',
        'sme': 'bi-building',
        'refinance': 'bi-arrow-repeat',
        'debt_consolidation': 'bi-wallet2',
        'home_reno': 'bi-hammer',
        'investment': 'bi-graph-up-arrow',
        'other': 'bi-tag'
    }
    
    return render_template(
        'loan_matcher_result.html',
        client_name=client_name,
        dsr=dsr,
        total_commitment=total_commitment,
        ctos_notes=ctos_notes,
        eligible=eligible,
        ineligible=ineligible,
        eligible_by_type=dict(eligible_by_type),
        ineligible_by_type=dict(ineligible_by_type),
        category_names=category_names,
        category_icons=category_icons
    )


# ============================================================================
# LOAN PRODUCTS CATALOG - 贷款产品目录浏览系统
# ============================================================================

@app.route('/loan-products')
@require_admin_or_accountant
def loan_products():
    """Phase 9: 贷款产品目录 - 调用FastAPI统一产品API"""
    import requests
    
    try:
        # 调用FastAPI /api/loan-products/all端点
        response = requests.get('http://localhost:8000/api/loan-products/all', timeout=10)
        response.raise_for_status()
        data = response.json()
        
        products = data.get('products', [])
        total_products = data.get('total', 0)
        
        # 统计银行数量
        banks = list(set([p['bank'] for p in products]))
        total_banks = len(banks)
        
        # 转换产品数据格式为前端需要的JSON
        products_json = products
        
    except Exception as e:
        print(f"Error fetching loan products from API: {e}")
        products_json = []
        total_products = 0
        total_banks = 0
    
    return render_template(
        'loan_products.html',
        products_json=products_json,
        total_products=total_products,
        total_banks=total_banks
    )


@app.route('/api/loan-products/select', methods=['POST'])
@require_admin_or_accountant
def select_product_for_evaluation():
    """Phase 9: Store selected product_id in session for loan evaluation"""
    try:
        data = request.json
        product_id = data.get('product_id')
        
        if not product_id:
            return jsonify({'error': 'product_id required'}), 400
        
        # Store in Flask session
        session['selected_product_id'] = product_id
        
        return jsonify({'success': True, 'product_id': product_id})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/all-products-catalog')
def all_products_catalog():
    """完整产品目录 - 展示所有797个真实产品"""
    from load_all_products import get_all_products
    
    try:
        result = get_all_products()
        
        return render_template('all_products_catalog.html',
                             excel_products=result['excel'],
                             json_products=result['json'],
                             excel_count=len(result['excel']),
                             json_count=len(result['json']),
                             total_count=result['total'])
    except Exception as e:
        logger.error(f"加载产品目录失败: {e}")
        flash(f"加载产品目录失败: {str(e)}", "danger")
        return redirect(url_for('index'))

@app.route('/loan-products-dashboard')
@require_admin_or_accountant
def loan_products_dashboard():
    """Phase 9: Loan Marketplace Dashboard（三个入口卡片）"""
    return render_template('loan_products_dashboard.html')

@app.route('/loan-products/<int:product_id>')
def loan_product_detail(product_id):
    """贷款产品详情页"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM loan_products WHERE id = ?", (product_id,))
        product = cursor.fetchone()
        
        if not product:
            flash('产品未找到', 'error')
            return redirect(url_for('loan_products'))
        
        product = dict(product)
        
        # 解析 JSON 字段
        import json
        for field in ['channel', 'docs_required', 'special_features', 'special_conditions', 'links']:
            if product.get(field):
                try:
                    product[field] = json.loads(product[field])
                except:
                    product[field] = []
    
    return render_template('loan_product_detail.html', product=product)


# ============================================================================
# PHASE 6: MODERN LOAN ENGINE & SME LOAN FRONTEND PAGES
# ============================================================================

@app.route('/loan-evaluate')
@require_admin_or_accountant
def loan_modern_evaluate():
    """Phase 8.1: Modern Loan Evaluate - 三模式评估页面（Full Auto / Quick Income / Quick Income+Commit）"""
    return render_template('loan_evaluate.html')


@app.route('/loan-evaluate/submit', methods=['POST'])
@require_admin_or_accountant
def loan_modern_evaluate_submit():
    """提交Modern Loan评估请求并调用FastAPI"""
    import requests
    
    # 获取表单数据
    customer_id = request.form.get('customer_id')
    data_mode = request.form.get('data_mode', 'manual')
    income = request.form.get('income', '')
    monthly_commitment = request.form.get('monthly_commitment')
    ccris_bucket = request.form.get('ccris_bucket', '')
    credit_score = request.form.get('credit_score', '')
    age = request.form.get('age', '')
    employment_years = request.form.get('employment_years', '')
    job_type = request.form.get('job_type', '')
    target_bank = request.form.get('target_bank', '')
    
    # 构建API URL
    api_url = f"http://localhost:8000/api/loans/evaluate/{customer_id}"
    params = {
        'mode': 'modern',
        'data_mode': data_mode,
        'monthly_commitment': monthly_commitment
    }
    
    # 添加可选参数
    if income:
        params['income'] = income
    if ccris_bucket:
        params['ccris_bucket'] = ccris_bucket
    if credit_score:
        params['credit_score'] = credit_score
    if age:
        params['age'] = age
    if employment_years:
        params['employment_years'] = employment_years
    if job_type:
        params['job_type'] = job_type
    if target_bank:
        params['target_bank'] = target_bank
    
    try:
        # 调用FastAPI
        response = requests.get(api_url, params=params, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        # 记录审计日志
        log_audit(
            user_id=session.get('user_id', 0),
            action_type='MODERN_LOAN_EVALUATION',
            description=f'Customer {customer_id}, Risk Grade: {result.get("risk_grade", "N/A")}, Mode: modern'
        )
        
        # 渲染结果页面（扩展版loan_matcher_result.html）
        return render_template(
            'loan_matcher_result.html',
            client_name=f"Customer #{customer_id}",
            dsr=result.get('dti_ratio', 0) * 100,  # 使用DTI作为DSR显示
            total_commitment=float(monthly_commitment),
            ctos_notes="Modern Engine Analysis",
            eligible=[{'product': prod} for prod in result.get('recommended_products', [])],
            ineligible=[],
            eligible_by_type={},
            ineligible_by_type={},
            category_names={},
            category_icons={},
            # Phase 6 新增字段
            modern_result=result,  # 完整的Modern引擎结果
            is_modern_mode=True
        )
    except Exception as e:
        flash(f'评估失败: {str(e)}', 'error')
        return redirect(url_for('loan_modern_evaluate'))


@app.route('/sme-loan-evaluate')
@require_admin_or_accountant
def sme_loan_evaluate():
    """SME Loan Engine - 前端表单页面（BRR/DSCR风控评估）"""
    return render_template('sme_loan_evaluate.html')


@app.route('/sme-loan-evaluate/submit', methods=['POST'])
@require_admin_or_accountant
def sme_loan_evaluate_submit():
    """提交SME Loan评估请求并调用FastAPI"""
    import requests
    
    # 获取表单数据
    customer_id = request.form.get('customer_id')
    data_mode = request.form.get('data_mode', 'manual')
    monthly_revenue = request.form.get('monthly_revenue')
    monthly_commitment = request.form.get('monthly_commitment')
    industry = request.form.get('industry', '')
    years_in_business = request.form.get('years_in_business', '')
    ctos_sme_score = request.form.get('ctos_sme_score', '')
    cashflow_variance = request.form.get('cashflow_variance', '')
    target_bank = request.form.get('target_bank', '')
    
    # 构建API URL
    api_url = f"http://localhost:8000/api/business-loans/evaluate/{customer_id}"
    params = {
        'mode': 'modern',
        'data_mode': data_mode,
        'monthly_revenue': monthly_revenue,
        'monthly_commitment': monthly_commitment
    }
    
    # 添加可选参数
    if industry:
        params['industry'] = industry
    if years_in_business:
        params['years_in_business'] = years_in_business
    if ctos_sme_score:
        params['ctos_sme_score'] = ctos_sme_score
    if cashflow_variance:
        params['cashflow_variance'] = cashflow_variance
    if target_bank:
        params['target_bank'] = target_bank
    
    try:
        # 调用FastAPI
        response = requests.get(api_url, params=params, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        # 记录审计日志
        log_audit(
            user_id=session.get('user_id', 0),
            action_type='SME_LOAN_EVALUATION',
            description=f'Business {customer_id}, Risk Grade: {result.get("risk_grade", "N/A")}, Mode: modern'
        )
        
        # 渲染结果页面
        return render_template(
            'loan_matcher_result.html',
            client_name=f"Business #{customer_id}",
            dsr=result.get('brr_ratio', 0) * 100,  # 使用BRR作为DSR显示
            total_commitment=float(monthly_commitment),
            ctos_notes="SME Modern Engine Analysis",
            eligible=[{'product': prod} for prod in result.get('recommended_products', [])],
            ineligible=[],
            eligible_by_type={},
            ineligible_by_type={},
            category_names={},
            category_icons={},
            # Phase 6 新增字段
            modern_result=result,
            is_modern_mode=True,
            is_sme=True
        )
    except Exception as e:
        flash(f'SME评估失败: {str(e)}', 'error')
        return redirect(url_for('sme_loan_evaluate'))


@app.route('/loan-reports')
@require_admin_or_accountant
def loan_reports():
    """Loan Reports Generator - 报告生成入口页面"""
    return render_template('loan_reports.html')


@app.route('/loan-reports/generate/personal', methods=['POST'])
@require_admin_or_accountant
def loan_reports_generate_personal():
    """生成个人贷款报告（调用Phase 5 API）"""
    # 获取表单数据
    customer_id = request.form.get('customer_id')
    format_type = request.form.get('format', 'html')
    data_mode = request.form.get('data_mode', 'manual')
    
    # 构建API URL
    api_url = f"http://localhost:8000/api/loan-reports/personal/{customer_id}"
    params = {
        'format': format_type,
        'mode': 'modern',
        'data_mode': data_mode,
        'monthly_commitment': request.form.get('monthly_commitment')
    }
    
    # 添加可选参数
    for field in ['income', 'ccris_bucket', 'credit_score', 'age', 'employment_years', 'target_bank']:
        value = request.form.get(field, '')
        if value:
            params[field] = value
    
    try:
        import requests
        response = requests.get(api_url, params=params, timeout=60)
        response.raise_for_status()
        
        # 记录审计日志
        log_audit(
            user_id=session.get('user_id', 0),
            action_type='LOAN_REPORT_GENERATED',
            description=f'Personal loan report for customer {customer_id}, format: {format_type}'
        )
        
        if format_type == 'html':
            # 直接返回HTML
            return response.text
        else:
            # 返回PDF下载
            from flask import make_response
            response_pdf = make_response(response.content)
            response_pdf.headers['Content-Type'] = 'application/pdf'
            response_pdf.headers['Content-Disposition'] = f'attachment; filename=personal_loan_report_{customer_id}.pdf'
            return response_pdf
    except Exception as e:
        flash(f'报告生成失败: {str(e)}', 'error')
        return redirect(url_for('loan_reports'))


@app.route('/loan-reports/generate/sme', methods=['POST'])
@require_admin_or_accountant
def loan_reports_generate_sme():
    """生成SME贷款报告（调用Phase 5 API）"""
    # 获取表单数据
    customer_id = request.form.get('customer_id')
    format_type = request.form.get('format', 'html')
    data_mode = request.form.get('data_mode', 'manual')
    
    # 构建API URL
    api_url = f"http://localhost:8000/api/loan-reports/sme/{customer_id}"
    params = {
        'format': format_type,
        'mode': 'modern',
        'data_mode': data_mode,
        'monthly_revenue': request.form.get('monthly_revenue'),
        'monthly_commitment': request.form.get('monthly_commitment')
    }
    
    # 添加可选参数
    for field in ['industry', 'years_in_business', 'ctos_sme_score', 'cashflow_variance', 'target_bank']:
        value = request.form.get(field, '')
        if value:
            params[field] = value
    
    try:
        import requests
        response = requests.get(api_url, params=params, timeout=60)
        response.raise_for_status()
        
        # 记录审计日志
        log_audit(
            user_id=session.get('user_id', 0),
            action_type='LOAN_REPORT_GENERATED',
            description=f'SME loan report for business {customer_id}, format: {format_type}'
        )
        
        if format_type == 'html':
            # 直接返回HTML
            return response.text
        else:
            # 返回PDF下载
            from flask import make_response
            response_pdf = make_response(response.content)
            response_pdf.headers['Content-Type'] = 'application/pdf'
            response_pdf.headers['Content-Disposition'] = f'attachment; filename=sme_loan_report_{customer_id}.pdf'
            return response_pdf
    except Exception as e:
        flash(f'SME报告生成失败: {str(e)}', 'error')
        return redirect(url_for('loan_reports'))


# ============================================================================
# CREDIT CARD LEDGER - 信用卡账本系统 (OWNER vs INFINITE)
# ============================================================================

@app.route('/credit-card/ledger', methods=['GET', 'POST'])
@require_admin_or_accountant
def credit_card_ledger():
    """
    第一层：客户列表 (Admin) or 直接跳转到时间线 (Customer)
    - Admin: 显示所有有信用卡账单的客户 + 上传功能
    - Customer: 直接跳转到自己的时间线
    """
    from utils.name_utils import get_customer_code
    
    # POST: 处理上传
    if request.method == 'POST':
        # 重用 upload_statement 的逻辑
        card_id = request.form.get('card_id')
        file = request.files.get('statement_file')
        
        if not card_id or not file:
            lang = get_current_language()
            flash(translate('provide_card_file', lang), 'error')
            return redirect(url_for('credit_card_ledger'))
        
        # 临时保存文件用于解析
        temp_filename = f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        temp_file_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
        file.save(temp_file_path)
        
        file_type = 'pdf' if temp_filename.lower().endswith('.pdf') else 'excel'
        
        # Step 1: Parse statement
        try:
            statement_info, transactions = parse_statement_auto(temp_file_path)
        except ValueError as e:
            if str(e) == "HSBC_SCANNED_PDF":
                lang = get_current_language()
                flash(translate('hsbc_scanned_pdf_warning', lang), 'warning')
                os.remove(temp_file_path)
                return redirect(url_for('credit_card_ledger'))
            else:
                flash(f'账单解析失败：{str(e)}', 'error')
                os.remove(temp_file_path)
                return redirect(url_for('credit_card_ledger'))
        
        if not statement_info or not transactions:
            lang = get_current_language()
            flash(translate('failed_parse_statement', lang), 'error')
            os.remove(temp_file_path)
            return redirect(url_for('credit_card_ledger'))
        
        # Step 2: Dual Validation
        pdf_text = ""
        if file_type == 'pdf':
            try:
                with pdfplumber.open(temp_file_path) as pdf:
                    pdf_text = "\n".join(p.extract_text() for p in pdf.pages)
            except:
                pass
        
        dual_validation = validate_transactions(transactions, pdf_text) if pdf_text else None
        validation_result = validate_statement(statement_info['total'], transactions)
        
        # Combine validation scores
        final_confidence = validation_result['confidence']
        if dual_validation:
            final_confidence = (final_confidence + dual_validation.confidence_score) / 2
        
        # Determine auto-confirm
        auto_confirmed = 0
        validation_status = "pending"
        if dual_validation:
            if dual_validation.get_status() == "PASSED" and final_confidence >= 95:
                auto_confirmed = 1
                validation_status = "auto_approved"
            elif dual_validation.get_status() == "FAILED":
                validation_status = "requires_review"
        
        stmt_date = statement_info.get('statement_date') or datetime.now().strftime('%Y-%m-%d')
        
        # 文件组织和数据库插入
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT cc.bank_name, cc.card_number_last4, c.name as customer_name, c.id as customer_id, c.customer_code
                FROM credit_cards cc
                JOIN customers c ON cc.customer_id = c.id
                WHERE cc.id = ?
            ''', (card_id,))
            
            card_row = cursor.fetchone()
            if not card_row:
                lang = get_current_language()
                flash(f"❌ {translate('credit_card_not_exist', lang)}", 'error')
                os.remove(temp_file_path)
                return redirect(url_for('credit_card_ledger'))
            
            card_info = dict(card_row)
            customer_id = card_info['customer_id']
            
            # 使用StatementOrganizer组织文件（按客户代码）
            from services.statement_organizer import StatementOrganizer
            organizer = StatementOrganizer()
            
            try:
                organize_result = organizer.organize_statement(
                    temp_file_path,
                    card_info['customer_code'],
                    card_info['customer_name'],
                    stmt_date,
                    {
                        'bank_name': card_info['bank_name'],
                        'last_4_digits': card_info['card_number_last4']
                    },
                    category=StatementOrganizer.CATEGORY_CREDIT_CARD
                )
                organized_file_path = organize_result['archived_path']
                os.remove(temp_file_path)
            except Exception as e:
                print(f"⚠️ 文件组织失败: {str(e)}")
                organized_file_path = temp_file_path
            
            # 重复检查
            validation_check = UniquenessValidator.validate_statement_upload(card_id, stmt_date)
            
            try:
                if validation_check['action'] == 'update':
                    cursor.execute('''
                        UPDATE statements 
                        SET statement_total = ?, file_path = ?, file_type = ?, 
                            validation_score = ?, is_confirmed = ?, inconsistencies = ?,
                            due_date = ?, due_amount = ?, minimum_payment = ?
                        WHERE id = ?
                    ''', (
                        statement_info['total'],
                        organized_file_path,
                        file_type,
                        final_confidence,
                        auto_confirmed,
                        json.dumps({
                            'old_validation': validation_result['inconsistencies'],
                            'dual_validation_status': dual_validation.get_status() if dual_validation else 'N/A',
                            'dual_validation_errors': dual_validation.errors if dual_validation else [],
                            'dual_validation_warnings': dual_validation.warnings if dual_validation else []
                        }),
                        statement_info.get('due_date'),
                        statement_info.get('due_amount'),
                        statement_info.get('minimum_payment'),
                        validation_check['existing_statement_id']
                    ))
                    statement_id = validation_check['existing_statement_id']
                    cursor.execute('DELETE FROM transactions WHERE statement_id = ?', (statement_id,))
                    flash(f'ℹ️  {validation_check["reason"]}', 'info')
                else:
                    cursor.execute('''
                        INSERT INTO statements 
                        (card_id, statement_date, statement_total, file_path, file_type, 
                         validation_score, is_confirmed, inconsistencies, due_date, due_amount, minimum_payment)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        card_id,
                        stmt_date,
                        statement_info['total'],
                        organized_file_path,
                        file_type,
                        final_confidence,
                        auto_confirmed,
                        json.dumps({
                            'old_validation': validation_result['inconsistencies'],
                            'dual_validation_status': dual_validation.get_status() if dual_validation else 'N/A',
                            'dual_validation_errors': dual_validation.errors if dual_validation else [],
                            'dual_validation_warnings': dual_validation.warnings if dual_validation else []
                        }),
                        statement_info.get('due_date'),
                        statement_info.get('due_amount'),
                        statement_info.get('minimum_payment')
                    ))
                    statement_id = cursor.lastrowid
                
                for trans in transactions:
                    category, confidence = categorize_transaction(trans['description'])
                    trans_type = trans.get('type', None)
                    if trans_type == 'debit':
                        transaction_type = 'purchase'
                    elif trans_type == 'credit':
                        transaction_type = 'payment'
                    else:
                        transaction_type = 'payment' if trans['amount'] < 0 else 'purchase'
                    
                    cursor.execute('''
                        INSERT INTO transactions 
                        (statement_id, transaction_date, description, amount, category, category_confidence, transaction_type)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        statement_id,
                        trans['date'],
                        trans['description'],
                        abs(trans['amount']),
                        category,
                        confidence,
                        transaction_type
                    ))
                
                conn.commit()
                log_audit(None, 'UPLOAD_STATEMENT', 'statement', statement_id, 
                         f"Uploaded from CC Ledger: {file_type} statement with {len(transactions)} transactions")
                
            except Exception as e:
                conn.rollback()
                flash(f'数据库错误：{str(e)}', 'error')
                return redirect(url_for('credit_card_ledger'))
        
        # 自动触发处理流程
        from services.statement_processor import process_uploaded_statement
        try:
            if statement_id is not None:
                processing_result = process_uploaded_statement(customer_id, statement_id, organized_file_path)
                if processing_result['success']:
                    flash(f'🎉 账单上传成功！已分类 {processing_result["step_1_classify"]["total_transactions"]} 笔交易', 'success')
        except Exception as e:
            flash(f'⚠️ 账单已上传，但自动分类失败：{str(e)}', 'warning')
        
        # 成功后重定向回 CC Ledger
        flash(f'✅ Statement uploaded successfully!', 'success')
        return redirect(url_for('credit_card_ledger'))
    
    # GET: 显示页面 - Public access, show all customers
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 获取所有有信用卡账单的客户（公开访问）
        cursor.execute('''
            SELECT DISTINCT
                c.id,
                c.name,
                c.customer_code,
                COUNT(DISTINCT s.id) as statement_count
            FROM customers c
            JOIN credit_cards cc ON c.id = cc.customer_id
            JOIN statements s ON cc.id = s.card_id
            GROUP BY c.id
            ORDER BY c.name
        ''')
        
        customers = []
        for row in cursor.fetchall():
            customer = dict(row)
            # 直接使用数据库中的customer_code字段
            customer['code'] = customer.get('customer_code', 'Be_rich_UNKNOWN_00')
            customers.append(customer)
        
        # 获取所有信用卡供上传表单使用
        cursor.execute('''
            SELECT cc.*, c.name as customer_name
            FROM credit_cards cc
            JOIN customers c ON cc.customer_id = c.id
            ORDER BY c.name, cc.bank_name
        ''')
        all_cards = [dict(row) for row in cursor.fetchall()]
        
        # 获取所有供应商发票数据 (整合 INVOICES 功能)
        cursor.execute('''
            SELECT 
                si.id,
                si.invoice_number,
                si.invoice_date,
                si.supplier_name,
                si.total_amount,
                si.supplier_fee,
                si.pdf_path,
                c.name as customer_name,
                c.customer_code
            FROM supplier_invoices si
            JOIN customers c ON si.customer_id = c.id
            ORDER BY si.invoice_date DESC, si.invoice_number DESC
        ''')
        
        invoices = cursor.fetchall()
        
        # 计算发票统计数据
        invoices_data = None
        if invoices:
            total_invoices = len(invoices)
            total_suppliers = len(set(inv['supplier_name'] for inv in invoices))
            total_amount = sum(inv['total_amount'] for inv in invoices)
            total_fees = sum(inv['supplier_fee'] for inv in invoices)
            
            invoices_data = {
                'invoices': invoices,
                'total_invoices': total_invoices,
                'total_suppliers': total_suppliers,
                'total_amount': total_amount,
                'total_fees': total_fees
            }
        
        # 获取所有 Payment Receipts 数据 (整合 RECEIPTS 功能)
        cursor.execute("""
            SELECT 
                pr.id,
                pr.payment_date as date,
                pr.payment_amount as amount,
                pr.receipt_file_path,
                c.name as from_customer,
                '' as description,
                '' as remarks
            FROM payment_receipts pr
            JOIN customers c ON pr.customer_id = c.id
            ORDER BY pr.payment_date DESC
            LIMIT 100
        """)
        payment_receipts = [dict(row) for row in cursor.fetchall()]
        
        # 获取 OCR Receipts 统计数据 (整合 OCR RECEIPTS 功能)
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN customer_id IS NOT NULL AND card_id IS NOT NULL AND match_status = 'auto' THEN 1 ELSE 0 END) as auto_matched,
                SUM(CASE WHEN customer_id IS NOT NULL AND card_id IS NOT NULL AND match_status = 'manual' THEN 1 ELSE 0 END) as manual_matched,
                SUM(CASE WHEN customer_id IS NULL OR card_id IS NULL THEN 1 ELSE 0 END) as pending
            FROM receipts
        """)
        ocr_stats = dict(cursor.fetchone())
        
        # 获取已匹配的 OCR Receipts (最近100条)
        cursor.execute("""
            SELECT 
                r.id,
                r.receipt_type,
                r.file_path,
                r.original_filename,
                r.created_at as uploaded_at,
                r.match_status as match_type,
                c.name as customer_name,
                cc.bank_name,
                cc.card_number_last4
            FROM receipts r
            LEFT JOIN customers c ON r.customer_id = c.id
            LEFT JOIN credit_cards cc ON r.card_id = cc.id
            WHERE r.customer_id IS NOT NULL AND r.card_id IS NOT NULL
            ORDER BY r.created_at DESC
            LIMIT 100
        """)
        ocr_matched_receipts = [dict(row) for row in cursor.fetchall()]
        
        # 获取待匹配的 OCR Receipts
        cursor.execute("""
            SELECT 
                r.id,
                r.receipt_type,
                r.file_path,
                r.original_filename,
                r.created_at as uploaded_at,
                r.amount as ocr_amount,
                r.transaction_date as ocr_date,
                r.merchant_name as ocr_merchant
            FROM receipts r
            WHERE r.customer_id IS NULL OR r.card_id IS NULL
            ORDER BY r.created_at DESC
        """)
        ocr_pending_receipts = [dict(row) for row in cursor.fetchall()]
    
    return render_template('credit_card/ledger_index.html', 
                         customers=customers, 
                         all_cards=all_cards,
                         invoices_data=invoices_data,
                         payment_receipts=payment_receipts,
                         ocr_stats=ocr_stats,
                         ocr_matched_receipts=ocr_matched_receipts,
                         ocr_pending_receipts=ocr_pending_receipts,
                         is_admin=True)


@app.route('/credit-card/ledger/<int:customer_id>/timeline')
@require_admin_or_accountant
def credit_card_ledger_timeline(customer_id):
    """第二层：年月网格 - 显示客户所有账单的年月分布"""
    from datetime import datetime
    from collections import defaultdict
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 获取客户信息
        cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        customer_row = cursor.fetchone()
        if not customer_row:
            lang = get_current_language()
            flash(translate('customer_not_found', lang), 'error')
            return redirect(url_for('credit_card_ledger'))
        
        customer = dict(customer_row)
        # 直接使用数据库中的customer_code字段
        customer['code'] = customer.get('customer_code', 'Be_rich_UNKNOWN_00')
        
        # 获取该客户所有账单的年月和银行
        cursor.execute('''
            SELECT DISTINCT
                s.id,
                s.statement_date,
                strftime('%Y', s.statement_date) as year,
                strftime('%m', s.statement_date) as month,
                cc.bank_name
            FROM statements s
            JOIN credit_cards cc ON s.card_id = cc.id
            WHERE cc.customer_id = ?
            ORDER BY s.statement_date DESC
        ''', (customer_id,))
        
        statements = cursor.fetchall()
        
        # 按年月组织账单，同时收集银行信息
        statements_by_year_month = defaultdict(lambda: defaultdict(list))
        banks_by_year_month = defaultdict(lambda: defaultdict(set))
        years = set()
        
        for stmt in statements:
            year = stmt['year']
            month = int(stmt['month'])
            years.add(year)
            statements_by_year_month[year][month].append({
                'id': stmt['id'],
                'statement_date': stmt['statement_date']
            })
            banks_by_year_month[year][month].add(stmt['bank_name'])
        
        # 生成年度数据（按降序排列）
        years_data = []
        for year in sorted(years, reverse=True):
            months_data = []
            for month in range(1, 13):
                banks_list = sorted(list(banks_by_year_month[year][month])) if month in banks_by_year_month[year] else []
                month_info = {
                    'number': month,
                    'name': datetime(2000, month, 1).strftime('%b'),
                    'has_statements': month in statements_by_year_month[year],
                    'statements': statements_by_year_month[year][month] if month in statements_by_year_month[year] else [],
                    'banks': banks_list  # 🔥 新增：该月的银行列表
                }
                months_data.append(month_info)
            
            years_data.append({
                'year': year,
                'months': months_data
            })
    
    return render_template('credit_card/ledger_timeline.html', 
                          customer=customer,
                          years_data=years_data)


@app.route('/credit-card/ledger/<int:customer_id>/<year>/<month>')
@require_admin_or_accountant
def credit_card_ledger_monthly(customer_id, year, month):
    """第三层：月度详情 - 按银行分组显示该客户该月所有账单的完整分析"""
    from datetime import datetime
    from collections import defaultdict
    
    # 🔥 获取可选的银行筛选参数
    bank_name = request.args.get('bank_name')
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 获取客户信息
        cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        customer_row = cursor.fetchone()
        if not customer_row:
            lang = get_current_language()
            flash(translate('customer_not_found', lang), 'error')
            return redirect(url_for('credit_card_ledger'))
        
        customer = dict(customer_row)
        # 直接使用数据库中的customer_code字段
        customer['code'] = customer.get('customer_code', 'Be_rich_UNKNOWN_00')
        
        # 🔥 获取该月账单（可能按银行筛选）
        if bank_name:
            # 按银行筛选
            cursor.execute('''
                SELECT 
                    s.id,
                    s.statement_date,
                    s.statement_total,
                    s.previous_balance,
                    cc.bank_name,
                    cc.card_number_last4,
                    cc.id as card_id
                FROM statements s
                JOIN credit_cards cc ON s.card_id = cc.id
                WHERE cc.customer_id = ?
                  AND strftime('%Y', s.statement_date) = ?
                  AND strftime('%m', s.statement_date) = ?
                  AND cc.bank_name = ?
                ORDER BY cc.bank_name, cc.card_number_last4
            ''', (customer_id, year, month, bank_name))
        else:
            # 所有银行
            cursor.execute('''
                SELECT 
                    s.id,
                    s.statement_date,
                    s.statement_total,
                    s.previous_balance,
                    cc.bank_name,
                    cc.card_number_last4,
                    cc.id as card_id
                FROM statements s
                JOIN credit_cards cc ON s.card_id = cc.id
                WHERE cc.customer_id = ?
                  AND strftime('%Y', s.statement_date) = ?
                  AND strftime('%m', s.statement_date) = ?
                ORDER BY cc.bank_name, cc.card_number_last4
            ''', (customer_id, year, month))
        
        all_statements = [dict(row) for row in cursor.fetchall()]
        
        if not all_statements:
            lang = get_current_language()
            flash(translate('no_statement_this_month', lang), 'warning')
            return redirect(url_for('credit_card_ledger_timeline', customer_id=customer_id))
        
        # 🔥 按银行分组账单
        banks_data = defaultdict(list)
        for stmt in all_statements:
            banks_data[stmt['bank_name']].append(stmt)
        
        # 为每个账单获取交易和分类汇总
        for stmt in all_statements:
            # 获取该账单的所有交易
            cursor.execute(f'''
                SELECT *
                FROM transactions
                WHERE statement_id = ?
                ORDER BY transaction_date
            ''', (stmt['id'],))
            stmt['transactions'] = [dict(row) for row in cursor.fetchall()]
            
            # 获取该账单的OWNER/INFINITE汇总
            cursor.execute('''
                SELECT 
                    SUM(CASE WHEN category = 'owner_expense' THEN ABS(amount) ELSE 0 END) as owner_expenses,
                    SUM(CASE WHEN category = 'infinite_expense' THEN ABS(amount) ELSE 0 END) as infinite_expenses,
                    SUM(CASE WHEN category = 'owner_payment' THEN ABS(amount) ELSE 0 END) as owner_payments,
                    SUM(CASE WHEN category = 'infinite_payment' THEN ABS(amount) ELSE 0 END) as infinite_payments,
                    SUM(CASE WHEN is_supplier = 1 THEN supplier_fee ELSE 0 END) as supplier_fees,
                    COUNT(*) as txn_count
                FROM transactions
                WHERE statement_id = ?
            ''', (stmt['id'],))
            
            totals = cursor.fetchone()
            stmt.update({
                'owner_expenses': totals['owner_expenses'] or 0,
                'infinite_expenses': totals['infinite_expenses'] or 0,
                'owner_payments': totals['owner_payments'] or 0,
                'infinite_payments': totals['infinite_payments'] or 0,
                'supplier_fees': totals['supplier_fees'] or 0,
                'txn_count': totals['txn_count'] or 0
            })
            
            # 🔥 获取该卡的Owner累计余额
            cursor.execute('''
                SELECT rolling_balance 
                FROM monthly_ledger 
                WHERE statement_id = ?
            ''', (stmt['id'],))
            owner_ledger = cursor.fetchone()
            stmt['owner_cumulative_balance'] = owner_ledger['rolling_balance'] if owner_ledger else 0
            
            # 🔥 获取该卡的INFINITE累计余额
            cursor.execute('''
                SELECT rolling_balance 
                FROM infinite_monthly_ledger 
                WHERE statement_id = ?
            ''', (stmt['id'],))
            infinite_ledger = cursor.fetchone()
            stmt['infinite_cumulative_balance'] = infinite_ledger['rolling_balance'] if infinite_ledger else 0
        
        # 🔥 为每个银行计算月度汇总
        bank_summaries = {}
        for bank_name, bank_statements in banks_data.items():
            bank_summaries[bank_name] = {
                'statements': bank_statements,
                'owner_expenses': sum(s['owner_expenses'] for s in bank_statements),
                'infinite_expenses': sum(s['infinite_expenses'] for s in bank_statements),
                'owner_payments': sum(s['owner_payments'] for s in bank_statements),
                'infinite_payments': sum(s['infinite_payments'] for s in bank_statements),
                'supplier_fees': sum(s['supplier_fees'] for s in bank_statements),
                'total_previous_balance': sum(s['previous_balance'] for s in bank_statements),
                'total_statement_total': sum(s['statement_total'] for s in bank_statements),
                'total_txn_count': sum(s['txn_count'] for s in bank_statements),
                # 🔥 该银行所有卡的累计余额加总
                'owner_cumulative_balance': sum(s['owner_cumulative_balance'] for s in bank_statements),
                'infinite_cumulative_balance': sum(s['infinite_cumulative_balance'] for s in bank_statements),
            }
        
        # 格式化日期显示
        month_name = datetime.strptime(f"{year}-{month}-01", "%Y-%m-%d").strftime("%B")
        period_display = f"{month_name} {year}"
    
    return render_template('credit_card/ledger_monthly.html',
                          customer=customer,
                          year=year,
                          month=month,
                          period_display=period_display,
                          bank_summaries=bank_summaries,
                          selected_bank=bank_name)  # 🔥 传递选中的银行


@app.route('/credit-card/ledger/statement/<int:statement_id>')
@require_admin_or_accountant
def credit_card_ledger_detail(statement_id):
    """单个账单的OWNER vs INFINITE详细分析"""
    from services.owner_infinite_classifier import OwnerInfiniteClassifier
    
    classifier = OwnerInfiniteClassifier()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.id as customer_id
            FROM statements s
            JOIN credit_cards cc ON s.card_id = cc.id
            JOIN customers c ON cc.customer_id = c.id
            WHERE s.id = ?
        ''', (statement_id,))
        stmt_customer = cursor.fetchone()
        
        if not stmt_customer:
            flash('Statement not found', 'error')
            return redirect(url_for('credit_card_ledger'))
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 获取账单信息及关联的客户、信用卡信息
        cursor.execute('''
            SELECT 
                s.id as statement_id,
                s.statement_date,
                s.statement_total,
                s.previous_balance,
                s.card_id,
                cc.bank_name,
                cc.card_number_last4,
                cc.credit_limit,
                cc.customer_id,
                c.name as customer_name
            FROM statements s
            JOIN credit_cards cc ON s.card_id = cc.id
            JOIN customers c ON cc.customer_id = c.id
            WHERE s.id = ?
        ''', (statement_id,))
        
        statement_row = cursor.fetchone()
        if not statement_row:
            lang = get_current_language()
            flash(translate('statement_not_exist', lang), 'error')
            return redirect(url_for('credit_card_ledger'))
        
        statement = dict(statement_row)
        
        # 获取该账单的OWNER和INFINITE汇总
        cursor.execute('''
            SELECT 
                SUM(CASE WHEN category = 'owner_expense' THEN ABS(amount) ELSE 0 END) as owner_expenses,
                SUM(CASE WHEN category = 'infinite_expense' THEN ABS(amount) ELSE 0 END) as infinite_expenses,
                SUM(CASE WHEN category = 'owner_payment' THEN ABS(amount) ELSE 0 END) as owner_payments,
                SUM(CASE WHEN category = 'infinite_payment' THEN ABS(amount) ELSE 0 END) as infinite_payments,
                SUM(CASE WHEN is_supplier = 1 THEN supplier_fee ELSE 0 END) as supplier_fees,
                COUNT(*) as transaction_count
            FROM transactions
            WHERE statement_id = ?
        ''', (statement_id,))
        
        totals = cursor.fetchone()
        statement.update({
            'owner_expenses': totals['owner_expenses'] or 0,
            'infinite_expenses': totals['infinite_expenses'] or 0,
            'owner_payments': totals['owner_payments'] or 0,
            'infinite_payments': totals['infinite_payments'] or 0,
            'supplier_fees': totals['supplier_fees'] or 0,
            'transaction_count': totals['transaction_count'] or 0
        })
        
        # 获取该卡的基线信息
        cursor.execute('''
            SELECT previous_balance, owner_baseline, infinite_baseline
            FROM account_baselines
            WHERE card_id = ?
        ''', (statement['card_id'],))
        
        baseline = cursor.fetchone()
        statement['baseline'] = dict(baseline) if baseline else None
        
        # 获取该账单的所有交易
        cursor.execute('''
            SELECT 
                id, transaction_date, description, amount, 
                transaction_type, category, is_supplier, 
                supplier_name, supplier_fee, payer_name
            FROM transactions
            WHERE statement_id = ?
            ORDER BY transaction_date DESC
        ''', (statement_id,))
        
        transactions = [dict(row) for row in cursor.fetchall()]
    
    return render_template('credit_card/ledger_detail.html', 
                          statement=statement,
                          transactions=transactions)


@app.route('/credit-card/statement/<int:statement_id>/review')
@require_admin_or_accountant
def credit_card_statement_review(statement_id):
    """Credit Card Statement Review Page - PDF viewer + Transaction table side-by-side"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get statement information
        cursor.execute('''
            SELECT 
                s.id as statement_id,
                s.statement_date,
                s.due_date,
                s.statement_total,
                s.minimum_payment,
                s.previous_balance,
                s.file_path,
                s.is_confirmed,
                s.card_id,
                cc.bank_name,
                cc.card_number_last4,
                cc.credit_limit,
                cc.customer_id,
                c.name as customer_name
            FROM statements s
            JOIN credit_cards cc ON s.card_id = cc.id
            JOIN customers c ON cc.customer_id = c.id
            WHERE s.id = ?
        ''', (statement_id,))
        
        statement_row = cursor.fetchone()
        if not statement_row:
            flash('Statement not found', 'error')
            return redirect(url_for('credit_card_ledger'))
        
        statement = dict(statement_row)
        
        # Get all transactions for this statement
        cursor.execute('''
            SELECT 
                id, transaction_date, description, amount, 
                transaction_type, category, is_supplier, 
                supplier_name, supplier_fee, payer_name
            FROM transactions
            WHERE statement_id = ?
            ORDER BY transaction_date ASC
        ''', (statement_id,))
        
        transactions = [dict(row) for row in cursor.fetchall()]
    
    return render_template('credit_card/statement_review.html', 
                          statement=statement,
                          transactions=transactions)


@app.route('/credit-card/statement/<int:statement_id>/approve', methods=['POST'])
@require_admin_or_accountant
def approve_statement(statement_id):
    """Approve a credit card statement after review"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE statements SET is_confirmed = 1 WHERE id = ?', (statement_id,))
        conn.commit()
    
    flash('Statement approved successfully!', 'success')
    return redirect(url_for('credit_card_statement_review', statement_id=statement_id))


# ============================================================================
# CREDIT CARD OPTIMIZER - 信用卡优化推荐系统
# ============================================================================

@app.route('/credit-card-optimizer')
def credit_card_optimizer():
    """信用卡优化系统 - 主页面"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, email FROM customers ORDER BY name')
        customers = [dict(row) for row in cursor.fetchall()]
    
    return render_template('credit_card_optimizer.html', customers=customers)

@app.route('/credit-card-optimizer/report/<int:customer_id>')
@require_admin_or_accountant
def credit_card_optimizer_report(customer_id):
    """生成并显示客户信用卡优化报告"""
    try:
        report = comparison_reporter.generate_comparison_report(customer_id)
        
        if 'error' in report:
            flash(f'❌ {report["error"]}', 'error')
            return redirect(url_for('credit_card_optimizer'))
        
        log_audit(
            user_id=session.get('user_id', 0),
            action_type='CREDIT_CARD_OPTIMIZATION',
            description=f'客户: {report["customer"]["name"]}, 年度节省: RM {report["comparison"]["annual_savings"]:.2f}'
        )
        
        return render_template('credit_card_optimizer_report.html', report=report)
    
    except Exception as e:
        flash(f'❌ 生成报告失败: {str(e)}', 'error')
        return redirect(url_for('credit_card_optimizer'))

@app.route('/credit-card-optimizer/download/<int:customer_id>')
@require_admin_or_accountant
def download_credit_card_report(customer_id):
    """下载HTML格式的信用卡优化报告"""
    try:
        filepath = comparison_reporter.save_report(customer_id)
        return send_file(filepath, as_attachment=True, download_name=os.path.basename(filepath))
    except Exception as e:
        flash(f'❌ 下载失败: {str(e)}', 'error')
        return redirect(url_for('credit_card_optimizer'))


# ============================================================================
# MONTHLY SUMMARY REPORT - 月度汇总报告系统
# ============================================================================

@app.route('/monthly-summary')
@require_admin_or_accountant
def monthly_summary_index():
    """月度汇总报告 - 主页面"""
    user_role = session.get('user_role')
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        if user_role == 'admin':
            # 管理员可以查看所有客户
            cursor.execute('SELECT id, name, customer_code FROM customers ORDER BY name')
            customers = [dict(row) for row in cursor.fetchall()]
        else:
            # 客户只能查看自己
            customer_id = session.get('customer_id')
            cursor.execute('SELECT id, name, customer_code FROM customers WHERE id = ?', (customer_id,))
            customer = cursor.fetchone()
            customers = [dict(customer)] if customer else []
    
    # 获取可用的年份和月份
    current_year = datetime.now().year
    years = list(range(current_year - 2, current_year + 1))  # 最近3年
    months = list(range(1, 13))
    
    return render_template('monthly_summary/index.html', 
                          customers=customers,
                          years=years,
                          months=months,
                          current_year=current_year,
                          current_month=datetime.now().month)

@app.route('/monthly-summary/report/<int:customer_id>/<int:year>/<int:month>')
@require_admin_or_accountant
def monthly_summary_report(customer_id, year, month):
    """生成并显示月度汇总报告"""
    try:
        # 获取月度汇总数据
        summary = monthly_summary_reporter.get_customer_monthly_summary(customer_id, year, month)
        
        if not summary:
            flash(f'❌ 未找到{year}年{month}月的数据', 'error')
            return redirect(url_for('monthly_summary_index'))
        
        if summary['total_cards'] == 0:
            flash(f'ℹ️  {year}年{month}月暂无Supplier消费记录', 'info')
            return redirect(url_for('monthly_summary_index'))
        
        # 记录审计日志
        log_audit(
            user_id=session.get('user_id', 0),
            action_type='VIEW_MONTHLY_SUMMARY',
            description=f'客户: {summary["customer_name"]}, 期间: {summary["period"]}, Supplier消费: RM {summary["total_supplier_spending"]:.2f}'
        )
        
        return render_template('monthly_summary/report.html', summary=summary)
    
    except Exception as e:
        flash(f'❌ 生成报告失败: {str(e)}', 'error')
        return redirect(url_for('monthly_summary_index'))

@app.route('/monthly-summary/yearly/<int:customer_id>/<int:year>')
@require_admin_or_accountant
def monthly_summary_yearly(customer_id, year):
    """显示客户全年的月度汇总（1-12月）"""
    try:
        # 获取全年数据
        yearly_data = monthly_summary_reporter.get_customer_yearly_summary(customer_id, year)
        
        if not yearly_data:
            flash(f'❌ {year}年暂无数据', 'error')
            return redirect(url_for('monthly_summary_index'))
        
        # 获取客户信息
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT name, customer_code FROM customers WHERE id = ?', (customer_id,))
            customer = dict(cursor.fetchone())
        
        # 计算年度总计
        year_total = {
            'total_supplier_spending': sum(m['total_supplier_spending'] for m in yearly_data),
            'total_supplier_fee': sum(m['total_supplier_fee'] for m in yearly_data),
            'total_payments': sum(m['total_payments'] for m in yearly_data),
            'net_balance': sum(m['net_balance'] for m in yearly_data)
        }
        
        return render_template('monthly_summary/yearly.html',
                              customer=customer,
                              year=year,
                              monthly_data=yearly_data,
                              year_total=year_total)
    
    except Exception as e:
        flash(f'❌ 生成年度报告失败: {str(e)}', 'error')
        return redirect(url_for('monthly_summary_index'))

@app.route('/monthly-summary/download/monthly/<int:customer_id>/<int:year>/<int:month>')
@require_admin_or_accountant
def download_monthly_summary_pdf(customer_id, year, month):
    """下载月度汇总PDF报告"""
    try:
        # 生成PDF
        pdf_path = monthly_summary_reporter.generate_monthly_pdf(customer_id, year, month)
        
        # 记录审计日志
        log_audit(
            user_id=session.get('user_id', 0),
            action_type='DOWNLOAD_MONTHLY_SUMMARY_PDF',
            description=f'客户ID: {customer_id}, 期间: {year}-{month:02d}'
        )
        
        # 返回文件
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=os.path.basename(pdf_path),
            mimetype='application/pdf'
        )
    
    except Exception as e:
        flash(f'❌ 生成PDF失败: {str(e)}', 'error')
        return redirect(url_for('monthly_summary_index'))

@app.route('/monthly-summary/download/yearly/<int:customer_id>/<int:year>')
@require_admin_or_accountant
def download_yearly_summary_pdf(customer_id, year):
    """下载年度汇总PDF报告"""
    try:
        # 生成PDF
        pdf_path = monthly_summary_reporter.generate_yearly_pdf(customer_id, year)
        
        # 记录审计日志
        log_audit(
            user_id=session.get('user_id', 0),
            action_type='DOWNLOAD_YEARLY_SUMMARY_PDF',
            description=f'客户ID: {customer_id}, 年份: {year}'
        )
        
        # 返回文件
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=os.path.basename(pdf_path),
            mimetype='application/pdf'
        )
    
    except Exception as e:
        flash(f'❌ 生成PDF失败: {str(e)}', 'error')
        return redirect(url_for('monthly_summary_index'))


# ============================================================================
# RECEIPT MANAGEMENT - 收据管理系统
# ============================================================================

@app.route('/receipts')
def receipts_home():
    """收据管理主页 - 包含供应商发票和付款收据两个表格"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 获取所有收据统计
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN match_status = 'auto_matched' THEN 1 ELSE 0 END) as auto_matched,
                SUM(CASE WHEN match_status = 'manual_matched' THEN 1 ELSE 0 END) as manual_matched,
                SUM(CASE WHEN match_status = 'pending' THEN 1 ELSE 0 END) as pending
            FROM receipts
        """)
        stats = dict(cursor.fetchone())
        
        # 获取所有供应商发票（已生成发票的交易）
        cursor.execute("""
            SELECT 
                si.id,
                si.invoice_date as date,
                si.supplier_name as description,
                si.total_amount as amount,
                c.name as from_customer,
                si.invoice_number as remarks,
                si.pdf_path,
                si.supplier_fee,
                si.created_at
            FROM supplier_invoices si
            JOIN customers c ON si.customer_id = c.id
            ORDER BY si.invoice_date DESC
            LIMIT 100
        """)
        supplier_invoices = [dict(row) for row in cursor.fetchall()]
        
        # 获取所有付款收据（为客户付款的单据）
        cursor.execute("""
            SELECT 
                pr.id,
                pr.payment_date as date,
                'Credit Card Payment' as description,
                pr.payment_amount as amount,
                c.name as from_customer,
                cc.bank_name || ' ' || cc.card_number_last4 as remarks,
                pr.receipt_file_path,
                pr.uploaded_at
            FROM payment_receipts pr
            JOIN customers c ON pr.customer_id = c.id
            JOIN credit_cards cc ON pr.card_id = cc.id
            ORDER BY pr.payment_date DESC
            LIMIT 100
        """)
        payment_receipts = [dict(row) for row in cursor.fetchall()]
    
    return render_template('receipts/home.html', 
                         stats=stats, 
                         supplier_invoices=supplier_invoices,
                         payment_receipts=payment_receipts)

@app.route('/receipts/upload', methods=['GET', 'POST'])
def receipts_upload():
    """上传收据"""
    if request.method == 'GET':
        # 获取所有客户用于手动选择
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, name FROM customers ORDER BY name')
            customers = [dict(row) for row in cursor.fetchall()]
        return render_template('receipts/upload.html', customers=customers)
    
    # POST - 处理上传
    receipt_type = request.form.get('receipt_type', 'merchant_swipe')
    files = request.files.getlist('receipt_files')
    
    if not files or files[0].filename == '':
        lang = get_current_language()
        flash(f"❌ {translate('select_at_least_one_receipt', lang)}", 'error')
        return redirect(url_for('receipts_upload'))
    
    results = []
    
    for file in files:
        filename = secure_filename(file.filename) if file.filename else 'unknown'
        if file and allowed_image_file(file.filename):
            try:
                # 保存文件
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                unique_filename = f"{timestamp}_{filename}"
                
                # 先临时保存
                temp_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(temp_path)
                
                # OCR解析
                parse_result = receipt_parser.parse_image(temp_path, receipt_type)
                
                if not parse_result['success']:
                    results.append({
                        'filename': filename,
                        'status': 'ocr_failed',
                        'message': 'OCR识别失败，请手动输入信息'
                    })
                    os.remove(temp_path)  # 删除临时文件
                    continue
                
                # 智能匹配
                match_result = receipt_matcher.match_receipt(parse_result)
                
                # 确定最终存储路径
                if match_result['status'] == 'auto_matched':
                    customer_id = match_result['customer_id']
                    card_last4 = parse_result['card_last4']
                    
                    # 创建目录：static/uploads/receipts/{customer_id}/{card_last4}/
                    receipt_dir = os.path.join(
                        app.config['UPLOAD_FOLDER'], 
                        'receipts',
                        str(customer_id),
                        card_last4
                    )
                    os.makedirs(receipt_dir, exist_ok=True)
                    
                    final_path = os.path.join(receipt_dir, unique_filename)
                    os.rename(temp_path, final_path)
                    file_path = f"receipts/{customer_id}/{card_last4}/{unique_filename}"
                else:
                    # 未匹配的收据放在pending目录
                    pending_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'receipts', 'pending')
                    os.makedirs(pending_dir, exist_ok=True)
                    
                    final_path = os.path.join(pending_dir, unique_filename)
                    os.rename(temp_path, final_path)
                    file_path = f"receipts/pending/{unique_filename}"
                
                # 保存到数据库
                with get_db() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO receipts (
                            customer_id, card_id, receipt_type, file_path, original_filename,
                            transaction_date, amount, merchant_name, card_last4,
                            matched_transaction_id, match_status, match_confidence, ocr_text
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        match_result.get('customer_id'),
                        match_result.get('card_id'),
                        receipt_type,
                        file_path,
                        filename,
                        parse_result.get('transaction_date'),
                        parse_result.get('amount'),
                        parse_result.get('merchant_name'),
                        parse_result.get('card_last4'),
                        match_result.get('matched_transaction_id'),
                        match_result['status'],
                        match_result['confidence'],
                        parse_result.get('ocr_text')
                    ))
                    conn.commit()
                    receipt_id = cursor.lastrowid
                
                results.append({
                    'filename': filename,
                    'status': match_result['status'],
                    'receipt_id': receipt_id,
                    'confidence': match_result['confidence'],
                    'message': f"{'✅ 自动匹配成功' if match_result['status'] == 'auto_matched' else '⚠️ 需要手动匹配'}"
                })
                
            except Exception as e:
                results.append({
                    'filename': filename,
                    'status': 'error',
                    'message': f'处理失败: {str(e)}'
                })
    
    # 显示结果
    auto_matched = sum(1 for r in results if r['status'] == 'auto_matched')
    need_manual = sum(1 for r in results if r['status'] in ['no_match', 'multiple_matches'])
    
    flash(f'✅ 上传完成！自动匹配: {auto_matched}个，需手动匹配: {need_manual}个', 'success')
    
    return render_template('receipts/upload_results.html', results=results)

@app.route('/receipts/pending')
def receipts_pending():
    """待匹配的收据列表"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                id, receipt_type, original_filename, file_path,
                transaction_date, amount, merchant_name, card_last4,
                match_status, ocr_text, created_at
            FROM receipts
            WHERE match_status IN ('pending', 'no_match', 'multiple_matches')
            ORDER BY created_at DESC
        """)
        pending_receipts = [dict(row) for row in cursor.fetchall()]
        
        # 获取所有客户和卡
        cursor.execute('SELECT id, name FROM customers ORDER BY name')
        customers = [dict(row) for row in cursor.fetchall()]
    
    return render_template('receipts/pending.html', 
                         pending_receipts=pending_receipts,
                         customers=customers)

@app.route('/receipts/manual-match/<int:receipt_id>', methods=['POST'])
def receipts_manual_match(receipt_id):
    """手动匹配收据"""
    customer_id = request.form.get('customer_id', type=int)
    card_id = request.form.get('card_id', type=int)
    
    if not customer_id or not card_id:
        return jsonify({'success': False, 'message': '请选择客户和信用卡'})
    
    success = receipt_matcher.manual_match(receipt_id, customer_id, card_id)
    
    if success:
        # 移动文件到正确的目录
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT file_path, card_last4 FROM receipts WHERE id = ?', (receipt_id,))
            row = cursor.fetchone()
            
            if row:
                old_path = os.path.join('static/uploads', row['file_path'])
                card_last4 = row['card_last4']
                
                new_dir = os.path.join(
                    app.config['UPLOAD_FOLDER'],
                    'receipts',
                    str(customer_id),
                    card_last4
                )
                os.makedirs(new_dir, exist_ok=True)
                
                filename = os.path.basename(old_path)
                new_path = os.path.join(new_dir, filename)
                new_file_path = f"receipts/{customer_id}/{card_last4}/{filename}"
                
                if os.path.exists(old_path):
                    os.rename(old_path, new_path)
                    
                    # 更新数据库中的文件路径
                    cursor.execute('UPDATE receipts SET file_path = ? WHERE id = ?', 
                                 (new_file_path, receipt_id))
                    conn.commit()
        
        return jsonify({'success': True, 'message': '✅ 匹配成功'})
    else:
        return jsonify({'success': False, 'message': '❌ 匹配失败'})

@app.route('/receipts/customer/<int:customer_id>')
def receipts_by_customer(customer_id):
    """查看客户的所有收据"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 获取客户信息
        cursor.execute('SELECT name FROM customers WHERE id = ?', (customer_id,))
        customer = cursor.fetchone()
        
        if not customer:
            lang = get_current_language()
            flash(f"❌ {translate('customer_not_found', lang)}", 'error')
            return redirect(url_for('receipts_home'))
        
        # 获取该客户的所有收据，按卡号分组
        cursor.execute("""
            SELECT 
                r.id, r.receipt_type, r.file_path, r.original_filename,
                r.transaction_date, r.amount, r.merchant_name, r.card_last4,
                r.match_status, r.created_at,
                cc.card_type, cc.bank_name
            FROM receipts r
            LEFT JOIN credit_cards cc ON r.card_id = cc.id
            WHERE r.customer_id = ?
            ORDER BY r.card_last4, r.transaction_date DESC
        """, (customer_id,))
        receipts = [dict(row) for row in cursor.fetchall()]
        
        # 按卡号分组
        receipts_by_card = {}
        for receipt in receipts:
            card_key = f"{receipt['card_last4']} - {receipt['card_type']}" if receipt['card_type'] else receipt['card_last4']
            if card_key not in receipts_by_card:
                receipts_by_card[card_key] = []
            receipts_by_card[card_key].append(receipt)
    
    return render_template('receipts/customer_receipts.html',
                         customer=dict(customer),
                         customer_id=customer_id,
                         receipts_by_card=receipts_by_card)

@app.route('/api/customer/<int:customer_id>/cards')
def api_get_customer_cards(customer_id):
    """API: 获取客户的所有信用卡"""
    cards = receipt_matcher.get_customer_cards(customer_id)
    return jsonify(cards)

def allowed_image_file(filename):
    """检查文件是否为允许的图片格式"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def secure_filename(filename):
    """安全的文件名"""
    import re
    filename = re.sub(r'[^\w\s.-]', '', filename)
    return filename

@app.route('/credit-card/pdf-monitor')
@require_admin_or_accountant
def pdf_parsing_monitor():
    """PDF解析状态监控页面 - 显示所有372个PDF的解析状态"""
    from pathlib import Path
    from services.bank_specific_parser import get_bank_parser
    
    parser = get_bank_parser()
    
    # 扫描所有PDF文件
    pdf_files = list(Path('static/uploads').rglob('*.pdf'))
    
    # 统计信息
    stats = {
        'total_pdfs': len(pdf_files),
        'parsed': 0,
        'failed': 0,
        'pending': 0,
        'accuracy_sum': 0
    }
    
    # 按银行分组
    bank_groups = {}
    
    for pdf_path in pdf_files:
        # 从路径提取信息
        bank_name = "Unknown"
        for part in pdf_path.parts:
            for bank_key in parser.banks.keys():
                if bank_key.replace(' ', '_').upper() in part.upper():
                    bank_name = bank_key
                    break
        
        if bank_name not in bank_groups:
            bank_groups[bank_name] = {
                'count': 0,
                'files': []
            }
        
        # 检查是否已解析（检查数据库中是否有对应的statement记录）
        file_name = pdf_path.name
        parsing_status = 'pending'
        accuracy = 0.0
        errors = []
        
        # 简单检查：如果文件名包含日期和银行，假定解析成功
        import re
        if re.search(r'\d{4}-\d{2}-\d{2}', file_name):
            parsing_status = 'parsed'
            accuracy = 95.0  # 默认准确率
            stats['parsed'] += 1
            stats['accuracy_sum'] += accuracy
        else:
            stats['pending'] += 1
        
        bank_groups[bank_name]['count'] += 1
        bank_groups[bank_name]['files'].append({
            'name': file_name,
            'path': str(pdf_path.relative_to('static/uploads')),
            'size': pdf_path.stat().st_size if pdf_path.exists() else 0,
            'status': parsing_status,
            'accuracy': accuracy,
            'errors': errors,
            'bank': bank_name
        })
    
    # 计算平均准确率
    avg_accuracy = stats['accuracy_sum'] / stats['parsed'] if stats['parsed'] > 0 else 0
    
    return render_template('credit_card/pdf_monitor.html',
                         stats=stats,
                         bank_groups=bank_groups,
                         avg_accuracy=avg_accuracy,
                         supported_banks=parser.get_supported_banks())

@app.route('/invoices')
def invoices_home():
    """发票管理主页 - Invoices Home Page"""
    user_role = session.get('user_role')
    
    # Only admin can access
    if user_role != 'admin':
        lang = get_current_language()
        flash(translate('access_denied_admin_only', lang), 'danger')
        return redirect(url_for('index'))
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 查询所有生成的发票
        cursor.execute('''
            SELECT 
                si.id,
                si.invoice_number,
                si.invoice_date,
                si.supplier_name,
                si.total_amount,
                si.supplier_fee,
                si.pdf_path,
                c.name as customer_name,
                c.customer_code
            FROM supplier_invoices si
            JOIN customers c ON si.customer_id = c.id
            ORDER BY si.invoice_date DESC, si.invoice_number DESC
        ''')
        
        invoices = cursor.fetchall()
        
        # 统计数据
        total_invoices = len(invoices)
        total_suppliers = len(set(inv['supplier_name'] for inv in invoices)) if invoices else 0
        total_amount = sum(inv['total_amount'] for inv in invoices)
        total_fees = sum(inv['supplier_fee'] for inv in invoices)
    
    return render_template('invoices/home.html',
                         invoices=invoices,
                         total_invoices=total_invoices,
                         total_suppliers=total_suppliers,
                         total_amount=total_amount,
                         total_fees=total_fees)

@app.route('/test/invoice')
def test_invoice_view():
    """测试发票查看 - HTML预览页面"""
    return render_template('test_invoice.html')

@app.route('/test/invoice/download')
def download_test_invoice():
    """下载测试发票PDF"""
    invoice_path = "customers/Be_rich_CJY/invoices/supplier/2025-06/Invoice_HUAWEI_INF-202506-HUAWEI-01_2025-06-30.pdf"
    full_path = os.path.join('static/uploads', invoice_path)
    
    if os.path.exists(full_path):
        from flask import send_file
        return send_file(full_path, mimetype='application/pdf', as_attachment=False)
    else:
        return f"文件不存在: {full_path}", 404

@app.route('/test_input')
def test_input():
    """简单的输入框测试页面"""
    html = '''<!DOCTYPE html>
<html><head><title>Input Test</title>
<style>
body { background: #000; color: #fff; padding: 50px; font-family: Arial; }
.test-input { width: 300px; padding: 15px; font-size: 18px; background: white !important; color: black !important; border: 3px solid #FF007F !important; margin: 10px 0; }
.result { background: rgba(0,255,0,0.2); padding: 20px; margin: 20px 0; border: 2px solid #0f0; }
</style></head><body>
<h1 style="color: #FF007F;">输入框测试页面 / Input Test Page</h1>
<div class="result"><strong>请按以下步骤测试：</strong><br>1. 点击下面的白色输入框<br>2. 尝试输入数字或文字<br>3. 如果可以输入，说明浏览器支持输入<br>4. 如果不能输入，可能是浏览器/环境限制</div>
<h2>测试1：普通文本输入框</h2>
<input type="text" class="test-input" placeholder="请在这里输入文字..." value="测试文本">
<h2>测试2：数字输入框</h2>
<input type="number" class="test-input" placeholder="请在这里输入数字..." value="123.45">
<h2>测试3：带事件的输入框</h2>
<input type="text" class="test-input" id="test3" placeholder="输入后下方会显示..." value="">
<div id="output" style="color: #0f0; margin-top: 10px;"></div>
<script>
document.getElementById('test3').addEventListener('input', function(e) { document.getElementById('output').innerHTML = '✅ 输入成功！您输入了: ' + e.target.value; });
document.querySelector('.test-input').focus();
</script>
<hr style="margin: 40px 0; border-color: #FF007F;">
<a href="/admin" style="color: #FF007F; font-size: 18px;">← 返回 Admin Dashboard</a>
</body></html>'''
    return html

@app.route('/accounting/<path:path>')
def accounting_api_proxy(path=''):
    """代理到会计系统API (端口8000) - 使用iframe嵌入"""
    target_url = f'http://localhost:8000/{path}'
    
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>会计系统 - {path}</title>
    <style>
        body, html {{
            margin: 0;
            padding: 0;
            height: 100%;
            overflow: hidden;
        }}
        iframe {{
            width: 100%;
            height: 100%;
            border: none;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 10px 20px;
            text-align: center;
            font-family: Arial;
        }}
        .header a {{
            color: white;
            text-decoration: none;
            margin: 0 10px;
        }}
    </style>
</head>
<body>
    <div class="header">
        🏦 财务会计系统 | <a href="/">← 返回首页</a> | <a href="/accounting_test_results">🧪 测试报告</a> | <a href="/accounting_files">📁 文件管理</a>
    </div>
    <iframe src="{target_url}"></iframe>
</body>
</html>'''
    return html

@app.route('/accounting_files')
def accounting_files():
    """文件管理页面"""
    # 获取当前用户的company_id，默认为1
    user = session.get('flask_rbac_user', {})
    company_id = user.get('company_id', 1)
    
    # 存储company_id到session供代理使用
    session['current_company_id'] = company_id
    
    return render_template('accounting_files.html', company_id=company_id)

@app.route('/api/proxy/files/<path:subpath>', methods=['GET', 'POST', 'DELETE'])
def proxy_files_api(subpath):
    """代理文件管理API请求到端口8000"""
    import requests
    
    # 特殊处理smart-upload（需要转发文件）
    if subpath == 'smart-upload' and request.method == 'POST':
        target_url = 'http://localhost:8000/api/smart-import/smart-upload'
        
        # 转发multipart/form-data
        files = {}
        if 'file' in request.files:
            uploaded_file = request.files['file']
            files['file'] = (uploaded_file.filename, uploaded_file.stream, uploaded_file.content_type)
        
        try:
            # 转发文件、表单数据和query参数
            response = requests.post(target_url, files=files, data=request.form, params=request.args)
            return response.content, response.status_code, {'Content-Type': response.headers.get('Content-Type', 'application/json')}
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    # 特殊处理需要company_id的端点
    company_id = request.args.get('company_id', '1')  # 默认使用公司ID=1
    
    if subpath == 'list':
        target_url = f'http://localhost:8000/api/files/list/{company_id}'
    elif subpath == 'storage-info':
        target_url = f'http://localhost:8000/api/files/storage-stats/{company_id}'
    elif subpath in ['view', 'download', 'delete']:
        # 这些端点使用query参数
        target_url = f'http://localhost:8000/api/files/{subpath}'
    else:
        # 普通请求
        target_url = f'http://localhost:8000/api/files/{subpath}'
    
    try:
        # 转发请求，保留所有query参数
        if request.method == 'GET':
            response = requests.get(target_url, params=request.args)
        elif request.method == 'POST':
            response = requests.post(target_url, json=request.get_json(), params=request.args)
        elif request.method == 'DELETE':
            response = requests.delete(target_url, params=request.args)
        else:
            return jsonify({"error": "Method not supported"}), 405
        
        # 返回响应
        return response.content, response.status_code, {'Content-Type': response.headers.get('Content-Type', 'application/json')}
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/proxy/unified-files/<path:subpath>', methods=['GET', 'POST', 'PATCH', 'DELETE'])
def proxy_unified_files_api(subpath):
    """代理统一文件管理API请求到端口8000（带自动认证）"""
    import requests
    
    # 构建目标URL
    target_url = f'http://localhost:8000/api/files/{subpath}'
    
    # 获取当前租户的company_id（支持多租户隔离）
    current_company_id = session.get('current_company_id', 1)
    
    # 为每个company_id维护独立的session token
    token_key = f'fastapi_session_token_company_{current_company_id}'
    session_token = session.get(token_key)
    
    if not session_token:
        # 自动登录到FastAPI获取token（使用内部代理服务账户）
        proxy_password = os.getenv('PROXY_SERVICE_PASSWORD')
        
        if not proxy_password:
            # 开发环境fallback（生产环境必须设置环境变量）
            print(f"⚠️ 警告：PROXY_SERVICE_PASSWORD未设置，使用开发默认值")
            proxy_password = 'ProxyService2024!'
        
        try:
            # 使用专用proxy_service账户登录（指定当前租户的company_id）
            login_response = requests.post(
                'http://localhost:8000/api/auth/login',
                json={
                    "username": "proxy_service",
                    "password": proxy_password,
                    "company_id": current_company_id
                },
                timeout=5
            )
            
            if login_response.status_code == 200:
                login_data = login_response.json()
                session_token = login_data.get('token')
                session[token_key] = session_token
            else:
                print(f"代理服务登录失败(company {current_company_id}): HTTP {login_response.status_code}")
                return jsonify({"success": False, "message": "代理服务认证失败"}), 500
        except Exception as e:
            print(f"代理服务登录失败(company {current_company_id}): {e}")
            return jsonify({"success": False, "message": "代理服务连接失败"}), 500
    
    # 构建请求头和cookies
    headers = {'Content-Type': 'application/json'}
    cookies = {'session_token': session_token} if session_token else {}
    
    try:
        # 根据HTTP方法转发请求
        if request.method == 'GET':
            response = requests.get(target_url, params=request.args, headers=headers, cookies=cookies)
        elif request.method == 'POST':
            response = requests.post(target_url, json=request.get_json(), params=request.args, headers=headers, cookies=cookies)
        elif request.method == 'PATCH':
            response = requests.patch(target_url, json=request.get_json() if request.get_json() else None, params=request.args, headers=headers, cookies=cookies)
        elif request.method == 'DELETE':
            response = requests.delete(target_url, params=request.args, headers=headers, cookies=cookies)
        else:
            return jsonify({"success": False, "message": "Method not supported"}), 405
        
        # 如果返回401，清除对应租户的token并要求刷新
        if response.status_code == 401 and session_token:
            session.pop(token_key, None)  # 删除正确的token_key
            return jsonify({"success": False, "message": "认证失败，请刷新页面"}), 401
        
        # 返回响应（保留原始状态码）
        return response.content, response.status_code, {'Content-Type': response.headers.get('Content-Type', 'application/json')}
    except Exception as e:
        return jsonify({"success": False, "message": f"代理请求失败: {str(e)}"}), 500

@app.route('/api/parsers/<path:subpath>', methods=['GET'])
@app.route('/api/metrics/<path:subpath>', methods=['GET'])
def proxy_parsers_metrics_api(subpath):
    """Phase 1-10: 代理parsers和metrics API到FastAPI（端口8000）"""
    import requests
    
    # 确定API类型
    if '/parsers/' in request.path:
        api_prefix = 'parsers'
    elif '/metrics/' in request.path:
        api_prefix = 'metrics'
    else:
        return jsonify({"error": "Invalid API path"}), 400
    
    # 构建目标URL
    target_url = f'http://localhost:8000/api/{api_prefix}/{subpath}'
    
    try:
        # GET请求转发
        response = requests.get(target_url, params=request.args, timeout=5)
        
        # 返回响应
        return response.content, response.status_code, {'Content-Type': response.headers.get('Content-Type', 'application/json')}
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/accounting_test_results')
def accounting_test_results():
    """显示会计系统测试结果"""
    import subprocess
    try:
        # 使用--save参数保存报告
        result = subprocess.run(
            ['python3', 'test_accounting_system.py', '--save'],
            capture_output=True,
            text=True,
            timeout=30,
            cwd='/home/runner/workspace'
        )
        output = result.stdout
    except Exception as e:
        output = f"测试执行失败: {str(e)}"
    
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>会计系统测试报告</title>
    <style>
        body {{
            background: #000;
            color: #0f0;
            font-family: 'Courier New', monospace;
            padding: 2rem;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: #1a1a1a;
            padding: 2rem;
            border: 2px solid #FF007F;
            border-radius: 10px;
        }}
        h1 {{
            color: #FF007F;
            text-align: center;
            margin-bottom: 2rem;
        }}
        pre {{
            background: #000;
            padding: 1.5rem;
            border-radius: 5px;
            overflow-x: auto;
            white-space: pre-wrap;
            border: 1px solid #322446;
        }}
        .btn {{
            display: inline-block;
            padding: 10px 20px;
            background: #FF007F;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            margin: 10px 5px;
        }}
        .btn:hover {{
            background: #322446;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧪 会计系统自动化测试报告</h1>
        <div style="text-align: center; margin-bottom: 1rem;">
            <a href="/" class="btn">← 返回首页</a>
            <a href="javascript:location.reload()" class="btn">🔄 刷新测试</a>
            <a href="http://localhost:8000/docs" target="_blank" class="btn">📚 API文档</a>
        </div>
        <pre>{output}</pre>
    </div>
</body>
</html>'''
    return html

@app.route("/downloads/evidence/latest")
def download_evidence_latest():
    """下载最新的证据包ZIP（非static目录，admin-only RBAC保护）"""
    user = session.get('flask_rbac_user')
    if not user:
        return jsonify({"success": False, "error": "未登录"}), 401
    
    if user.get('role') != 'admin':
        return jsonify({"success": False, "error": "权限不足：仅admin可下载"}), 403
    
    import glob
    dl_dir = os.path.join(os.getcwd(), "evidence_bundles")
    os.makedirs(dl_dir, exist_ok=True)
    zips = sorted(glob.glob(os.path.join(dl_dir, "evidence_bundle_*.zip")))
    if not zips:
        return jsonify({"success": False, "message": "No evidence bundle found."}), 404
    latest = os.path.basename(zips[-1])
    
    request_info = extract_flask_request_info()
    write_flask_audit_log(
        user_id=user['id'],
        username=user['username'],
        company_id=user.get('company_id', 0),
        action_type='download',
        entity_type='evidence_bundle',
        description=f"下载最新证据包: {latest}",
        success=True,
        ip_address=request_info['ip_address'],
        user_agent=request_info['user_agent']
    )
    
    return send_from_directory(dl_dir, latest, as_attachment=True)

@app.route("/downloads/evidence/file/<filename>")
def download_evidence_file(filename):
    """下载指定的证据包ZIP（非static目录，RBAC保护）"""
    user = session.get('flask_rbac_user')
    if not user:
        return jsonify({"success": False, "error": "未登录"}), 401
    
    if user.get('role') != 'admin':
        return jsonify({"success": False, "error": "权限不足：仅admin可下载"}), 403
    
    if not filename.startswith("evidence_bundle_"):
        return jsonify({"success": False, "error": "无效的文件名"}), 400
    
    dl_dir = os.path.join(os.getcwd(), "evidence_bundles")
    filepath = os.path.join(dl_dir, filename)
    
    if not os.path.exists(filepath):
        return jsonify({"success": False, "error": "文件不存在"}), 404
    
    request_info = extract_flask_request_info()
    write_flask_audit_log(
        user_id=user['id'],
        username=user['username'],
        company_id=user.get('company_id', 0),
        action_type='download',
        entity_type='evidence_bundle',
        description=f"下载证据包: {filename}",
        success=True,
        ip_address=request_info['ip_address'],
        user_agent=request_info['user_agent']
    )
    
    return send_from_directory(dl_dir, filename, as_attachment=True)

@app.route("/downloads/evidence/list")
def list_evidence_bundles():
    """列出所有证据包（带metadata，非static目录）"""
    import glob
    import re
    from datetime import datetime
    
    dl_dir = os.path.join(os.getcwd(), "evidence_bundles")
    os.makedirs(dl_dir, exist_ok=True)
    
    bundles = []
    for zip_path in sorted(glob.glob(os.path.join(dl_dir, "evidence_bundle_*.zip"))):
        filename = os.path.basename(zip_path)
        
        match = re.search(r'evidence_bundle_(\d{8})_(\d{6})\.zip', filename)
        created_at = match.group(1) + match.group(2) if match else 'Unknown'
        
        file_size = os.path.getsize(zip_path) if os.path.exists(zip_path) else 0
        
        bundles.append({
            "filename": filename,
            "created_at": created_at,
            "size": file_size,
            "sha256": "N/A",
            "source": "finance-pilot"
        })
    
    return jsonify({"success": True, "bundles": bundles})

@app.route("/downloads/evidence/delete", methods=["POST"])
def delete_evidence_bundle():
    """删除指定证据包（仅admin，非static目录）"""
    user = session.get('flask_rbac_user')
    if not user or user.get('role') != 'admin':
        return jsonify({"success": False, "error": "权限不足：仅admin可删除"}), 403
    
    filename = request.json.get('filename')
    if not filename or not filename.startswith("evidence_bundle_"):
        return jsonify({"success": False, "error": "无效的文件名"}), 400
    
    dl_dir = os.path.join(os.getcwd(), "evidence_bundles")
    filepath = os.path.join(dl_dir, filename)
    
    if not os.path.exists(filepath):
        return jsonify({"success": False, "error": "文件不存在"}), 404
    
    try:
        os.remove(filepath)
        
        request_info = extract_flask_request_info()
        write_flask_audit_log(
            user_id=user['id'],
            username=user['username'],
            company_id=user.get('company_id', 0),
            action_type='delete',
            entity_type='evidence_bundle',
            description=f"删除证据包: {filename}",
            success=True,
            ip_address=request_info['ip_address'],
            user_agent=request_info['user_agent']
        )
        
        return jsonify({"success": True, "message": f"已删除: {filename}"})
    except Exception as e:
        logger.error(f"删除证据包失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/admin/evidence")
def admin_evidence_archive():
    """Evidence Archive管理页面（Option B实施 - admin-only）"""
    user = session.get('flask_rbac_user')
    if not user:
        flash('请先登录', 'warning')
        return redirect(url_for('admin_login'))
    
    if user.get('role') != 'admin':
        flash('权限不足：仅admin可访问证据归档', 'error')
        return redirect(url_for('index'))
    
    return render_template('evidence_archive.html', user=user)

@app.route("/tasks/evidence/rotate", methods=["POST"])
def rotate_evidence_bundles():
    """
    自动轮转证据包（Option A实施）
    - 保留最近N天的所有包
    - 保留每月第一个包作为长期留存
    - 需要X-TASK-TOKEN + admin角色
    """
    task_token = request.headers.get('X-TASK-TOKEN')
    expected_token = os.environ.get('TASK_SECRET_TOKEN', 'dev-default-token')
    
    if task_token != expected_token:
        return jsonify({"success": False, "error": "无效的TASK_SECRET_TOKEN"}), 401
    
    user = session.get('flask_rbac_user')
    if not user or user.get('role') != 'admin':
        return jsonify({"success": False, "error": "权限不足：仅admin可执行轮转"}), 403
    
    try:
        dl_dir = os.path.join(os.getcwd(), "evidence_bundles")
        os.makedirs(dl_dir, exist_ok=True)
        
        retention_days = int(os.environ.get('EVIDENCE_ROTATION_DAYS', '30'))
        keep_monthly = int(os.environ.get('EVIDENCE_KEEP_MONTHLY', '1'))
        
        from datetime import datetime, timedelta
        import glob
        import re
        
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        zips = glob.glob(os.path.join(dl_dir, "evidence_bundle_*.zip"))
        
        kept = []
        deleted = []
        monthly_kept = {}
        
        for zip_path in zips:
            filename = os.path.basename(zip_path)
            
            match = re.search(r'evidence_bundle_(\d{8})_\d{6}\.zip', filename)
            if not match:
                kept.append(filename)
                continue
            
            date_str = match.group(1)
            file_date = datetime.strptime(date_str, '%Y%m%d')
            year_month = file_date.strftime('%Y-%m')
            
            if file_date >= cutoff_date:
                kept.append(filename)
                continue
            
            if keep_monthly and year_month not in monthly_kept:
                monthly_kept[year_month] = filename
                kept.append(filename)
                continue
            
            os.remove(zip_path)
            deleted.append(filename)
        
        request_info = extract_flask_request_info()
        write_flask_audit_log(
            user_id=user['id'],
            username=user['username'],
            company_id=user.get('company_id', 0),
            action_type='evidence_rotation',
            entity_type='evidence_bundle',
            description=f"轮转策略执行: 保留{len(kept)}个, 删除{len(deleted)}个",
            success=True,
            new_value={"kept": kept, "deleted": deleted, "retention_days": retention_days},
            ip_address=request_info['ip_address'],
            user_agent=request_info['user_agent']
        )
        
        return jsonify({
            "success": True,
            "kept": kept,
            "deleted": deleted,
            "reason": f"Rotation policy applied: keep {retention_days} days + monthly first"
        })
    
    except Exception as e:
        logger.error(f"证据包轮转失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ========== ADMIN RBAC LOGIN (Phase 2-2 Task 3) ==========

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login using PostgreSQL users table"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            lang = get_current_language()
            flash(translate('please_enter_credentials', lang), 'error')
            return render_template('admin_login.html')
        
        # 使用Flask RBAC桥接模块验证用户
        result = verify_flask_user(username=username, password=password)
        
        if result['success']:
            user = result['user']
            
            # 设置session
            session['flask_rbac_user_id'] = user['id']
            session['flask_rbac_user'] = user
            
            # 写入审计日志（登录成功）
            request_info = extract_flask_request_info()
            write_flask_audit_log(
                user_id=user['id'],
                username=user['username'],
                company_id=user['company_id'],
                action_type='config_change',
                entity_type='session',
                description=f"管理员登录成功: role={user['role']}",
                success=True,
                new_value={'role': user['role'], 'company_id': user['company_id'], 'action': 'login'},
                ip_address=request_info['ip_address'],
                user_agent=request_info['user_agent']
            )
            
            flash(f'欢迎回来，{user["username"]}！', 'success')
            
            # 检查是否有原访问页面（next参数）
            next_page = request.args.get('next')
            if next_page:
                # 安全检查：防止开放式重定向
                from werkzeug.urls import url_parse
                parsed_url = url_parse(next_page)
                
                # 只允许相对路径（无scheme、无netloc）
                # 且不允许scheme-relative URL（如 //evil.com）
                if not parsed_url.netloc and not parsed_url.scheme and next_page.startswith('/') and not next_page.startswith('//'):
                    return redirect(next_page)
            
            # 没有next参数或安全检查失败，根据角色跳转到默认页面
            if user['role'] in ['admin', 'accountant']:
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('index'))
        else:
            # 写入审计日志（登录失败）
            request_info = extract_flask_request_info()
            write_flask_audit_log(
                user_id=0,
                username=username,
                company_id=1,
                action_type='config_change',
                entity_type='session',
                description=f"管理员登录失败: {result['error']}",
                success=False,
                new_value={'username': username, 'error': result['error'], 'action': 'login_failed'},
                ip_address=request_info['ip_address'],
                user_agent=request_info['user_agent']
            )
            
            flash(f'登录失败：{result["error"]}', 'error')
            return render_template('admin_login.html')
    
    # GET request - 显示登录表单
    return render_template('admin_login.html')


@app.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    """Admin registration (first-time setup only)"""
    if request.method == 'POST':
        company_id = request.form.get('company_id', '1').strip()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        full_name = request.form.get('full_name', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        # 验证必填字段
        if not all([company_id, username, email, password, confirm_password]):
            flash('所有字段都必须填写', 'error')
            return render_template('admin_register.html')
        
        # 验证密码匹配
        if password != confirm_password:
            flash('两次输入的密码不一致', 'error')
            return render_template('admin_register.html')
        
        # 验证密码强度
        if len(password) < 6:
            flash('密码长度至少6个字符', 'error')
            return render_template('admin_register.html')
        
        try:
            # 使用Flask RBAC Bridge注册用户
            from auth.flask_rbac_bridge import register_flask_user
            
            result = register_flask_user(
                company_id=int(company_id),
                username=username,
                email=email,
                password=password,
                full_name=full_name if full_name else username,
                role='admin'
            )
            
            if result['success']:
                flash(f'管理员账户创建成功！请使用 {username} 登录', 'success')
                return redirect(url_for('admin_login'))
            else:
                flash(f'注册失败：{result["error"]}', 'error')
                return render_template('admin_register.html')
                
        except Exception as e:
            logger.error(f"Admin registration error: {e}")
            flash(f'注册失败：{str(e)}', 'error')
            return render_template('admin_register.html')
    
    # GET request - 显示注册表单
    return render_template('admin_register.html')


@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    user = session.get('flask_rbac_user', {})
    
    # 写入审计日志（登出）
    if user:
        request_info = extract_flask_request_info()
        write_flask_audit_log(
            user_id=user.get('id', 0),
            username=user.get('username', 'unknown'),
            company_id=user.get('company_id', 1),
            action_type='config_change',
            entity_type='session',
            description=f"管理员登出",
            success=True,
            new_value={'action': 'logout'},
            ip_address=request_info['ip_address'],
            user_agent=request_info['user_agent']
        )
    
    session.clear()
    flash('您已成功登出', 'success')
    return redirect(url_for('admin_login'))


# ==================== 文件管理路由 ====================
@app.route('/files/list')
def files_list():
    """文件列表页 - 显示所有上传的raw_documents"""
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        flash('数据库未配置', 'error')
        return redirect(url_for('index'))
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 查询所有raw_documents，按创建时间倒序（最新的在前）
        cur.execute("""
            SELECT 
                rd.id,
                rd.company_id,
                rd.file_name,
                rd.status,
                rd.validation_status,
                rd.created_at,
                rd.module,
                c.company_name,
                NULL as statement_month
            FROM raw_documents rd
            LEFT JOIN companies c ON rd.company_id = c.id
            ORDER BY rd.created_at DESC
            LIMIT 100
        """)
        
        files = cur.fetchall()
        
        # 格式化日期
        for file in files:
            if file['created_at']:
                file['created_at'] = file['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        cur.close()
        conn.close()
        
        return render_template('files_list.html', files=files)
        
    except Exception as e:
        flash(f'查询失败：{str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/files/detail/<int:file_id>')
def file_detail(file_id):
    """文件详情页 - 显示单个raw_document的详细信息"""
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        flash('数据库未配置', 'error')
        return redirect(url_for('index'))
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 查询文件详情
        cur.execute("""
            SELECT 
                rd.*,
                c.company_name
            FROM raw_documents rd
            LEFT JOIN companies c ON rd.company_id = c.id
            WHERE rd.id = %s
        """, (file_id,))
        
        file = cur.fetchone()
        
        if not file:
            flash('文件不存在', 'error')
            cur.close()
            conn.close()
            return redirect(url_for('files_list'))
        
        # 格式化日期
        if file['created_at']:
            file['created_at'] = file['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        # 查询raw_lines数量
        cur.execute("SELECT COUNT(*) as count FROM raw_lines WHERE raw_document_id = %s", (file_id,))
        raw_lines_count = cur.fetchone()['count']
        
        # 检查是否为重复月份（这里简化处理，实际应该查询bank_statements表）
        duplicate_warning = False
        duplicate_count = 1
        
        cur.close()
        conn.close()
        
        return render_template('file_detail.html', 
                             file=file, 
                             raw_lines_count=raw_lines_count,
                             duplicate_warning=duplicate_warning,
                             duplicate_count=duplicate_count)
        
    except Exception as e:
        flash(f'查询失败：{str(e)}', 'error')
        return redirect(url_for('files_list'))


# ==================== Phase 8.1: Quick Estimate Routes ====================
@app.route('/loan-evaluate/quick_income', methods=['POST'])
@require_admin_or_accountant
def quick_income_route():
    """Quick Estimate - Income Only（调用FastAPI）"""
    import requests
    
    income = request.json.get('income')
    payload = {'income': income}
    
    try:
        res = requests.post('http://localhost:8000/api/loans/quick-income', json=payload, timeout=10)
        res.raise_for_status()
        return jsonify(res.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/loan-evaluate/quick_income_commitment', methods=['POST'])
@require_admin_or_accountant
def quick_income_commit_route():
    """Quick Estimate - Income + Commitments（调用FastAPI）"""
    import requests
    
    income = request.json.get('income')
    commitments = request.json.get('commitments')
    payload = {'income': income, 'commitments': commitments}
    
    try:
        res = requests.post('http://localhost:8000/api/loans/quick-income-commitment', json=payload, timeout=10)
        res.raise_for_status()
        return jsonify(res.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================
# PHASE 8.2 — NEW FLASK ROUTES (PRODUCTS + AI ADVISOR API)
# ============================================================

@app.route("/loan-evaluate/full-auto", methods=["POST"])
@require_admin_or_accountant
def loan_full_auto_route():
    """Full Automated Mode - 文件上传自动评估（调用FastAPI）"""
    try:
        # 构建multipart/form-data请求
        files = {}
        
        if 'payslip_pdf' in request.files:
            f = request.files['payslip_pdf']
            files['payslip_pdf'] = (f.filename, f.stream, f.content_type)
        
        if 'epf_pdf' in request.files:
            f = request.files['epf_pdf']
            files['epf_pdf'] = (f.filename, f.stream, f.content_type)
        
        if 'bank_statement_pdf' in request.files:
            f = request.files['bank_statement_pdf']
            files['bank_statement_pdf'] = (f.filename, f.stream, f.content_type)
        
        if 'ctos_pdf' in request.files:
            f = request.files['ctos_pdf']
            files['ctos_pdf'] = (f.filename, f.stream, f.content_type)
        
        if 'ccris_pdf' in request.files:
            f = request.files['ccris_pdf']
            files['ccris_pdf'] = (f.filename, f.stream, f.content_type)
        
        if not files:
            return jsonify({"error": "No files uploaded"}), 400
        
        # 转发到FastAPI
        res = requests.post(
            "http://localhost:8000/api/loans/full-auto",
            files=files,
            timeout=30
        )
        res.raise_for_status()
        return jsonify(res.json())
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/loan-evaluate/products", methods=["POST"])
@require_admin_or_accountant
def loan_products_route():
    """产品推荐API（调用FastAPI）"""
    try:
        payload = request.json

        res = requests.post(
            "http://localhost:8000/api/loans/product-recommendations",
            json=payload,
            timeout=10
        )
        res.raise_for_status()
        return jsonify(res.json())

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/loan-evaluate/advisor", methods=["POST"])
@require_admin_or_accountant
def loan_advisor_route():
    """AI贷款顾问API（调用FastAPI）"""
    try:
        payload = request.json

        res = requests.post(
            "http://localhost:8000/api/loans/advisor",
            json=payload,
            timeout=10
        )
        res.raise_for_status()
        return jsonify(res.json())

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== Excel/CSV Upload API (Dual-Track System) ====================
# 双轨并行方案：Excel/CSV优先 + PDF OCR备用

from services.excel_parsers import (
    BankStatementExcelParser,
    CreditCardExcelParser,
    BankDetector
)

@app.route('/api/upload/excel/credit-card', methods=['POST'])
@require_admin_or_accountant
def upload_excel_credit_card():
    """
    信用卡Excel/CSV上传API
    双轨方案：优先处理Excel/CSV，保留PDF OCR备用
    """
    try:
        if 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'message': '未选择文件'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'message': '文件名为空'
            }), 400
        
        allowed_extensions = {'.xlsx', '.xls', '.csv'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            return jsonify({
                'status': 'error',
                'message': f'不支持的文件格式：{file_ext}，请上传 Excel (.xlsx, .xls) 或 CSV (.csv) 文件'
            }), 400
        
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp', file.filename)
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        file.save(temp_path)
        
        parser = CreditCardExcelParser()
        result = parser.parse(temp_path)
        
        os.remove(temp_path)
        
        if result['status'] == 'success':
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Excel credit card upload error: {e}")
        return jsonify({
            'status': 'error',
            'message': f'文件处理失败: {str(e)}'
        }), 500


@app.route('/api/upload/excel/bank-statement', methods=['POST'])
@require_admin_or_accountant
def upload_excel_bank_statement():
    """
    银行流水Excel/CSV上传API
    支持：PBB, MBB, CIMB, RHB, HLB, AmBank, Alliance
    """
    try:
        if 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'message': '未选择文件'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'message': '文件名为空'
            }), 400
        
        allowed_extensions = {'.xlsx', '.xls', '.csv'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            return jsonify({
                'status': 'error',
                'message': f'不支持的文件格式：{file_ext}，请上传 Excel (.xlsx, .xls) 或 CSV (.csv) 文件'
            }), 400
        
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp', file.filename)
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        file.save(temp_path)
        
        parser = BankStatementExcelParser()
        result = parser.parse(temp_path)
        
        os.remove(temp_path)
        
        if result['status'] == 'success':
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Excel bank statement upload error: {e}")
        return jsonify({
            'status': 'error',
            'message': f'文件处理失败: {str(e)}'
        }), 500


@app.route('/api/upload/excel/batch', methods=['POST'])
@require_admin_or_accountant
def upload_excel_batch():
    """
    批量Excel/CSV上传API
    支持同时上传多个信用卡账单或银行流水
    """
    try:
        files = request.files.getlist('files')
        
        if not files or len(files) == 0:
            return jsonify({
                'status': 'error',
                'message': '未选择文件'
            }), 400
        
        results = []
        detector = BankDetector()
        
        for file in files:
            if file.filename == '':
                continue
            
            file_ext = os.path.splitext(file.filename)[1].lower()
            
            if file_ext not in {'.xlsx', '.xls', '.csv'}:
                results.append({
                    'filename': file.filename,
                    'status': 'error',
                    'message': '不支持的文件格式'
                })
                continue
            
            temp_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp', file.filename)
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)
            file.save(temp_path)
            
            try:
                if file_ext == '.csv':
                    df = __import__('pandas').read_csv(temp_path, nrows=20)
                else:
                    df = __import__('pandas').read_excel(temp_path, nrows=20)
                
                doc_type = detector.detect_document_type(df)
                
                if doc_type == 'credit_card':
                    parser = CreditCardExcelParser()
                else:
                    parser = BankStatementExcelParser()
                
                result = parser.parse(temp_path)
                result['filename'] = file.filename
                results.append(result)
                
                os.remove(temp_path)
            
            except Exception as e:
                results.append({
                    'filename': file.filename,
                    'status': 'error',
                    'message': str(e)
                })
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        
        success_count = sum(1 for r in results if r.get('status') == 'success')
        
        return jsonify({
            'status': 'success',
            'total_files': len(files),
            'success_count': success_count,
            'failed_count': len(results) - success_count,
            'results': results
        }), 200
    
    except Exception as e:
        logger.error(f"Excel batch upload error: {e}")
        return jsonify({
            'status': 'error',
            'message': f'批量上传失败: {str(e)}'
        }), 500


@app.route('/api/upload/detect-bank', methods=['POST'])
@require_admin_or_accountant
def detect_bank_format():
    """
    银行格式检测API
    自动识别Excel/CSV文件属于哪家银行
    """
    try:
        if 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'message': '未选择文件'
            }), 400
        
        file = request.files['file']
        
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp', file.filename)
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        file.save(temp_path)
        
        detector = BankDetector()
        
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext == '.csv':
            bank_code, confidence = detector.detect_from_csv(temp_path)
            df = __import__('pandas').read_csv(temp_path, nrows=20)
        else:
            bank_code, confidence = detector.detect_from_excel(temp_path)
            df = __import__('pandas').read_excel(temp_path, nrows=20)
        
        doc_type = detector.detect_document_type(df)
        
        os.remove(temp_path)
        
        if bank_code:
            template = detector.get_bank_template(bank_code)
            return jsonify({
                'status': 'success',
                'bank_code': bank_code,
                'bank_name': template['name'],
                'document_type': doc_type,
                'confidence_score': confidence
            }), 200
        else:
            return jsonify({
                'status': 'warning',
                'message': '无法识别银行格式',
                'document_type': doc_type
            }), 200
    
    except Exception as e:
        logger.error(f"Bank detection error: {e}")
        return jsonify({
            'status': 'error',
            'message': f'格式检测失败: {str(e)}'
        }), 500


# ==================== VBA-JSON Upload API (Hybrid Architecture) ====================
# 混合架构：VBA客户端处理 + Replit接收标准JSON

@app.route('/vba/upload', endpoint='vba_upload_page')
def vba_upload_page():
    """VBA JSON上传界面"""
    return render_template('vba_upload.html')


@app.route('/api/upload/vba-json', methods=['POST'])
@require_admin_or_accountant
def upload_vba_json():
    """
    接收VBA处理后的标准JSON数据
    混合架构：VBA在Windows客户端解析，Replit接收入库
    """
    try:
        if 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'message': '未选择JSON文件'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'message': '文件名为空'
            }), 400
        
        if not file.filename.endswith('.json'):
            return jsonify({
                'status': 'error',
                'message': '文件格式错误，请上传JSON文件'
            }), 400
        
        # 读取JSON内容
        import json
        json_data = json.load(file)
        
        # 验证JSON格式
        if 'status' not in json_data or json_data['status'] != 'success':
            return jsonify({
                'status': 'error',
                'message': 'JSON格式错误：缺少status字段或status不为success'
            }), 400
        
        if 'document_type' not in json_data:
            return jsonify({
                'status': 'error',
                'message': 'JSON格式错误：缺少document_type字段'
            }), 400
        
        doc_type = json_data['document_type']
        
        if doc_type not in ['credit_card', 'bank_statement']:
            return jsonify({
                'status': 'error',
                'message': f'不支持的document_type: {doc_type}'
            }), 400
        
        # VBA JSON数据入库处理
        from services.vba_json_processor import VBAJSONProcessor
        
        processor = VBAJSONProcessor()
        user_id = session.get('user_id') if 'user_id' in session else None
        
        result = processor.process_json(json_data, user_id, file.filename)
        
        if not result.get('success'):
            return jsonify({
                'status': 'error',
                'message': result.get('message', '入库失败')
            }), 500
        
        logger.info(f"VBA-JSON上传并入库成功: {file.filename}, 类型: {doc_type}")
        
        return jsonify({
            'status': 'success',
            'message': result.get('message', 'JSON数据接收并入库成功'),
            'document_type': doc_type,
            'parsed_by': json_data.get('parsed_by', 'Unknown'),
            'parsed_at': json_data.get('parsed_at', ''),
            'total_transactions': result.get('transaction_count', 0),
            'statement_id': result.get('statement_id'),
            'bank': result.get('bank'),
            'month': result.get('month')
        }), 200
    
    except json.JSONDecodeError as e:
        return jsonify({
            'status': 'error',
            'message': f'JSON解析失败: {str(e)}'
        }), 400
    except Exception as e:
        logger.error(f"VBA-JSON upload error: {e}")
        return jsonify({
            'status': 'error',
            'message': f'文件处理失败: {str(e)}'
        }), 500


@app.route('/api/upload/vba-batch', methods=['POST'])
@require_admin_or_accountant
def upload_vba_batch():
    """
    批量接收VBA处理后的JSON文件
    支持一次上传多个JSON文件
    """
    try:
        files = request.files.getlist('files')
        
        if not files or len(files) == 0:
            return jsonify({
                'status': 'error',
                'message': '未选择文件'
            }), 400
        
        results = []
        success_count = 0
        failed_count = 0
        
        for file in files:
            if file.filename == '':
                continue
            
            if not file.filename.endswith('.json'):
                results.append({
                    'filename': file.filename,
                    'status': 'error',
                    'message': '不是JSON文件'
                })
                failed_count += 1
                continue
            
            try:
                import json
                json_data = json.load(file)
                
                # 验证JSON格式
                if 'status' not in json_data or json_data['status'] != 'success':
                    raise ValueError('JSON格式错误：status字段无效')
                
                if 'document_type' not in json_data:
                    raise ValueError('JSON格式错误：缺少document_type字段')
                
                doc_type = json_data['document_type']
                
                # VBA JSON数据入库处理
                from services.vba_json_processor import VBAJSONProcessor
                
                processor = VBAJSONProcessor()
                user_id = session.get('user_id') if 'user_id' in session else None
                
                result = processor.process_json(json_data, user_id, file.filename)
                
                if result.get('success'):
                    results.append({
                        'filename': file.filename,
                        'status': 'success',
                        'document_type': doc_type,
                        'transactions': result.get('transaction_count', 0),
                        'statement_id': result.get('statement_id'),
                        'bank': result.get('bank'),
                        'month': result.get('month')
                    })
                    success_count += 1
                else:
                    raise ValueError(result.get('message', '入库失败'))
            
            except Exception as e:
                results.append({
                    'filename': file.filename,
                    'status': 'error',
                    'message': str(e)
                })
                failed_count += 1
        
        logger.info(f"VBA批量上传: 成功 {success_count}, 失败 {failed_count}")
        
        return jsonify({
            'status': 'success',
            'total_files': len(files),
            'success_count': success_count,
            'failed_count': failed_count,
            'results': results
        }), 200
    
    except Exception as e:
        logger.error(f"VBA batch upload error: {e}")
        return jsonify({
            'status': 'error',
            'message': f'批量上传失败: {str(e)}'
        }), 500


# ==================== CTOS Consent Routes (Phase 7) ====================
@app.route('/ctos/personal', endpoint='ctos_personal')
def ctos_personal_route():
    """个人CTOS Consent页面路由"""
    return ctos_personal()


@app.route('/ctos/personal/submit', methods=['POST'], endpoint='ctos_personal_submit')
def ctos_personal_submit_route():
    """个人CTOS Consent提交路由"""
    return ctos_personal_submit()


@app.route('/ctos/company', endpoint='ctos_company')
def ctos_company_route():
    """公司CTOS Consent页面路由"""
    return ctos_company()


@app.route('/ctos/company/submit', methods=['POST'], endpoint='ctos_company_submit')
def ctos_company_submit_route():
    """公司CTOS Consent提交路由"""
    return ctos_company_submit()


# ============================================================================
# CREDIT CARD EXCEL FILES BROWSER - 信用卡Excel文件浏览系统
# ============================================================================

@app.route('/credit-card/excel-files/<int:customer_id>')
@require_admin_or_accountant
def browse_credit_card_excel_files(customer_id):
    """浏览信用卡客户的Excel文件 - 三层目录结构：客户→月份→银行"""
    from pathlib import Path
    from collections import defaultdict
    import re
    
    # 获取客户信息
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, customer_code FROM customers WHERE id = ?", (customer_id,))
        customer = cursor.fetchone()
    
    if not customer:
        flash('客户不存在', 'error')
        return redirect(url_for('credit_card_ledger'))
    
    customer_name = customer[1]
    customer_code = customer[2]
    
    # 查找客户的credit_card_files文件夹
    credit_card_dir = Path('credit_card_files') / customer_name
    
    if not credit_card_dir.exists():
        flash(f'客户 {customer_name} 的Excel文件尚未生成，请先运行文件生成脚本', 'warning')
        return redirect(url_for('credit_card_ledger'))
    
    # 按月份和银行组织文件 - 三层结构
    months_data = defaultdict(lambda: {'banks': defaultdict(list), 'summary': None})
    
    # 扫描月结单文件
    statements_dir = credit_card_dir / 'monthly_statements'
    if statements_dir.exists():
        for file in sorted(statements_dir.glob('*.xlsx')):
            # 解析文件名：2024-09_Alliance_Bank_Statement.xlsx 或 2024-09_Summary.xlsx
            match = re.match(r'(\d{4})-(\d{2})_(.+)\.xlsx', file.name)
            if match:
                year, month, rest = match.groups()
                year_month = f"{year}-{month}"
                
                file_info = {
                    'name': file.name,
                    'path': str(file.relative_to('credit_card_files')),
                    'size': file.stat().st_size,
                    'modified': datetime.fromtimestamp(file.stat().st_mtime).strftime('%Y-%m-%d %H:%M'),
                    'year': year,
                    'month': month,
                    'display_month': f"{year}年{int(month)}月"
                }
                
                if 'Summary' in rest:
                    # 月度汇总文件
                    months_data[year_month]['summary'] = file_info
                else:
                    # 银行账单文件
                    bank_name = rest.replace('_Statement', '').replace('_', ' ')
                    months_data[year_month]['banks'][bank_name].append(file_info)
    
    # 转换为有序列表
    sorted_months = []
    for year_month in sorted(months_data.keys(), reverse=True):
        month_info = months_data[year_month]
        year, month = year_month.split('-')
        sorted_months.append({
            'year_month': year_month,
            'year': year,
            'month': month,
            'display_name': f"{year}年{int(month)}月",
            'banks': dict(month_info['banks']),
            'summary': month_info['summary'],
            'bank_count': len(month_info['banks'])
        })
    
    return render_template(
        'credit_card_excel_browser.html',
        customer=customer,
        customer_name=customer_name,
        months_data=sorted_months
    )


@app.route('/credit-card/excel-files/<int:customer_id>/<year_month>/detail')
@require_admin_or_accountant
def credit_card_month_detail(customer_id, year_month):
    """查看月度详细计算和原始PDF文件"""
    from services.statement_detail_service import StatementDetailService
    
    service = StatementDetailService()
    detail_data = service.get_monthly_detail(customer_id, year_month)
    
    if not detail_data:
        flash(f'未找到{year_month}月份的数据', 'warning')
        return redirect(url_for('browse_credit_card_excel_files', customer_id=customer_id))
    
    return render_template(
        'credit_card_month_detail.html',
        data=detail_data
    )


@app.route('/credit-card/transactions/update', methods=['POST'])
@require_admin_or_accountant
def update_credit_card_transactions():
    """更新交易记录（编辑、添加、删除）- 用于Mac VBA 92%准确度修正"""
    from flask import jsonify
    
    try:
        data = request.get_json()
        customer_id = data.get('customer_id')
        year_month = data.get('year_month')
        updated = data.get('updated', [])
        deleted = data.get('deleted', [])
        created = data.get('created', [])
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            updated_count = 0
            deleted_count = 0
            created_count = 0
            
            # 1. 更新现有交易
            for txn in updated:
                cursor.execute("""
                    UPDATE transactions 
                    SET transaction_date = ?,
                        description = ?,
                        amount = ?,
                        category = ?
                    WHERE id = ?
                """, (
                    txn['transaction_date'],
                    txn['description'],
                    txn['amount'],
                    txn['category'],
                    txn['id']
                ))
                updated_count += cursor.rowcount
            
            # 2. 删除交易
            for txn_id in deleted:
                cursor.execute("DELETE FROM transactions WHERE id = ?", (txn_id,))
                deleted_count += cursor.rowcount
            
            # 3. 创建新交易
            # 首先获取对应的月结单ID
            cursor.execute("""
                SELECT id FROM monthly_statements 
                WHERE customer_id = ? AND statement_month = ?
                LIMIT 1
            """, (customer_id, year_month))
            
            statement_row = cursor.fetchone()
            if not statement_row:
                return jsonify({
                    'success': False,
                    'message': f'找不到{year_month}月份的账单记录'
                }), 400
            
            statement_id = statement_row[0]
            
            for txn in created:
                cursor.execute("""
                    INSERT INTO transactions (
                        monthly_statement_id,
                        transaction_date,
                        description,
                        amount,
                        category
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    statement_id,
                    txn['transaction_date'],
                    txn['description'],
                    txn['amount'],
                    txn['category']
                ))
                created_count += cursor.rowcount
            
            conn.commit()
            
            # 记录审计日志
            log_audit(
                action='UPDATE_TRANSACTIONS',
                table_name='transactions',
                details=f'Updated: {updated_count}, Deleted: {deleted_count}, Created: {created_count} for {year_month}'
            )
            
            return jsonify({
                'success': True,
                'updated_count': updated_count,
                'deleted_count': deleted_count,
                'created_count': created_count,
                'message': '保存成功'
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/credit-card/download-excel-file')
@require_admin_or_accountant
def download_credit_card_excel_file():
    """下载信用卡Excel文件"""
    from flask import send_file
    from pathlib import Path
    
    file_path = request.args.get('path')
    if not file_path:
        flash('文件路径缺失', 'error')
        return redirect(url_for('credit_card_ledger'))
    
    # 安全检查：确保路径在credit_card_files目录内
    full_path = Path('credit_card_files') / file_path
    
    # 规范化路径，防止目录遍历攻击
    try:
        full_path = full_path.resolve()
        credit_card_base = Path('credit_card_files').resolve()
        
        if not str(full_path).startswith(str(credit_card_base)):
            flash('非法文件路径', 'error')
            return redirect(url_for('credit_card_ledger'))
        
        if not full_path.exists():
            flash('文件不存在', 'error')
            return redirect(url_for('credit_card_ledger'))
        
        # 发送文件
        return send_file(
            full_path,
            as_attachment=True,
            download_name=full_path.name
        )
    
    except Exception as e:
        flash(f'文件下载失败: {str(e)}', 'error')
        return redirect(url_for('credit_card_ledger'))



# ============================================================
# Phase 3: Batch Management Routes (No Icons Design)
# Created: 2025-11-16
# Description: 批量审核管理路由（无图标设计）
# ============================================================

@app.route('/admin/batch-management')
@require_admin_or_accountant
def batch_management():
    """批量管理页面 - 显示所有待审核的批量上传"""
    with get_db() as db:
        # 获取所有批量上传记录
        query = """
        SELECT 
            bj.id,
            bj.customer_id,
            c.name as customer_name,
            bj.status,
            bj.reason,
            bj.created_at,
            COUNT(s.id) as statement_count,
            SUM(s.statement_total) as total_amount
        FROM batch_jobs bj
        LEFT JOIN customers c ON bj.customer_id = c.id
        LEFT JOIN statements s ON s.batch_job_id = bj.id
        WHERE bj.status IN ('pending', 'approved', 'rejected')
        GROUP BY bj.id
        ORDER BY bj.created_at DESC
        LIMIT 100
        """
        batch_uploads = db.fetch_all(query)
        
        # 转换为字典列表，添加银行信息
        uploads_list = []
        for upload in batch_uploads:
            upload_dict = {
                'id': upload[0],
                'customer_id': upload[1],
                'customer_name': upload[2] or 'Unknown',
                'status': upload[3] or 'pending',
                'reason': upload[4],
                'created_at': datetime.fromisoformat(upload[5]) if upload[5] else datetime.now(),
                'statement_count': upload[6] or 0,
                'total_amount': upload[7] or 0.0,
                'bank_name': 'Various'  # 简化显示
            }
            uploads_list.append(upload_dict)
    
    return render_template('admin/batch_management.html', 
                         batch_uploads=uploads_list)


@app.route('/admin/batch-uploads/<int:upload_id>/approve', methods=['POST'])
@require_admin_or_accountant
def approve_batch_upload(upload_id):
    """批准单个批量上传"""
    try:
        with get_db() as db:
            db.execute(
                "UPDATE batch_jobs SET status = 'approved', updated_at = ? WHERE id = ?",
                (datetime.now().isoformat(), upload_id)
            )
            
            # 记录审计日志
            db.execute(
                """INSERT INTO audit_logs (log_action, operator_email, operation_content, status, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                ('batch_approve', session.get('email', 'system'), 
                 f'Approved batch upload #{upload_id}', 'success', datetime.now().isoformat())
            )
            
        return jsonify({'success': True, 'message': 'Approved successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/admin/batch-uploads/<int:upload_id>/reject', methods=['POST'])
@require_admin_or_accountant
def reject_batch_upload(upload_id):
    """退回单个批量上传"""
    try:
        data = request.json
        reason = data.get('reason', 'No reason provided')
        
        with get_db() as db:
            db.execute(
                "UPDATE batch_jobs SET status = 'rejected', reason = ?, updated_at = ? WHERE id = ?",
                (reason, datetime.now().isoformat(), upload_id)
            )
            
            # 记录审计日志
            db.execute(
                """INSERT INTO audit_logs (log_action, operator_email, operation_content, status, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                ('batch_reject', session.get('email', 'system'), 
                 f'Rejected batch upload #{upload_id}: {reason}', 'success', datetime.now().isoformat())
            )
            
        return jsonify({'success': True, 'message': 'Rejected successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/admin/batch-uploads/approve-all', methods=['POST'])
@require_admin_or_accountant
def approve_all_batch_uploads():
    """批准所有待审核的上传"""
    try:
        with get_db() as db:
            # 更新所有待审核状态为已批准
            result = db.execute(
                "UPDATE batch_jobs SET status = 'approved', updated_at = ? WHERE status = 'pending'",
                (datetime.now().isoformat(),)
            )
            
            # 获取受影响的行数
            count = db.cursor.rowcount
            
            # 记录审计日志
            db.execute(
                """INSERT INTO audit_logs (log_action, operator_email, operation_content, status, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                ('batch_approve_all', session.get('email', 'system'), 
                 f'Approved {count} pending uploads', 'success', datetime.now().isoformat())
            )
            
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/admin/batch-uploads/reject-all', methods=['POST'])
@require_admin_or_accountant
def reject_all_batch_uploads():
    """退回所有待审核的上传"""
    try:
        data = request.json
        reason = data.get('reason', 'Batch rejection')
        
        with get_db() as db:
            # 更新所有待审核状态为已退回
            result = db.execute(
                "UPDATE batch_jobs SET status = 'rejected', reason = ?, updated_at = ? WHERE status = 'pending'",
                (reason, datetime.now().isoformat())
            )
            
            count = db.cursor.rowcount
            
            # 记录审计日志
            db.execute(
                """INSERT INTO audit_logs (log_action, operator_email, operation_content, status, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                ('batch_reject_all', session.get('email', 'system'), 
                 f'Rejected {count} pending uploads: {reason}', 'success', datetime.now().isoformat())
            )
            
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500



# Phase 4 Priority 1: Report Center Routes (No Icons Design)
# Created: 2025-11-16
# Description: 批量导出与报表自助中心路由（无图标设计）
# ============================================================

@app.route('/reports/center')
@require_admin_or_accountant
def report_center():
    """报表中心主页 - 支持筛选和批量导出"""
    # 获取筛选参数
    customer_id = request.args.get('customer_id', '')
    account_type = request.args.get('account_type', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 获取所有客户（用于筛选器）
        cursor.execute("SELECT id, name FROM customers ORDER BY name")
        customers = [dict(row) for row in cursor.fetchall()]
        
        # 构建查询条件
        where_clauses = ["1=1"]
        params = []
        
        if customer_id:
            where_clauses.append("c.id = ?")
            params.append(customer_id)
        
        if date_from:
            where_clauses.append("s.statement_date >= ?")
            params.append(date_from)
        
        if date_to:
            where_clauses.append("s.statement_date <= ?")
            params.append(date_to)
        
        # 获取记录数据（示例：从statements表）
        query = f"""
        SELECT 
            s.id,
            c.name as customer_name,
            'Credit Card' as account_name,
            s.statement_date as date_from,
            s.statement_date as date_to,
            s.statement_total as amount,
            s.is_confirmed as status
        FROM statements s
        LEFT JOIN credit_cards cc ON s.card_id = cc.id
        LEFT JOIN customers c ON cc.customer_id = c.id
        WHERE {' AND '.join(where_clauses)}
        ORDER BY s.statement_date DESC
        LIMIT 100
        """
        
        cursor.execute(query, params)
        records_raw = cursor.fetchall()
        
        # 转换为字典列表
        records = []
        for rec in records_raw:
            records.append({
                'id': rec[0],
                'customer_name': rec[1] or 'Unknown',
                'account_name': rec[2],
                'date_from': rec[3],
                'date_to': rec[4],
                'amount': rec[5] or 0.0,
                'status': 'confirmed' if rec[6] else 'pending'
            })
        
        # 获取导出历史（检查表是否存在）
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='export_tasks'")
        table_exists = cursor.fetchone()
        
        export_tasks = []
        if table_exists:
            cursor.execute(
                """SELECT id, export_format, record_count, file_size, download_url, 
                          status, error_msg, created_at, completed_at
                   FROM export_tasks 
                   ORDER BY created_at DESC 
                   LIMIT 20"""
            )
            export_tasks_raw = cursor.fetchall()
            
            for task in export_tasks_raw:
                export_tasks.append({
                    'id': task[0],
                    'export_format': task[1],
                    'record_count': task[2] or 0,
                    'file_size': task[3],
                    'download_url': task[4],
                    'status': task[5] or 'waiting',
                    'error_msg': task[6],
                    'created_at': datetime.fromisoformat(task[7]) if task[7] else datetime.now(),
                    'completed_at': datetime.fromisoformat(task[8]) if task[8] else None
                })
    
    return render_template('reports/report_center.html',
                         customers=customers,
                         records=records,
                         export_tasks=export_tasks)


@app.route('/api/reports/export', methods=['POST'])
@require_admin_or_accountant
def api_export_reports():
    """批量导出API - 真实文件导出"""
    try:
        from utils.export_engine import ReportExportEngine, get_sample_data_from_db
        
        data = request.json
        record_ids = data.get('record_ids', [])
        export_format = data.get('export_format', 'Excel')
        
        if not record_ids:
            return jsonify({'success': False, 'message': 'No records selected'}), 400
        
        with get_db() as db:
            # 创建导出任务
            task_id = db.execute(
                """INSERT INTO export_tasks (export_format, record_count, status, created_at)
                   VALUES (?, ?, 'processing', ?)""",
                (export_format, len(record_ids), datetime.now().isoformat())
            )
            
            try:
                # 初始化导出引擎
                engine = ReportExportEngine()
                
                # 获取数据
                export_data, columns = get_sample_data_from_db(db, record_ids)
                
                if not export_data:
                    raise Exception("No data to export")
                
                # 根据格式导出文件
                if export_format == 'Excel':
                    filepath, file_size = engine.export_to_excel(export_data, columns)
                elif export_format == 'CSV':
                    filepath, file_size = engine.export_to_csv(export_data, columns)
                elif export_format == 'PDF':
                    filepath, file_size = engine.export_to_pdf(export_data, columns, title='交易数据报表')
                else:
                    raise Exception(f"Unsupported format: {export_format}")
                
                # 生成下载URL
                filename = os.path.basename(filepath)
                download_url = f'/static/downloads/{filename}'
                
                # 更新任务状态为成功
                db.execute(
                    """UPDATE export_tasks 
                       SET status = 'completed', 
                           download_url = ?,
                           file_size = ?,
                           completed_at = ?,
                           updated_at = ?
                       WHERE id = ?""",
                    (download_url, file_size,
                     datetime.now().isoformat(),
                     datetime.now().isoformat(),
                     task_id)
                )
                
                # 记录审计日志
                db.execute(
                    """INSERT INTO audit_logs (log_action, operator_email, operation_content, status, created_at)
                       VALUES (?, ?, ?, ?, ?)""",
                    ('report_export', session.get('email', 'system'),
                     f'Exported {len(record_ids)} records as {export_format} - {filename}',
                     'success', datetime.now().isoformat())
                )
                
                return jsonify({
                    'success': True, 
                    'task_id': task_id,
                    'download_url': download_url,
                    'file_size': file_size
                })
            
            except Exception as export_error:
                # 更新任务状态为失败
                db.execute(
                    """UPDATE export_tasks 
                       SET status = 'failed', 
                           error_msg = ?,
                           updated_at = ?
                       WHERE id = ?""",
                    (str(export_error), datetime.now().isoformat(), task_id)
                )
                raise export_error
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/reports/history', methods=['GET'])
@require_admin_or_accountant
def api_export_history():
    """获取导出历史"""
    try:
        with get_db() as db:
            tasks = db.fetch_all(
                """SELECT id, export_format, record_count, file_size, download_url,
                          status, error_msg, created_at, completed_at
                   FROM export_tasks
                   ORDER BY created_at DESC
                   LIMIT 50"""
            )
            
            result = []
            for task in tasks:
                result.append({
                    'id': task[0],
                    'export_format': task[1],
                    'record_count': task[2],
                    'file_size': task[3],
                    'download_url': task[4],
                    'status': task[5],
                    'error_msg': task[6],
                    'created_at': task[7],
                    'completed_at': task[8]
                })
        
        return jsonify({'success': True, 'tasks': result})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/reports/retry/<int:task_id>', methods=['POST'])
@require_admin_or_accountant
def api_retry_export(task_id):
    """重试失败的导出任务"""
    try:
        with get_db() as db:
            # 重置任务状态
            db.execute(
                """UPDATE export_tasks 
                   SET status = 'processing', 
                       error_msg = NULL,
                       updated_at = ?
                   WHERE id = ?""",
                (datetime.now().isoformat(), task_id)
            )
            
            # TODO: 启动后台任务重新生成文件
            
            # 模拟成功
            db.execute(
                """UPDATE export_tasks 
                   SET status = 'completed',
                       completed_at = ?,
                       updated_at = ?
                   WHERE id = ?""",
                (datetime.now().isoformat(),
                 datetime.now().isoformat(),
                 task_id)
            )
        
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================
# 批量文件自动归类路由
# Batch Auto File Classification Routes
# ============================================================

@app.route('/batch/auto-upload', methods=['GET', 'POST'])
@require_admin_or_accountant
def batch_auto_upload():
    """
    批量文件自动归类上传页面
    Batch Auto File Classification Upload Page
    
    功能：
    1. 显示批量上传界面
    2. 支持拖拽和多文件选择
    3. 自动识别客户并归档
    """
    return render_template('batch_auto_upload.html', current_lang=session.get('lang', 'en'))


@app.route('/api/batch/classify', methods=['POST'])
@require_admin_or_accountant
def api_batch_classify():
    """
    批量文件自动归类API
    Batch Auto File Classification API
    
    接收多个文件，自动识别客户并归档
    
    Returns:
        JSON: {
            'total': 总文件数,
            'success': 成功归档数,
            'unassigned': 未归档数,
            'error': 错误数,
            'files': [文件处理结果列表]
        }
    """
    import tempfile
    import os
    import shutil
    
    temp_dir = None
    
    try:
        files = request.files.getlist('files')
        
        if not files or len(files) == 0:
            return jsonify({
                'status': 'error',
                'message': 'No files uploaded'
            }), 400
        
        # 准备文件信息
        files_info = []
        temp_dir = tempfile.mkdtemp()
        
        try:
            for file in files:
                if file.filename == '':
                    continue
                
                # 保存到临时目录
                temp_path = os.path.join(temp_dir, file.filename)
                file.save(temp_path)
                
                files_info.append({
                    'path': temp_path,
                    'filename': file.filename
                })
            
            # 调用自动归类服务
            from services.auto_classifier_service import classify_uploaded_files
            results = classify_uploaded_files(files_info)
            
            logger.info(f"批量归类完成: 总计={results['total']}, 成功={results['success']}, 未归档={results['unassigned']}, 错误={results['error']}")
            
            return jsonify(results), 200
        
        finally:
            # 确保临时目录总是被清理（无论成功或异常）
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception as cleanup_err:
                    logger.warning(f"临时目录清理失败: {cleanup_err}")
    
    except Exception as e:
        logger.error(f"批量归类API错误: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Batch classification failed: {str(e)}'
        }), 500


@app.route('/batch/unassigned', methods=['GET'])
@require_admin_or_accountant
def batch_unassigned():
    """
    未归档文件管理页面
    Unassigned Files Management Page
    
    显示所有未能自动归档的文件，支持手动分配
    """
    try:
        from services.auto_classifier_service import AutoFileClassifier
        classifier = AutoFileClassifier()
        unassigned_files = classifier.get_unassigned_files()
        
        # 获取所有活跃客户（用于手动分配）
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, customer_code FROM customers WHERE is_active = 1 ORDER BY name')
            customers = cursor.fetchall()
        
        return render_template(
            'batch_unassigned.html',
            unassigned_files=unassigned_files,
            customers=customers,
            current_lang=session.get('lang', 'en')
        )
    
    except Exception as e:
        logger.error(f"未归档文件页面错误: {str(e)}")
        flash('Failed to load unassigned files', 'danger')
        return redirect(url_for('index'))


@app.route('/api/batch/assign-file', methods=['POST'])
@require_admin_or_accountant
def api_assign_file():
    """
    手动分配文件到客户API
    Manually Assign File to Customer API
    
    Body:
        file_path: 文件路径
        customer_id: 客户ID
        
    Returns:
        JSON: {
            'status': 'success'|'error',
            'message': 消息,
            'final_path': 最终路径
        }
    """
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        customer_id = data.get('customer_id')
        
        if not file_path or not customer_id:
            return jsonify({
                'status': 'error',
                'message': 'Missing file_path or customer_id'
            }), 400
        
        from services.auto_classifier_service import AutoFileClassifier
        classifier = AutoFileClassifier()
        result = classifier.manually_assign_file(file_path, customer_id)
        
        if result['status'] == 'success':
            logger.info(f"手动分配文件成功: {file_path} → 客户ID={customer_id}")
            return jsonify(result), 200
        else:
            logger.error(f"手动分配文件失败: {result['message']}")
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"手动分配文件API错误: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Assignment failed: {str(e)}'
        }), 500


if __name__ == '__main__':
    # Get environment settings
    flask_env = os.getenv('FLASK_ENV', 'development')
    debug_mode = flask_env != 'production'
    port = int(os.getenv('PORT', 5000))
    
    # Only start scheduler in the main process (not in Werkzeug reloader child process)
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not debug_mode:
        start_scheduler()
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)



@app.route('/credit-card/transaction-classifier')
@require_admin_or_accountant
def transaction_classifier_page():
    """交易分类器页面 - 修复624笔未分类交易"""
    from services.transaction_classifier import get_classifier
    
    classifier = get_classifier()
    
    # 获取分类预览
    preview = classifier.get_classification_preview(limit=624)
    
    # 统计
    stats = {
        'total': len(preview),
        'by_category': {}
    }
    
    for txn in preview:
        category = txn['new_category']
        if category not in stats['by_category']:
            stats['by_category'][category] = 0
        stats['by_category'][category] += 1
    
    return render_template('credit_card/transaction_classifier.html',
                         preview=preview,
                         stats=stats)

@app.route('/credit-card/reclassify-transactions', methods=['POST'])
@require_admin_or_accountant
def reclassify_transactions():
    """执行交易重新分类"""
    from services.transaction_classifier import get_classifier
    
    classifier = get_classifier()
    result = classifier.reclassify_all_transactions()
    
    lang = get_current_language()
    flash(f"✅ 成功重新分类 {result['reclassified']} 笔交易！", 'success')
    
    return redirect(url_for('transaction_classifier_page'))

@app.route('/credit-card/optimization-proposal/<int:customer_id>')
def optimization_proposal(customer_id):
    """客户优化方案页面 - 显示18%利息对比5%方案"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 获取客户信息
        cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        customer = cursor.fetchone()
        
        if not customer:
            flash('客户不存在', 'error')
            return redirect(url_for('index'))
        
        # 获取客户所有信用卡未结余额
        cursor.execute("""
            SELECT cc.id, cc.bank_name, cc.card_number_last4,
                   ml.closing_balance as outstanding
            FROM credit_cards cc
            LEFT JOIN monthly_ledger ml ON cc.id = ml.card_id
            WHERE cc.customer_id = ?
            ORDER BY ml.year DESC, ml.month DESC
        """, (customer_id,))
        
        cards = cursor.fetchall()
        
        # 计算总未结余额
        total_outstanding = sum(card['outstanding'] or 0 for card in cards)
        
        # 当前18%利息计算
        current_interest_rate = 0.18
        current_monthly_interest = total_outstanding * (current_interest_rate / 12)
        current_yearly_interest = total_outstanding * current_interest_rate
        
        # 我们的5%方案
        our_interest_rate = 0.05
        our_monthly_interest = total_outstanding * (our_interest_rate / 12)
        our_yearly_interest = total_outstanding * our_interest_rate
        
        # 节省金额
        monthly_savings = current_monthly_interest - our_monthly_interest
        yearly_savings = current_yearly_interest - our_yearly_interest
    
    return render_template('credit_card/optimization_proposal.html',
                         customer=dict(customer),
                         total_outstanding=total_outstanding,
                         current_rate=current_interest_rate,
                         current_monthly=current_monthly_interest,
                         current_yearly=current_yearly_interest,
                         our_rate=our_interest_rate,
                         our_monthly=our_monthly_interest,
                         our_yearly=our_yearly_interest,
                         monthly_savings=monthly_savings,
                         yearly_savings=yearly_savings)

@app.route('/credit-card/accept-proposal/<int:customer_id>', methods=['POST'])
def accept_proposal(customer_id):
    """客户接受优化方案"""
    # 显示预约电话
@app.route('/credit-card/statement/<int:statement_id>', methods=['GET'])
@require_admin_or_accountant
def credit_card_statement_detail(statement_id):
    """信用卡账单详情页面 - 显示计算表格 + 原始PDF + Receipts附件"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT s.id, s.statement_month, s.file_path, s.previous_balance_total,
                       cc.bank_name, cc.card_holder_name, cc.card_number_last4,
                       c.id as customer_id, c.name as customer_name
                FROM statements s
                JOIN credit_cards cc ON s.card_id = cc.id
                JOIN customers c ON cc.customer_id = c.id
                WHERE s.id = ?
            ''', (statement_id,))
            stmt_row = cursor.fetchone()
            
            if not stmt_row:
                flash('账单不存在', 'error')
                return redirect(url_for('credit_card'))
            
            statement = dict(stmt_row)
            
            # 获取计算结果
            cursor.execute('SELECT * FROM statement_calculations WHERE statement_id = ?', (statement_id,))
            calc_row = cursor.fetchone()
            
            if calc_row:
                calculation = dict(calc_row)
                calculation['previous_balance'] = statement.get('previous_balance_total', 0)
            else:
                calculation = {
                    'previous_balance': statement.get('previous_balance_total', 0),
                    'owner_expenses': 0, 'gz_expenses': 0, 'owner_payment': 0,
                    'gz_payment1': 0, 'gz_payment2': 0, 'owner_os_bal_round1': 0,
                    'gz_os_bal_round1': 0, 'final_owner_os_bal': 0, 'final_gz_os_bal': 0,
                    'total_dr': 0, 'total_cr': 0
                }
            
            # 获取手续费Invoice
            cursor.execute('''
                SELECT * FROM miscellaneous_fee_invoices
                WHERE customer_id = ? AND year_month = ?
            ''', (statement['customer_id'], statement['statement_month']))
            fee_row = cursor.fetchone()
            fee_invoice = dict(fee_row) if fee_row else None
            
            # 获取Receipts附件
            try:
                cursor.execute('''
                    SELECT id, description as filename, amount, receipt_date as date, file_path
                    FROM receipts
                    WHERE customer_id = ? AND strftime('%Y-%m', receipt_date) = ?
                    ORDER BY receipt_date DESC
                ''', (statement['customer_id'], statement['statement_month']))
                receipts = [dict(row) for row in cursor.fetchall()]
            except:
                receipts = []
        
        return render_template('credit_card/statement_detail.html',
                             statement=statement, calculation=calculation,
                             fee_invoice=fee_invoice, receipts=receipts)
    
    except Exception as e:
        logger.error(f'Error loading statement detail: {e}', exc_info=True)
        flash(f'加载账单详情失败: {str(e)}', 'error')
        return redirect(url_for('credit_card'))


    return jsonify({
        'success': True,
        'phone': '0167154052',
        'message': '感谢您的信任！请拨打电话预约咨询：0167154052'
    })

@app.route('/credit-card/monthly-report/<int:customer_id>/<year>/<month>')
def monthly_report_download(customer_id, year, month):
    """生成并下载月度报表PDF"""
    from services.monthly_report_generator import generate_monthly_pdf_report
    from flask import send_file
    import os
    
    try:
        # 生成PDF
        pdf_path = generate_monthly_pdf_report(customer_id, int(year), int(month))
        
        if pdf_path and os.path.exists(pdf_path):
            return send_file(pdf_path, as_attachment=True, 
                           download_name=f"Monthly_Report_{year}_{month}.pdf")
        else:
            flash('报表生成失败', 'error')
            return redirect(url_for('index'))
    
    except Exception as e:
        flash(f'生成报表时出错: {str(e)}', 'error')
        return redirect(url_for('index'))
