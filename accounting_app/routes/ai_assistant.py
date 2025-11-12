"""
AI智能助手路由
功能：跨模块财务分析（Savings + Credit Card + Loans）
"""
import os
from fastapi import APIRouter, Depends, Request, HTTPException
from datetime import datetime
import traceback
import sqlite3

router = APIRouter()

def get_openai_client():
    """获取OpenAI客户端（使用Replit集成）"""
    try:
        from openai import OpenAI
        api_key = os.getenv("AI_INTEGRATIONS_OPENAI_API_KEY")
        base_url = os.getenv("AI_INTEGRATIONS_OPENAI_BASE_URL", "https://api.openai.com/v1")
        
        if not api_key:
            raise ValueError("OpenAI API密钥未配置")
        
        return OpenAI(api_key=api_key, base_url=base_url)
    except Exception as e:
        print(f"❌ OpenAI客户端初始化失败: {e}")
        raise

@router.post("/api/ai-assistant/query")
async def ai_assistant_query(request: Request):
    """
    智能问答接口
    功能：基于储蓄账户数据回答用户问题
    """
    try:
        body = await request.json()
        msg = body.get("message", "")
        
        if not msg or not msg.strip():
            return {"error": "请输入问题"}
        
        # 连接SQLite数据库
        db = sqlite3.connect('db/smart_loan_manager.db')
        db.row_factory = sqlite3.Row
        cursor = db.cursor()
        
        # 获取储蓄账户统计数据
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT sa.id) as total_accounts,
                COUNT(DISTINCT st.id) as total_transactions,
                COALESCE(SUM(CASE WHEN st.transaction_type = 'CR' THEN st.amount ELSE 0 END), 0) as total_credits,
                COALESCE(SUM(CASE WHEN st.transaction_type = 'DR' THEN st.amount ELSE 0 END), 0) as total_debits
            FROM savings_accounts sa
            LEFT JOIN savings_statements ss ON sa.id = ss.savings_account_id
            LEFT JOIN savings_transactions st ON ss.id = st.savings_statement_id
        """)
        savings_data = dict(cursor.fetchone())
        
        # 构建上下文
        context = f"""
储蓄账户概况：
- 账户数量：{savings_data['total_accounts']}个
- 交易记录：{savings_data['total_transactions']}笔
- 总收入（CR）：RM {savings_data['total_credits']:.2f}
- 总支出（DR）：RM {savings_data['total_debits']:.2f}
- 净余额：RM {(savings_data['total_credits'] - savings_data['total_debits']):.2f}

客户提问：{msg}
"""
        
        # 调用OpenAI
        client = get_openai_client()
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": "你是CreditPilot智能理财助手。请基于储蓄账户数据给出专业分析和建议。回答要简洁、专业、有建设性。使用中文回复。"
                },
                {
                    "role": "user", 
                    "content": context
                }
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        reply = completion.choices[0].message.content
        
        # 记录到数据库
        cursor.execute("""
            INSERT INTO ai_logs (query, response, created_at)
            VALUES (?, ?, ?)
        """, (msg, reply, datetime.utcnow().isoformat()))
        db.commit()
        db.close()
        
        return {"reply": reply, "timestamp": datetime.utcnow().isoformat()}
        
    except Exception as e:
        traceback.print_exc()
        return {"error": f"AI助手错误: {str(e)}"}


@router.post("/api/ai-assistant/analyze-system")
async def analyze_system(request: Request):
    """
    跨模块财务分析接口
    功能：分析Savings + Credit Card + Loans整体财务健康状况
    """
    try:
        # 连接SQLite数据库
        db = sqlite3.connect('db/smart_loan_manager.db')
        db.row_factory = sqlite3.Row
        cursor = db.cursor()
        
        # 1. 储蓄账户统计
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT sa.id) as accounts,
                COALESCE(SUM(CASE WHEN st.transaction_type = 'CR' THEN st.amount ELSE 0 END), 0) as total_credits,
                COALESCE(SUM(CASE WHEN st.transaction_type = 'DR' THEN st.amount ELSE 0 END), 0) as total_debits
            FROM savings_accounts sa
            LEFT JOIN savings_statements ss ON sa.id = ss.savings_account_id
            LEFT JOIN savings_transactions st ON ss.id = st.savings_statement_id
        """)
        savings = dict(cursor.fetchone())
        savings_balance = savings['total_credits'] - savings['total_debits']
        
        # 2. 信用卡统计（从月结单获取最新余额）
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='monthly_statements'")
        if cursor.fetchone():
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT cc.id) as cards,
                    COALESCE(SUM(cc.credit_limit), 0) as total_limit,
                    COALESCE(
                        (SELECT SUM(closing_balance_total) 
                         FROM monthly_statements 
                         WHERE id IN (
                             SELECT MAX(id) FROM monthly_statements GROUP BY customer_id, bank_name
                         )), 0
                    ) as total_balance
                FROM credit_cards cc
            """)
            credit = dict(cursor.fetchone())
        else:
            credit = {"cards": 0, "total_limit": 0, "total_balance": 0}
        
        # 3. 贷款统计（如果表存在）
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='loans'")
        if cursor.fetchone():
            cursor.execute("""
                SELECT 
                    COUNT(*) as loans,
                    COALESCE(SUM(loan_amount), 0) as total_amount,
                    COALESCE(SUM(remaining_balance), 0) as total_remaining
                FROM loans
            """)
            loans = dict(cursor.fetchone())
        else:
            loans = {"loans": 0, "total_amount": 0, "total_remaining": 0}
        
        # 构建综合分析上下文
        context = f"""
请生成整体财务健康分析报告：

💰 储蓄账户：
- 账户数：{savings['accounts']}个
- 总收入：RM {savings['total_credits']:.2f}
- 总支出：RM {savings['total_debits']:.2f}
- 净余额：RM {savings_balance:.2f}

💳 信用卡：
- 卡数量：{credit['cards']}张
- 总额度：RM {credit['total_limit']:.2f}
- 当前欠款：RM {credit['total_balance']:.2f}
- 使用率：{(credit['total_balance']/credit['total_limit']*100 if credit['total_limit'] > 0 else 0):.1f}%

🏦 贷款：
- 贷款数：{loans['loans']}笔
- 总贷款额：RM {loans['total_amount']:.2f}
- 剩余欠款：RM {loans['total_remaining']:.2f}

请分析：
1. 整体资金流动性
2. 债务健康度
3. 优化建议
"""
        
        # 调用OpenAI生成报告
        client = get_openai_client()
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "你是一名专业财务分析师。请评估企业资金结构和流动性趋势，给出专业的财务健康分析报告。使用中文，格式清晰，包含具体数字和建议。"
                },
                {
                    "role": "user",
                    "content": context
                }
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        report = completion.choices[0].message.content
        
        # 记录到数据库
        cursor.execute("""
            INSERT INTO ai_logs (query, response, created_at)
            VALUES (?, ?, ?)
        """, ("系统财务分析", report, datetime.utcnow().isoformat()))
        db.commit()
        db.close()
        
        return {
            "analysis": report,
            "data": {
                "savings": {
                    "accounts": savings['accounts'],
                    "balance": round(savings_balance, 2)
                },
                "credit_cards": {
                    "cards": credit['cards'],
                    "balance": round(credit['total_balance'], 2),
                    "limit": round(credit['total_limit'], 2)
                },
                "loans": {
                    "count": loans['loans'],
                    "total_amount": round(loans['total_amount'], 2),
                    "remaining": round(loans['total_remaining'], 2)
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        traceback.print_exc()
        return {"error": f"系统分析错误: {str(e)}"}


@router.get("/api/ai-assistant/history")
async def get_ai_history(limit: int = 20):
    """
    获取AI对话历史
    """
    try:
        db = sqlite3.connect('db/smart_loan_manager.db')
        db.row_factory = sqlite3.Row
        cursor = db.cursor()
        
        cursor.execute("""
            SELECT id, query, response, created_at
            FROM ai_logs
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        
        history = [dict(row) for row in cursor.fetchall()]
        db.close()
        
        return {"history": history}
        
    except Exception as e:
        return {"error": f"获取历史记录失败: {str(e)}"}


@router.get("/api/ai-assistant/reports")
async def get_recent_ai_reports():
    """
    返回最近7天的AI日报摘要，用于Dashboard展示
    V2企业智能版新增
    """
    try:
        db = sqlite3.connect('db/smart_loan_manager.db')
        db.row_factory = sqlite3.Row
        cursor = db.cursor()
        
        cursor.execute("""
            SELECT query, response, created_at
            FROM ai_logs
            WHERE query LIKE 'AI日报%'
            ORDER BY created_at DESC
            LIMIT 7
        """)
        
        rows = cursor.fetchall()
        
        reports = []
        for r in rows:
            # 提取日期
            created_at = r["created_at"]
            if isinstance(created_at, str):
                date = created_at.split("T")[0] if "T" in created_at else created_at.split(" ")[0]
            else:
                date = str(created_at).split(" ")[0]
            
            # 截取摘要（前120字符）
            summary = r["response"][:120].replace("\n", " ").replace("*", "").strip()
            if len(r["response"]) > 120:
                summary += "..."
            
            reports.append({
                "date": date,
                "summary": summary
            })
        
        db.close()
        
        return {"reports": reports, "total": len(reports)}
        
    except Exception as e:
        traceback.print_exc()
        return {"error": f"获取日报失败: {str(e)}", "reports": []}
