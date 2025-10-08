def calculate_dsr(monthly_income, total_monthly_repayments):
    if monthly_income <= 0:
        return 0
    dsr = total_monthly_repayments / monthly_income
    return round(dsr, 4)

def calculate_max_loan_amount(monthly_income, current_repayments, dsr_threshold=0.45, interest_rate=0.04, loan_term_months=360):
    max_monthly_repayment = (monthly_income * dsr_threshold) - current_repayments
    
    if max_monthly_repayment <= 0:
        return {
            'max_loan_amount': 0,
            'monthly_installment': 0,
            'dsr': calculate_dsr(monthly_income, current_repayments),
            'max_monthly_repayment': 0,
            'message': 'Current DSR exceeds threshold. No additional loan capacity.'
        }
    
    monthly_rate = interest_rate / 12
    
    if monthly_rate == 0:
        max_loan = max_monthly_repayment * loan_term_months
    else:
        max_loan = max_monthly_repayment * ((1 - (1 + monthly_rate) ** -loan_term_months) / monthly_rate)
    
    return {
        'max_loan_amount': round(max_loan, 2),
        'monthly_installment': round(max_monthly_repayment, 2),
        'dsr': calculate_dsr(monthly_income, current_repayments + max_monthly_repayment),
        'max_monthly_repayment': round(max_monthly_repayment, 2),
        'interest_rate': interest_rate,
        'loan_term_months': loan_term_months,
        'message': 'Loan calculation successful'
    }

def calculate_monthly_payment(loan_amount, interest_rate, loan_term_months):
    if loan_amount <= 0 or loan_term_months <= 0:
        return 0
    
    monthly_rate = interest_rate / 12
    
    if monthly_rate == 0:
        return loan_amount / loan_term_months
    
    monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** loan_term_months) / ((1 + monthly_rate) ** loan_term_months - 1)
    return round(monthly_payment, 2)

def simulate_loan_scenarios(monthly_income, current_repayments):
    scenarios = []
    
    loan_amounts = [50000, 100000, 200000, 300000, 500000]
    interest_rates = [0.03, 0.04, 0.05, 0.06]
    loan_terms = [120, 180, 240, 300, 360]
    
    base_interest = 0.04
    base_term = 360
    
    for amount in loan_amounts:
        monthly_payment = calculate_monthly_payment(amount, base_interest, base_term)
        new_dsr = calculate_dsr(monthly_income, current_repayments + monthly_payment)
        
        scenarios.append({
            'loan_amount': amount,
            'interest_rate': base_interest,
            'term_months': base_term,
            'monthly_payment': monthly_payment,
            'new_dsr': round(new_dsr, 4),
            'affordable': new_dsr <= 0.45
        })
    
    return scenarios
