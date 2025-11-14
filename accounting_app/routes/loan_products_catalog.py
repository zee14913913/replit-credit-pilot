"""
Phase 9 — Loan Products Catalog API Router
统一产品目录输出端点（从数据库读取804个真实产品）
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Optional
import sqlite3
import os

router = APIRouter(prefix="/api/loan-products", tags=["Loan Products Catalog"])

DB_PATH = os.path.join(os.path.dirname(__file__), "../../db/smart_loan_manager.db")


def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def normalize_product_from_db(row: sqlite3.Row) -> dict:
    """将数据库行转换为标准产品格式"""
    import json
    
    # 解析利率范围
    rate_text = row['rate_display'] or row['rate_text'] or ""
    try:
        # 尝试从rate_text提取最小和最大利率
        if '-' in rate_text:
            parts = rate_text.replace('%', '').split('-')
            min_rate = float(parts[0].strip()) / 100
            max_rate = float(parts[1].strip()) / 100
        else:
            # 单一利率
            min_rate = max_rate = float(rate_text.replace('%', '').strip()) / 100 if rate_text else 0.06
    except:
        min_rate = max_rate = 0.06
    
    # 解析JSON字段
    def safe_json_parse(field):
        if not field:
            return []
        try:
            return json.loads(field) if isinstance(field, str) else field
        except:
            return []
    
    return {
        "product_id": row['product_id'] or f"product_{row['id']}",
        "bank": row['bank'] or "Unknown Bank",
        "product_name": row['name'] or "Unknown Product",
        "category": row['category'] or "personal",
        "type": "traditional_bank" if not row['shariah'] else "islamic_bank",
        "shariah_compliant": bool(row['shariah']),
        "interest_rate": {
            "min": min_rate,
            "max": max_rate
        },
        "base_rate": min_rate,
        "max_loan_amount": row['amount_max'] or 100000,
        "min_loan_amount": row['amount_min'] or 5000,
        "max_tenure": row['tenure_max_months'] or 84,
        "min_tenure": row['tenure_min_months'] or 12,
        "min_income": row['income_min'] or 2000,
        "age_min": row['age_min'] or 21,
        "age_max": row['age_max'] or 65,
        "dsr_max": row['dsr_max'] or 70,
        "features": safe_json_parse(row['special_features']) or [],
        "eligibility": {
            "min_credit_score": 600,
            "ccris_bucket_max": 2,
            "employment_requirement": "Salaried/Self-employed",
            "citizenship": row['citizenship'] or "Malaysian"
        },
        "fees": safe_json_parse(row['fees_charges']) or [],
        "approval_time_hours": 48,
        "digital_application": True if 'online' in str(row['channel']).lower() else False,
        "rate_range": (min_rate, max_rate),
        "description": row['description'] or "",
        "docs_required": safe_json_parse(row['docs_required']) or [],
        "special_conditions": safe_json_parse(row['special_conditions']) or [],
        "links": safe_json_parse(row['links']) or [],
        "collateral_required": bool(row['collateral_required'])
    }


@router.get("/all")
async def get_all_products():
    """
    GET /api/loan-products/all
    返回所有贷款产品（从数据库读取804个真实产品）
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT * FROM loan_products 
            ORDER BY bank, category, name
        """)
        
        rows = cursor.fetchall()
        products = [normalize_product_from_db(row) for row in rows]
        
        return {
            "total": len(products),
            "products": products,
            "source": "database",
            "message": f"Loaded {len(products)} real loan products from database"
        }
    
    finally:
        conn.close()


@router.get("/{product_id}")
async def get_product_detail(product_id: str):
    """
    GET /api/loan-products/{product_id}
    返回单个产品详情（从数据库）
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT * FROM loan_products 
            WHERE product_id = ? OR id = ?
        """, (product_id, product_id))
        
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
        
        return normalize_product_from_db(row)
    
    finally:
        conn.close()


@router.get("/filter")
async def filter_products(
    type: Optional[str] = Query(None, description="Product type: traditional_bank, islamic_bank"),
    min_rate: Optional[float] = Query(None, description="Minimum interest rate filter"),
    max_rate: Optional[float] = Query(None, description="Maximum interest rate filter"),
    category: Optional[str] = Query(None, description="Loan category: personal, sme, home, auto, business"),
    min_amount: Optional[int] = Query(None, description="Minimum loan amount"),
    max_amount: Optional[int] = Query(None, description="Maximum loan amount"),
    bank: Optional[str] = Query(None, description="Filter by bank name")
):
    """
    GET /api/loan-products/filter
    筛选产品（从数据库，支持多种筛选条件）
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 构建动态SQL查询
        query = "SELECT * FROM loan_products WHERE 1=1"
        params = []
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        if bank:
            query += " AND bank LIKE ?"
            params.append(f"%{bank}%")
        
        if min_amount:
            query += " AND amount_max >= ?"
            params.append(min_amount)
        
        if max_amount:
            query += " AND amount_min <= ?"
            params.append(max_amount)
        
        if type:
            if type == "islamic_bank":
                query += " AND shariah = 'Yes'"
            elif type == "traditional_bank":
                query += " AND (shariah IS NULL OR shariah != 'Yes')"
        
        query += " ORDER BY bank, category, name"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # 转换为标准格式
        products = [normalize_product_from_db(row) for row in rows]
        
        # 应用利率筛选（在Python中处理，因为rate_display格式不统一）
        if min_rate is not None:
            products = [p for p in products if p["interest_rate"]["min"] >= min_rate]
        
        if max_rate is not None:
            products = [p for p in products if p["interest_rate"]["max"] <= max_rate]
        
        return {
            "total": len(products),
            "filters_applied": {
                "type": type,
                "category": category,
                "bank": bank,
                "min_rate": min_rate,
                "max_rate": max_rate,
                "min_amount": min_amount,
                "max_amount": max_amount
            },
            "products": products,
            "source": "database"
        }
    
    finally:
        conn.close()


@router.get("/banks")
async def get_banks_list():
    """
    GET /api/loan-products/banks
    获取所有银行列表
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT DISTINCT bank, COUNT(*) as product_count
            FROM loan_products
            GROUP BY bank
            ORDER BY product_count DESC, bank
        """)
        
        banks = [{"name": row[0], "product_count": row[1]} for row in cursor.fetchall()]
        
        return {
            "total_banks": len(banks),
            "banks": banks
        }
    
    finally:
        conn.close()


@router.get("/categories")
async def get_categories_list():
    """
    GET /api/loan-products/categories
    获取所有产品类别
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT DISTINCT category, COUNT(*) as product_count
            FROM loan_products
            GROUP BY category
            ORDER BY product_count DESC
        """)
        
        categories = [{"name": row[0], "product_count": row[1]} for row in cursor.fetchall()]
        
        return {
            "total_categories": len(categories),
            "categories": categories
        }
    
    finally:
        conn.close()
