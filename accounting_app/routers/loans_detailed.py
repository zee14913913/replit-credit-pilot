"""
贷款产品详细信息API路由
支持12个详细字段的查询和导出
"""
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
import sqlite3
import csv
import io
import os
from typing import List, Optional

router = APIRouter(prefix="/loans/detailed", tags=["Loans Detailed"])

DB = os.getenv("LOANS_DB_PATH", "/home/runner/loans.db")

def _conn():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


@router.get("/", summary="获取详细贷款产品列表（12个字段）")
def list_detailed_products(
    q: Optional[str] = Query(None, description="搜索关键词"),
    company: Optional[str] = Query(None, description="按公司筛选"),
    loan_type: Optional[str] = Query(None, description="按贷款类型筛选"),
    institution_type: Optional[str] = Query(None, description="按机构类型筛选"),
    preferred_customer: Optional[str] = Query(None, description="按客户偏好筛选"),
    limit: int = Query(100, description="返回记录数")
):
    """
    获取包含12个详细字段的贷款产品列表
    
    字段说明：
    1. company - 金融机构
    2. loan_type - 贷款类型
    3. required_doc - 所需文件
    4. features - 产品特点
    5. benefits - 产品优势
    6. fees_charges - 费用与收费
    7. tenure - 贷款期限
    8. rate - 利率
    9. application_form_url - 申请表链接
    10. product_disclosure_url - 产品披露链接
    11. terms_conditions_url - 条款与条件链接
    12. preferred_customer_type - 借贷人偏好
    """
    con = _conn()
    cur = con.cursor()
    
    # 构建查询
    query = "SELECT * FROM loan_products_detailed WHERE 1=1"
    params = []
    
    # 关键词搜索
    if q:
        query += """ AND (
            company LIKE ? OR 
            product_name LIKE ? OR 
            loan_type LIKE ? OR 
            features LIKE ? OR 
            benefits LIKE ?
        )"""
        like_param = f"%{q}%"
        params.extend([like_param] * 5)
    
    # 公司筛选
    if company:
        query += " AND company LIKE ?"
        params.append(f"%{company}%")
    
    # 贷款类型筛选
    if loan_type:
        query += " AND loan_type LIKE ?"
        params.append(f"%{loan_type}%")
    
    # 机构类型筛选
    if institution_type:
        query += " AND institution_type = ?"
        params.append(institution_type)
    
    # 客户偏好筛选
    if preferred_customer:
        query += " AND preferred_customer_type LIKE ?"
        params.append(f"%{preferred_customer}%")
    
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    
    # 执行查询
    cur.execute(query, params)
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    
    return JSONResponse({
        "total": len(rows),
        "data": rows
    })


@router.get("/export.csv", summary="导出详细产品数据为CSV")
def export_detailed_csv(
    q: Optional[str] = Query(None),
    company: Optional[str] = Query(None),
    loan_type: Optional[str] = Query(None),
    limit: int = Query(1000)
):
    """导出包含12个字段的CSV文件"""
    con = _conn()
    cur = con.cursor()
    
    # 构建查询（与list接口相同逻辑）
    query = "SELECT * FROM loan_products_detailed WHERE 1=1"
    params = []
    
    if q:
        query += " AND (company LIKE ? OR product_name LIKE ? OR loan_type LIKE ?)"
        like_param = f"%{q}%"
        params.extend([like_param] * 3)
    
    if company:
        query += " AND company LIKE ?"
        params.append(f"%{company}%")
    
    if loan_type:
        query += " AND loan_type LIKE ?"
        params.append(f"%{loan_type}%")
    
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    
    cur.execute(query, params)
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    
    # 生成CSV
    if not rows:
        raise HTTPException(404, "No products found")
    
    output = io.StringIO()
    fieldnames = [
        'id', 'company', 'loan_type', 'product_name',
        'required_doc', 'features', 'benefits', 'fees_charges',
        'tenure', 'rate', 'application_form_url', 
        'product_disclosure_url', 'terms_conditions_url',
        'preferred_customer_type', 'institution_type',
        'source_url', 'pulled_at'
    ]
    
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    
    csv_data = output.getvalue().encode('utf-8-sig')
    
    return StreamingResponse(
        iter([csv_data]),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=malaysia_loans_detailed.csv",
            "Cache-Control": "private, max-age=600"
        }
    )


@router.get("/{product_id}", summary="获取单个产品完整详情")
def get_product_details(product_id: int):
    """获取单个贷款产品的完整12个字段详情"""
    con = _conn()
    cur = con.cursor()
    
    cur.execute("SELECT * FROM loan_products_detailed WHERE id = ?", (product_id,))
    row = cur.fetchone()
    con.close()
    
    if not row:
        raise HTTPException(404, f"Product ID {product_id} not found")
    
    return JSONResponse(dict(row))


@router.get("/stats/summary", summary="数据统计摘要")
def get_stats():
    """
    获取数据库统计摘要
    - 总产品数
    - 按机构类型分组
    - 按贷款类型分组
    - 按客户偏好分组
    """
    con = _conn()
    cur = con.cursor()
    
    # 总数
    cur.execute("SELECT COUNT(*) as total FROM loan_products_detailed")
    total = cur.fetchone()['total']
    
    # 按机构类型
    cur.execute("""
        SELECT institution_type, COUNT(*) as count 
        FROM loan_products_detailed 
        GROUP BY institution_type
    """)
    by_institution = [dict(r) for r in cur.fetchall()]
    
    # 按贷款类型
    cur.execute("""
        SELECT loan_type, COUNT(*) as count 
        FROM loan_products_detailed 
        GROUP BY loan_type 
        ORDER BY count DESC
    """)
    by_loan_type = [dict(r) for r in cur.fetchall()]
    
    # 按客户偏好
    cur.execute("""
        SELECT preferred_customer_type, COUNT(*) as count 
        FROM loan_products_detailed 
        GROUP BY preferred_customer_type 
        ORDER BY count DESC
    """)
    by_customer = [dict(r) for r in cur.fetchall()]
    
    con.close()
    
    return JSONResponse({
        "total_products": total,
        "by_institution_type": by_institution,
        "by_loan_type": by_loan_type,
        "by_preferred_customer": by_customer
    })
