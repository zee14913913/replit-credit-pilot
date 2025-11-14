"""
Risk Tables - 马来西亚银行风控标准表
包含真实银行DTI/FOIR/DSCR限制和数字银行标准
"""

# =================================================================
# PERSONAL LOAN - DTI/FOIR LIMITS (马来西亚主要银行)
# =================================================================

BANK_DTI_LIMITS = {
    # 传统银行
    "maybank": {
        "name": "Maybank",
        "max_dti": 0.50,
        "min_income": 2000,
        "max_tenure": 84,
        "interest_rate_range": (0.065, 0.12)
    },
    "cimb": {
        "name": "CIMB Bank",
        "max_foir": 0.60,
        "min_income": 2500,
        "max_tenure": 84,
        "interest_rate_range": (0.068, 0.115)
    },
    "public_bank": {
        "name": "Public Bank",
        "max_dti": 0.55,
        "min_income": 2000,
        "max_tenure": 72,
        "interest_rate_range": (0.07, 0.13)
    },
    "hong_leong": {
        "name": "Hong Leong Bank",
        "max_dti": 0.55,
        "min_income": 2000,
        "max_tenure": 84,
        "interest_rate_range": (0.069, 0.125)
    },
    "rhb": {
        "name": "RHB Bank",
        "max_dti": 0.50,
        "min_income": 2000,
        "max_tenure": 72,
        "interest_rate_range": (0.072, 0.13)
    },
    "alliance": {
        "name": "Alliance Bank",
        "max_foir": 0.60,
        "min_income": 3000,
        "max_tenure": 60,
        "interest_rate_range": (0.075, 0.14)
    },
    "ambank": {
        "name": "AmBank",
        "max_dti": 0.55,
        "min_income": 2500,
        "max_tenure": 72,
        "interest_rate_range": (0.07, 0.125)
    },
    "standard_chartered": {
        "name": "Standard Chartered",
        "max_dti": 0.55,
        "min_income": 3000,
        "max_tenure": 60,
        "interest_rate_range": (0.08, 0.15)
    },
    
    # 数字银行 (Digital Banks)
    "gxbank": {
        "name": "GXBank",
        "max_dti": 0.65,  # 更灵活
        "min_income": 1500,
        "max_tenure": 60,
        "interest_rate_range": (0.06, 0.11),
        "risk_band_based": True
    },
    "boost_bank": {
        "name": "Boost Bank",
        "max_dti": 0.60,
        "min_income": 1800,
        "max_tenure": 48,
        "interest_rate_range": (0.065, 0.12),
        "risk_band_based": True
    },
    
    # Fintech (BNPL & Personal Loan)
    "aeon_credit": {
        "name": "AEON Credit",
        "max_dti": 0.60,
        "min_income": 1500,
        "max_tenure": 60,
        "interest_rate_range": (0.08, 0.18)
    },
    "grab_paylater": {
        "name": "Grab PayLater",
        "max_dti": 0.70,  # 高风险容忍
        "min_income": 1000,
        "max_tenure": 36,
        "interest_rate_range": (0.10, 0.20),
        "risk_score_based": True
    }
}

# =================================================================
# CCRIS BEHAVIOUR SCORE MAPPING
# =================================================================

CCRIS_BUCKET_RISK = {
    "0_bucket": {
        "bucket_range": "0",
        "risk_level": "Excellent",
        "risk_score": 1,
        "dti_adjustment": -0.05,  # 可以给予更高DTI
        "approval_probability": 0.95
    },
    "1_bucket": {
        "bucket_range": "1",
        "risk_level": "Good",
        "risk_score": 3,
        "dti_adjustment": 0.0,
        "approval_probability": 0.85
    },
    "2_bucket": {
        "bucket_range": "2",
        "risk_level": "Medium",
        "risk_score": 6,
        "dti_adjustment": 0.05,  # 降低DTI限制
        "approval_probability": 0.60
    },
    "3_bucket": {
        "bucket_range": "3+",
        "risk_level": "High Risk",
        "risk_score": 9,
        "dti_adjustment": 0.10,
        "approval_probability": 0.30
    }
}

# =================================================================
# SME LOAN - DSCR/DSR LIMITS (马来西亚SME标准)
# =================================================================

SME_BANK_STANDARDS = {
    "maybank_sme": {
        "name": "Maybank SME",
        "min_dscr": 1.25,
        "min_dsr": 1.20,
        "max_cashflow_variance": 0.40,
        "min_ctos_sme_score": 600,
        "max_loan_amount": 5000000,
        "max_tenure": 84,
        "interest_rate_range": (0.055, 0.09)
    },
    "cimb_sme": {
        "name": "CIMB SME",
        "min_dscr": 1.30,
        "min_dsr": 1.25,
        "max_cashflow_variance": 0.35,
        "min_ctos_sme_score": 650,
        "max_loan_amount": 3000000,
        "max_tenure": 72,
        "interest_rate_range": (0.058, 0.095)
    },
    "public_bank_sme": {
        "name": "Public Bank Bizz",
        "min_dscr": 1.25,
        "min_dsr": 1.20,
        "max_cashflow_variance": 0.40,
        "min_ctos_sme_score": 600,
        "max_loan_amount": 5000000,
        "max_tenure": 84,
        "interest_rate_range": (0.056, 0.088)
    },
    "rhb_sme": {
        "name": "RHB SME",
        "min_dscr": 1.25,
        "min_dsr": 1.15,
        "max_cashflow_variance": 0.45,
        "min_ctos_sme_score": 550,
        "max_loan_amount": 2000000,
        "max_tenure": 60,
        "interest_rate_range": (0.06, 0.10)
    },
    
    # Fintech SME
    "funding_societies": {
        "name": "Funding Societies",
        "min_dscr": 1.15,
        "min_dsr": 1.10,
        "max_cashflow_variance": 0.50,
        "min_ctos_sme_score": 500,
        "max_loan_amount": 1000000,
        "max_tenure": 36,
        "interest_rate_range": (0.08, 0.18),
        "alternative_data": True
    },
    "boost_credit": {
        "name": "Boost Credit",
        "min_dscr": 1.10,
        "min_dsr": 1.00,
        "max_cashflow_variance": 0.55,
        "min_ctos_sme_score": 450,
        "max_loan_amount": 500000,
        "max_tenure": 24,
        "interest_rate_range": (0.10, 0.22),
        "alternative_data": True
    }
}

# =================================================================
# CTOS SME SCORE BANDS
# =================================================================

CTOS_SME_SCORE_BANDS = {
    "excellent": {
        "score_range": (750, 999),
        "risk_level": "Excellent",
        "brr_grade": "1-2",
        "approval_probability": 0.95,
        "rate_discount": 0.015
    },
    "good": {
        "score_range": (650, 749),
        "risk_level": "Good",
        "brr_grade": "3-4",
        "approval_probability": 0.85,
        "rate_discount": 0.01
    },
    "fair": {
        "score_range": (550, 649),
        "risk_level": "Fair",
        "brr_grade": "5-6",
        "approval_probability": 0.65,
        "rate_discount": 0.0
    },
    "poor": {
        "score_range": (450, 549),
        "risk_level": "Poor",
        "brr_grade": "7-8",
        "approval_probability": 0.40,
        "rate_discount": -0.02
    },
    "high_risk": {
        "score_range": (0, 449),
        "risk_level": "High Risk",
        "brr_grade": "9-10",
        "approval_probability": 0.15,
        "rate_discount": -0.05
    }
}

# =================================================================
# BNM INDUSTRY SECTOR RISK (Bank Negara Malaysia Standard)
# =================================================================

BNM_INDUSTRY_RISK = {
    # Low Risk (1-3)
    "professional_services": {
        "sector": "Professional Services",
        "risk_level": "Low",
        "risk_score": 2,
        "max_exposure_multiplier": 1.5,
        "cgc_eligible": True
    },
    "healthcare": {
        "sector": "Healthcare",
        "risk_level": "Low",
        "risk_score": 2,
        "max_exposure_multiplier": 1.5,
        "cgc_eligible": True
    },
    "education": {
        "sector": "Education",
        "risk_level": "Low",
        "risk_score": 2,
        "max_exposure_multiplier": 1.4,
        "cgc_eligible": True
    },
    
    # Medium Risk (4-6)
    "trading": {
        "sector": "Trading",
        "risk_level": "Medium",
        "risk_score": 5,
        "max_exposure_multiplier": 1.2,
        "cgc_eligible": True
    },
    "retail": {
        "sector": "Retail",
        "risk_level": "Medium",
        "risk_score": 5,
        "max_exposure_multiplier": 1.2,
        "cgc_eligible": True
    },
    "fnb": {
        "sector": "F&B",
        "risk_level": "Medium",
        "risk_score": 6,
        "max_exposure_multiplier": 1.1,
        "cgc_eligible": True
    },
    "manufacturing": {
        "sector": "Manufacturing",
        "risk_level": "Medium",
        "risk_score": 5,
        "max_exposure_multiplier": 1.3,
        "cgc_eligible": True
    },
    
    # High Risk (7-10)
    "construction": {
        "sector": "Construction",
        "risk_level": "High",
        "risk_score": 8,
        "max_exposure_multiplier": 0.9,
        "cgc_eligible": False
    },
    "property_development": {
        "sector": "Property Development",
        "risk_level": "High",
        "risk_score": 7,
        "max_exposure_multiplier": 1.0,
        "cgc_eligible": False
    },
    "agriculture": {
        "sector": "Agriculture",
        "risk_level": "High",
        "risk_score": 7,
        "max_exposure_multiplier": 1.1,
        "cgc_eligible": True
    },
    "tourism_hospitality": {
        "sector": "Tourism & Hospitality",
        "risk_level": "High",
        "risk_score": 8,
        "max_exposure_multiplier": 0.8,
        "cgc_eligible": False
    }
}

# =================================================================
# DIGITAL BANK RISK BAND TIERS
# =================================================================

DIGITAL_BANK_RISK_BANDS = {
    "band_a": {
        "name": "Band A - Premium",
        "min_credit_score": 750,
        "max_dti": 0.65,
        "max_emi_multiplier": 1.2,
        "interest_discount": 0.02,
        "approval_probability": 0.95
    },
    "band_b": {
        "name": "Band B - Standard",
        "min_credit_score": 650,
        "max_dti": 0.60,
        "max_emi_multiplier": 1.0,
        "interest_discount": 0.0,
        "approval_probability": 0.80
    },
    "band_c": {
        "name": "Band C - Subprime",
        "min_credit_score": 550,
        "max_dti": 0.50,
        "max_emi_multiplier": 0.8,
        "interest_discount": -0.02,
        "approval_probability": 0.55
    },
    "band_d": {
        "name": "Band D - High Risk",
        "min_credit_score": 0,
        "max_dti": 0.40,
        "max_emi_multiplier": 0.6,
        "interest_discount": -0.05,
        "approval_probability": 0.30
    }
}

# =================================================================
# CGC (Credit Guarantee Corporation) ELIGIBILITY
# =================================================================

CGC_ELIGIBILITY_CRITERIA = {
    "sme_financing": {
        "max_loan_amount": 5000000,
        "guarantee_coverage": 0.80,  # 80% coverage
        "eligible_sectors": ["manufacturing", "trading", "services", "agriculture"],
        "min_business_age_years": 2
    },
    "micro_enterprises": {
        "max_loan_amount": 500000,
        "guarantee_coverage": 0.90,  # 90% coverage
        "eligible_sectors": ["all"],
        "min_business_age_years": 1
    }
}
