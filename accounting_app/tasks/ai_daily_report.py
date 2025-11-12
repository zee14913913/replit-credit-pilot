"""
AI财务日报自动生成系统
功能：每天早上08:00自动生成财务健康日报
"""
import os
import sqlite3
from datetime import datetime, timedelta
from openai import OpenAI


def get_openai_client():
    """获取OpenAI客户端（使用Replit集成）"""
    api_key = os.getenv("AI_INTEGRATIONS_OPENAI_API_KEY")
    base_url = os.getenv("AI_INTEGRATIONS_OPENAI_BASE_URL", "https://api.openai.com/v1")
    
    if not api_key:
        raise ValueError("OpenAI API密钥未配置")
    
    return OpenAI(api_key=api_key, base_url=base_url)


def generate_daily_report():
    """
    生成AI财务日报
    
    功能：
    1. 汇总昨日储蓄、信用卡、贷款数据
    2. 调用OpenAI生成日报摘要
    3. 存入ai_logs表
    4. 输出控制台日志
    """
    try:
        # 连接SQLite数据库
        db = sqlite3.connect('db/smart_loan_manager.db')
        db.row_factory = sqlite3.Row
        cursor = db.cursor()
        
        # 计算日期
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)
        
        print(f"\n{'='*50}")
        print(f"🤖 正在生成AI财务日报：{yesterday}")
        print(f"{'='*50}")
        
        # 1. 储蓄账户昨日交易统计
        cursor.execute("""
            SELECT 
                COUNT(*) as transaction_count,
                COALESCE(SUM(CASE WHEN transaction_type = 'CR' THEN amount ELSE 0 END), 0) as total_credits,
                COALESCE(SUM(CASE WHEN transaction_type = 'DR' THEN amount ELSE 0 END), 0) as total_debits
            FROM savings_transactions
            WHERE DATE(created_at) = ?
        """, (str(yesterday),))
        savings = dict(cursor.fetchone())
        
        # 2. 信用卡当前状态（从月结单获取最新余额）
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
        
        # 3. 贷款当前状态
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
        
        # 打印数据摘要
        print(f"\n📊 数据摘要：")
        print(f"  💰 储蓄交易：{savings['transaction_count']}笔 (收入RM {savings['total_credits']:.2f}, 支出RM {savings['total_debits']:.2f})")
        print(f"  💳 信用卡：{credit['cards']}张 (余额RM {credit['total_balance']:.2f} / 额度RM {credit['total_limit']:.2f})")
        print(f"  🏦 贷款：{loans['loans']}笔 (欠款RM {loans['total_remaining']:.2f})")
        
        # 构建AI提示词
        net_savings = savings['total_credits'] - savings['total_debits']
        credit_usage = (credit['total_balance'] / credit['total_limit'] * 100) if credit['total_limit'] > 0 else 0
        
        context = f"""
日期：{yesterday}

昨日财务数据概况：
1. 储蓄账户
   - 交易笔数：{savings['transaction_count']}笔
   - 收入：RM {savings['total_credits']:.2f}
   - 支出：RM {savings['total_debits']:.2f}
   - 净变化：RM {net_savings:.2f}

2. 信用卡
   - 卡数量：{credit['cards']}张
   - 当前欠款：RM {credit['total_balance']:.2f}
   - 总额度：RM {credit['total_limit']:.2f}
   - 使用率：{credit_usage:.1f}%

3. 贷款
   - 贷款数：{loans['loans']}笔
   - 剩余欠款：RM {loans['total_remaining']:.2f}

请生成一份简洁的财务日报摘要（200字以内），包含：
1. 昨日资金变化总结
2. 当前财务健康度评估
3. 一条具体的优化建议
"""
        
        # 调用OpenAI生成日报
        print(f"\n🤖 正在调用AI生成日报...")
        client = get_openai_client()
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "你是CreditPilot系统的AI财务分析师。请生成每日财务报告，用简洁、专业、易懂的语气描述资金变化与建议。回答要控制在200字以内。"
                },
                {
                    "role": "user",
                    "content": context
                }
            ],
            temperature=0.7,
            max_tokens=400
        )
        
        report = completion.choices[0].message.content
        
        # 存入ai_logs表
        cursor.execute("""
            INSERT INTO ai_logs (query, response, created_at)
            VALUES (?, ?, ?)
        """, (f"AI日报 {yesterday}", report, datetime.utcnow().isoformat()))
        db.commit()
        
        # 输出成功日志
        print(f"\n✅ AI日报已生成并存储")
        print(f"{'='*50}")
        print(f"\n📄 日报内容：\n")
        print(report)
        print(f"\n{'='*50}\n")
        
        db.close()
        return report
        
    except Exception as e:
        print(f"\n❌ AI日报生成失败：{str(e)}")
        import traceback
        traceback.print_exc()
        return None


# 支持直接运行测试
if __name__ == "__main__":
    print("🧪 手动测试AI日报生成...")
    generate_daily_report()
