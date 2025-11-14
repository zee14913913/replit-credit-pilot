"""
Product Catalog - 马来西亚银行与Fintech贷款产品目录
包含12+家真实金融机构的产品信息
"""
from typing import Dict, List

# ============================================================
# PERSONAL LOAN PRODUCTS (个人贷款产品)
# ============================================================

PERSONAL_LOAN_CATALOG = {
    "maybank_pl": {
        "bank": "Maybank",
        "product_name": "Maybank Personal Loan",
        "category": "personal",
        "type": "traditional_bank",
        "base_rate": 0.055,  # 5.5% p.a.
        "rate_range": (0.055, 0.120),
        "max_tenure": 84,  # months
        "max_amount": 150000,  # RM
        "min_income": 2000,
        "required_risk_bands": ["A+", "A", "B+", "B"],
        "min_credit_score": 650,
        "ccris_bucket_max": 1,
        "features": ["Flexible tenure", "No early settlement fee", "Fast approval"],
        "digital_application": True,
        "approval_time_hours": 48
    },
    
    "cimb_cashplus": {
        "bank": "CIMB",
        "product_name": "CIMB CashPlus",
        "category": "personal",
        "type": "traditional_bank",
        "base_rate": 0.060,
        "rate_range": (0.060, 0.125),
        "max_tenure": 60,
        "max_amount": 100000,
        "min_income": 1500,
        "required_risk_bands": ["A+", "A", "B+", "B", "C"],
        "min_credit_score": 600,
        "ccris_bucket_max": 2,
        "features": ["No income proof required (salary crediting)", "Instant approval", "Balance transfer"],
        "digital_application": True,
        "approval_time_hours": 24
    },
    
    "public_bae": {
        "bank": "Public Bank",
        "product_name": "Public Bank BAE Personal Financing",
        "category": "personal",
        "type": "traditional_bank",
        "base_rate": 0.048,
        "rate_range": (0.048, 0.110),
        "max_tenure": 84,
        "max_amount": 200000,
        "min_income": 3000,
        "required_risk_bands": ["A+", "A", "B+"],
        "min_credit_score": 700,
        "ccris_bucket_max": 0,
        "features": ["Lowest rate in market", "Premium segment", "Flexible repayment"],
        "digital_application": False,
        "approval_time_hours": 72
    },
    
    "hong_leong_pf": {
        "bank": "Hong Leong Bank",
        "product_name": "Hong Leong Personal Financing",
        "category": "personal",
        "type": "traditional_bank",
        "base_rate": 0.058,
        "rate_range": (0.058, 0.115),
        "max_tenure": 72,
        "max_amount": 120000,
        "min_income": 2000,
        "required_risk_bands": ["A+", "A", "B+", "B"],
        "min_credit_score": 650,
        "ccris_bucket_max": 1,
        "features": ["Competitive rates", "Quick disbursement", "Flexi payment"],
        "digital_application": True,
        "approval_time_hours": 48
    },
    
    "rhb_smart": {
        "bank": "RHB Bank",
        "product_name": "RHB Smart Instalment",
        "category": "personal",
        "type": "traditional_bank",
        "base_rate": 0.062,
        "rate_range": (0.062, 0.128),
        "max_tenure": 60,
        "max_amount": 100000,
        "min_income": 1800,
        "required_risk_bands": ["A+", "A", "B+", "B", "C"],
        "min_credit_score": 620,
        "ccris_bucket_max": 2,
        "features": ["Instant approval", "Online application", "No prepayment penalty"],
        "digital_application": True,
        "approval_time_hours": 24
    },
    
    "alliance_cashvantage": {
        "bank": "Alliance Bank",
        "product_name": "Alliance CashVantage",
        "category": "personal",
        "type": "traditional_bank",
        "base_rate": 0.065,
        "rate_range": (0.065, 0.130),
        "max_tenure": 60,
        "max_amount": 80000,
        "min_income": 1500,
        "required_risk_bands": ["A+", "A", "B+", "B"],
        "min_credit_score": 640,
        "ccris_bucket_max": 1,
        "features": ["Flexible repayment", "Balance transfer option", "Fast approval"],
        "digital_application": True,
        "approval_time_hours": 36
    },
    
    "ambank_signature": {
        "bank": "AmBank",
        "product_name": "AmBank Signature Personal Loan",
        "category": "personal",
        "type": "traditional_bank",
        "base_rate": 0.059,
        "rate_range": (0.059, 0.118),
        "max_tenure": 72,
        "max_amount": 150000,
        "min_income": 2500,
        "required_risk_bands": ["A+", "A", "B+", "B"],
        "min_credit_score": 680,
        "ccris_bucket_max": 1,
        "features": ["Premium service", "Personalized rates", "Relationship pricing"],
        "digital_application": True,
        "approval_time_hours": 48
    },
    
    "sc_cashone": {
        "bank": "Standard Chartered",
        "product_name": "Standard Chartered CashOne",
        "category": "personal",
        "type": "traditional_bank",
        "base_rate": 0.052,
        "rate_range": (0.052, 0.112),
        "max_tenure": 60,
        "max_amount": 180000,
        "min_income": 3500,
        "required_risk_bands": ["A+", "A", "B+"],
        "min_credit_score": 720,
        "ccris_bucket_max": 0,
        "features": ["Premium product", "Ultra-low rates", "Priority service"],
        "digital_application": True,
        "approval_time_hours": 48
    },
    
    # DIGITAL BANKS
    "gxbank_pf": {
        "bank": "GXBank",
        "product_name": "GXBank Personal Financing",
        "category": "personal",
        "type": "digital_bank",
        "base_rate": 0.068,
        "rate_range": (0.068, 0.145),
        "max_tenure": 60,
        "max_amount": 50000,
        "min_income": 1200,
        "required_risk_bands": ["A+", "A", "B+", "B", "C", "D"],
        "min_credit_score": 550,
        "ccris_bucket_max": 3,
        "features": ["100% digital", "Instant approval", "Risk-based pricing"],
        "digital_application": True,
        "approval_time_hours": 2,
        "risk_score_based": True
    },
    
    "boost_bank_micro": {
        "bank": "Boost Bank",
        "product_name": "Boost Bank Micro Financing",
        "category": "personal",
        "type": "digital_bank",
        "base_rate": 0.075,
        "rate_range": (0.075, 0.160),
        "max_tenure": 36,
        "max_amount": 30000,
        "min_income": 1000,
        "required_risk_bands": ["A+", "A", "B+", "B", "C", "D"],
        "min_credit_score": 500,
        "ccris_bucket_max": 3,
        "features": ["Micro-lending", "AI-driven approval", "Fast disbursement"],
        "digital_application": True,
        "approval_time_hours": 1,
        "risk_score_based": True
    },
    
    # FINTECH
    "aeon_credit_pl": {
        "bank": "AEON Credit",
        "product_name": "AEON Credit Personal Loan",
        "category": "personal",
        "type": "fintech",
        "base_rate": 0.072,
        "rate_range": (0.072, 0.155),
        "max_tenure": 48,
        "max_amount": 60000,
        "min_income": 1200,
        "required_risk_bands": ["A+", "A", "B+", "B", "C"],
        "min_credit_score": 580,
        "ccris_bucket_max": 2,
        "features": ["Easy approval", "Minimal documentation", "Quick disbursement"],
        "digital_application": True,
        "approval_time_hours": 24
    },
    
    "grab_paylater": {
        "bank": "Grab PayLater",
        "product_name": "Grab PayLater Personal Loan",
        "category": "personal",
        "type": "fintech",
        "base_rate": 0.080,
        "rate_range": (0.080, 0.180),
        "max_tenure": 24,
        "max_amount": 20000,
        "min_income": 800,
        "required_risk_bands": ["A+", "A", "B+", "B", "C", "D"],
        "min_credit_score": 480,
        "ccris_bucket_max": 3,
        "features": ["Instant approval", "App-based", "Alternative credit scoring"],
        "digital_application": True,
        "approval_time_hours": 0.5,
        "risk_score_based": True
    }
}

# ============================================================
# SME LOAN PRODUCTS (中小企业贷款产品)
# ============================================================

SME_LOAN_CATALOG = {
    "maybank_sme": {
        "bank": "Maybank",
        "product_name": "Maybank SME Business Term Loan",
        "category": "sme",
        "type": "traditional_bank",
        "base_rate": 0.048,
        "rate_range": (0.048, 0.095),
        "max_tenure": 120,  # months
        "max_amount": 5000000,  # RM
        "min_revenue": 500000,
        "required_brr_grades": [1, 2, 3, 4],
        "min_dscr": 1.50,
        "min_ctos_sme_score": 700,
        "industry_allowed": ["all"],
        "industry_excluded": ["oil_gas", "property_development"],
        "features": ["Flexible tenure", "CGC scheme available", "Working capital support"],
        "cgc_eligible": True
    },
    
    "cimb_bizfinance": {
        "bank": "CIMB",
        "product_name": "CIMB BizFinance SME",
        "category": "sme",
        "type": "traditional_bank",
        "base_rate": 0.052,
        "rate_range": (0.052, 0.100),
        "max_tenure": 84,
        "max_amount": 3000000,
        "min_revenue": 300000,
        "required_brr_grades": [1, 2, 3, 4, 5],
        "min_dscr": 1.40,
        "min_ctos_sme_score": 650,
        "industry_allowed": ["all"],
        "industry_excluded": ["construction", "property_development"],
        "features": ["Fast approval", "Digital application", "Trade finance support"],
        "cgc_eligible": True
    },
    
    "public_sme": {
        "bank": "Public Bank",
        "product_name": "Public Bank SME Term Financing",
        "category": "sme",
        "type": "traditional_bank",
        "base_rate": 0.045,
        "rate_range": (0.045, 0.090),
        "max_tenure": 120,
        "max_amount": 10000000,
        "min_revenue": 1000000,
        "required_brr_grades": [1, 2, 3],
        "min_dscr": 1.60,
        "min_ctos_sme_score": 720,
        "industry_allowed": ["all"],
        "industry_excluded": [],
        "features": ["Lowest SME rates", "Established businesses", "Premium service"],
        "cgc_eligible": True
    },
    
    "hong_leong_sme": {
        "bank": "Hong Leong Bank",
        "product_name": "Hong Leong SME Financing",
        "category": "sme",
        "type": "traditional_bank",
        "base_rate": 0.050,
        "rate_range": (0.050, 0.098),
        "max_tenure": 96,
        "max_amount": 2000000,
        "min_revenue": 250000,
        "required_brr_grades": [1, 2, 3, 4, 5],
        "min_dscr": 1.45,
        "min_ctos_sme_score": 670,
        "industry_allowed": ["all"],
        "industry_excluded": ["oil_gas"],
        "features": ["Competitive rates", "SME-focused", "Quick turnaround"],
        "cgc_eligible": True
    },
    
    "rhb_sme": {
        "bank": "RHB Bank",
        "product_name": "RHB SME Term Loan",
        "category": "sme",
        "type": "traditional_bank",
        "base_rate": 0.055,
        "rate_range": (0.055, 0.105),
        "max_tenure": 84,
        "max_amount": 2500000,
        "min_revenue": 300000,
        "required_brr_grades": [1, 2, 3, 4, 5],
        "min_dscr": 1.40,
        "min_ctos_sme_score": 660,
        "industry_allowed": ["all"],
        "industry_excluded": [],
        "features": ["Flexible repayment", "CGC support", "Halal financing option"],
        "cgc_eligible": True
    },
    
    # FINTECH SME
    "funding_societies": {
        "bank": "Funding Societies",
        "product_name": "Funding Societies SME Financing",
        "category": "sme",
        "type": "fintech",
        "base_rate": 0.068,
        "rate_range": (0.068, 0.180),
        "max_tenure": 36,
        "max_amount": 1000000,
        "min_revenue": 100000,
        "required_brr_grades": [1, 2, 3, 4, 5, 6, 7],
        "min_dscr": 1.20,
        "min_ctos_sme_score": 580,
        "industry_allowed": ["all"],
        "industry_excluded": ["oil_gas", "construction"],
        "features": ["Fast approval (24hrs)", "Minimal collateral", "Flexible terms"],
        "cgc_eligible": False
    },
    
    "aspirasi_sme": {
        "bank": "Aspirasi",
        "product_name": "Aspirasi SME Growth Loan",
        "category": "sme",
        "type": "fintech",
        "base_rate": 0.072,
        "rate_range": (0.072, 0.190),
        "max_tenure": 24,
        "max_amount": 500000,
        "min_revenue": 80000,
        "required_brr_grades": [1, 2, 3, 4, 5, 6, 7, 8],
        "min_dscr": 1.15,
        "min_ctos_sme_score": 550,
        "industry_allowed": ["all"],
        "industry_excluded": [],
        "features": ["Alternative scoring", "Quick disbursement", "Micro SME focus"],
        "cgc_eligible": False
    },
    
    "capitalbay_sme": {
        "bank": "CapitalBay",
        "product_name": "CapitalBay SME Financing",
        "category": "sme",
        "type": "fintech",
        "base_rate": 0.075,
        "rate_range": (0.075, 0.200),
        "max_tenure": 36,
        "max_amount": 800000,
        "min_revenue": 120000,
        "required_brr_grades": [1, 2, 3, 4, 5, 6, 7],
        "min_dscr": 1.25,
        "min_ctos_sme_score": 600,
        "industry_allowed": ["trading", "fnb", "retail", "services", "logistics"],
        "industry_excluded": ["construction", "property_development", "oil_gas"],
        "features": ["Invoice financing", "Trade finance", "Working capital"],
        "cgc_eligible": False
    }
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_all_personal_products() -> Dict:
    """获取所有个人贷款产品"""
    return PERSONAL_LOAN_CATALOG


def get_all_sme_products() -> Dict:
    """获取所有SME贷款产品"""
    return SME_LOAN_CATALOG


def get_product_by_id(product_id: str, category: str = "personal") -> Dict:
    """根据ID获取产品"""
    catalog = PERSONAL_LOAN_CATALOG if category == "personal" else SME_LOAN_CATALOG
    return catalog.get(product_id, {})


def filter_products_by_type(product_type: str, category: str = "personal") -> List[Dict]:
    """
    按类型过滤产品
    
    Args:
        product_type: traditional_bank, digital_bank, fintech
        category: personal, sme
    """
    catalog = PERSONAL_LOAN_CATALOG if category == "personal" else SME_LOAN_CATALOG
    return [
        {**data, "product_id": pid}
        for pid, data in catalog.items()
        if data.get("type") == product_type
    ]
