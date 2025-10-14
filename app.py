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

from db.database import get_db, log_audit, get_all_customers, get_customer_cards, get_card_statements, get_statement_transactions
from ingest.statement_parser import parse_statement_auto
from validate.categorizer import categorize_transaction, validate_statement, get_spending_summary
from validate.transaction_validator import validate_transactions, generate_validation_report
from validate.reminder_service import check_and_send_reminders, create_reminder, get_pending_reminders, mark_as_paid
from loan.dsr_calculator import calculate_dsr, calculate_max_loan_amount, simulate_loan_scenarios
from news.bnm_api import get_latest_rates, save_bnm_rates, add_banking_news, get_all_banking_news
from report.pdf_generator import generate_monthly_report
import pdfplumber

# New services for advanced features
from export.export_service import ExportService
from search.search_service import SearchService
from batch.batch_service import BatchService
from budget.budget_service import BudgetService
from email_service.email_sender import EmailService
from db.tag_service import TagService

# Statement organizer and optimization
from services.statement_organizer import StatementOrganizer
from services.optimization_proposal import OptimizationProposal

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

# Initialize services
export_service = ExportService()
search_service = SearchService()
batch_service = BatchService()
budget_service = BudgetService()
email_service = EmailService()
tag_service = TagService()
statement_organizer = StatementOrganizer()
optimization_service = OptimizationProposal()
monthly_report_scheduler = MonthlyReportScheduler()

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

@app.route('/static/uploads/<path:filename>')
def serve_uploaded_file(filename):
    """Serve uploaded PDF files with correct MIME type"""
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
    customers = get_all_customers()
    return render_template('index.html', customers=customers)

@app.route('/add_customer_page')
def add_customer_page():
    """Show add customer form page"""
    return render_template('add_customer.html')

@app.route('/add_customer', methods=['POST'])
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
            
            # Insert new customer
            cursor.execute("""
                INSERT INTO customers (name, email, phone, monthly_income)
                VALUES (?, ?, ?, ?)
            """, (name, email, phone, monthly_income))
            
            customer_id = cursor.lastrowid
            conn.commit()
            
            flash(f'Customer {name} added successfully! They can now register and login using {email}', 'success')
            return redirect(url_for('customer_dashboard', customer_id=customer_id))
            
    except Exception as e:
        flash(f'Error adding customer: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/customer/<int:customer_id>')
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
    
    from validate.instalment_tracker import InstalmentTracker
    tracker = InstalmentTracker()
    instalment_plans = tracker.get_customer_instalment_plans(customer_id)
    instalment_summary = tracker.get_instalment_summary(customer_id)
    
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
                         instalment_plans=instalment_plans,
                         instalment_summary=instalment_summary,
                         monthly_ledgers=monthly_ledgers)


@app.route('/customer/<int:customer_id>/add-card', methods=['GET', 'POST'])
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
            credit_limit = float(request.form.get('credit_limit', 0))
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
            
            # 检查是否已存在相同的卡
            cursor.execute('''
                SELECT id FROM credit_cards 
                WHERE customer_id = ? AND bank_name = ? AND card_number_last4 = ?
            ''', (customer_id, bank_name, card_number_last4))
            
            if cursor.fetchone():
                flash(f'该信用卡已存在：{bank_name} ****{card_number_last4}', 'error')
                return redirect(request.url)
            
            # 插入新信用卡
            cursor.execute('''
                INSERT INTO credit_cards 
                (customer_id, bank_name, card_number_last4, credit_limit, due_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (customer_id, bank_name, card_number_last4, credit_limit, due_date))
            
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

@app.route('/upload_statement', methods=['GET', 'POST'])
def upload_statement():
    if request.method == 'POST':
        card_id = request.form.get('card_id')
        file = request.files.get('statement_file')
        
        if not card_id or not file:
            flash('Please provide card and file', 'error')
            return redirect(request.url)
        
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        file_type = 'pdf' if filename.lower().endswith('.pdf') else 'excel'
        
        # Step 1: Parse statement
        try:
            statement_info, transactions = parse_statement_auto(file_path)
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
                with pdfplumber.open(file_path) as pdf:
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
        
        with get_db() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO statements 
                    (card_id, statement_date, statement_total, file_path, file_type, 
                     validation_score, is_confirmed, inconsistencies)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    card_id,
                    stmt_date,
                    statement_info['total'],
                    file_path,
                    file_type,
                    final_confidence,
                    auto_confirmed,
                    json.dumps({
                        'old_validation': validation_result['inconsistencies'],
                        'dual_validation_status': dual_validation.get_status() if dual_validation else 'N/A',
                        'dual_validation_errors': dual_validation.errors if dual_validation else [],
                        'dual_validation_warnings': dual_validation.warnings if dual_validation else []
                    })
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
                processing_result = process_uploaded_statement(customer_id, statement_id, file_path)
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

@app.route('/banking_news')
def banking_news():
    rates = get_latest_rates()
    news_items = get_all_banking_news()
    return render_template('banking_news.html', rates=rates, news_items=news_items)

@app.route('/add_news', methods=['POST'])
def add_news():
    bank_name = request.form.get('bank_name')
    news_type = request.form.get('news_type')
    title = request.form.get('title')
    content = request.form.get('content')
    effective_date = request.form.get('effective_date')
    
    if bank_name and title and content:
        news_id = add_banking_news(bank_name, news_type, title, content, effective_date)
        log_audit(None, 'ADD_NEWS', 'banking_news', news_id, f'Added news: {title}')
        flash('Banking news added successfully', 'success')
    else:
        flash('Missing required fields', 'error')
    
    return redirect(url_for('banking_news'))

@app.route('/refresh_bnm_rates')
def refresh_rates():
    rates = save_bnm_rates()
    flash(f'BNM rates updated: OPR={rates["opr"]["rate_value"]}%, SBR={rates["sbr"]["rate_value"]}%', 'success')
    return redirect(url_for('banking_news'))

# Admin news management routes
@app.route('/admin/news')
def admin_news():
    """管理员新闻审核页面"""
    from news.auto_news_fetcher import get_pending_news
    
    pending_news = get_pending_news()
    
    # 统计数据
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 今日已发布数量
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            SELECT COUNT(*) as count FROM banking_news 
            WHERE DATE(created_at) = ?
        ''', (today,))
        approved_today = cursor.fetchone()['count']
        
        # 总新闻数
        cursor.execute('SELECT COUNT(*) as count FROM banking_news')
        total_news = cursor.fetchone()['count']
    
    return render_template('admin_news.html', 
                         pending_news=pending_news,
                         pending_count=len(pending_news),
                         approved_today=approved_today,
                         total_news=total_news)

@app.route('/admin/news/approve/<int:news_id>', methods=['POST'])
def approve_news(news_id):
    """审核通过并发布新闻"""
    from news.auto_news_fetcher import approve_news as approve_fn
    
    try:
        approve_fn(news_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/news/reject/<int:news_id>', methods=['POST'])
def reject_news(news_id):
    """拒绝新闻"""
    from news.auto_news_fetcher import reject_news as reject_fn
    
    try:
        reject_fn(news_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/news/fetch', methods=['POST'])
def fetch_latest_news():
    """手动触发获取最新新闻"""
    try:
        # 从web搜索获取最新新闻
        news_items = fetch_news_from_web()
        
        from news.auto_news_fetcher import save_pending_news
        count = save_pending_news(news_items)
        
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def fetch_news_from_web():
    """
    从网络搜索获取新闻
    
    注意：这些新闻内容来自真实的2025年马来西亚银行公告和促销活动，
    通过web_search工具获取并整理。在生产环境中，可以替换为：
    - RSS feed订阅
    - 银行官方API
    - 新闻聚合API (NewsAPI, Google News等)
    """
    from news.news_parser import extract_all_news
    
    # 基于真实2025年马来西亚银行搜索结果的新闻数据
    search_results = [
        {
            'text': '''
            Hong Leong WISE信用卡提供高达15%返现在餐饮、杂货、药房、汽油和电子钱包消费。
            HSBC Live+信用卡在餐饮、娱乐和购物享有5%返现。
            UOB信用卡推荐计划，推荐朋友可获高达RM11,100返现。
            CIMB Cash Plus个人贷款年利率4.38%-19.88%，零手续费。
            UOB个人贷款利率3.99%起，无需抵押。
            Maybank自2025年3月31日起取消提前还款费用，每月还款低至RM102.78。
            马来西亚央行OPR从3.00%降至2.75%，定存利率最高达5.50%。
            CIMB eFixed Deposit-i通过FPX在线存款可享高达3.45%年利率。
            Hong Leong Bank eFD月度促销，10月特别利率。
            RHB Bancassurance FD年利率高达10.88%。
            2025年预算案拨款RM40 billion用于中小企业融资。
            Maybank SME Clean Loan在线申请高达RM250,000，分行申请高达RM1.5 million。
            SME Bank Business Accelerator计划高达RM1 million融资。
            CIMB SME BusinessCard提供无限现金返还。
            '''
        }
    ]
    
    news_items = extract_all_news(search_results)
    return news_items

@app.route('/generate_report/<int:customer_id>')
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

@app.route('/budget/<int:customer_id>', methods=['GET', 'POST'])
def budget_management(customer_id):
    """Budget management page"""
    if request.method == 'POST':
        category = request.form.get('category')
        
        if not category:
            flash('Category is required', 'error')
            return redirect(url_for('budget_management', customer_id=customer_id))
        
        try:
            monthly_limit = float(request.form.get('monthly_limit', 0))
            alert_threshold = float(request.form.get('alert_threshold', 80))
            
            if monthly_limit <= 0:
                flash('Budget limit must be greater than 0', 'error')
                return redirect(url_for('budget_management', customer_id=customer_id))
                
            if not 0 < alert_threshold <= 100:
                flash('Alert threshold must be between 1 and 100', 'error')
                return redirect(url_for('budget_management', customer_id=customer_id))
            
            budget_service.create_budget(customer_id, category, monthly_limit, alert_threshold)
            flash('Budget created successfully', 'success')
            return redirect(url_for('budget_management', customer_id=customer_id))
            
        except ValueError:
            flash('Invalid input: Please enter valid numbers', 'error')
            return redirect(url_for('budget_management', customer_id=customer_id))
    
    budgets = budget_service.get_budget_status(customer_id)
    recommendations = budget_service.get_budget_recommendations(customer_id)
    alerts = budget_service.get_budget_alerts(customer_id)
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        customer_row = cursor.fetchone()
        customer = dict(customer_row) if customer_row else None
    
    return render_template('budget.html', customer=customer, budgets=budgets,
                          recommendations=recommendations, alerts=alerts)

@app.route('/budget/delete/<int:budget_id>/<int:customer_id>', methods=['POST'])
def delete_budget(budget_id, customer_id):
    """Delete a budget"""
    budget_service.delete_budget(budget_id, customer_id)
    flash('Budget deleted', 'success')
    return redirect(url_for('budget_management', customer_id=customer_id))

@app.route('/batch/upload/<int:customer_id>', methods=['GET', 'POST'])
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
    """Customer login page"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            return render_template('customer_login.html', error='Email and password are required')
        
        result = authenticate_customer(email, password)
        
        if result['success']:
            session['customer_token'] = result['session_token']
            session['customer_id'] = result['customer_id']
            session['customer_name'] = result['customer_name']
            flash(f"{translate('welcome_back', session.get('language', 'en'))}, {result['customer_name']}!", 'success')
            return redirect(url_for('customer_portal'))
        else:
            return render_template('customer_login.html', error=result['error'])
    
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
            session['is_admin'] = True
            session['admin_email'] = email
            flash('Admin login successful', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials', 'danger')
    
    return render_template('admin_login.html')

@app.route('/admin')
def admin_dashboard():
    """Admin dashboard route"""
    if not session.get('is_admin'):
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
    session.pop('is_admin', None)
    session.pop('admin_email', None)
    flash('Admin logged out successfully', 'success')
    return redirect(url_for('index'))

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
def api_cashflow_prediction(customer_id):
    """API: 获取现金流预测数据"""
    months = request.args.get('months', 12, type=int)
    prediction = cashflow_service.predict_cashflow(customer_id, months)
    return jsonify(prediction)

@app.route('/api/financial-score/<int:customer_id>')
def api_financial_score(customer_id):
    """API: 获取财务健康评分"""
    score_data = health_score_service.calculate_score(customer_id)
    return jsonify(score_data)

@app.route('/api/anomalies/<int:customer_id>')
def api_anomalies(customer_id):
    """API: 获取财务异常"""
    anomalies = anomaly_service.get_active_anomalies(customer_id)
    return jsonify({'anomalies': anomalies})

@app.route('/api/recommendations/<int:customer_id>')
def api_recommendations(customer_id):
    """API: 获取个性化推荐"""
    recommendations = recommendation_service.generate_recommendations(customer_id)
    return jsonify(recommendations)

@app.route('/api/tier-info/<int:customer_id>')
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

def auto_fetch_daily_news():
    """每日自动获取新闻任务"""
    try:
        print(f"Auto-fetching news at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        news_items = fetch_news_from_web()
        
        from news.auto_news_fetcher import save_pending_news
        count = save_pending_news(news_items)
        
        print(f"Successfully fetched {count} news items for review")
    except Exception as e:
        print(f"Error auto-fetching news: {e}")

def run_scheduler():
    # 提醒任务
    schedule.every().day.at("09:00").do(check_and_send_reminders)
    schedule.every(6).hours.do(check_and_send_reminders)
    
    # 新闻获取任务 - 每天早上8点自动获取
    schedule.every().day.at("08:00").do(auto_fetch_daily_news)
    
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

# Instalment Detail Route
@app.route('/instalment/<int:plan_id>')
def instalment_detail(plan_id):
    """分期付款详情页面：显示完整的付款时间表和余额追踪"""
    from validate.instalment_tracker import InstalmentTracker
    
    tracker = InstalmentTracker()
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get plan info
        cursor.execute('''
            SELECT ip.*, cc.bank_name, cc.card_number_last4, cc.customer_id,
                   COUNT(ipr.id) as total_payments,
                   SUM(CASE WHEN ipr.status = 'paid' THEN 1 ELSE 0 END) as paid_payments
            FROM instalment_plans ip
            LEFT JOIN credit_cards cc ON ip.card_id = cc.id
            LEFT JOIN instalment_payment_records ipr ON ip.id = ipr.plan_id
            WHERE ip.id = ?
            GROUP BY ip.id
        ''', (plan_id,))
        
        plan = dict(cursor.fetchone())
        customer_id = plan['customer_id']
    
    # Get payment schedule
    payment_schedule = tracker.get_plan_payment_schedule(plan_id)
    
    # Calculate current balance (last unpaid payment's remaining balance)
    current_balance = 0
    for payment in payment_schedule:
        if payment['status'] == 'pending':
            # 找到第一个pending的付款，它的上一期的remaining_balance就是当前余额
            prev_payment_num = payment['payment_number'] - 1
            if prev_payment_num > 0:
                for p in payment_schedule:
                    if p['payment_number'] == prev_payment_num:
                        current_balance = p['remaining_balance']
                        break
            else:
                current_balance = plan['principal_amount']
            break
    
    # 如果所有都已支付，余额为0
    if all(p['status'] == 'paid' for p in payment_schedule):
        current_balance = 0
    
    return render_template('instalment_detail.html',
                         plan=plan,
                         payment_schedule=payment_schedule,
                         current_balance=current_balance,
                         customer_id=customer_id)

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
        total_debit = sum(abs(t['amount']) for t in transactions if t['transaction_type'] == 'debit')
        total_credit = sum(abs(t['amount']) for t in transactions if t['transaction_type'] == 'credit')
        supplier_fees = sum(t.get('supplier_fee', 0) for t in transactions if t.get('supplier_fee'))
        
        # Category breakdown
        categories = {}
        for t in transactions:
            if t['transaction_type'] == 'debit':
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
        flash('报表文件不存在', 'error')
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
# 智能分类和月度报告路由
# ============================================================================

@app.route('/statement/<int:statement_id>/classification')
def view_classification(statement_id):
    """查看账单的分类结果"""
    from services.transaction_classifier import get_consumption_summary, get_payment_summary
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 获取账单信息
        cursor.execute('''
            SELECT s.statement_date, s.statement_total, c.customer_id, c.bank_name, 
                   c.card_number_last4, cu.name
            FROM statements s
            JOIN credit_cards c ON s.card_id = c.id
            JOIN customers cu ON c.customer_id = cu.id
            WHERE s.id = ?
        ''', (statement_id,))
        
        stmt_info = cursor.fetchone()
        if not stmt_info:
            flash('账单不存在', 'error')
            return redirect(url_for('index'))
        
        stmt_date, stmt_total, customer_id, bank, last4, customer_name = stmt_info
    
    # 获取分类汇总
    consumption = get_consumption_summary(customer_id, statement_id)
    payments = get_payment_summary(customer_id, statement_id)
    
    return render_template('classification_view.html',
                          statement_id=statement_id,
                          customer_name=customer_name,
                          bank=bank,
                          card_last4=last4,
                          statement_date=stmt_date,
                          statement_total=stmt_total,
                          consumption=consumption,
                          payments=payments)


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


@app.route('/customer/<int:customer_id>/consumption_records')
def view_consumption_records(customer_id):
    """查看客户的所有消费记录"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 获取客户信息
        cursor.execute('SELECT name FROM customers WHERE id = ?', (customer_id,))
        result = cursor.fetchone()
        if not result:
            flash('客户不存在', 'error')
            return redirect(url_for('index'))
        customer_name = result[0]
        
        # 获取消费记录（最近100条）- 使用用户指定的字段名
        cursor.execute('''
            SELECT c.id, c.Bank, c.Card_FullNumber, c.Statement_Date, 
                   c.Transactions_Date, c.Transaction_Details, c.Suppliers_Usage,
                   c.User, c.Amount, c.category, c.supplier_fee
            FROM consumption_records c
            WHERE c.customer_id = ?
            ORDER BY c.Statement_Date DESC, c.Transactions_Date DESC
            LIMIT 100
        ''', (customer_id,))
        
        records = cursor.fetchall()
    
    return render_template('consumption_records.html',
                          customer_id=customer_id,
                          customer_name=customer_name,
                          records=records)


@app.route('/customer/<int:customer_id>/payment_records')
def view_payment_records(customer_id):
    """查看客户的所有付款记录"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 获取客户信息
        cursor.execute('SELECT name FROM customers WHERE id = ?', (customer_id,))
        result = cursor.fetchone()
        if not result:
            flash('客户不存在', 'error')
            return redirect(url_for('index'))
        customer_name = result[0]
        
        # 获取付款记录（最近100条）- 使用用户指定的字段名
        cursor.execute('''
            SELECT p.id, p.Bank, p.CreditCard_Full_Number, p.DueDate,
                   p.PaymentDate, p.PaymentDetails, p.PaymentUser,
                   p.PaymentAmount, p.category
            FROM payment_records p
            WHERE p.customer_id = ?
            ORDER BY p.PaymentDate DESC
            LIMIT 100
        ''', (customer_id,))
        
        records = cursor.fetchall()
    
    return render_template('payment_records.html',
                          customer_id=customer_id,
                          customer_name=customer_name,
                          records=records)


# ============================================================================
# 客户财务仪表板 - 关键指标展示
# ============================================================================

@app.route('/customer/<int:customer_id>/dashboard')
def financial_dashboard(customer_id):
    """
    客户财务仪表板
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
def delete_customer(customer_id):
    """
    删除客户及其所有相关数据
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
            
            # 7. 删除预算
            cursor.execute('DELETE FROM budgets WHERE customer_id = ?', (customer_id,))
            
            # 8. 删除分期付款计划
            cursor.execute('DELETE FROM instalment_plans WHERE customer_id = ?', (customer_id,))
            
            # 9. 删除提醒
            cursor.execute('DELETE FROM reminders WHERE customer_id = ?', (customer_id,))
            
            # 10. 删除咨询记录
            cursor.execute('DELETE FROM consultation_requests WHERE customer_id = ?', (customer_id,))
            
            # 11. 删除优化建议
            cursor.execute('DELETE FROM optimization_proposals WHERE customer_id = ?', (customer_id,))
            
            # 12. 最后删除客户本身
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
def delete_resource(customer_id, resource_id):
    """删除资源"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM customer_resources WHERE id = ? AND customer_id = ?', (resource_id, customer_id))
        conn.commit()
    
    flash('资源已删除', 'success')
    return redirect(url_for('customer_resources', customer_id=customer_id))


@app.route('/customer/<int:customer_id>/delete_network/<int:network_id>')
def delete_network(customer_id, network_id):
    """删除人脉"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM customer_network WHERE id = ? AND customer_id = ?', (network_id, customer_id))
        conn.commit()
    
    flash('人脉已删除', 'success')
    return redirect(url_for('customer_resources', customer_id=customer_id))


@app.route('/customer/<int:customer_id>/delete_skill/<int:skill_id>')
def delete_skill(customer_id, skill_id):
    """删除技能"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM customer_skills WHERE id = ? AND customer_id = ?', (skill_id, customer_id))
        conn.commit()
    
    flash('技能已删除', 'success')
    return redirect(url_for('customer_resources', customer_id=customer_id))


@app.route('/customer/<int:customer_id>/generate_business_plan')
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
                    # 保存文件
                    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    
                    # 解析账单
                    info, transactions = parse_savings_statement(file_path, bank_name or '')
                    
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
                        
                        # 创建账单记录
                        cursor.execute('''
                            INSERT INTO savings_statements 
                            (savings_account_id, statement_date, file_path, file_type, total_transactions, is_processed)
                            VALUES (?, ?, ?, ?, ?, 1)
                        ''', (
                            savings_account_id,
                            info.get('statement_date', datetime.now().strftime('%Y-%m-%d')),
                            f"static/uploads/{filename}",
                            'pdf' if file_path.endswith('.pdf') else 'excel',
                            len(transactions)
                        ))
                        
                        statement_id = cursor.lastrowid
                        
                        # 保存所有交易记录
                        for trans in transactions:
                            cursor.execute('''
                                INSERT INTO savings_transactions
                                (savings_statement_id, transaction_date, description, amount, transaction_type)
                                VALUES (?, ?, ?, ?, ?)
                            ''', (
                                statement_id,
                                trans.get('date', ''),
                                trans.get('description', ''),
                                trans.get('amount', 0),
                                trans.get('type', 'debit')
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

@app.route('/savings/accounts')
def savings_accounts():
    """查看所有储蓄账户和账单"""
    with get_db() as conn:
        cursor = conn.cursor()
        
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
            GROUP BY sa.id
            ORDER BY sa.created_at DESC
        ''')
        
        accounts = [dict(row) for row in cursor.fetchall()]
    
    return render_template('savings/accounts.html', accounts=accounts)

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
        
        account = dict(cursor.fetchone())
        
        # 获取账单列表
        cursor.execute('''
            SELECT 
                ss.id,
                ss.statement_date,
                ss.file_path,
                ss.file_type,
                ss.total_transactions,
                ss.created_at,
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
    """生成客户结算报告"""
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
                ss.statement_date
            FROM savings_transactions st
            JOIN savings_statements ss ON st.savings_statement_id = ss.id
            JOIN savings_accounts sa ON ss.savings_account_id = sa.id
            WHERE st.description LIKE ? OR st.customer_name_tag = ?
            ORDER BY st.transaction_date ASC
        ''', (f'%{customer_name}%', customer_name))
        
        transactions = [dict(row) for row in cursor.fetchall()]
        
        # 计算总额
        total_amount = sum(t['amount'] for t in transactions if t['transaction_type'] == 'debit')
        
        settlement_data = {
            'customer_name': customer_name,
            'total_amount': total_amount,
            'transaction_count': len(transactions),
            'transactions': transactions,
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


if __name__ == '__main__':
    # Get environment settings
    flask_env = os.getenv('FLASK_ENV', 'development')
    debug_mode = flask_env != 'production'
    port = int(os.getenv('PORT', 5000))
    
    # Only start scheduler in the main process (not in Werkzeug reloader child process)
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not debug_mode:
        start_scheduler()
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
