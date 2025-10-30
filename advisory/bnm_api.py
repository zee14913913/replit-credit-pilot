"""
Bank Negara Malaysia API - Fetches current interest rates
"""

def fetch_bnm_rates():
    """
    Fetch current BNM interest rates
    Returns dummy rates for now - can be replaced with actual API call
    """
    return {
        'opr': 3.0,  # Overnight Policy Rate
        'sbr': 5.5,  # Statutory Reserve Requirement
        'updated_at': '2025-10-30'
    }
