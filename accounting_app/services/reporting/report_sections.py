"""
Report Sections - 报告分段模板
PHASE 5: 可复用的HTML段落生成器
"""
from typing import Dict, List, Optional
from datetime import datetime


def build_customer_profile_section(customer_data: Dict, is_sme: bool = False) -> str:
    """
    构建客户资料段落
    
    Args:
        customer_data: 客户数据
        is_sme: 是否为SME
    
    Returns:
        HTML段落
    """
    if is_sme:
        return f"""
        <div class="report-section">
            <h2>🏢 企业资料 | Business Profile</h2>
            <table class="info-table">
                <tr>
                    <td><strong>企业名称</strong></td>
                    <td>{customer_data.get('company_name', 'N/A')}</td>
                </tr>
                <tr>
                    <td><strong>注册编号</strong></td>
                    <td>{customer_data.get('registration_number', 'N/A')}</td>
                </tr>
                <tr>
                    <td><strong>成立年限</strong></td>
                    <td>{customer_data.get('company_age_years', 'N/A')} 年</td>
                </tr>
                <tr>
                    <td><strong>行业分类</strong></td>
                    <td>{customer_data.get('industry_sector', 'N/A')}</td>
                </tr>
                <tr>
                    <td><strong>员工人数</strong></td>
                    <td>{customer_data.get('employee_count', 'N/A')} 人</td>
                </tr>
                <tr>
                    <td><strong>年度营业额</strong></td>
                    <td>RM {customer_data.get('operating_income', 0):,.2f}</td>
                </tr>
            </table>
        </div>
        """
    else:
        return f"""
        <div class="report-section">
            <h2>👤 申请人资料 | Applicant Profile</h2>
            <table class="info-table">
                <tr>
                    <td><strong>姓名</strong></td>
                    <td>{customer_data.get('name', 'N/A')}</td>
                </tr>
                <tr>
                    <td><strong>身份证号</strong></td>
                    <td>{customer_data.get('ic_number', 'N/A')}</td>
                </tr>
                <tr>
                    <td><strong>年龄</strong></td>
                    <td>{customer_data.get('age', 'N/A')} 岁</td>
                </tr>
                <tr>
                    <td><strong>就业状况</strong></td>
                    <td>{customer_data.get('employment_status', 'N/A')}</td>
                </tr>
                <tr>
                    <td><strong>工作年限</strong></td>
                    <td>{customer_data.get('employment_years', 'N/A')} 年</td>
                </tr>
                <tr>
                    <td><strong>月收入</strong></td>
                    <td>RM {customer_data.get('income', 0):,.2f}</td>
                </tr>
            </table>
        </div>
        """


def build_income_commitment_section(
    income: float,
    monthly_commitment: float,
    annual_commitment: float = None,
    is_sme: bool = False
) -> str:
    """构建收入与承诺段落"""
    if is_sme:
        operating_income = income
        annual_debt = annual_commitment or 0
        debt_ratio = (annual_debt / operating_income * 100) if operating_income > 0 else 0
        
        return f"""
        <div class="report-section">
            <h2>💰 收入与债务分析 | Income & Debt Analysis</h2>
            <table class="info-table">
                <tr>
                    <td><strong>年度营业收入</strong></td>
                    <td style="color: #00FF7F;">RM {operating_income:,.2f}</td>
                </tr>
                <tr>
                    <td><strong>年度债务承诺</strong></td>
                    <td style="color: #FF6347;">RM {annual_debt:,.2f}</td>
                </tr>
                <tr>
                    <td><strong>债务收入比</strong></td>
                    <td style="color: {'#00FF7F' if debt_ratio <= 30 else '#FFA500' if debt_ratio <= 50 else '#FF4444'};">
                        {debt_ratio:.1f}%
                    </td>
                </tr>
                <tr>
                    <td><strong>可用营运资金</strong></td>
                    <td>RM {max(0, operating_income - annual_debt):,.2f}</td>
                </tr>
            </table>
        </div>
        """
    else:
        dti = (monthly_commitment / income * 100) if income > 0 else 0
        available = max(0, income * 0.70 - monthly_commitment)
        
        return f"""
        <div class="report-section">
            <h2>💰 收入与承诺分析 | Income & Commitment Analysis</h2>
            <table class="info-table">
                <tr>
                    <td><strong>月收入</strong></td>
                    <td style="color: #00FF7F;">RM {income:,.2f}</td>
                </tr>
                <tr>
                    <td><strong>现有月度承诺</strong></td>
                    <td style="color: #FF6347;">RM {monthly_commitment:,.2f}</td>
                </tr>
                <tr>
                    <td><strong>DTI比率</strong></td>
                    <td style="color: {'#00FF7F' if dti <= 40 else '#FFA500' if dti <= 60 else '#FF4444'};">
                        {dti:.1f}% {'✓ 优秀' if dti <= 40 else '✓ 良好' if dti <= 60 else '⚠ 偏高'}
                    </td>
                </tr>
                <tr>
                    <td><strong>可用还款能力</strong></td>
                    <td>RM {available:,.2f}</td>
                </tr>
            </table>
        </div>
        """


def build_risk_assessment_section(evaluation_result: Dict, is_sme: bool = False) -> str:
    """构建风险评估段落"""
    if is_sme:
        brr_grade = evaluation_result.get("brr_grade", 5)
        dscr = evaluation_result.get("dscr", 0)
        cashflow_variance = evaluation_result.get("cashflow_variance", 0)
        ctos_sme_score = evaluation_result.get("ctos_sme_score", 650)
        
        brr_color = "#00FF7F" if brr_grade <= 3 else "#FFD700" if brr_grade <= 5 else "#FFA500" if brr_grade <= 7 else "#FF4444"
        dscr_color = "#00FF7F" if dscr >= 2.0 else "#FFD700" if dscr >= 1.5 else "#FFA500" if dscr >= 1.25 else "#FF4444"
        
        return f"""
        <div class="report-section">
            <h2>📊 风险评估 | Risk Assessment</h2>
            <table class="info-table">
                <tr>
                    <td><strong>BRR等级 (Business Risk Rating)</strong></td>
                    <td style="color: {brr_color}; font-size: 18px; font-weight: bold;">
                        {brr_grade}/10
                    </td>
                </tr>
                <tr>
                    <td><strong>DSCR (Debt Service Coverage Ratio)</strong></td>
                    <td style="color: {dscr_color};">
                        {dscr:.2f}x {'✓ 优秀' if dscr >= 2.0 else '✓ 良好' if dscr >= 1.5 else '⚠ 中等'}
                    </td>
                </tr>
                <tr>
                    <td><strong>现金流波动率</strong></td>
                    <td style="color: {'#00FF7F' if cashflow_variance <= 0.20 else '#FFA500' if cashflow_variance <= 0.35 else '#FF4444'};">
                        {cashflow_variance:.1%} {'✓ 稳定' if cashflow_variance <= 0.20 else '⚠ 中等波动'}
                    </td>
                </tr>
                <tr>
                    <td><strong>CTOS SME评分</strong></td>
                    <td style="color: {'#00FF7F' if ctos_sme_score >= 700 else '#FFD700' if ctos_sme_score >= 650 else '#FFA500'};">
                        {ctos_sme_score}/999
                    </td>
                </tr>
                <tr>
                    <td><strong>最大可贷额</strong></td>
                    <td style="color: #00FF7F; font-size: 18px;">
                        RM {evaluation_result.get('max_loan_amount', 0):,.2f}
                    </td>
                </tr>
            </table>
        </div>
        """
    else:
        risk_grade = evaluation_result.get("risk_grade", "C")
        dti = evaluation_result.get("dti", 0) * 100
        foir = evaluation_result.get("foir", 0) * 100
        ccris_bucket = evaluation_result.get("ccris_bucket", 0)
        credit_score = evaluation_result.get("credit_score", 700)
        
        grade_color = {
            "A+": "#00FF7F",
            "A": "#32CD32",
            "B+": "#FFD700",
            "B": "#FFA500",
            "C": "#FF6347",
            "D": "#FF4444"
        }.get(risk_grade, "#999")
        
        return f"""
        <div class="report-section">
            <h2>📊 风险评估 | Risk Assessment</h2>
            <table class="info-table">
                <tr>
                    <td><strong>风险等级 (Risk Grade)</strong></td>
                    <td style="color: {grade_color}; font-size: 24px; font-weight: bold;">
                        {risk_grade}
                    </td>
                </tr>
                <tr>
                    <td><strong>DTI (Debt-to-Income)</strong></td>
                    <td style="color: {'#00FF7F' if dti <= 40 else '#FFA500' if dti <= 60 else '#FF4444'};">
                        {dti:.1f}% {'✓ 优秀' if dti <= 40 else '✓ 良好' if dti <= 60 else '⚠ 偏高'}
                    </td>
                </tr>
                <tr>
                    <td><strong>FOIR (Fixed Obligation to Income)</strong></td>
                    <td style="color: {'#00FF7F' if foir <= 50 else '#FFA500' if foir <= 60 else '#FF4444'};">
                        {foir:.1f}% {'✓ 符合标准' if foir <= 60 else '⚠ 超标'}
                    </td>
                </tr>
                <tr>
                    <td><strong>CCRIS Bucket</strong></td>
                    <td style="color: {'#00FF7F' if ccris_bucket == 0 else '#FFD700' if ccris_bucket == 1 else '#FF6347'};">
                        Bucket {ccris_bucket} {'✓ 完美' if ccris_bucket == 0 else '⚠ 有延迟记录'}
                    </td>
                </tr>
                <tr>
                    <td><strong>信用分数</strong></td>
                    <td style="color: {'#00FF7F' if credit_score >= 700 else '#FFA500'};">
                        {credit_score}/999
                    </td>
                </tr>
                <tr>
                    <td><strong>最大可贷额</strong></td>
                    <td style="color: #00FF7F; font-size: 18px;">
                        RM {evaluation_result.get('max_loan_amount', 0):,.2f}
                    </td>
                </tr>
            </table>
        </div>
        """


def build_product_recommendation_section(products: List[Dict], top_n: int = 5) -> str:
    """
    构建产品推荐段落
    
    Args:
        products: 产品列表
        top_n: 显示前N个产品
    
    Returns:
        HTML段落
    """
    if not products:
        return """
        <div class="report-section">
            <h2>🏦 推荐产品 | Recommended Products</h2>
            <p style="color: #999;">暂无符合条件的产品推荐。</p>
        </div>
        """
    
    html = """
    <div class="report-section">
        <h2>🏦 推荐产品 | Recommended Products</h2>
        <p style="margin-bottom: 20px;">
            根据您的风险评估结果，以下是系统智能匹配的Top {top_n}个贷款产品：
        </p>
        <table class="products-table">
            <thead>
                <tr>
                    <th>#</th>
                    <th>银行/金融机构</th>
                    <th>产品名称</th>
                    <th>匹配分数</th>
                    <th>利率</th>
                    <th>最大贷款额</th>
                    <th>批准概率</th>
                </tr>
            </thead>
            <tbody>
    """.replace("{top_n}", str(top_n))
    
    for i, product in enumerate(products[:top_n], 1):
        match_score = product.get("match_score", 0)
        interest_rate = product.get("interest_rate", 0)
        max_amount = product.get("max_loan_amount", 0)
        approval_odds = product.get("approval_odds", 0)
        
        # 颜色编码
        match_color = "#00FF7F" if match_score >= 85 else "#FFD700" if match_score >= 70 else "#FFA500"
        approval_color = "#00FF7F" if approval_odds >= 80 else "#FFD700" if approval_odds >= 60 else "#FFA500"
        
        html += f"""
                <tr>
                    <td style="font-weight: bold;">{i}</td>
                    <td>{product.get('bank', 'N/A')}</td>
                    <td>{product.get('product_name', 'N/A')}</td>
                    <td style="color: {match_color}; font-weight: bold;">{match_score:.1f}</td>
                    <td>{interest_rate * 100:.2f}%</td>
                    <td>RM {max_amount:,.0f}</td>
                    <td style="color: {approval_color}; font-weight: bold;">{approval_odds:.0f}%</td>
                </tr>
        """
    
    html += """
            </tbody>
        </table>
        <p style="margin-top: 15px; font-size: 12px; color: #999;">
            * 匹配分数基于风险等级、信用分数、CCRIS记录等多维度评估<br>
            * 实际利率以银行最终批准为准
        </p>
    </div>
    """
    
    return html


def build_final_decision_section(
    is_eligible: bool,
    max_loan_amount: float,
    max_tenure: int = 84,
    estimated_emi: float = None
) -> str:
    """构建最终决策段落"""
    if is_eligible and max_loan_amount > 0:
        status_color = "#00FF7F"
        status_text = "✅ 符合贷款资格"
        decision = "恭喜！根据我们的风险评估，您符合贷款申请资格。"
    else:
        status_color = "#FF4444"
        status_text = "⚠️ 暂不符合标准"
        decision = "根据目前的财务状况，建议先改善相关指标后再申请。"
    
    html = f"""
    <div class="report-section">
        <h2>📋 评估结果 | Final Decision</h2>
        <div style="background: linear-gradient(135deg, {status_color}22 0%, {status_color}11 100%); 
                    border-left: 5px solid {status_color}; padding: 20px; margin: 20px 0;">
            <h3 style="color: {status_color}; margin: 0 0 10px 0;">{status_text}</h3>
            <p style="font-size: 16px; margin: 10px 0;">{decision}</p>
            <table class="info-table" style="margin-top: 15px;">
                <tr>
                    <td><strong>最大可贷金额</strong></td>
                    <td style="color: {status_color}; font-size: 20px;">RM {max_loan_amount:,.2f}</td>
                </tr>
                <tr>
                    <td><strong>最长贷款期限</strong></td>
                    <td>{max_tenure} 个月 ({max_tenure//12} 年)</td>
                </tr>
    """
    
    if estimated_emi:
        html += f"""
                <tr>
                    <td><strong>预估月供</strong></td>
                    <td>RM {estimated_emi:,.2f}</td>
                </tr>
        """
    
    html += """
            </table>
        </div>
    </div>
    """
    
    return html


def build_report_header(report_title: str, customer_name: str) -> str:
    """构建报告头部"""
    today = datetime.now().strftime("%Y年%m月%d日")
    
    return f"""
    <!DOCTYPE html>
    <html lang="zh">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{report_title}</title>
        {_get_report_styles()}
    </head>
    <body>
        <div class="report-container">
            <div class="report-header">
                <h1>{report_title}</h1>
                <div class="header-info">
                    <p><strong>申请人：</strong>{customer_name}</p>
                    <p><strong>报告日期：</strong>{today}</p>
                    <p><strong>评估系统：</strong>CREDITPILOT Malaysia Lending Engine</p>
                </div>
            </div>
    """


def build_report_footer() -> str:
    """构建报告底部"""
    return """
            <div class="report-footer">
                <h3>⚠️ 免责声明 | Disclaimer</h3>
                <p style="font-size: 12px; color: #999; line-height: 1.6;">
                    本报告由CREDITPILOT系统自动生成，仅供参考。实际贷款批准以银行最终审批为准。
                    所有利率、金额、批准概率均为系统预测值，实际情况可能因银行政策、市场条件等因素有所不同。
                    申请人应向相关金融机构咨询最新信息。本系统不对任何贷款申请结果承担责任。
                </p>
                <p style="font-size: 11px; color: #666; margin-top: 15px; text-align: center;">
                    © 2025 CREDITPILOT - Smart Credit & Loan Manager<br>
                    Powered by Malaysian Banking Standards (DTI/FOIR/CCRIS/BRR)
                </p>
            </div>
        </div>
    </body>
    </html>
    """


def _get_report_styles() -> str:
    """获取报告CSS样式"""
    return """
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #0a0a0a;
            color: #ffffff;
            line-height: 1.6;
        }
        
        .report-container {
            max-width: 1000px;
            margin: 0 auto;
            padding: 40px 20px;
        }
        
        .report-header {
            background: linear-gradient(135deg, #FF007F 0%, #322446 100%);
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 15px rgba(255, 0, 127, 0.3);
        }
        
        .report-header h1 {
            font-size: 28px;
            margin-bottom: 15px;
            color: #ffffff;
        }
        
        .header-info p {
            margin: 5px 0;
            font-size: 14px;
            color: #f0f0f0;
        }
        
        .report-section {
            background: #1a1a1a;
            border: 1px solid #322446;
            border-radius: 8px;
            padding: 25px;
            margin-bottom: 25px;
        }
        
        .report-section h2 {
            color: #FF007F;
            font-size: 22px;
            margin-bottom: 20px;
            border-bottom: 2px solid #322446;
            padding-bottom: 10px;
        }
        
        .info-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        
        .info-table tr {
            border-bottom: 1px solid #333;
        }
        
        .info-table td {
            padding: 12px 15px;
            font-size: 15px;
        }
        
        .info-table td:first-child {
            width: 40%;
            color: #999;
        }
        
        .info-table td:last-child {
            font-weight: 500;
        }
        
        .products-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        
        .products-table thead {
            background: #322446;
        }
        
        .products-table th {
            padding: 12px;
            text-align: left;
            font-size: 13px;
            color: #FF007F;
            font-weight: 600;
        }
        
        .products-table td {
            padding: 12px;
            border-bottom: 1px solid #333;
            font-size: 14px;
        }
        
        .products-table tr:hover {
            background: #222;
        }
        
        .report-footer {
            margin-top: 40px;
            padding: 25px;
            background: #1a1a1a;
            border: 1px solid #322446;
            border-radius: 8px;
        }
        
        .report-footer h3 {
            color: #FFA500;
            margin-bottom: 15px;
        }
        
        @media print {
            body {
                background: white;
                color: black;
            }
            
            .report-section {
                page-break-inside: avoid;
            }
        }
    </style>
    """
