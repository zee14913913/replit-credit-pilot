#!/usr/bin/env python3
"""
导入网络搜索获取的产品数据到数据库
"""
import psycopg2, os
from psycopg2.extras import execute_values
from datetime import datetime

DATABASE_URL = os.getenv('DATABASE_URL')

# 从网络搜索获取的产品数据
products = [
    # Maybank
    {'company': 'Malayan Banking Berhad (Maybank)', 'type': 'PERSONAL_LOAN', 'name': 'Maybank Personal Loan', 
     'rate': '11.53% - 14.68% p.a.', 'tenure': '2-6 years', 
     'features': 'RM5,000-RM100,000, No processing fees, No stamping fees, Fast approval within 48 hours, No early settlement fee (2025)',
     'url': 'https://www.maybank2u.com.my/maybank2u/malaysia/en/personal/loans/personal/personal_loan.page'},
    
    {'company': 'Malayan Banking Berhad (Maybank)', 'type': 'PERSONAL_LOAN', 'name': 'Maybank Personal Financing-i (Islamic)', 
     'rate': '11.53% - 14.68% p.a.', 'tenure': '2-6 years',
     'features': 'Shariah-compliant, Similar to conventional personal loan',
     'url': 'https://www.maybank2u.com.my/maybank2u/malaysia/en/personal/loans/personal/islamic_personal_financing.page'},
    
    {'company': 'Malayan Banking Berhad (Maybank)', 'type': 'HOME_LOAN', 'name': 'MaxiHome Flexi', 
     'rate': '请联系银行', 'tenure': '请联系银行',
     'features': 'Hassle-free home financing, Campaign promo: Chance to win Apple iMac worth RM5,799',
     'url': 'https://www.maybank2u.com.my/maybank2u/malaysia/en/personal/loans/home/maxihome_flexi_loan.page'},
    
    {'company': 'Malayan Banking Berhad (Maybank)', 'type': 'HOME_LOAN', 'name': 'Youth Home Financing', 
     'rate': '请联系银行', 'tenure': '请联系银行',
     'features': 'Designed for young working adults',
     'url': 'https://www.maybank2u.com.my/maybank2u/malaysia/en/personal/loans/home/'},
    
    {'company': 'Malayan Banking Berhad (Maybank)', 'type': 'FIXED_DEPOSIT', 'name': 'eFixed Deposit', 
     'rate': '标准利率', 'tenure': '1-60 months',
     'features': 'Min RM1,000-RM5,000, Real-time account creation via Maybank2u, Certless placement, Automatic renewal',
     'url': 'https://www.maybank2u.com.my/maybank2u/malaysia/en/personal/accounts/fixed_deposits/efixed_deposit.page'},
    
    {'company': 'Malayan Banking Berhad (Maybank)', 'type': 'FIXED_DEPOSIT', 'name': 'e-Islamic Fixed Deposit-i', 
     'rate': 'Up to 3.50% p.a.', 'tenure': '请联系银行',
     'features': 'Min RM1,000, Max RM15,000,000, Shariah-compliant, Campaign until Dec 31 2025',
     'url': 'https://www.maybank2u.com.my/maybank2u/malaysia/en/personal/promotions/account_and_banking/efd-promo.page'},
    
    # Public Bank
    {'company': 'Public Bank Berhad', 'type': 'CREDIT_CARD', 'name': 'PB Visa Infinite', 
     'rate': '15-18% p.a.', 'tenure': '请联系银行',
     'features': 'Premium card, 3x Plaza Premium Lounge access, Travel insurance up to RM500,000',
     'url': 'https://www.pbebank.com/en/cards/our-cards/pb-visa-infinite-credit-card/'},
    
    {'company': 'Public Bank Berhad', 'type': 'CREDIT_CARD', 'name': 'PB World Mastercard', 
     'rate': '15-18% p.a.', 'tenure': '请联系银行',
     'features': '3X Air Miles Points, 3x lounge access, Travel insurance up to RM500,000',
     'url': 'https://www.pbebank.com/en/cards/'},
    
    {'company': 'Public Bank Berhad', 'type': 'CREDIT_CARD', 'name': 'PB Visa Signature', 
     'rate': '15-18% p.a.', 'tenure': '请联系银行',
     'features': '2% cashback on groceries/online/dining (min RM100), 10X Green Points, 2x lounge access',
     'url': 'https://www.pbebank.com/en/cards/our-cards/pb-visa-signature-credit-card/'},
    
    {'company': 'Public Bank Berhad', 'type': 'PERSONAL_LOAN', 'name': 'BAE AG Personal Financing-i', 
     'rate': 'From 3% p.a.', 'tenure': 'Up to 10 years',
     'features': 'For Government Staff, RM5,000-RM150,000, Fixed flat rate, No guarantor needed',
     'url': 'https://ringgitplus.com/en/personal-loan/Public-Bank-BAE-AG-Personal-Financing-i.html'},
    
    {'company': 'Public Bank Berhad', 'type': 'PERSONAL_LOAN', 'name': 'PLUS BAE Personal Financing-i', 
     'rate': '请联系银行', 'tenure': 'Up to 10 years',
     'features': 'RM10,000-RM150,000, For existing Public Bank customers, Optional Takaful coverage',
     'url': 'https://www.publicislamicbank.com.my/personal-banking/banking/financing/personal-financing-i/plus-bae-personal-financing-i/'},
    
    # Maybank Islamic
    {'company': 'Maybank Islamic Berhad', 'type': 'PERSONAL_LOAN', 'name': 'Maybank Islamic Personal Financing-i', 
     'rate': '请联系银行', 'tenure': '请联系银行',
     'features': 'Fast approval, Monthly payments from RM102.78, Optional Takaful coverage up to RM100,000',
     'url': 'https://www.maybank2u.com.my/maybank2u/malaysia/en/personal/loans/personal/islamic_personal_financing.page'},
    
    {'company': 'Maybank Islamic Berhad', 'type': 'HOME_LOAN', 'name': 'Commodity Murabahah Home Financing-i', 
     'rate': '请联系银行', 'tenure': '请联系银行',
     'features': 'Stamp duty waiver on conversion, Flexible repayment, Redraw facility, Ceiling profit rate cap',
     'url': 'https://www.maybank2u.com.my/maybank2u/malaysia/en/personal/loans/home/commodity_murabahah_home_financing_i.page'},
    
    {'company': 'Maybank Islamic Berhad', 'type': 'CAR_LOAN', 'name': 'Murabahah Vehicle Term Financing-i (MVTF-i)', 
     'rate': '请联系银行', 'tenure': '请联系银行',
     'features': 'Purchase new/used vehicles, Death/TPD coverage, No early settlement penalty',
     'url': 'https://www.maybank2u.com.my/maybank2u/malaysia/en/personal/loans/hire_purchase/mvtf-i.page'},
    
    {'company': 'Maybank Islamic Berhad', 'type': 'CAR_LOAN', 'name': 'Electric Vehicle (EV) Financing', 
     'rate': '请联系银行', 'tenure': '请联系银行',
     'features': 'First-in-Malaysia EV insurance and takaful coverage, Access to Maybank EV charging stations, Free EV home charger insurance',
     'url': 'https://www.maybank.com/islamic/en/financing/'},
    
    {'company': 'Maybank Islamic Berhad', 'type': 'SME_LOAN', 'name': 'SME Digital Financing', 
     'rate': '请联系银行', 'tenure': 'Up to 25 years',
     'features': 'RM3,000-RM20,000,000, No documents/collateral for amounts below RM500,000, Instant approval',
     'url': 'https://www.maybank.com/islamic/en/business/financing/sme_digital_financing.page'},
    
    # Bank Islam
    {'company': 'Bank Islam Malaysia Berhad', 'type': 'PERSONAL_LOAN', 'name': 'Personal Financing-i (Package)', 
     'rate': 'From SBR + 1.75% p.a.', 'tenure': 'Up to 10 years',
     'features': 'Up to RM400,000, Min income RM2,000/month, No guarantor, Optional Takaful coverage',
     'url': 'https://www.bankislam.com/personal-banking/financing/personal-financing/personal-financing-i-package/'},
    
    {'company': 'Bank Islam Malaysia Berhad', 'type': 'PERSONAL_LOAN', 'name': 'Personal Financing-i (Professional Program)', 
     'rate': 'From BR + 1.90% p.a.', 'tenure': 'Up to 10 years',
     'features': 'RM10,000-RM300,000, For professionals (doctors, engineers, etc), Min income RM3,500-RM4,000/month',
     'url': 'https://www.bankislam.com/personal-banking/financing/'},
    
    {'company': 'Bank Islam Malaysia Berhad', 'type': 'PERSONAL_LOAN', 'name': 'Be U Personal Financing-i', 
     'rate': '请联系银行', 'tenure': '6 or 12 months',
     'features': 'Up to RM5,000, For gig workers (freelancers, drivers, delivery workers), No security deposit',
     'url': 'https://getbeu.com/product/Be-U-PF-i'},
    
    {'company': 'Bank Islam Malaysia Berhad', 'type': 'SME_LOAN', 'name': 'SME Biz G.R.O.W Financing Program', 
     'rate': '请联系银行', 'tenure': '请联系银行',
     'features': 'Working capital and capital expenses, For Private Limited Companies and Professional Service Providers',
     'url': 'https://www.bankislam.com/business-banking/sme-banking/sme-biz-g-r-o-w-financing-program/'},
    
    {'company': 'Bank Islam Malaysia Berhad', 'type': 'SME_LOAN', 'name': 'Business Premises Financing (BPF)', 
     'rate': '请联系银行', 'tenure': 'Up to 20 years',
     'features': 'Min RM150,000, Purchase/refinance commercial properties, Up to 150% of OMV',
     'url': 'https://www.bankislam.com/business-banking/commercial-banking/business-premises-financing/'},
    
    # Boost Bank
    {'company': 'Boost Bank Berhad', 'type': 'FIXED_DEPOSIT', 'name': 'Savings Account', 
     'rate': '3.3% p.a.', 'tenure': '请联系银行',
     'features': 'Daily interest, Open with RM1, No monthly fees, PIDM protected up to RM250,000',
     'url': 'https://myboostbank.co/'},
    
    {'company': 'Boost Bank Berhad', 'type': 'SME_LOAN', 'name': 'SME Term Loan', 
     'rate': 'From 9.9% p.a.', 'tenure': 'Up to 36 months',
     'features': 'For business expansion, equipment, renovations, Eligible: Sole proprietors, private limited cos',
     'url': 'https://myboostbank.co/business/financing/term-loan'},
    
    {'company': 'Boost Bank Berhad', 'type': 'CAR_LOAN', 'name': 'Motorbike Loan', 
     'rate': 'Up to 10% p.a.', 'tenure': 'Up to 60 months',
     'features': 'Up to 90% financing for new mopeds <250cc, AI-powered credit approval, Popular among gig workers',
     'url': 'https://myboostbank.co/'},
]

print("=" * 80)
print("导入网络搜索获取的产品数据")
print("=" * 80)

con = psycopg2.connect(DATABASE_URL)
cur = con.cursor()

sql = """
    INSERT INTO loan_products_ultimate(
        company, loan_type, product_name, required_doc, features, benefits,
        fees_charges, tenure, rate, application_form_url, product_disclosure_url,
        terms_conditions_url, preferred_customer_type, source_url, scraped_at
    ) VALUES %s
    ON CONFLICT (company, product_name) DO NOTHING
"""

items = [(
    p['company'], p['type'], p['name'], 
    '请访问银行官网了解详情',
    p.get('features', '请访问银行官网了解详情'),
    '请访问银行官网了解详情',
    '请联系银行',
    p.get('tenure', '请联系银行'),
    p.get('rate', '请联系银行'),
    '', '', '', '所有客户',
    p.get('url', ''),
    datetime.now()
) for p in products]

execute_values(cur, sql, items)
con.commit()

inserted = cur.rowcount
print(f"\n✅ 成功导入 {inserted} 个新产品")

# 统计
cur.execute("SELECT COUNT(*), COUNT(DISTINCT company) FROM loan_products_ultimate")
total, companies = cur.fetchone()
print(f"📊 数据库总计: {total} 个产品，{companies} 家公司")

cur.close()
con.close()

print("\n完成！")
