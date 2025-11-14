"""
Bank Loan Advisor AI - 银行风控官风格的专业解释
PHASE 5: 自动解释风险评估结果，提供改进建议
"""
from typing import Dict, Optional


def explain_risk_grade(
    risk_grade: str,
    dti: float,
    ccris_bucket: int,
    credit_score: int,
    foir: float = None
) -> str:
    """
    解释个人贷款风险等级
    
    Args:
        risk_grade: A+, A, B+, B, C, D
        dti: Debt-to-Income比率
        ccris_bucket: CCRIS bucket (0~3)
        credit_score: 信用分数
        foir: Fixed Obligation to Income Ratio
    
    Returns:
        专业解释文本
    """
    explanations = {
        "A+": f"""
        <strong>卓越信用等级 (A+)</strong><br>
        您的财务状况处于最优水平。DTI比率为{dti:.1%}（银行标准≤70%），
        CCRIS记录完美（Bucket {ccris_bucket}），信用分数{credit_score}分显示您拥有优秀的还款历史。
        马来西亚各大银行均愿意以<strong>最优惠利率</strong>为您提供贷款服务。
        """,
        
        "A": f"""
        <strong>优质信用等级 (A)</strong><br>
        您的财务健康状况良好。DTI比率{dti:.1%}处于安全范围，
        CCRIS Bucket {ccris_bucket}显示还款记录稳定。您的信用分数{credit_score}分
        符合主流银行的优质客户标准，可获得<strong>竞争性利率</strong>。
        """,
        
        "B+": f"""
        <strong>良好信用等级 (B+)</strong><br>
        您的整体信用状况可以接受。DTI比率{dti:.1%}略高于理想水平，
        但仍在银行可接受范围内。CCRIS Bucket {ccris_bucket}和信用分数{credit_score}分
        显示您具备稳定的还款能力。传统银行和数字银行均可考虑您的申请。
        """,
        
        "B": f"""
        <strong>中等信用等级 (B)</strong><br>
        您的DTI比率达到{dti:.1%}，接近银行风控上限。CCRIS Bucket {ccris_bucket}
        显示有轻微延迟还款记录。信用分数{credit_score}分处于中等水平。
        建议优先考虑<strong>数字银行</strong>或提供风险定价的金融机构。
        """,
        
        "C": f"""
        <strong>较高风险等级 (C)</strong><br>
        您的DTI比率{dti:.1%}已超出传统银行标准，CCRIS Bucket {ccris_bucket}
        显示有多次延迟还款。信用分数{credit_score}分偏低。
        建议考虑<strong>Fintech平台</strong>或改善财务状况后重新申请。
        """,
        
        "D": f"""
        <strong>高风险等级 (D)</strong><br>
        您的DTI比率高达{dti:.1%}，债务负担较重。CCRIS Bucket {ccris_bucket}
        显示严重还款问题，信用分数{credit_score}分低于银行最低要求。
        <strong>建议先进行债务整合</strong>，降低现有承诺后再申请新贷款。
        """
    }
    
    base_explanation = explanations.get(risk_grade, "无法评估风险等级")
    
    # 添加FOIR解释（如果提供）
    if foir is not None:
        foir_comment = f"""
        <br><br><strong>FOIR分析：</strong>
        您的固定义务收入比为{foir:.1%}。根据马来西亚银行监管要求，
        FOIR应控制在60%以下。{'您的FOIR符合标准。' if foir <= 0.60 else '您的FOIR偏高，建议降低固定支出。'}
        """
        base_explanation += foir_comment
    
    return base_explanation.strip()


def explain_sme_brr(
    brr_grade: int,
    dscr: float,
    cashflow_variance: float,
    ctos_sme_score: int,
    industry_sector: str
) -> str:
    """
    解释SME贷款BRR等级
    
    Args:
        brr_grade: Business Risk Rating (1~10)
        dscr: Debt Service Coverage Ratio
        cashflow_variance: 现金流波动率
        ctos_sme_score: CTOS SME分数
        industry_sector: 行业分类
    
    Returns:
        专业解释文本
    """
    industry_names = {
        "fnb": "餐饮业",
        "trading": "贸易业",
        "manufacturing": "制造业",
        "services": "服务业",
        "construction": "建筑业",
        "retail": "零售业",
        "logistics": "物流业",
        "agriculture": "农业",
        "property_development": "房地产开发",
        "oil_gas": "石油天然气",
        "it_tech": "科技业",
        "healthcare": "医疗保健",
        "education": "教育业"
    }
    
    industry_name = industry_names.get(industry_sector, industry_sector)
    
    if brr_grade <= 3:
        risk_level = "低风险"
        comment = """
        您的企业展现出<strong>卓越的财务稳健性</strong>。DSCR比率显示充足的现金流覆盖能力，
        现金流波动率低，CTOS SME评分优秀。主流银行均愿意以优惠条件提供融资支持。
        """
    elif brr_grade <= 5:
        risk_level = "中低风险"
        comment = """
        您的企业财务状况<strong>良好</strong>。DSCR比率符合银行标准，
        现金流管理稳定。传统银行和政府担保计划（CGC）均可考虑。
        """
    elif brr_grade <= 7:
        risk_level = "中等风险"
        comment = """
        您的企业处于<strong>中等风险水平</strong>。DSCR比率接近银行最低要求，
        现金流存在一定波动。建议优先考虑Fintech平台或提升DSCR后申请传统银行。
        """
    else:
        risk_level = "较高风险"
        comment = """
        您的企业面临<strong>较大财务压力</strong>。DSCR比率低于银行标准，
        现金流不稳定。建议先改善营运现金流，或寻求替代融资方案。
        """
    
    explanation = f"""
    <strong>BRR等级 {brr_grade}/10 - {risk_level}</strong><br>
    行业：{industry_name}<br><br>
    
    {comment}
    
    <br><strong>关键指标分析：</strong>
    <ul>
        <li><strong>DSCR：</strong>{dscr:.2f}倍 {'（优秀）' if dscr >= 2.0 else '（良好）' if dscr >= 1.5 else '（中等）' if dscr >= 1.25 else '（偏低）'}</li>
        <li><strong>现金流波动率：</strong>{cashflow_variance:.1%} {'（稳定）' if cashflow_variance <= 0.20 else '（中等）' if cashflow_variance <= 0.35 else '（不稳定）'}</li>
        <li><strong>CTOS SME评分：</strong>{ctos_sme_score}分 {'（优秀）' if ctos_sme_score >= 700 else '（良好）' if ctos_sme_score >= 650 else '（中等）'}</li>
    </ul>
    """
    
    return explanation.strip()


def explain_why_approved(risk_grade: str, approval_odds: float) -> str:
    """解释为什么批准"""
    if approval_odds >= 85:
        return f"""
        <strong>批准概率：{approval_odds:.0f}%（极高）</strong><br>
        您的{risk_grade}风险等级显示优秀的信用质量。银行系统预测您的申请
        将获得<strong>快速批准</strong>，并可能享受优惠利率。
        """
    elif approval_odds >= 70:
        return f"""
        <strong>批准概率：{approval_odds:.0f}%（高）</strong><br>
        您的{risk_grade}风险等级符合大多数银行的审批标准。
        预期您的申请将顺利通过，批准时间约<strong>48-72小时</strong>。
        """
    elif approval_odds >= 50:
        return f"""
        <strong>批准概率：{approval_odds:.0f}%（中等）</strong><br>
        您的{risk_grade}风险等级处于银行可接受范围。建议补充完整文件，
        并考虑数字银行以提高批准机会。
        """
    else:
        return f"""
        <strong>批准概率：{approval_odds:.0f}%（偏低）</strong><br>
        您的{risk_grade}风险等级可能影响传统银行审批。
        建议先改善财务指标或考虑Fintech平台。
        """


def explain_why_declined() -> str:
    """解释为什么拒绝"""
    return """
    <strong>申请未通过的可能原因：</strong>
    <ul>
        <li>DTI/FOIR比率超出银行风控上限（70%）</li>
        <li>CCRIS记录显示多次延迟还款（Bucket 2或3）</li>
        <li>信用分数低于最低要求（通常600-650分）</li>
        <li>现有债务承诺过高</li>
        <li>收入证明不足或不稳定</li>
    </ul>
    """


def explain_how_to_improve(risk_grade: str, dti: float, ccris_bucket: int) -> str:
    """提供改进建议"""
    suggestions = []
    
    if dti > 0.70:
        suggestions.append("降低现有债务承诺（目标DTI ≤ 60%）")
    
    if ccris_bucket >= 2:
        suggestions.append("保持至少6个月的按时还款记录，改善CCRIS评级")
    
    if risk_grade in ["C", "D"]:
        suggestions.append("考虑债务整合（Balance Transfer）降低月供")
        suggestions.append("增加共同申请人或担保人")
        suggestions.append("提供额外收入证明（如兼职、投资收入）")
    
    if not suggestions:
        suggestions.append("维持良好的还款记录")
        suggestions.append("定期检查CCRIS报告")
    
    html = "<strong>改进建议：</strong><ul>"
    for suggestion in suggestions:
        html += f"<li>{suggestion}</li>"
    html += "</ul>"
    
    return html


def generate_overall_summary(
    evaluation_result: Dict,
    is_sme: bool = False
) -> str:
    """
    生成整体摘要
    
    Args:
        evaluation_result: 风控评估结果
        is_sme: 是否为SME贷款
    
    Returns:
        HTML格式的整体摘要
    """
    if is_sme:
        brr_grade = evaluation_result.get("brr_grade", 5)
        max_loan = evaluation_result.get("max_loan_amount", 0)
        
        if brr_grade <= 3:
            verdict = "强烈推荐"
            color = "#00FF7F"
        elif brr_grade <= 5:
            verdict = "推荐"
            color = "#FFD700"
        elif brr_grade <= 7:
            verdict = "谨慎考虑"
            color = "#FFA500"
        else:
            verdict = "需改善"
            color = "#FF4444"
        
        summary = f"""
        <div style="background: linear-gradient(135deg, {color}22 0%, {color}11 100%); 
                    border-left: 4px solid {color}; padding: 20px; margin: 20px 0;">
            <h3 style="color: {color}; margin-top: 0;">🏢 SME贷款评估总结</h3>
            <p style="font-size: 16px;">
                <strong>综合评估：</strong><span style="color: {color}; font-size: 18px;">{verdict}</span><br>
                <strong>BRR等级：</strong>{brr_grade}/10<br>
                <strong>最大可贷额：</strong>RM {max_loan:,.2f}<br>
                <strong>推荐产品数：</strong>{len(evaluation_result.get('recommended_products', []))}家银行/Fintech
            </p>
        </div>
        """
    else:
        risk_grade = evaluation_result.get("risk_grade", "C")
        max_loan = evaluation_result.get("max_loan_amount", 0)
        
        grade_colors = {
            "A+": "#00FF7F",
            "A": "#32CD32",
            "B+": "#FFD700",
            "B": "#FFA500",
            "C": "#FF6347",
            "D": "#FF4444"
        }
        color = grade_colors.get(risk_grade, "#999")
        
        summary = f"""
        <div style="background: linear-gradient(135deg, {color}22 0%, {color}11 100%); 
                    border-left: 4px solid {color}; padding: 20px; margin: 20px 0;">
            <h3 style="color: {color}; margin-top: 0;">👤 个人贷款评估总结</h3>
            <p style="font-size: 16px;">
                <strong>风险等级：</strong><span style="color: {color}; font-size: 20px; font-weight: bold;">{risk_grade}</span><br>
                <strong>最大可贷额：</strong>RM {max_loan:,.2f}<br>
                <strong>推荐产品数：</strong>{len(evaluation_result.get('recommended_products', []))}家银行/Fintech
            </p>
        </div>
        """
    
    return summary
