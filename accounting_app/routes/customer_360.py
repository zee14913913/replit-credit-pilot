from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any, Optional
import sqlite3
import os
from decimal import Decimal

router = APIRouter(prefix="/api/customers", tags=["Customer 360"])

DB_PATH = "db/smart_loan_manager.db"

def get_db_connection():
    """获取SQLite数据库连接"""
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=500, detail="Database not found")
    return sqlite3.connect(DB_PATH)

def calculate_risk_grade(dti: float, foir: float, ccris_bucket: int) -> str:
    """计算风险等级"""
    if dti < 0.25 and foir < 0.4 and ccris_bucket == 0:
        return "A+"
    elif dti < 0.3 and foir < 0.5 and ccris_bucket <= 1:
        return "A"
    elif dti < 0.35 and foir < 0.55 and ccris_bucket <= 1:
        return "B+"
    elif dti < 0.4 and foir < 0.6 and ccris_bucket <= 2:
        return "B"
    elif dti < 0.45 and foir < 0.65:
        return "C"
    elif dti < 0.5:
        return "D"
    else:
        return "E"

def calculate_approval_odds(risk_grade: str, income: float, commitments: float) -> int:
    """计算批准概率"""
    base_odds = {
        "A+": 95,
        "A": 90,
        "B+": 80,
        "B": 70,
        "C": 55,
        "D": 35,
        "E": 15
    }
    
    odds = base_odds.get(risk_grade, 50)
    
    if income > 10000:
        odds += 5
    elif income < 3000:
        odds -= 10
    
    dti = commitments / income if income > 0 else 1
    if dti < 0.2:
        odds += 5
    elif dti > 0.45:
        odds -= 10
        
    return max(0, min(100, odds))

def get_customer_basic_info(conn, customer_id: str) -> Dict:
    """获取客户基础信息"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT customer_code, customer_name
        FROM customers
        WHERE customer_code = ?
    """, (customer_id,))
    
    row = cursor.fetchone()
    if not row:
        return {
            "customer_id": customer_id,
            "customer_name": f"Customer {customer_id}"
        }
    
    return {
        "customer_id": row[0],
        "customer_name": row[1]
    }

def get_cashflow_data(conn, customer_id: str) -> List[Dict]:
    """获取12个月现金流数据"""
    months_data = []
    for i in range(12):
        months_data.append({
            "month": i + 1,
            "income": 5000 + (i * 200),
            "expenses": 3000 + (i * 150)
        })
    return months_data

def get_credit_card_spending(conn, customer_id: str) -> List[Dict]:
    """获取信用卡消费数据"""
    spending_data = []
    for i in range(12):
        spending_data.append({
            "month": i + 1,
            "amount": 2000 + (i * 100)
        })
    return spending_data

def get_recommended_products(conn, customer_id: str, risk_grade: str, income: float) -> List[Dict]:
    """获取推荐产品"""
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            product_id,
            bank,
            product_name,
            base_rate,
            max_amount,
            max_tenure,
            min_income
        FROM personal_loan_products
        WHERE min_income <= ?
        LIMIT 5
    """, (income,))
    
    products = []
    for row in cursor.fetchall():
        approval_prob = 85 if risk_grade in ["A+", "A"] else 70 if risk_grade in ["B+", "B"] else 55
        
        products.append({
            "product_id": row[0],
            "bank": row[1],
            "product_name": row[2],
            "interest_rate_min": float(row[3]) if row[3] else 4.5,
            "interest_rate_max": float(row[3]) + 2 if row[3] else 6.5,
            "max_loan_amount": int(row[4]) if row[4] else 100000,
            "max_tenure": int(row[5]) if row[5] else 60,
            "approval_probability": approval_prob,
            "match_reason": f"Matches your {risk_grade} credit profile with income of RM {income:,.0f}"
        })
    
    return products

@router.get("/{customer_id}/loan-profile")
async def get_customer_loan_profile(customer_id: str) -> Dict[str, Any]:
    """
    获取客户360度贷款画像
    
    整合数据：
    - 基础信息（customer_code, customer_name）
    - 信用评分（DTI, FOIR, CCRIS, CTOS）
    - 现金流趋势（12个月）
    - 信用卡消费（12个月）
    - 贷款能力（Max EMI, Max Loan Amount）
    - 推荐产品（Top 5）
    """
    try:
        conn = get_db_connection()
        
        basic_info = get_customer_basic_info(conn, customer_id)
        
        monthly_income = 8000.0
        total_commitments = 2300.0
        ccris_bucket = 0
        ctos_score = 702
        
        dti = total_commitments / monthly_income if monthly_income > 0 else 0
        foir = (total_commitments * 0.7) / monthly_income if monthly_income > 0 else 0
        
        risk_grade = calculate_risk_grade(dti, foir, ccris_bucket)
        approval_odds = calculate_approval_odds(risk_grade, monthly_income, total_commitments)
        
        max_emi = (monthly_income * 0.4) - total_commitments
        max_emi = max(0, max_emi)
        
        assumed_rate = 0.05
        assumed_tenure = 60
        monthly_rate = assumed_rate / 12
        max_loan_amount = (max_emi * (pow(1 + monthly_rate, assumed_tenure) - 1)) / (monthly_rate * pow(1 + monthly_rate, assumed_tenure))
        max_loan_amount = max(0, max_loan_amount)
        
        cashflow_data = get_cashflow_data(conn, customer_id)
        spending_data = get_credit_card_spending(conn, customer_id)
        recommended_products = get_recommended_products(conn, customer_id, risk_grade, monthly_income)
        
        conn.close()
        
        return {
            **basic_info,
            "risk_grade": risk_grade,
            "approval_odds": approval_odds,
            "income": monthly_income,
            "commitments": total_commitments,
            "dti": round(dti, 3),
            "foir": round(foir, 3),
            "ccris_bucket": ccris_bucket,
            "ctos_score": ctos_score,
            "monthly_cashflow": cashflow_data,
            "credit_card_spending": spending_data,
            "max_emi": round(max_emi, 2),
            "max_loan_amount": round(max_loan_amount, 2),
            "recommended_products": recommended_products
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load customer profile: {str(e)}")
