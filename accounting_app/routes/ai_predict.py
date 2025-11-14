"""
AI预测分析路由模块
Safe for AI V3 Stable Baseline - 不修改现有ai_assistant.py
"""
from fastapi import APIRouter, Request, HTTPException
from accounting_app.utils.ai_client import get_ai_client
from accounting_app.services.predict_engine import PredictEngine
from accounting_app.services.trend_engine import TrendEngine
from accounting_app.services.health_engine import HealthEngine
import sqlite3
from datetime import datetime

router = APIRouter()

DB_PATH = "db/smart_loan_manager.db"


# ----------------------------
# Helper - Save AI logs
# ----------------------------
def save_ai_log(query: str, response: str, category: str = "prediction"):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO ai_logs (query, response, created_at) VALUES (?, ?, ?)",
        (f"[{category}] {query}", response, datetime.now()),
    )
    conn.commit()
    conn.close()


# ======================================================
# 1) 未来 3 个月预测
# POST /api/ai-assistant/predict
# ======================================================
@router.post("/api/ai-assistant/predict")
async def ai_predict(request: Request):
    """
    AI预测未来3个月财务趋势
    基于monthly_statements历史数据
    """
    body = await request.json()
    customer_id = body.get("customer_id")

    if not customer_id:
        raise HTTPException(status_code=400, detail="customer_id is required")

    # 调用预测服务
    engine = PredictEngine()
    prediction = engine.predict_next_3_months(customer_id)
    
    if "error" in prediction:
        raise HTTPException(status_code=404, detail=prediction["error"])

    # AI 洞察生成（使用V3统一客户端）
    client = get_ai_client()
    
    insights_prompt = f"""
基于以下财务预测数据，生成50-120字的专业洞察建议：

历史数据：
- 平均月支出：RM {prediction['summary']['avg_monthly_expenses']}
- 平均月还款：RM {prediction['summary']['avg_monthly_payments']}
- 支出趋势：{prediction['summary']['expense_trend']}

未来3个月预测：
"""
    for p in prediction['predictions']:
        insights_prompt += f"\n- {p['statement_month']}: 预测支出 RM {p['predicted_expenses']}, 预测余额 RM {p['predicted_balance']}"
    
    insights_prompt += f"\n\n预测置信度：{prediction['confidence']*100}%"
    
    insights = client.chat(
        messages=[
            {"role": "system", "content": "你是专业财务分析师，请生成简洁、可执行的财务预测洞察。使用中文，50-120字。"},
            {"role": "user", "content": insights_prompt}
        ],
        temperature=0.7,
        max_tokens=300
    )

    # 写入AI日志
    save_ai_log(f"AI Predict customer={customer_id}", insights, "prediction")

    return {
        "prediction": prediction,
        "ai_insights": insights
    }


# ======================================================
# 2) 趋势图表数据
# GET /api/ai-assistant/trends/{customer_id}
# ======================================================
@router.get("/api/ai-assistant/trends/{customer_id}")
async def ai_trends(customer_id: int):
    """
    获取客户财务趋势图表数据
    返回最近12个月的支出、还款、余额数据
    """
    engine = TrendEngine()
    data = engine.get_trends(customer_id)

    if data["count"] == 0:
        raise HTTPException(status_code=404, detail="No trend data found")

    save_ai_log(f"AI Trends customer={customer_id}", "Trends data fetched", "trends")

    return data


# ======================================================
# 3) 财务健康评分（轻量版）
# GET /api/ai-assistant/health-score/{customer_id}
# ======================================================
@router.get("/api/ai-assistant/health-score/{customer_id}")
async def ai_health_score(customer_id: int):
    """
    计算客户财务健康评分（0-100分）
    包含AI生成的评分解释
    """
    engine = HealthEngine()
    score = engine.calculate_health_score(customer_id)

    if "error" in score:
        raise HTTPException(status_code=404, detail=score["error"])

    # AI解释评分（使用V3统一客户端）
    client = get_ai_client()
    
    explanation_prompt = f"""
客户财务健康评分数据：

总分：{score['total_score']}/100
评级：{score['grade']}
健康状态：{score['health_status']}

评分细分：
"""
    for key, item in score['breakdown'].items():
        explanation_prompt += f"\n- {item['description']}: {item['score']}/{item['max']}分 (当前值: {item['value']})"
    
    explanation_prompt += f"\n\n当前余额：RM {score['current_balance']}"
    explanation_prompt += f"\n信用额度：RM {score['credit_limit']}"
    explanation_prompt += "\n\n请用50-120字解释客户的财务健康状况并给出建议。"
    
    explanation = client.chat(
        messages=[
            {"role": "system", "content": "你是理财顾问，请用50-120字解释客户的财务健康状况。使用中文，语气专业但友好。"},
            {"role": "user", "content": explanation_prompt}
        ],
        temperature=0.7,
        max_tokens=300
    )

    save_ai_log(f"AI HealthScore customer={customer_id}", explanation, "health")

    return {
        "score": score,
        "ai_explanation": explanation
    }
