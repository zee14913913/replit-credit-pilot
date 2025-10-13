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

# Initialize services
export_service = ExportService()
search_service = SearchService()
batch_service = BatchService()
budget_service = BudgetService()
email_service = EmailService()
tag_service = TagService()

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
    
    return render_template('customer_dashboard.html', 
                         customer=customer, 
                         cards=cards,
                         spending_summary=spending_summary,
                         total_spending=total_spending,
                         instalment_plans=instalment_plans,
                         instalment_summary=instalment_summary)

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
        statement_info, transactions = parse_statement_auto(file_path)
        
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
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO statements 
                (card_id, statement_date, statement_total, file_path, file_type, 
                 validation_score, is_confirmed, inconsistencies)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                card_id,
                statement_info.get('statement_date', datetime.now().strftime('%Y-%m-%d')),
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
                cursor.execute('''
                    INSERT INTO transactions 
                    (statement_id, transaction_date, description, amount, category, category_confidence)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    statement_id,
                    trans['date'],
                    trans['description'],
                    trans['amount'],
                    category,
                    confidence
                ))
            
            conn.commit()
            log_audit(None, 'UPLOAD_STATEMENT', 'statement', statement_id, 
                     f"Uploaded {file_type} statement with {len(transactions)} transactions. Validation: {validation_status}")
        
        # Flash message based on validation status
        if validation_status == "auto_approved":
            flash(f'✅ Statement uploaded & auto-approved! Dual validation passed with {final_confidence:.0f}% confidence.', 'success')
        elif validation_status == "requires_review":
            flash(f'⚠️ Statement uploaded but requires manual review. Validation issues detected.', 'warning')
        else:
            flash(f'Statement uploaded. Validation Score: {final_confidence:.0f}%. Please review.', 'info')
        
        return redirect(url_for('validate_statement', statement_id=statement_id))
    
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
    """Batch upload statements"""
    if request.method == 'POST':
        files = request.files.getlist('statement_files')
        card_id = request.form.get('card_id')
        
        if not files or not card_id:
            flash('Please select files and card', 'error')
            return redirect(request.url)
        
        batch_id = batch_service.create_batch_job('upload', customer_id, len(files))
        
        processed = 0
        failed = 0
        
        for file in files:
            try:
                filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                
                result = parse_statement_auto(file_path)
                
                # Extract data from result tuple (data_dict, transactions_list)
                if isinstance(result, tuple) and len(result) >= 2:
                    data_dict, _ = result
                    if data_dict and isinstance(data_dict, dict):
                        statement_date = str(data_dict.get('statement_date', ''))
                        total = float(data_dict.get('total', 0))
                    else:
                        statement_date = ''
                        total = 0.0
                else:
                    statement_date = ''
                    total = 0.0
                
                with get_db() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO statements (card_id, statement_date, statement_total, file_path, batch_job_id)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (card_id, statement_date, total, file_path, batch_id))
                    statement_id = cursor.lastrowid
                    conn.commit()
                
                processed += 1
                batch_service.update_batch_progress(batch_id, processed, failed)
            except:
                failed += 1
                batch_service.update_batch_progress(batch_id, processed, failed)
        
        batch_service.complete_batch_job(batch_id, 'completed')
        flash(f'Batch upload completed: {processed} succeeded, {failed} failed', 'success')
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
    
    # 月度报表自动生成 - 每月5号早上10点自动生成上月报表（银河主题）
    from report.galaxy_report_generator import generate_galaxy_monthly_reports
    
    def check_and_generate_monthly_reports():
        """检查是否为每月5号，如果是则生成银河主题报表"""
        today = datetime.now()
        if today.day == 5:
            print(f"🌌 Generating galaxy-themed monthly reports for {today.strftime('%Y-%m')}...")
            reports = generate_galaxy_monthly_reports()
            print(f"✨ Generated {len(reports)} galaxy-themed monthly reports")
    
    schedule.every().day.at("10:00").do(check_and_generate_monthly_reports)
    
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
        df.to_excel(output, index=False, engine='openpyxl')
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


start_scheduler()

if __name__ == '__main__':
    # Get environment settings
    flask_env = os.getenv('FLASK_ENV', 'development')
    debug_mode = flask_env != 'production'
    port = int(os.getenv('PORT', 5000))
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
