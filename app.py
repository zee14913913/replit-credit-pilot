from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, session
import os
from datetime import datetime, timedelta
import json
import threading
import time
import schedule
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from db.database import get_db, log_audit, get_all_customers, get_customer, get_customer_cards, get_card_statements, get_statement_transactions
from utils.auth_decorators import login_required, admin_required, customer_access_required, get_accessible_customers
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

# Admin Portfolio Management
from admin.portfolio_manager import PortfolioManager

# Dashboard Metrics Service
from services.dashboard_metrics import get_customer_monthly_metrics, get_all_cards_summary

# Business Plan AI Service
from services.business_plan_ai import generate_business_plan

# Credit Card Recommendation Services
from modules.recommendations.card_recommendation_engine import CardRecommendationEngine
from modules.recommendations.comparison_report_generator import ComparisonReportGenerator
from modules.recommendations.benefit_calculator import BenefitCalculator

# Receipt Management Services
from ingest.receipt_parser import ReceiptParser
from services.receipt_matcher import ReceiptMatcher

# Initialize services
export_service = ExportService()
search_service = SearchService()
batch_service = BatchService()
# Removed: budget_service initialization (feature deleted)
email_service = EmailService()
tag_service = TagService()
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
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable static file caching

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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
@app.context_processor
def inject_language():
    """Inject language into all templates"""
    lang = session.get('language', 'en')
    return {
        'current_lang': lang,
        't': lambda key, **kwargs: translate(key, lang, **kwargs)
    }

@app.route('/set-language/<lang>')
def set_language(lang):
    """Set user language preference"""
    if lang in ['en', 'zh']:
        session['language'] = lang
    return redirect(request.referrer or url_for('index'))

@app.route('/view_statement_file/<int:statement_id>')
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
@login_required
def index():
    """
    Dashboard - Admin sees all customers, Customer redirected to portal
    - Admin: Show all customers
    - Customer: Redirect to customer portal
    """
    user_role = session.get('user_role')
    
    # SECURITY FIX: Use single trusted user_role source
    if user_role == 'admin':
        # Admin: show all customers
        customers = get_all_customers()
        return render_template('index.html', customers=customers)
    elif user_role == 'customer':
        # Customer: redirect to portal
        customer_id = session.get('customer_id')
        if customer_id:
            return redirect(url_for('customer_portal'))
        else:
            flash('Customer ID not found', 'error')
            return redirect(url_for('customer_login'))
    else:
        # Unknown role: redirect to login
        flash('Please login first', 'warning')
        return redirect(url_for('customer_login'))

@app.route('/add_customer_page')
@admin_required
def add_customer_page():
    """Show add customer form page - Admin only"""
    return render_template('add_customer.html')

@app.route('/add_customer', methods=['POST'])
@admin_required
def add_customer():
    """Admin: Add a new customer"""
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        monthly_income = float(request.form.get('monthly_income', 0))
        
        if not all([name, email, phone]):
            flash('All fields are required', 'error')
            return redirect(url_for('index'))
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Check if email already exists
            cursor.execute("SELECT id FROM customers WHERE email = ?", (email,))
            if cursor.fetchone():
                flash(f'Customer with email {email} already exists', 'error')
                return redirect(url_for('index'))
            
            # 自动生成customer_code（简化版，无序号）
            def generate_customer_code(name):
                """生成客户代码：Be_rich_{首字母缩写}"""
                words = name.upper().split()
                initials = ''.join([word[0] for word in words if word])
                return f"Be_rich_{initials}"
            
            customer_code = generate_customer_code(name)
            
            # Insert new customer with customer_code
            cursor.execute("""
                INSERT INTO customers (name, email, phone, monthly_income, customer_code)
                VALUES (?, ?, ?, ?, ?)
            """, (name, email, phone, monthly_income, customer_code))
            
            customer_id = cursor.lastrowid
            conn.commit()
            
            flash(f'Customer {name} ({customer_code}) added successfully! They can now register and login using {email}', 'success')
            return redirect(url_for('customer_dashboard', customer_id=customer_id))
            
    except Exception as e:
        flash(f'Error adding customer: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/customer/<int:customer_id>')
@login_required
@customer_access_required
def customer_dashboard(customer_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        customer_row = cursor.fetchone()
        customer = dict(customer_row) if customer_row else None
    
    if not customer:
        flash('Customer not found', 'error')
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
@login_required
@customer_access_required
def add_credit_card(customer_id):
    """添加信用卡"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        customer = cursor.fetchone()
        
        if not customer:
            flash('客户不存在', 'error')
            return redirect(url_for('index'))
        
        if request.method == 'POST':
            bank_name = request.form.get('bank_name')
            card_number_last4 = request.form.get('card_number_last4')
            credit_limit = int(float(request.form.get('credit_limit', 0)))
            due_date_str = request.form.get('due_date')
            
            # 验证必填字段
            if not all([bank_name, card_number_last4, due_date_str]):
                flash('请填写所有必填字段', 'error')
                return redirect(request.url)
            
            # 验证卡号后四位
            if not card_number_last4 or not card_number_last4.isdigit() or len(card_number_last4) != 4:
                flash('卡号后四位必须是4位数字', 'error')
                return redirect(request.url)
            
            # 转换due_date
            try:
                due_date = int(due_date_str) if due_date_str else 0
                if due_date == 0:
                    raise ValueError("Invalid due date")
            except (ValueError, TypeError):
                flash('还款日期必须是数字', 'error')
                return redirect(request.url)
            
            # ✅ 强制性唯一性检查（大小写无关，去除空格）
            card_id, is_new = UniquenessValidator.get_or_create_credit_card(
                customer_id, bank_name, card_number_last4, credit_limit
            )
            
            if not is_new:
                flash(f'⚠️ 该信用卡已存在：{bank_name} ****{card_number_last4}（卡ID: {card_id}）', 'error')
                return redirect(request.url)
            
            # 更新due_date（get_or_create不包含此字段）
            cursor.execute('''
                UPDATE credit_cards SET due_date = ? WHERE id = ?
            ''', (due_date, card_id))
            
            conn.commit()
            
            flash(f'✅ 信用卡添加成功：{bank_name} ****{card_number_last4}', 'success')
            log_audit('credit_card_added', customer_id, 
                     f'添加信用卡：{bank_name} ****{card_number_last4}')
            
            return redirect(url_for('customer_dashboard', customer_id=customer_id))
        
        # GET 请求：显示添加表单
        cursor.execute('SELECT * FROM credit_cards WHERE customer_id = ?', (customer_id,))
        existing_cards = cursor.fetchall()
    
    return render_template('add_credit_card.html', 
                          customer=customer,
                          existing_cards=existing_cards)

# 已废弃：上传功能已整合到 CC Ledger 页面 (/credit-card/ledger)
# @app.route('/upload_statement', methods=['GET', 'POST'])
def upload_statement_deprecated():
    if request.method == 'POST':
        card_id = request.form.get('card_id')
        file = request.files.get('statement_file')
        
        if not card_id or not file:
            flash('Please provide card and file', 'error')
            return redirect(request.url)
        
        # 临时保存文件用于解析
        temp_filename = f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        temp_file_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
        file.save(temp_file_path)
        
        file_type = 'pdf' if temp_filename.lower().endswith('.pdf') else 'excel'
        
        # Step 1: Parse statement
        try:
            statement_info, transactions = parse_statement_auto(temp_file_path)
        except ValueError as e:
            # Check if this is HSBC scanned PDF
            if str(e) == "HSBC_SCANNED_PDF":
                flash('''
                <div class="alert alert-warning">
                    <h5><i class="bi bi-exclamation-triangle-fill"></i> 检测到HSBC扫描版PDF账单</h5>
                    <p class="mb-2">您上传的HSBC账单是扫描图片格式，系统需要文本格式才能准确提取交易记录。</p>
                    
                    <div class="mt-3">
                        <p class="mb-2"><strong>💡 解决方法很简单（只需1分钟）：</strong></p>
                        
                        <div class="conversion-step mb-3 p-3 bg-light rounded border">
                            <strong class="text-primary">方法1: 使用Microsoft Word转换（最简单）</strong>
                            <ol class="mt-2 mb-0">
                                <li class="mb-2">
                                    <strong>找到您下载的HSBC PDF文件</strong><br>
                                    <small class="text-muted">（通常在"下载"文件夹，文件名如：Statement_xxx.pdf）</small>
                                </li>
                                <li class="mb-2">
                                    <strong>用鼠标右键点击这个PDF文件</strong><br>
                                    <small class="text-muted">（在文件上按鼠标右键，会弹出菜单）</small>
                                </li>
                                <li class="mb-2">
                                    <strong>选择"打开方式" → "Microsoft Word"</strong><br>
                                    <small class="text-muted">（如果没看到Word选项，选"选择其他应用"，然后找Word）</small>
                                </li>
                                <li class="mb-2">
                                    <strong>Word会自动将PDF转换成文档</strong><br>
                                    <small class="text-muted">（会弹出提示，点"确定"，等待5-10秒转换完成）</small>
                                </li>
                                <li class="mb-2">
                                    <strong>在Word中点击"文件" → "另存为"</strong><br>
                                    <small class="text-muted">（左上角的"文件"菜单）</small>
                                </li>
                                <li class="mb-2">
                                    <strong>选择"PDF"格式保存</strong><br>
                                    <small class="text-muted">（文件类型选"PDF"，改个文件名如：HSBC_转换后.pdf）</small>
                                </li>
                                <li class="mb-0">
                                    <strong>将新保存的PDF文件重新上传到本系统</strong><br>
                                    <small class="text-muted">（这个新PDF就可以被系统识别了！）</small>
                                </li>
                            </ol>
                        </div>
                        
                        <div class="conversion-step mb-2 p-3 bg-light rounded border">
                            <strong class="text-primary">方法2: 从HSBC网银重新下载</strong>
                            <p class="mb-1 mt-2">登录HSBC网上银行 → 下载账单时选择"可搜索PDF"或"文本PDF"格式</p>
                            <small class="text-muted">（这样下载的PDF就可以直接上传使用）</small>
                        </div>
                        
                        <div class="alert alert-info mt-3 mb-0">
                            <i class="bi bi-lightbulb-fill"></i>
                            <strong>好消息：</strong>转换后的PDF可以永久使用，以后上传同一张账单就不用再转换了！
                        </div>
                    </div>
                </div>
                ''', 'warning')
                return redirect(request.url)
            else:
                # Other parsing errors
                flash(f'账单解析失败：{str(e)}', 'error')
                return redirect(request.url)
        
        if not statement_info or not transactions:
            flash('Failed to parse statement', 'error')
            return redirect(request.url)
        
        # Step 2: Dual Validation - Extract PDF text for cross-verification
        pdf_text = ""
        if file_type == 'pdf':
            try:
                with pdfplumber.open(temp_file_path) as pdf:
                    pdf_text = "\n".join(p.extract_text() for p in pdf.pages)
            except:
                pass
        
        dual_validation = validate_transactions(transactions, pdf_text) if pdf_text else None
        
        # Print validation report to console (for monitoring)
        if dual_validation:
            print("\n" + "="*80)
            print(f"📋 Statement Upload - Dual Validation Report")
            print("="*80)
            print(generate_validation_report(dual_validation))
        
        # Step 3: Original validation for backwards compatibility
        validation_result = validate_statement(statement_info['total'], transactions)
        
        # Combine validation scores
        final_confidence = validation_result['confidence']
        if dual_validation:
            final_confidence = (final_confidence + dual_validation.confidence_score) / 2
        
        # Determine auto-confirm based on dual validation
        auto_confirmed = 0
        validation_status = "pending"
        if dual_validation:
            if dual_validation.get_status() == "PASSED" and final_confidence >= 95:
                auto_confirmed = 1
                validation_status = "auto_approved"
            elif dual_validation.get_status() == "FAILED":
                validation_status = "requires_review"
        
        # Ensure statement_date is never None
        stmt_date = statement_info.get('statement_date') or datetime.now().strftime('%Y-%m-%d')
        
        # 🔥 强制性文件组织系统：获取客户和信用卡信息
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 获取信用卡和客户信息（包含customer_code用于文件组织）
            cursor.execute('''
                SELECT cc.bank_name, cc.card_number_last4, c.name as customer_name, c.customer_code
                FROM credit_cards cc
                JOIN customers c ON cc.customer_id = c.id
                WHERE cc.id = ?
            ''', (card_id,))
            
            card_row = cursor.fetchone()
            if not card_row:
                flash('❌ 信用卡不存在', 'error')
                os.remove(temp_file_path)  # 清理临时文件
                return redirect(request.url)
            
            card_info = dict(card_row)
            
            # 使用StatementOrganizer强制性组织文件（按客户代码）
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
                
                # 使用组织后的文件路径
                organized_file_path = organize_result['archived_path']
                
                # 删除临时文件
                os.remove(temp_file_path)
                
                print(f"✅ 文件已组织到: {organized_file_path}")
                
            except Exception as e:
                print(f"⚠️ 文件组织失败，使用临时路径: {str(e)}")
                organized_file_path = temp_file_path
            
            # ✅ 强制性重复检查
            validation_check = UniquenessValidator.validate_statement_upload(card_id, stmt_date)
            
            try:
                if validation_check['action'] == 'update':
                    # 更新现有账单而不是创建新的
                    print(f"ℹ️  检测到重复账单，更新现有记录 ID: {validation_check['existing_statement_id']}")
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
                    
                    # 删除旧交易记录
                    cursor.execute('DELETE FROM transactions WHERE statement_id = ?', (statement_id,))
                    flash(f'ℹ️  {validation_check["reason"]}', 'info')
                else:
                    # 创建新账单
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
                    
                    # 从parser返回的type字段映射到transaction_type
                    # type='debit' -> transaction_type='purchase' (消费DR)
                    # type='credit' -> transaction_type='payment' (付款CR)
                    trans_type = trans.get('type', None)
                    if trans_type == 'debit':
                        transaction_type = 'purchase'
                    elif trans_type == 'credit':
                        transaction_type = 'payment'
                    else:
                        # 兼容旧parser：根据amount判断（负数=付款，正数=消费）
                        transaction_type = 'payment' if trans['amount'] < 0 else 'purchase'
                    
                    cursor.execute('''
                        INSERT INTO transactions 
                        (statement_id, transaction_date, description, amount, category, category_confidence, transaction_type)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        statement_id,
                        trans['date'],
                        trans['description'],
                        abs(trans['amount']),  # 统一存储为正数
                        category,
                        confidence,
                        transaction_type
                    ))
                
                conn.commit()
                log_audit(None, 'UPLOAD_STATEMENT', 'statement', statement_id, 
                         f"Uploaded {file_type} statement with {len(transactions)} transactions. Validation: {validation_status}")
                
                # **NEW: 自动分类和处理账单**
                # 获取客户ID
                cursor.execute('''
                    SELECT customer_id FROM credit_cards WHERE id = ?
                ''', (card_id,))
                customer_id = cursor.fetchone()[0]
                
            except Exception as e:
                conn.rollback()
                raise e
        
        # **NEW: 自动触发综合处理流程**
        from services.statement_processor import process_uploaded_statement
        try:
            print("\n" + "="*80)
            print("🚀 启动智能分类处理流程...")
            print("="*80)
            if statement_id is not None:
                processing_result = process_uploaded_statement(customer_id, statement_id, organized_file_path)
            else:
                raise ValueError("Statement ID is None")
            
            if processing_result['success']:
                flash(f'🎉 账单处理完成！已分类 {processing_result["step_1_classify"]["total_transactions"]} 笔交易', 'success')
                if processing_result.get('step_2_invoices'):
                    flash(f'📄 已生成 {len(processing_result["step_2_invoices"])} 张供应商发票', 'info')
            else:
                flash(f'⚠️ 账单已上传，但处理时出现问题：{"; ".join(processing_result["errors"])}', 'warning')
        except Exception as e:
            flash(f'⚠️ 账单已上传，但自动分类失败：{str(e)}', 'warning')
            print(f"❌ 处理异常: {str(e)}")
        
        # Flash message based on validation status
        if validation_status == "auto_approved":
            flash(f'✅ Statement uploaded & auto-approved! Dual validation passed with {final_confidence:.0f}% confidence.', 'success')
        elif validation_status == "requires_review":
            flash(f'⚠️ Statement uploaded but requires manual review. Validation issues detected.', 'warning')
        else:
            flash(f'Statement uploaded. Validation Score: {final_confidence:.0f}%. Please review.', 'info')
        
        return redirect(url_for('validate_statement_view', statement_id=statement_id))
    
    customers = get_all_customers()
    all_cards = []
    for customer in customers:
        cards = get_customer_cards(customer['id'])
        for card in cards:
            card['customer_name'] = customer['name']
            all_cards.append(card)
    
    return render_template('upload_statement.html', cards=all_cards)

@app.route('/validate_statement/<int:statement_id>')
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
        flash('Statement not found', 'error')
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
def confirm_statement(statement_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE statements SET is_confirmed = 1 WHERE id = ?', (statement_id,))
        conn.commit()
        log_audit(None, 'CONFIRM_STATEMENT', 'statement', statement_id, 'Statement confirmed by user')
    
    flash('Statement confirmed successfully', 'success')
    return redirect(url_for('index'))

@app.route('/reminders')
def reminders():
    pending_reminders = get_pending_reminders()
    return render_template('reminders.html', reminders=pending_reminders)

@app.route('/create_reminder', methods=['POST'])
def create_reminder_route():
    card_id = request.form.get('card_id')
    due_date = request.form.get('due_date')
    amount_due = request.form.get('amount_due')
    
    if card_id and due_date and amount_due:
        reminder_id = create_reminder(int(card_id), due_date, float(amount_due))
        log_audit(None, 'CREATE_REMINDER', 'reminder', reminder_id, f'Created reminder for card {card_id}')
        flash('Reminder created successfully', 'success')
    else:
        flash('Missing required fields', 'error')
    
    return redirect(url_for('reminders'))

@app.route('/mark_paid/<int:reminder_id>', methods=['POST'])
def mark_paid_route(reminder_id):
    mark_as_paid(reminder_id)
    log_audit(None, 'MARK_PAID', 'reminder', reminder_id, 'Marked reminder as paid')
    flash('Payment marked as completed', 'success')
    return redirect(url_for('reminders'))

@app.route('/loan_evaluation/<int:customer_id>')
@login_required
@customer_access_required
def loan_evaluation(customer_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        customer_row = cursor.fetchone()
        customer = dict(customer_row) if customer_row else None
    
    if not customer:
        flash('Customer not found', 'error')
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
@login_required
@customer_access_required
def generate_report(customer_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        customer_row = cursor.fetchone()
        customer = dict(customer_row) if customer_row else None
    
    if not customer:
        flash('Customer not found', 'error')
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
@login_required
@customer_access_required
def analytics(customer_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        customer_row = cursor.fetchone()
        customer = dict(customer_row) if customer_row else None
    
    if not customer:
        flash('Customer not found', 'error')
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
@login_required
@customer_access_required
def export_transactions(customer_id, format):
    """Export transactions to Excel or CSV"""
    filters = {
        'start_date': request.args.get('start_date'),
        'end_date': request.args.get('end_date'),
        'category': request.args.get('category')
    }
    filters = {k: v for k, v in filters.items() if v}
    
    try:
        if format == 'excel':
            filepath = export_service.export_to_excel(customer_id, filters)
        elif format == 'csv':
            filepath = export_service.export_to_csv(customer_id, filters)
        else:
            flash('Invalid export format', 'error')
            return redirect(request.referrer or url_for('index'))
        
        return send_file(filepath, as_attachment=True)
    except Exception as e:
        flash(f'Export failed: {str(e)}', 'error')
        return redirect(request.referrer or url_for('index'))

@app.route('/search/<int:customer_id>', methods=['GET'])
@login_required
@customer_access_required
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
@login_required
@customer_access_required
def batch_upload(customer_id):
    """Batch upload statements with auto-create credit cards"""
    if request.method == 'POST':
        files = request.files.getlist('statement_files')
        
        if not files:
            flash('Please select files to upload', 'error')
            return redirect(request.url)
        
        batch_id = batch_service.create_batch_job('upload', customer_id, len(files))
        
        processed = 0
        failed = 0
        created_cards = []
        
        for file in files:
            try:
                filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                
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
                            failed += 1
                        elif bank_name == 'Unknown':
                            print(f"❌ Skipped {file.filename}: Cannot detect bank")
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
                            
                            processed += 1
                    else:
                        failed += 1
                else:
                    failed += 1
                    
                batch_service.update_batch_progress(batch_id, processed, failed)
            except Exception as e:
                print(f"❌ Batch upload error: {e}")
                failed += 1
                batch_service.update_batch_progress(batch_id, processed, failed)
        
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
@login_required
@customer_access_required
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
        flash('Customer not found', 'error')
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
@login_required
@customer_access_required
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
    
    flash('咨询请求已提交！我们的财务顾问将尽快与您联系。', 'success')
    return redirect(url_for('financial_advisory', customer_id=customer_id))

@app.route('/customer/<int:customer_id>/employment', methods=['GET', 'POST'])
@login_required
@customer_access_required
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
        
        flash('雇佣信息已更新', 'success')
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
@login_required
@customer_access_required
def generate_enhanced_report(customer_id):
    """Generate enhanced monthly report with financial advisory"""
    from report.enhanced_pdf_generator import generate_enhanced_monthly_report
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        customer_row = cursor.fetchone()
        customer = dict(customer_row) if customer_row else None
    
    if not customer:
        flash('Customer not found', 'error')
        return redirect(url_for('index'))
    
    output_filename = f"enhanced_report_{customer_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
    
    generate_enhanced_monthly_report(customer, output_path)
    
    flash('增强版月结报告生成成功！包含信用卡推荐和财务优化建议。', 'success')
    return send_file(output_path, as_attachment=True, download_name=output_filename)

# ==================== CUSTOMER AUTHENTICATION SYSTEM ====================

@app.route('/customer/login', methods=['GET', 'POST'])
def customer_login():
    """统一登录页面（支持Admin和Customer）"""
    import hashlib
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            return render_template('customer_login.html', error='Email and password are required')
        
        # 使用users表进行认证
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT u.id, u.email, u.role, u.full_name, c.id as customer_id, c.name as customer_name
                FROM users u
                LEFT JOIN customers c ON u.id = c.user_id
                WHERE u.email = ? AND u.password_hash = ? AND u.is_active = 1
            ''', (email, password_hash))
            
            user = cursor.fetchone()
        
        if user:
            # 保存登录信息到session
            session['user_id'] = user['id']
            session['user_email'] = user['email']
            session['user_role'] = user['role']
            session['user_name'] = user['full_name'] or user['customer_name']
            
            if user['role'] == 'customer' and user['customer_id']:
                session['customer_id'] = user['customer_id']
                session['customer_name'] = user['customer_name']
            
            flash(f"欢迎回来, {session['user_name']}!", 'success')
            
            # 根据角色跳转
            if user['role'] == 'admin':
                return redirect(url_for('index'))  # 管理员看到所有功能
            else:
                return redirect(url_for('customer_portal'))  # 客户看到自己的数据
        else:
            return render_template('customer_login.html', error='Invalid email or password')
    
    return render_template('customer_login.html')

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
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('customer_login'))
        else:
            return render_template('customer_register.html', error=result['error'])
    
    return render_template('customer_register.html')

@app.route('/customer/portal')
def customer_portal():
    """Customer data portal - view and download personal records"""
    token = session.get('customer_token')
    
    if not token:
        flash('Please login to access your portal', 'warning')
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

@app.route('/customer/logout')
def customer_logout():
    """Logout customer"""
    token = session.get('customer_token')
    
    if token:
        logout_customer(token)
    
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('customer_login'))

@app.route('/customer/download/<int:statement_id>')
def customer_download_statement(statement_id):
    """Download specific statement (customer access only)"""
    token = session.get('customer_token')
    
    if not token:
        flash('Please login to access your data', 'warning')
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
            flash('Statement not found or access denied', 'danger')
            return redirect(url_for('customer_portal'))
        
        file_path = result[0]
        
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            flash('File not found', 'danger')
            return redirect(url_for('customer_portal'))

# ==================== END CUSTOMER AUTHENTICATION ====================

# ==================== ADMIN AUTHENTICATION ====================

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    """Admin login route"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        admin_email = os.environ.get('ADMIN_EMAIL')
        admin_password = os.environ.get('ADMIN_PASSWORD')
        
        if not admin_email or not admin_password:
            flash('Admin credentials not configured. Please set ADMIN_EMAIL and ADMIN_PASSWORD environment variables.', 'danger')
            return render_template('admin_login.html')
        
        if email == admin_email and password == admin_password:
            # SECURITY FIX: Use single trusted user_role source
            session['user_role'] = 'admin'
            session['user_email'] = email
            session['user_name'] = 'Administrator'
            # Keep is_admin for backward compatibility during transition
            session['is_admin'] = True
            flash('Admin login successful', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials', 'danger')
    
    return render_template('admin_login.html')

@app.route('/admin')
def admin_dashboard():
    """Admin dashboard route"""
    if session.get('user_role') != 'admin':
        flash('Please login as admin first', 'warning')
        return redirect(url_for('admin_login'))
    
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
    
    return render_template('admin_dashboard.html', 
                         customers=customers,
                         statement_count=statement_count,
                         txn_count=txn_count,
                         active_cards=active_cards)

@app.route('/admin-logout')
def admin_logout():
    """Admin logout route"""
    session.clear()
    flash('Admin logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/admin/customers-cards')
def admin_customers_cards():
    """Admin page showing all customers and their credit cards"""
    if session.get('user_role') != 'admin':
        flash('Please login as admin first', 'warning')
        return redirect(url_for('admin_login'))
    
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
def admin_portfolio():
    """管理员Portfolio管理仪表板 - 核心运营工具"""
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
def admin_client_detail(customer_id):
    """查看单个客户完整workflow详情"""
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

# Import new analytics modules
from analytics.financial_health_score import FinancialHealthScore
from analytics.cashflow_predictor import CashflowPredictor
from analytics.customer_tier_system import CustomerTierSystem
from analytics.anomaly_detector import AnomalyDetector
from analytics.recommendation_engine import RecommendationEngine

# Initialize analytics services
health_score_service = FinancialHealthScore()
cashflow_service = CashflowPredictor()
tier_service = CustomerTierSystem()
anomaly_service = AnomalyDetector()
recommendation_service = RecommendationEngine()

@app.route('/advanced-analytics/<int:customer_id>')
@login_required
@customer_access_required
def advanced_analytics(customer_id):
    """高级财务分析仪表板"""
    lang = session.get('language', 'en')
    
    # 财务健康评分
    health_score = health_score_service.calculate_score(customer_id)
    score_trend = health_score_service.get_score_trend(customer_id, months=6)
    
    # 客户等级
    tier_info = tier_service.calculate_customer_tier(customer_id)
    
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
@login_required
@customer_access_required
def api_cashflow_prediction(customer_id):
    """API: 获取现金流预测数据"""
    months = request.args.get('months', 12, type=int)
    prediction = cashflow_service.predict_cashflow(customer_id, months)
    return jsonify(prediction)

@app.route('/api/financial-score/<int:customer_id>')
@login_required
@customer_access_required
def api_financial_score(customer_id):
    """API: 获取财务健康评分"""
    score_data = health_score_service.calculate_score(customer_id)
    return jsonify(score_data)

@app.route('/api/anomalies/<int:customer_id>')
@login_required
@customer_access_required
def api_anomalies(customer_id):
    """API: 获取财务异常"""
    anomalies = anomaly_service.get_active_anomalies(customer_id)
    return jsonify({'anomalies': anomalies})

@app.route('/api/recommendations/<int:customer_id>')
@login_required
@customer_access_required
def api_recommendations(customer_id):
    """API: 获取个性化推荐"""
    recommendations = recommendation_service.generate_recommendations(customer_id)
    return jsonify(recommendations)

@app.route('/api/tier-info/<int:customer_id>')
@login_required
@customer_access_required
def api_tier_info(customer_id):
    """API: 获取客户等级信息"""
    tier_info = tier_service.calculate_customer_tier(customer_id)
    return jsonify(tier_info)

@app.route('/resolve-anomaly/<int:anomaly_id>', methods=['POST'])
def resolve_anomaly_route(anomaly_id):
    """解决财务异常"""
    resolution_note = request.form.get('resolution_note', '')
    anomaly_service.resolve_anomaly(anomaly_id, resolution_note)
    flash('异常已成功解决', 'success')
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

@app.route('/export_statement_transactions/<int:statement_id>/<format>')
def export_statement_transactions(statement_id, format):
    """导出单个statement的交易记录"""
    import pandas as pd
    from io import BytesIO
    
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
        return send_file(output, 
                        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        as_attachment=True,
                        download_name=f'Statement_{statement_id}_Transactions.xlsx')
    else:
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return send_file(output, 
                        mimetype='text/csv',
                        as_attachment=True,
                        download_name=f'Statement_{statement_id}_Transactions.csv')

# Monthly Reports Routes
@app.route('/customer/<int:customer_id>/monthly-reports')
@login_required
@customer_access_required
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
@login_required
@customer_access_required
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
        flash('报表文件不存在', 'error')
        return redirect(url_for('index'))


# ============================================================================
# OPTIMIZATION PROPOSAL ROUTES - 自动化获客系统
# ============================================================================

@app.route('/customer/<int:customer_id>/optimization-proposal')
@login_required
@customer_access_required
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
            flash('客户不存在', 'error')
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
@login_required
@customer_access_required
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
            flash('客户不存在', 'error')
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
        
        flash('✅ 咨询申请已提交！我们的顾问将尽快与您联系。', 'success')
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
@login_required
@customer_access_required
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
            flash('客户不存在', 'error')
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
@login_required
@customer_access_required
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
            flash('客户不存在', 'error')
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
@admin_required
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
@login_required
@customer_access_required
def customer_resources(customer_id):
    """客户资源、人脉、技能管理页面"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 获取客户信息
        cursor.execute('SELECT full_name FROM customers WHERE id = ?', (customer_id,))
        result = cursor.fetchone()
        if not result:
            flash('客户不存在', 'error')
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
@login_required
@customer_access_required
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
    
    flash('资源添加成功！', 'success')
    return redirect(url_for('customer_resources', customer_id=customer_id))


@app.route('/customer/<int:customer_id>/add_network', methods=['POST'])
@login_required
@customer_access_required
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
    
    flash('人脉联系人添加成功！', 'success')
    return redirect(url_for('customer_resources', customer_id=customer_id))


@app.route('/customer/<int:customer_id>/add_skill', methods=['POST'])
@login_required
@customer_access_required
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
    
    flash('技能添加成功！', 'success')
    return redirect(url_for('customer_resources', customer_id=customer_id))


@app.route('/customer/<int:customer_id>/delete_resource/<int:resource_id>')
@login_required
@customer_access_required
def delete_resource(customer_id, resource_id):
    """删除资源"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM customer_resources WHERE id = ? AND customer_id = ?', (resource_id, customer_id))
        conn.commit()
    
    flash('资源已删除', 'success')
    return redirect(url_for('customer_resources', customer_id=customer_id))


@app.route('/customer/<int:customer_id>/delete_network/<int:network_id>')
@login_required
@customer_access_required
def delete_network(customer_id, network_id):
    """删除人脉"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM customer_network WHERE id = ? AND customer_id = ?', (network_id, customer_id))
        conn.commit()
    
    flash('人脉已删除', 'success')
    return redirect(url_for('customer_resources', customer_id=customer_id))


@app.route('/customer/<int:customer_id>/delete_skill/<int:skill_id>')
@login_required
@customer_access_required
def delete_skill(customer_id, skill_id):
    """删除技能"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM customer_skills WHERE id = ? AND customer_id = ?', (skill_id, customer_id))
        conn.commit()
    
    flash('技能已删除', 'success')
    return redirect(url_for('customer_resources', customer_id=customer_id))


@app.route('/customer/<int:customer_id>/generate_business_plan')
@login_required
@customer_access_required
def generate_plan(customer_id):
    """生成AI商业计划"""
    result = generate_business_plan(customer_id)
    
    if result['success']:
        flash('AI商业计划生成成功！', 'success')
        return redirect(url_for('view_business_plan', customer_id=customer_id, plan_id=result['plan_id']))
    else:
        flash(f'生成失败：{result["error"]}', 'error')
        return redirect(url_for('customer_resources', customer_id=customer_id))


@app.route('/customer/<int:customer_id>/business_plan/<int:plan_id>')
@login_required
@customer_access_required
def view_business_plan(customer_id, plan_id):
    """查看商业计划"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 获取客户信息
        cursor.execute('SELECT full_name FROM customers WHERE id = ?', (customer_id,))
        result = cursor.fetchone()
        if not result:
            flash('客户不存在', 'error')
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
            flash('商业计划不存在', 'error')
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
@login_required
@customer_access_required
def list_business_plans(customer_id):
    """查看所有商业计划历史"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute('SELECT full_name FROM customers WHERE id = ?', (customer_id,))
        result = cursor.fetchone()
        if not result:
            flash('客户不存在', 'error')
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
                flash('请上传至少一个账单文件', 'error')
                return redirect(url_for('upload_savings_statement'))
            
            processed_count = 0
            total_transactions = 0
            
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
            
            flash(f'✅ 成功上传{processed_count}个账单，共{total_transactions}笔交易记录', 'success')
            return redirect(url_for('savings_accounts'))
            
        except Exception as e:
            flash(f'上传失败: {str(e)}', 'error')
            import traceback
            traceback.print_exc()
            return redirect(url_for('upload_savings_statement'))
    
    # GET request - show upload form
    customers = get_all_customers()
    return render_template('savings/upload.html', customers=customers)

@app.route('/savings/customers')
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
@login_required
def savings_accounts_redirect():
    """Redirect to savings customers list"""
    return redirect(url_for('savings_customers'))

@app.route('/savings/accounts/<int:customer_id>')
@login_required
@customer_access_required
def savings_accounts(customer_id):
    """Layer 2: 查看特定客户的所有储蓄账户和账单"""
    import re
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 获取客户信息
        cursor.execute('SELECT id, name, customer_code FROM customers WHERE id = ?', (customer_id,))
        customer_row = cursor.fetchone()
        if not customer_row:
            flash('客户不存在', 'error')
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
            flash('⚠️ Savings account not found', 'error')
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
    
    flash('✅ 交易信息已更新', 'success')
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

@app.route('/savings/verify/<int:statement_id>')
def savings_verify_statement(statement_id):
    """100%准确性验证页面 - PDF原件 vs 系统记录逐笔对比"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 获取账单信息
        cursor.execute('''
            SELECT 
                ss.id,
                ss.savings_account_id,
                ss.statement_date,
                ss.file_path,
                ss.file_type,
                ss.total_transactions,
                ss.verification_status,
                ss.verified_by,
                ss.verified_at,
                ss.discrepancy_notes,
                sa.bank_name,
                sa.account_number_last4,
                sa.account_holder_name,
                sa.customer_id
            FROM savings_statements ss
            JOIN savings_accounts sa ON ss.savings_account_id = sa.id
            WHERE ss.id = ?
        ''', (statement_id,))
        
        statement_row = cursor.fetchone()
        if not statement_row:
            flash('客户不存在', 'danger')
            return redirect(url_for('savings_customers'))
        
        statement = dict(statement_row)
        
        # 获取所有交易记录（按日期和金额排序，与PDF一致）
        cursor.execute('''
            SELECT 
                id,
                transaction_date,
                description,
                amount,
                transaction_type,
                balance,
                reference_number,
                customer_name_tag
            FROM savings_transactions
            WHERE savings_statement_id = ?
            ORDER BY transaction_date ASC, id ASC
        ''', (statement_id,))
        
        transactions = [dict(row) for row in cursor.fetchall()]
        
        # 统计数据
        total_debit = sum(t['amount'] for t in transactions if t['transaction_type'] == 'debit')
        total_credit = sum(t['amount'] for t in transactions if t['transaction_type'] == 'credit')
        
        # 获取客户信息
        if statement['customer_id']:
            cursor.execute('SELECT name FROM customers WHERE id = ?', (statement['customer_id'],))
            customer_row = cursor.fetchone()
            customer_name = dict(customer_row)['name'] if customer_row else 'Unknown'
        else:
            customer_name = 'Unknown'
    
    return render_template('savings/verify.html',
                         statement=statement,
                         transactions=transactions,
                         total_debit=total_debit,
                         total_credit=total_credit,
                         customer_name=customer_name)

@app.route('/savings/verify/<int:statement_id>/mark_verified', methods=['POST'])
def mark_statement_verified(statement_id):
    """标记账单为已验证（100%准确）"""
    from datetime import datetime
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE savings_statements 
            SET verification_status = 'verified',
                verified_by = ?,
                verified_at = ?
            WHERE id = ?
        ''', (session.get('user_email', 'admin'), datetime.now().isoformat(), statement_id))
        conn.commit()
    
    flash('✅ Statement verified successfully! 100% accuracy confirmed.', 'success')
    return redirect(url_for('savings_verify_statement', statement_id=statement_id))

@app.route('/savings/verify/<int:statement_id>/flag_discrepancy', methods=['POST'])
def flag_statement_discrepancy(statement_id):
    """标记账单存在差异"""
    from datetime import datetime
    
    notes = request.form.get('discrepancy_notes', '').strip()
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE savings_statements 
            SET verification_status = 'discrepancy',
                verified_by = ?,
                verified_at = ?,
                discrepancy_notes = ?
            WHERE id = ?
        ''', (session.get('user_email', 'admin'), datetime.now().isoformat(), notes, statement_id))
        conn.commit()
    
    flash('⚠️ Discrepancy flagged. Please review and correct the differences.', 'warning')
    return redirect(url_for('savings_verify_statement', statement_id=statement_id))

@app.route('/view_savings_statement_file/<int:statement_id>')
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
def loan_matcher():
    """贷款产品匹配系统 - 表单页面"""
    return render_template('loan_matcher.html')

@app.route('/loan-matcher/analyze', methods=['POST'])
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
# CREDIT CARD LEDGER - 信用卡账本系统 (OWNER vs INFINITE)
# ============================================================================

@app.route('/credit-card/ledger', methods=['GET', 'POST'])
@login_required
def credit_card_ledger():
    """
    第一层：客户列表 (Admin) or 直接跳转到时间线 (Customer)
    - Admin: 显示所有有信用卡账单的客户 + 上传功能
    - Customer: 直接跳转到自己的时间线
    """
    from utils.name_utils import get_customer_code
    
    user_role = session.get('user_role')
    
    # SECURITY FIX: Use single trusted user_role source
    if user_role == 'admin':
        # Admin: show all customer list + upload functionality
        accessible_customer_ids = get_accessible_customers(session['user_id'], session['user_role'])
    elif user_role == 'customer':
        # Customer: redirect directly to their timeline (skip Layer 1)
        customer_id = session.get('customer_id')
        if customer_id:
            return redirect(url_for('credit_card_ledger_timeline', customer_id=customer_id))
        else:
            flash('Customer ID not found', 'error')
            return redirect(url_for('customer_login'))
    else:
        # Unknown role
        flash('Please login first', 'warning')
        return redirect(url_for('customer_login'))
    
    # POST: 处理上传
    if request.method == 'POST':
        # 重用 upload_statement 的逻辑
        card_id = request.form.get('card_id')
        file = request.files.get('statement_file')
        
        if not card_id or not file:
            flash('Please provide card and file', 'error')
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
                flash('检测到HSBC扫描版PDF账单，请使用Microsoft Word转换后重新上传', 'warning')
                os.remove(temp_file_path)
                return redirect(url_for('credit_card_ledger'))
            else:
                flash(f'账单解析失败：{str(e)}', 'error')
                os.remove(temp_file_path)
                return redirect(url_for('credit_card_ledger'))
        
        if not statement_info or not transactions:
            flash('Failed to parse statement', 'error')
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
                flash('❌ 信用卡不存在', 'error')
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
    
    # GET: 显示页面
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 获取所有有信用卡账单的客户（筛选权限）
        if accessible_customer_ids:
            placeholders = ','.join('?' * len(accessible_customer_ids))
            cursor.execute(f'''
                SELECT DISTINCT
                    c.id,
                    c.name,
                    c.customer_code,
                    COUNT(DISTINCT s.id) as statement_count
                FROM customers c
                JOIN credit_cards cc ON c.id = cc.customer_id
                JOIN statements s ON cc.id = s.card_id
                WHERE c.id IN ({placeholders})
                GROUP BY c.id
                ORDER BY c.name
            ''', accessible_customer_ids)
        else:
            # 如果没有可访问的客户，返回空列表
            cursor.execute('SELECT * FROM customers WHERE 1=0')
        
        customers = []
        for row in cursor.fetchall():
            customer = dict(row)
            # 直接使用数据库中的customer_code字段
            customer['code'] = customer.get('customer_code', 'Be_rich_UNKNOWN_00')
            customers.append(customer)
        
        # 获取所有信用卡供上传表单使用（仅可访问的客户）
        all_cards = []
        for cust_id in accessible_customer_ids:
            cursor.execute('SELECT * FROM customers WHERE id = ?', (cust_id,))
            customer = cursor.fetchone()
            if customer:
                cards = get_customer_cards(cust_id)
                for card in cards:
                    card['customer_name'] = customer['name']
                    all_cards.append(card)
    
    return render_template('credit_card/ledger_index.html', 
                         customers=customers, 
                         all_cards=all_cards,
                         is_admin=(session['user_role'] == 'admin'))


@app.route('/credit-card/ledger/<int:customer_id>/timeline')
@login_required
@customer_access_required
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
            flash('客户不存在', 'error')
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
@login_required
@customer_access_required
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
            flash('客户不存在', 'error')
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
            flash('该月没有账单', 'warning')
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
@login_required
def credit_card_ledger_detail(statement_id):
    """单个账单的OWNER vs INFINITE详细分析"""
    from services.owner_infinite_classifier import OwnerInfiniteClassifier
    
    classifier = OwnerInfiniteClassifier()
    
    # 权限检查：验证statement属于当前用户可访问的客户
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
            flash('账单不存在', 'error')
            return redirect(url_for('credit_card_ledger'))
        
        # 检查权限
        accessible_ids = get_accessible_customers(session['user_id'], session['user_role'])
        if stmt_customer['customer_id'] not in accessible_ids:
            flash('您没有权限访问此账单', 'error')
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
            flash('账单不存在', 'error')
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
@login_required
@customer_access_required
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
@login_required
@customer_access_required
def download_credit_card_report(customer_id):
    """下载HTML格式的信用卡优化报告"""
    try:
        filepath = comparison_reporter.save_report(customer_id)
        return send_file(filepath, as_attachment=True, download_name=os.path.basename(filepath))
    except Exception as e:
        flash(f'❌ 下载失败: {str(e)}', 'error')
        return redirect(url_for('credit_card_optimizer'))


# ============================================================================
# RECEIPT MANAGEMENT - 收据管理系统
# ============================================================================

@app.route('/receipts')
def receipts_home():
    """收据管理主页"""
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
        
        # 获取最近上传的收据
        cursor.execute("""
            SELECT 
                r.id,
                r.receipt_type,
                r.original_filename,
                r.transaction_date,
                r.amount,
                r.merchant_name,
                r.card_last4,
                r.match_status,
                r.match_confidence,
                r.created_at,
                c.name as customer_name,
                cc.card_type
            FROM receipts r
            LEFT JOIN customers c ON r.customer_id = c.id
            LEFT JOIN credit_cards cc ON r.card_id = cc.id
            ORDER BY r.created_at DESC
            LIMIT 50
        """)
        recent_receipts = [dict(row) for row in cursor.fetchall()]
    
    return render_template('receipts/home.html', stats=stats, recent_receipts=recent_receipts)

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
        flash('❌ 请选择至少一个收据图片', 'error')
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
@login_required
@customer_access_required
def receipts_by_customer(customer_id):
    """查看客户的所有收据"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 获取客户信息
        cursor.execute('SELECT name FROM customers WHERE id = ?', (customer_id,))
        customer = cursor.fetchone()
        
        if not customer:
            flash('❌ 客户不存在', 'error')
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
@login_required
@customer_access_required
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


if __name__ == '__main__':
    # Get environment settings
    flask_env = os.getenv('FLASK_ENV', 'development')
    debug_mode = flask_env != 'production'
    port = int(os.getenv('PORT', 5000))
    
    # Only start scheduler in the main process (not in Werkzeug reloader child process)
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not debug_mode:
        start_scheduler()
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
