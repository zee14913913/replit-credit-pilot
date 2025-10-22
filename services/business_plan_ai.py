"""
AI Business Plan Generator
使用OpenAI分析客户资源、人脉和技能，生成个性化商业计划建议
"""

import os
import json
from openai import OpenAI
from db.database import get_db

# This is using Replit's AI Integrations service, which provides OpenAI-compatible API access without requiring your own OpenAI API key.
# the newest OpenAI model is "gpt-5" which was released August 7, 2025. do not change this unless explicitly requested by the user

def get_openai_client():
    """获取OpenAI客户端（延迟初始化）"""
    AI_INTEGRATIONS_OPENAI_API_KEY = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY")
    AI_INTEGRATIONS_OPENAI_BASE_URL = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
    
    if not AI_INTEGRATIONS_OPENAI_API_KEY or not AI_INTEGRATIONS_OPENAI_BASE_URL:
        raise Exception("OpenAI集成未配置，请联系管理员")
    
    return OpenAI(
        api_key=AI_INTEGRATIONS_OPENAI_API_KEY,
        base_url=AI_INTEGRATIONS_OPENAI_BASE_URL
    )


def generate_business_plan(customer_id: int) -> dict:
    """
    分析客户的资源、人脉和技能，生成AI商业计划建议
    
    Returns:
        {
            'success': bool,
            'plan_id': int (如果成功),
            'error': str (如果失败)
        }
    """
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 1. 获取客户基本信息
        cursor.execute('SELECT full_name, email, phone FROM customers WHERE id = ?', (customer_id,))
        customer = cursor.fetchone()
        if not customer:
            return {'success': False, 'error': '客户不存在'}
        
        customer_name = customer[0]
        
        # 2. 获取客户资源
        cursor.execute('''
            SELECT resource_type, resource_name, description, estimated_value, availability
            FROM customer_resources
            WHERE customer_id = ?
        ''', (customer_id,))
        resources = cursor.fetchall()
        
        # 3. 获取客户人脉
        cursor.execute('''
            SELECT contact_name, relationship_type, industry, position, company, can_provide_help
            FROM customer_network
            WHERE customer_id = ?
        ''', (customer_id,))
        networks = cursor.fetchall()
        
        # 4. 获取客户技能
        cursor.execute('''
            SELECT skill_name, skill_category, proficiency_level, years_experience, certifications
            FROM customer_skills
            WHERE customer_id = ?
        ''', (customer_id,))
        skills = cursor.fetchall()
        
        # 5. 获取财务数据（累计消费和付款）
        cursor.execute('''
            SELECT COALESCE(SUM(Amount), 0) as total_consumption
            FROM consumption_records
            WHERE customer_id = ?
        ''', (customer_id,))
        total_consumption = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COALESCE(SUM(PaymentAmount), 0) as total_payment
            FROM payment_records
            WHERE customer_id = ?
        ''', (customer_id,))
        total_payment = cursor.fetchone()[0]
        
        # 检查是否有足够数据
        if not resources and not networks and not skills:
            return {'success': False, 'error': '请先添加个人资源、人脉或技能信息'}
    
    # 6. 构建AI提示词
    prompt = f"""
你是一位资深的商业顾问和创业导师。请基于以下客户信息，生成一份详细的、个性化的商业计划建议。

**客户概况：**
- 姓名：{customer_name}
- 累计消费：RM {total_consumption:,.2f}
- 累计付款：RM {total_payment:,.2f}
- 当前欠款：RM {(total_consumption - total_payment):,.2f}

**个人资源：**
{format_resources(resources)}

**人脉网络：**
{format_networks(networks)}

**专业技能：**
{format_skills(skills)}

请提供以下内容（必须使用JSON格式返回）：

1. 推荐的商业类型（3-5个）
2. 目标市场分析
3. 所需投资金额范围
4. 预期投资回报率（ROI）
5. 风险评估（高/中/低，并说明原因）
6. 具体行动步骤（至少5步）
7. 如何利用现有资源、人脉和技能
8. 马来西亚市场特定建议

请返回JSON格式：
{{
    "business_types": ["类型1", "类型2", "类型3"],
    "recommended_type": "最推荐的类型",
    "target_market": "目标市场描述",
    "investment_required": "RM X - RM Y",
    "expected_roi": "X%-Y% 年回报率",
    "risk_level": "高/中/低",
    "risk_reasons": "风险原因说明",
    "action_steps": ["步骤1", "步骤2", ...],
    "resource_utilization": "如何利用资源、人脉和技能的具体建议",
    "malaysia_insights": "马来西亚市场特定建议",
    "ai_reasoning": "AI分析推理过程"
}}
"""
    
    try:
        # 7. 调用OpenAI API
        openai_client = get_openai_client()
        response = openai_client.chat.completions.create(
            model="gpt-5",  # the newest OpenAI model is "gpt-5" which was released August 7, 2025. do not change this unless explicitly requested by the user
            messages=[
                {"role": "system", "content": "你是一位专业的商业顾问，擅长为马来西亚客户提供个性化商业计划建议。请用中文回答，并以JSON格式返回结果。"},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=8192
        )
        
        # 8. 解析AI响应
        ai_response = response.choices[0].message.content
        if not ai_response:
            return {'success': False, 'error': 'AI未返回有效响应'}
        plan_data = json.loads(ai_response)
        
        # 9. 保存到数据库
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO business_plans (
                    customer_id, plan_title, business_type, target_market,
                    investment_required, expected_roi, risk_assessment,
                    action_steps, ai_analysis
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                customer_id,
                f"{customer_name}的商业计划建议",
                plan_data.get('recommended_type', ''),
                plan_data.get('target_market', ''),
                plan_data.get('investment_required', ''),
                plan_data.get('expected_roi', ''),
                f"{plan_data.get('risk_level', '')} - {plan_data.get('risk_reasons', '')}",
                json.dumps(plan_data.get('action_steps', []), ensure_ascii=False),
                json.dumps(plan_data, ensure_ascii=False)
            ))
            
            plan_id = cursor.lastrowid
            conn.commit()
        
        return {
            'success': True,
            'plan_id': plan_id,
            'plan_data': plan_data
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'AI分析失败: {str(e)}'
        }


def format_resources(resources):
    """格式化资源列表"""
    if not resources:
        return "暂无资源信息"
    
    lines = []
    for r in resources:
        resource_type, name, desc, value, availability = r
        line = f"- {resource_type}：{name}"
        if desc:
            line += f"（{desc}）"
        if value:
            line += f"，价值约 RM {value:,.2f}"
        if availability:
            line += f"，{availability}"
        lines.append(line)
    
    return "\n".join(lines)


def format_networks(networks):
    """格式化人脉列表"""
    if not networks:
        return "暂无人脉信息"
    
    lines = []
    for n in networks:
        name, rel_type, industry, position, company, help_desc = n
        line = f"- {name}（{rel_type}）"
        if industry:
            line += f"，{industry}行业"
        if position and company:
            line += f"，{position}@{company}"
        if help_desc:
            line += f"，可提供：{help_desc}"
        lines.append(line)
    
    return "\n".join(lines)


def format_skills(skills):
    """格式化技能列表"""
    if not skills:
        return "暂无技能信息"
    
    lines = []
    for s in skills:
        skill_name, category, level, years, certs = s
        line = f"- {skill_name}（{category}，{level}）"
        if years:
            line += f"，{years}年经验"
        if certs:
            line += f"，持有：{certs}"
        lines.append(line)
    
    return "\n".join(lines)
