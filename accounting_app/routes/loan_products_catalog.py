"""
Phase 9 — Loan Products Catalog API Router
统一产品目录输出端点（Personal + SME）
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Optional
from ..services.risk_engine.product_catalog import (
    PERSONAL_LOAN_CATALOG,
    SME_LOAN_CATALOG
)

router = APIRouter(prefix="/api/loan-products", tags=["Loan Products Catalog"])


def normalize_product(product_id: str, product_data: dict, category: str) -> dict:
    """统一产品数据格式"""
    rate_range = product_data.get("rate_range", (product_data.get("base_rate", 0), product_data.get("base_rate", 0)))
    
    return {
        "product_id": product_id,
        "bank": product_data.get("bank", "Unknown"),
        "product_name": product_data.get("product_name", "Unknown Product"),
        "category": category,
        "type": product_data.get("type", "traditional_bank"),
        "interest_rate": {
            "min": rate_range[0],
            "max": rate_range[1]
        },
        "base_rate": product_data.get("base_rate", rate_range[0]),
        "max_loan_amount": product_data.get("max_amount", 0),
        "max_tenure": product_data.get("max_tenure", 0),
        "min_income": product_data.get("min_income") or product_data.get("min_revenue"),
        "features": product_data.get("features", []),
        "eligibility": {
            "min_credit_score": product_data.get("min_credit_score"),
            "ccris_bucket_max": product_data.get("ccris_bucket_max"),
            "employment_requirement": product_data.get("employment_requirement", "Salaried/Self-employed"),
        },
        "fees": product_data.get("fees", []),
        "approval_time_hours": product_data.get("approval_time_hours", 48),
        "digital_application": product_data.get("digital_application", False),
        "rate_range": rate_range
    }


@router.get("/all")
async def get_all_products():
    """
    GET /api/loan-products/all
    返回所有贷款产品（Personal + SME合并）
    """
    products = []
    
    # Personal loans
    for product_id, product_data in PERSONAL_LOAN_CATALOG.items():
        products.append(normalize_product(product_id, product_data, "personal"))
    
    # SME loans
    for product_id, product_data in SME_LOAN_CATALOG.items():
        products.append(normalize_product(product_id, product_data, "sme"))
    
    return {
        "total": len(products),
        "products": products
    }


@router.get("/{product_id}")
async def get_product_detail(product_id: str):
    """
    GET /api/loan-products/{product_id}
    返回单个产品详情
    """
    # Search in personal loans
    if product_id in PERSONAL_LOAN_CATALOG:
        product = normalize_product(product_id, PERSONAL_LOAN_CATALOG[product_id], "personal")
        return product
    
    # Search in SME loans
    if product_id in SME_LOAN_CATALOG:
        product = normalize_product(product_id, SME_LOAN_CATALOG[product_id], "sme")
        return product
    
    raise HTTPException(status_code=404, detail=f"Product {product_id} not found")


@router.get("/filter")
async def filter_products(
    type: Optional[str] = Query(None, description="Product type: traditional_bank, digital_bank, fintech"),
    min_rate: Optional[float] = Query(None, description="Minimum interest rate filter"),
    max_rate: Optional[float] = Query(None, description="Maximum interest rate filter"),
    category: Optional[str] = Query(None, description="Loan category: personal, sme"),
    min_amount: Optional[int] = Query(None, description="Minimum loan amount"),
    max_amount: Optional[int] = Query(None, description="Maximum loan amount")
):
    """
    GET /api/loan-products/filter
    筛选产品（按类型、利率范围、贷款类别等）
    """
    products = []
    
    # Collect all products
    for product_id, product_data in PERSONAL_LOAN_CATALOG.items():
        products.append(normalize_product(product_id, product_data, "personal"))
    
    for product_id, product_data in SME_LOAN_CATALOG.items():
        products.append(normalize_product(product_id, product_data, "sme"))
    
    # Apply filters
    filtered = products
    
    if type:
        filtered = [p for p in filtered if p["type"] == type]
    
    if category:
        filtered = [p for p in filtered if p["category"] == category]
    
    if min_rate is not None:
        filtered = [p for p in filtered if p["interest_rate"]["min"] >= min_rate]
    
    if max_rate is not None:
        filtered = [p for p in filtered if p["interest_rate"]["max"] <= max_rate]
    
    if min_amount is not None:
        filtered = [p for p in filtered if p["max_loan_amount"] >= min_amount]
    
    if max_amount is not None:
        filtered = [p for p in filtered if p["max_loan_amount"] <= max_amount]
    
    return {
        "total": len(filtered),
        "filters_applied": {
            "type": type,
            "category": category,
            "min_rate": min_rate,
            "max_rate": max_rate,
            "min_amount": min_amount,
            "max_amount": max_amount
        },
        "products": filtered
    }
