"""
Credit Card Optimizer & Financial Advisory System - Database Migration
Adds tables for credit card recommendations, financial optimization, and success-based fee calculation
"""

import sqlite3
from contextlib import contextmanager

DB_PATH = 'db/smart_loan_manager.db'

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def migrate():
    """Add tables for credit card optimizer and financial advisory system"""
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 1. Credit Card Products Database (马来西亚各大银行信用卡)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS credit_card_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bank_name TEXT NOT NULL,
                card_name TEXT NOT NULL,
                card_type TEXT NOT NULL, -- Cashback, Rewards Points, Travel, Premium, Islamic
                
                -- Benefits 福利信息
                cashback_rate_general REAL DEFAULT 0,
                cashback_rate_dining REAL DEFAULT 0,
                cashback_rate_petrol REAL DEFAULT 0,
                cashback_rate_grocery REAL DEFAULT 0,
                cashback_rate_online REAL DEFAULT 0,
                cashback_rate_travel REAL DEFAULT 0,
                cashback_cap_monthly REAL DEFAULT 0,
                
                points_rate_general REAL DEFAULT 0,  -- Points per RM1
                points_rate_dining REAL DEFAULT 0,
                points_rate_petrol REAL DEFAULT 0,
                points_rate_grocery REAL DEFAULT 0,
                points_rate_online REAL DEFAULT 0,
                points_rate_travel REAL DEFAULT 0,
                points_value REAL DEFAULT 0,  -- Value of 1 point in RM
                
                -- Fees 费用
                annual_fee REAL DEFAULT 0,
                annual_fee_waiver_conditions TEXT,
                min_income_requirement REAL DEFAULT 0,
                
                -- Special Benefits 特殊福利
                lounge_access BOOLEAN DEFAULT 0,
                insurance_coverage TEXT,
                welcome_bonus TEXT,
                special_promotions TEXT,
                
                -- Suitability 适用场景
                best_for_category TEXT,  -- e.g., "Dining", "Petrol", "Online Shopping"
                
                is_active BOOLEAN DEFAULT 1,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                UNIQUE(bank_name, card_name)
            )
        ''')
        
        # 2. Card Recommendations (智能推荐记录)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS card_recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                card_product_id INTEGER NOT NULL,
                
                -- Recommendation Score 推荐评分
                match_score REAL NOT NULL,  -- 0-100
                estimated_monthly_benefit REAL NOT NULL,  -- Expected RM savings/earnings
                
                -- Reasoning 推荐理由
                recommendation_reason TEXT,
                spending_analysis TEXT,
                
                -- Status
                status TEXT DEFAULT 'pending',  -- pending, accepted, rejected, applied
                recommended_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (customer_id) REFERENCES customers(id),
                FOREIGN KEY (card_product_id) REFERENCES credit_card_products(id)
            )
        ''')
        
        # 3. Customer Types (客户类型管理)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customer_employment_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL UNIQUE,
                
                employment_type TEXT NOT NULL,  -- employee, self_employed, business_owner
                
                -- Income Documentation Requirements
                required_documents TEXT,  -- JSON list of required docs
                documents_uploaded TEXT,  -- JSON list of uploaded docs
                verification_status TEXT DEFAULT 'pending',  -- pending, verified, rejected
                
                -- Employment Details
                employer_name TEXT,
                business_name TEXT,
                business_registration_no TEXT,
                years_in_business REAL,
                
                -- Additional Income Sources
                additional_income_sources TEXT,  -- JSON
                total_verified_income REAL,
                
                notes TEXT,
                updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )
        ''')
        
        # 4. Financial Optimization Suggestions (财务优化建议)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS financial_optimization_suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                
                -- Optimization Type
                optimization_type TEXT NOT NULL,  -- debt_consolidation, refinancing, credit_card_switch, loan_restructure
                
                -- Current Situation (优化前)
                current_monthly_payment REAL NOT NULL,
                current_interest_rate REAL NOT NULL,
                current_total_cost REAL NOT NULL,
                
                -- Optimized Situation (优化后)
                optimized_monthly_payment REAL NOT NULL,
                optimized_interest_rate REAL NOT NULL,
                optimized_total_cost REAL NOT NULL,
                
                -- Savings Calculation (省下的钱)
                monthly_savings REAL NOT NULL,
                total_savings REAL NOT NULL,
                
                -- Additional Benefits (额外收益)
                additional_benefits TEXT,  -- e.g., "Lower DSR from 45% to 32%"
                
                -- Implementation Details
                recommended_bank TEXT,
                recommended_product TEXT,
                implementation_steps TEXT,
                
                -- Based on Latest Data
                bnm_policy_reference TEXT,  -- 参考的BNM政策
                bank_rates_reference TEXT,  -- 参考的银行利率
                data_as_of_date DATE,
                
                -- Status
                status TEXT DEFAULT 'proposed',  -- proposed, client_interested, implemented, rejected
                consultation_requested BOOLEAN DEFAULT 0,
                
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )
        ''')
        
        # 5. Consultation Requests (咨询请求通知)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS consultation_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                optimization_suggestion_id INTEGER,
                
                request_type TEXT NOT NULL,  -- full_optimization, card_recommendation, loan_restructure
                customer_message TEXT,
                
                -- Contact Preferences
                preferred_contact_method TEXT,  -- email, phone, whatsapp
                preferred_contact_time TEXT,
                
                -- Status
                status TEXT DEFAULT 'new',  -- new, contacted, in_progress, completed, cancelled
                assigned_to TEXT,
                
                request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                response_date TIMESTAMP,
                
                FOREIGN KEY (customer_id) REFERENCES customers(id),
                FOREIGN KEY (optimization_suggestion_id) REFERENCES financial_optimization_suggestions(id)
            )
        ''')
        
        # 6. Fee Calculations (成功收费计算)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS success_fee_calculations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                optimization_id INTEGER NOT NULL,
                
                -- Actual Results (实际成果)
                actual_savings_achieved REAL NOT NULL,
                actual_additional_benefits_value REAL DEFAULT 0,
                total_customer_benefit REAL NOT NULL,
                
                -- Fee Calculation (50% profit sharing)
                fee_percentage REAL DEFAULT 50.0,  -- 50% of benefit
                calculated_fee REAL NOT NULL,
                
                -- Fee Status
                fee_status TEXT DEFAULT 'calculated',  -- calculated, invoiced, paid, waived
                invoice_date DATE,
                payment_date DATE,
                
                -- Zero Fee Guarantee
                zero_benefit_confirmed BOOLEAN DEFAULT 0,  -- If TRUE, no fee charged
                
                notes TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (customer_id) REFERENCES customers(id),
                FOREIGN KEY (optimization_id) REFERENCES financial_optimization_suggestions(id)
            )
        ''')
        
        # 7. Service Terms & Disclaimers (服务条款声明)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS service_terms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                term_type TEXT NOT NULL UNIQUE,  -- fee_policy, income_requirements, disclaimers
                
                title_en TEXT NOT NULL,
                title_cn TEXT,
                
                content_en TEXT NOT NULL,
                content_cn TEXT,
                
                display_order INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                
                updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_card_reco_customer ON card_recommendations(customer_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_card_reco_status ON card_recommendations(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_optimization_customer ON financial_optimization_suggestions(customer_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_optimization_status ON financial_optimization_suggestions(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_consultation_status ON consultation_requests(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_fee_calc_customer ON success_fee_calculations(customer_id)')
        
        conn.commit()
        print("✅ Credit Card Optimizer & Financial Advisory tables created successfully!")

if __name__ == '__main__':
    migrate()
