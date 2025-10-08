"""
Seed Malaysian Credit Card Products
Data from major Malaysian banks (Maybank, CIMB, Public Bank, RHB, Hong Leong, etc.)
"""

import sqlite3
from contextlib import contextmanager

DB_PATH = 'db/smart_loan_manager.db'

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()

def seed_credit_cards():
    """Insert Malaysian credit card products with realistic data"""
    
    cards = [
        # Maybank Cards
        {
            'bank_name': 'Maybank',
            'card_name': 'Maybank 2 Cards',
            'card_type': 'Cashback',
            'cashback_rate_general': 0.02,
            'cashback_rate_dining': 0.02,
            'cashback_rate_petrol': 0.02,
            'cashback_rate_grocery': 0.02,
            'cashback_cap_monthly': 200.0,
            'annual_fee': 0.0,
            'annual_fee_waiver_conditions': 'Permanent waiver',
            'min_income_requirement': 2000.0,
            'best_for_category': 'General Cashback',
            'special_promotions': 'Unlimited 2% cashback on all categories'
        },
        {
            'bank_name': 'Maybank',
            'card_name': 'Maybank Petronas Visa',
            'card_type': 'Rewards Points',
            'cashback_rate_petrol': 0.01,
            'points_rate_petrol': 5.0,
            'points_rate_general': 1.0,
            'points_value': 0.01,
            'annual_fee': 88.0,
            'annual_fee_waiver_conditions': 'Spend RM10,000 annually',
            'min_income_requirement': 2000.0,
            'best_for_category': 'Petrol',
            'special_promotions': '5x Treats Points at Petronas, 20 sen/L rebate'
        },
        
        # CIMB Cards
        {
            'bank_name': 'CIMB',
            'card_name': 'CIMB Cash Rebate Platinum',
            'card_type': 'Cashback',
            'cashback_rate_general': 0.01,
            'cashback_rate_petrol': 0.08,
            'cashback_cap_monthly': 50.0,
            'annual_fee': 188.0,
            'annual_fee_waiver_conditions': 'Spend RM1,500 in 3 months',
            'min_income_requirement': 2500.0,
            'best_for_category': 'Petrol',
            'special_promotions': '8% cashback on petrol (up to RM50/month)'
        },
        {
            'bank_name': 'CIMB',
            'card_name': 'CIMB e Credit Card',
            'card_type': 'Cashback',
            'cashback_rate_online': 0.10,
            'cashback_cap_monthly': 20.0,
            'annual_fee': 0.0,
            'annual_fee_waiver_conditions': 'Permanent waiver',
            'min_income_requirement': 2000.0,
            'best_for_category': 'Online Shopping',
            'special_promotions': '10% cashback on online spending (Lazada, Shopee, Grab)'
        },
        
        # Public Bank Cards
        {
            'bank_name': 'Public Bank',
            'card_name': 'Public Bank Visa Infinite',
            'card_type': 'Premium',
            'cashback_rate_dining': 0.05,
            'cashback_rate_travel': 0.05,
            'points_rate_general': 3.0,
            'points_value': 0.01,
            'annual_fee': 800.0,
            'min_income_requirement': 10000.0,
            'lounge_access': 1,
            'insurance_coverage': 'Travel insurance up to RM2 million',
            'best_for_category': 'Travel & Dining',
            'special_promotions': 'Unlimited lounge access, 5% cashback dining & travel'
        },
        {
            'bank_name': 'Public Bank',
            'card_name': 'Public Bank Quantum',
            'card_type': 'Cashback',
            'cashback_rate_grocery': 0.05,
            'cashback_rate_dining': 0.05,
            'cashback_cap_monthly': 100.0,
            'annual_fee': 0.0,
            'min_income_requirement': 2000.0,
            'best_for_category': 'Grocery & Dining',
            'special_promotions': '5% cashback on grocery and dining'
        },
        
        # RHB Cards
        {
            'bank_name': 'RHB',
            'card_name': 'RHB Rewards Visa',
            'card_type': 'Rewards Points',
            'points_rate_general': 2.0,
            'points_rate_dining': 4.0,
            'points_value': 0.01,
            'annual_fee': 150.0,
            'annual_fee_waiver_conditions': 'Spend RM12,000 annually',
            'min_income_requirement': 2000.0,
            'best_for_category': 'Rewards Points',
            'special_promotions': '4x points on dining, 2x on other spending'
        },
        
        # Hong Leong Cards
        {
            'bank_name': 'Hong Leong',
            'card_name': 'Hong Leong Wise Credit Card',
            'card_type': 'Cashback',
            'cashback_rate_petrol': 0.08,
            'cashback_rate_grocery': 0.08,
            'cashback_cap_monthly': 80.0,
            'annual_fee': 0.0,
            'min_income_requirement': 2000.0,
            'best_for_category': 'Petrol & Grocery',
            'special_promotions': '8% cashback on petrol & groceries (up to RM80/month)'
        },
        
        # AmBank Cards
        {
            'bank_name': 'AmBank',
            'card_name': 'AmBank True Visa',
            'card_type': 'Cashback',
            'cashback_rate_general': 0.02,
            'cashback_cap_monthly': 999999.0,
            'annual_fee': 0.0,
            'min_income_requirement': 2000.0,
            'best_for_category': 'Unlimited Cashback',
            'special_promotions': 'Unlimited 2% cashback on all spending'
        },
        
        # UOB Cards
        {
            'bank_name': 'UOB',
            'card_name': 'UOB One Card',
            'card_type': 'Rewards Points',
            'points_rate_dining': 10.0,
            'points_rate_general': 1.2,
            'points_value': 0.01,
            'annual_fee': 180.0,
            'annual_fee_waiver_conditions': 'Spend RM2,000 in first 2 months',
            'min_income_requirement': 2500.0,
            'best_for_category': 'Dining',
            'special_promotions': '10x UNI$ on dining (weekends), 1.2x on all spending'
        },
        
        # Standard Chartered Cards
        {
            'bank_name': 'Standard Chartered',
            'card_name': 'Standard Chartered Platinum Cashback',
            'card_type': 'Cashback',
            'cashback_rate_general': 0.015,
            'cashback_cap_monthly': 999999.0,
            'annual_fee': 195.0,
            'annual_fee_waiver_conditions': 'Spend RM20,000 annually',
            'min_income_requirement': 3000.0,
            'best_for_category': 'General Spending',
            'special_promotions': '1.5% unlimited cashback on all purchases'
        }
    ]
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        for card in cards:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO credit_card_products (
                        bank_name, card_name, card_type,
                        cashback_rate_general, cashback_rate_dining, cashback_rate_petrol,
                        cashback_rate_grocery, cashback_rate_online, cashback_rate_travel,
                        cashback_cap_monthly,
                        points_rate_general, points_rate_dining, points_rate_petrol,
                        points_rate_grocery, points_rate_online, points_rate_travel,
                        points_value,
                        annual_fee, annual_fee_waiver_conditions, min_income_requirement,
                        lounge_access, insurance_coverage, special_promotions,
                        best_for_category, is_active
                    ) VALUES (
                        ?, ?, ?,
                        ?, ?, ?,
                        ?, ?, ?,
                        ?,
                        ?, ?, ?,
                        ?, ?, ?,
                        ?,
                        ?, ?, ?,
                        ?, ?, ?,
                        ?, 1
                    )
                ''', (
                    card['bank_name'], card['card_name'], card['card_type'],
                    card.get('cashback_rate_general', 0), card.get('cashback_rate_dining', 0), card.get('cashback_rate_petrol', 0),
                    card.get('cashback_rate_grocery', 0), card.get('cashback_rate_online', 0), card.get('cashback_rate_travel', 0),
                    card.get('cashback_cap_monthly', 0),
                    card.get('points_rate_general', 0), card.get('points_rate_dining', 0), card.get('points_rate_petrol', 0),
                    card.get('points_rate_grocery', 0), card.get('points_rate_online', 0), card.get('points_rate_travel', 0),
                    card.get('points_value', 0),
                    card.get('annual_fee', 0), card.get('annual_fee_waiver_conditions', ''), card.get('min_income_requirement', 0),
                    card.get('lounge_access', 0), card.get('insurance_coverage', ''), card.get('special_promotions', ''),
                    card.get('best_for_category', ''), 
                ))
            except Exception as e:
                print(f"Error inserting {card['card_name']}: {e}")
        
        conn.commit()
        print(f"✅ Inserted {len(cards)} Malaysian credit cards successfully!")

def seed_service_terms():
    """Insert service terms and fee policy"""
    
    terms = [
        {
            'term_type': 'fee_policy',
            'title_en': 'Success-Based Fee Policy',
            'title_cn': '成功收费政策',
            'content_en': '''We are committed to delivering real value to our clients. Our fee structure reflects this commitment:

• NO RESULTS, NO FEE: If our optimization does not generate any savings or additional benefits for you, we will NOT charge any fees whatsoever.

• 50% PROFIT SHARING: When we successfully save you money or earn you additional benefits, we charge 50% of the total benefit as our service fee.

• TRANSPARENT CALCULATION: All savings and fees are clearly calculated and presented to you before any charges are applied.

• CLIENT FIRST: We only earn when you earn. Your success is our success.

This policy ensures that we are always motivated to find the best possible solutions for your financial situation.''',
            'content_cn': '''我们致力于为客户提供真正的价值。我们的收费结构反映了这一承诺：

• 无收益，不收费：如果我们的优化方案未能为您节省任何费用或创造额外收益，我们将不收取任何一分一毫的费用。

• 50%收益分成：当我们成功为您节省费用或赚取额外收益时，我们收取总收益的50%作为服务费用。

• 透明计算：所有节省的费用和收费都将在收费前清楚地计算并呈现给您。

• 客户至上：只有您获益，我们才获益。您的成功就是我们的成功。

这一政策确保我们始终致力于为您的财务状况找到最佳解决方案。''',
            'display_order': 1
        },
        {
            'term_type': 'income_requirements_employee',
            'title_en': 'Income Documentation - Employees',
            'title_cn': '收入证明要求 - 打工一族',
            'content_en': '''For salaried employees, we require the following income documentation for bank loan optimization assessment:

REQUIRED DOCUMENTS:
• Latest 3 months payslips
• EPF (KWSP) statement for last 6 months
• Bank statement showing salary credit for last 3 months
• Employment confirmation letter (if available)

WHY WE NEED THIS:
Banks require consistent proof of income to evaluate loan eligibility. As an employee, your regular salary and EPF contributions provide strong evidence of stable income, which helps us negotiate better loan terms and interest rates for you.

VERIFICATION PROCESS:
Our team will verify your income documents to ensure accuracy before presenting optimization proposals to banks. This ensures we can secure the best possible rates and terms for your situation.''',
            'content_cn': '''对于打工一族，我们需要以下收入证明文件用于银行贷款优化评估：

所需文件：
• 最近3个月的工资单
• 最近6个月的公积金（EPF/KWSP）报表
• 显示工资入账的最近3个月银行对账单
• 雇主确认信（如有）

为什么需要这些：
银行需要一致的收入证明来评估贷款资格。作为受薪员工，您的固定工资和公积金缴纳提供了稳定收入的有力证据，这有助于我们为您争取更好的贷款条件和利率。

验证流程：
我们的团队将验证您的收入文件以确保准确性，然后再向银行提交优化方案。这确保我们能为您的情况争取到最优惠的利率和条款。''',
            'display_order': 2
        },
        {
            'term_type': 'income_requirements_self_employed',
            'title_en': 'Income Documentation - Self-Employed',
            'title_cn': '收入证明要求 - 自雇人士',
            'content_en': '''For self-employed professionals, income verification requires different documentation:

REQUIRED DOCUMENTS:
• Latest 6 months bank statements (business account)
• Income tax returns (Form B/BE) for last 2 years
• Financial statements or accounting records
• Business license or professional registration
• Client invoices or contracts (as proof of ongoing business)

WHY WE NEED THIS:
Self-employed income can fluctuate, so banks require more comprehensive documentation to assess your average earnings and business stability. These documents help us demonstrate your true earning capacity.

VERIFICATION PROCESS:
We calculate your average monthly income based on the last 6-12 months of business activity. Our specialized assessment for self-employed clients often reveals opportunities for better loan terms that traditional applications might miss.''',
            'content_cn': '''对于自雇专业人士，收入验证需要不同的文件：

所需文件：
• 最近6个月的银行对账单（商业账户）
• 最近2年的所得税申报表（Form B/BE）
• 财务报表或会计记录
• 营业执照或专业注册证
• 客户发票或合同（作为持续经营的证明）

为什么需要这些：
自雇收入可能波动，因此银行需要更全面的文件来评估您的平均收入和业务稳定性。这些文件帮助我们展示您的真实收入能力。

验证流程：
我们根据最近6-12个月的业务活动计算您的平均月收入。我们针对自雇客户的专业评估常能发现传统申请可能错过的更优贷款条件机会。''',
            'display_order': 3
        },
        {
            'term_type': 'income_requirements_business_owner',
            'title_en': 'Income Documentation - Business Owners',
            'title_cn': '收入证明要求 - 企业主',
            'content_en': '''For business owners, we require comprehensive business and personal income documentation:

REQUIRED DOCUMENTS:
• Company financial statements (last 2 years) - audited if available
• Company bank statements (last 6 months)
• Personal bank statements (last 6 months)
• Business registration documents (SSM)
• Income tax returns - both personal (Form B/BE) and company (Form C)
• Director's remuneration or dividend declarations
• Proof of business ownership (shareholding documents)

WHY WE NEED THIS:
Banks assess both your personal income and company financial health. As a business owner, you may have multiple income streams (salary, dividends, rental). Complete documentation helps us present your full financial picture.

VERIFICATION PROCESS:
We analyze both business profitability and personal income extraction methods. Our assessment often identifies optimal ways to structure your income declaration to maximize loan eligibility while remaining compliant with banking requirements.

SPECIAL CONSIDERATIONS:
Business owners often have complex income structures. Our experienced team knows how to present your finances in the most favorable light to banks, potentially qualifying you for larger loans or better rates than standard applications.''',
            'content_cn': '''对于企业主，我们需要全面的企业和个人收入文件：

所需文件：
• 公司财务报表（最近2年）- 如有审计报告更佳
• 公司银行对账单（最近6个月）
• 个人银行对账单（最近6个月）
• 企业注册文件（SSM）
• 所得税申报表 - 个人（Form B/BE）和公司（Form C）
• 董事薪酬或股息申报
• 企业所有权证明（股权文件）

为什么需要这些：
银行会评估您的个人收入和公司财务健康状况。作为企业主，您可能有多种收入来源（工资、股息、租金）。完整的文件帮助我们呈现您的完整财务状况。

验证流程：
我们分析企业盈利能力和个人收入提取方法。我们的评估常能识别出最佳的收入申报结构方式，在符合银行要求的同时最大化贷款资格。

特别考虑：
企业主通常有复杂的收入结构。我们经验丰富的团队知道如何以最有利的方式向银行呈现您的财务状况，可能让您获得比标准申请更大额度的贷款或更优惠的利率。''',
            'display_order': 4
        }
    ]
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        for term in terms:
            cursor.execute('''
                INSERT OR REPLACE INTO service_terms (
                    term_type, title_en, title_cn, content_en, content_cn, display_order
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                term['term_type'], term['title_en'], term['title_cn'],
                term['content_en'], term['content_cn'], term['display_order']
            ))
        
        conn.commit()
        print(f"✅ Inserted {len(terms)} service terms successfully!")

if __name__ == '__main__':
    seed_credit_cards()
    seed_service_terms()
