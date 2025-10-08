from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
import os
from datetime import datetime, timedelta
import json
import threading
import time
import schedule

from db.database import get_db, log_audit, get_all_customers, get_customer_cards, get_card_statements, get_statement_transactions
from ingest.statement_parser import parse_statement_auto
from validate.categorizer import categorize_transaction, validate_statement, get_spending_summary
from validate.reminder_service import check_and_send_reminders, create_reminder, get_pending_reminders, mark_as_paid
from loan.dsr_calculator import calculate_dsr, calculate_max_loan_amount, simulate_loan_scenarios
from news.bnm_api import get_latest_rates, save_bnm_rates, add_banking_news, get_all_banking_news
from report.pdf_generator import generate_monthly_report

app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


@app.route('/')
def index():
    customers = get_all_customers()
    return render_template('index.html', customers=customers)

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
    
    return render_template('customer_dashboard.html', 
                         customer=customer, 
                         cards=cards,
                         spending_summary=spending_summary,
                         total_spending=total_spending)

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
        
        statement_info, transactions = parse_statement_auto(file_path)
        
        if not statement_info or not transactions:
            flash('Failed to parse statement', 'error')
            return redirect(request.url)
        
        validation_result = validate_statement(statement_info['total'], transactions)
        
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
                validation_result['confidence'],
                0,
                json.dumps(validation_result['inconsistencies'])
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
                     f"Uploaded {file_type} statement with {len(transactions)} transactions")
        
        flash(f'Statement uploaded successfully. Validation Score: {validation_result["confidence"]:.0%}', 'success')
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

def run_scheduler():
    schedule.every().day.at("09:00").do(check_and_send_reminders)
    schedule.every(6).hours.do(check_and_send_reminders)
    
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

start_scheduler()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
