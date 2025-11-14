"""
Loan Report Builder - 贷款报告构建器
PHASE 5: 组装完整的HTML/PDF报告
"""
from typing import Dict, Optional
from .report_sections import (
    build_customer_profile_section,
    build_income_commitment_section,
    build_risk_assessment_section,
    build_product_recommendation_section,
    build_final_decision_section,
    build_report_header,
    build_report_footer
)
from .advisor_explanations import (
    explain_risk_grade,
    explain_sme_brr,
    explain_why_approved,
    explain_how_to_improve,
    generate_overall_summary
)


class LoanReportBuilder:
    """贷款报告构建器"""
    
    @staticmethod
    def build_personal_report(
        evaluation_result: Dict,
        customer_data: Dict,
        enriched_data: Optional[Dict] = None
    ) -> str:
        """
        构建个人贷款完整报告
        
        Args:
            evaluation_result: 风控评估结果
            customer_data: 客户数据
            enriched_data: 数据增强信息（可选）
        
        Returns:
            完整的HTML报告
        """
        # 提取关键数据
        customer_name = customer_data.get("name", "N/A")
        income = customer_data.get("income", evaluation_result.get("income", 0))
        monthly_commitment = evaluation_result.get("monthly_commitment", 0)
        risk_grade = evaluation_result.get("risk_grade", "C")
        dti = evaluation_result.get("dti", 0)
        foir = evaluation_result.get("foir", 0)
        ccris_bucket = evaluation_result.get("ccris_bucket", 0)
        credit_score = evaluation_result.get("credit_score", 700)
        max_loan_amount = evaluation_result.get("max_loan_amount", 0)
        products = evaluation_result.get("recommended_products", [])
        
        # 开始构建报告
        html = build_report_header(
            report_title="个人贷款评估报告 | Personal Loan Assessment Report",
            customer_name=customer_name
        )
        
        # 1. 整体摘要
        html += generate_overall_summary(evaluation_result, is_sme=False)
        
        # 2. 客户资料
        profile_data = {
            "name": customer_name,
            "ic_number": customer_data.get("ic_number", "N/A"),
            "age": evaluation_result.get("age", customer_data.get("age", 30)),
            "employment_status": customer_data.get("employment_status", "Permanent"),
            "employment_years": evaluation_result.get("employment_years", 3.0),
            "income": income
        }
        html += build_customer_profile_section(profile_data, is_sme=False)
        
        # 3. 收入与承诺分析
        html += build_income_commitment_section(
            income=income,
            monthly_commitment=monthly_commitment,
            is_sme=False
        )
        
        # 4. 风险评估
        html += build_risk_assessment_section(evaluation_result, is_sme=False)
        
        # 5. AI顾问解释 - 风险等级
        html += f"""
        <div class="report-section">
            <h2>🤖 AI风控顾问分析 | AI Risk Advisor</h2>
            {explain_risk_grade(risk_grade, dti, ccris_bucket, credit_score, foir)}
        </div>
        """
        
        # 6. 批准概率说明
        approval_odds = products[0].get("approval_odds", 50) if products else 50
        html += f"""
        <div class="report-section">
            <h2>📈 批准概率分析 | Approval Probability</h2>
            {explain_why_approved(risk_grade, approval_odds)}
        </div>
        """
        
        # 7. 产品推荐
        html += build_product_recommendation_section(products, top_n=5)
        
        # 8. 改进建议
        if risk_grade in ["B", "C", "D"] or dti > 0.60:
            html += f"""
            <div class="report-section">
                <h2>💡 改进建议 | Improvement Recommendations</h2>
                {explain_how_to_improve(risk_grade, dti, ccris_bucket)}
            </div>
            """
        
        # 9. 最终决策
        html += build_final_decision_section(
            is_eligible=(max_loan_amount > 0),
            max_loan_amount=max_loan_amount,
            max_tenure=84,
            estimated_emi=evaluation_result.get("max_emi")
        )
        
        # 10. 数据增强摘要（如果有）
        if enriched_data:
            html += LoanReportBuilder._build_data_enrichment_section(enriched_data)
        
        # 报告底部
        html += build_report_footer()
        
        return html
    
    @staticmethod
    def build_sme_report(
        evaluation_result: Dict,
        customer_data: Dict,
        enriched_data: Optional[Dict] = None
    ) -> str:
        """
        构建SME贷款完整报告
        
        Args:
            evaluation_result: 风控评估结果
            customer_data: 企业数据
            enriched_data: 数据增强信息（可选）
        
        Returns:
            完整的HTML报告
        """
        # 提取关键数据
        company_name = customer_data.get("company_name", "N/A")
        operating_income = customer_data.get("operating_income", evaluation_result.get("operating_income", 0))
        annual_commitment = evaluation_result.get("annual_commitment", 0)
        brr_grade = evaluation_result.get("brr_grade", 5)
        dscr = evaluation_result.get("dscr", 0)
        cashflow_variance = evaluation_result.get("cashflow_variance", 0.30)
        ctos_sme_score = evaluation_result.get("ctos_sme_score", 650)
        industry_sector = evaluation_result.get("industry_sector", "services")
        max_loan_amount = evaluation_result.get("max_loan_amount", 0)
        products = evaluation_result.get("recommended_products", [])
        
        # 开始构建报告
        html = build_report_header(
            report_title="SME贷款评估报告 | SME Loan Assessment Report",
            customer_name=company_name
        )
        
        # 1. 整体摘要
        html += generate_overall_summary(evaluation_result, is_sme=True)
        
        # 2. 企业资料
        company_profile = {
            "company_name": company_name,
            "registration_number": customer_data.get("registration_number", "N/A"),
            "company_age_years": evaluation_result.get("company_age_years", 5),
            "industry_sector": industry_sector,
            "employee_count": customer_data.get("employee_count", "N/A"),
            "operating_income": operating_income
        }
        html += build_customer_profile_section(company_profile, is_sme=True)
        
        # 3. 收入与债务分析
        html += build_income_commitment_section(
            income=operating_income,
            monthly_commitment=0,
            annual_commitment=annual_commitment,
            is_sme=True
        )
        
        # 4. 风险评估
        html += build_risk_assessment_section(evaluation_result, is_sme=True)
        
        # 5. AI顾问解释 - BRR等级
        html += f"""
        <div class="report-section">
            <h2>🤖 AI风控顾问分析 | AI Risk Advisor</h2>
            {explain_sme_brr(brr_grade, dscr, cashflow_variance, ctos_sme_score, industry_sector)}
        </div>
        """
        
        # 6. 批准概率说明
        approval_odds = products[0].get("approval_odds", 50) if products else 50
        html += f"""
        <div class="report-section">
            <h2>📈 批准概率分析 | Approval Probability</h2>
            <p style="font-size: 16px;">
                基于您的BRR等级{brr_grade}/10和DSCR {dscr:.2f}x，
                系统预测您的SME贷款批准概率为<strong style="color: #FFD700;">{approval_odds:.0f}%</strong>。
            </p>
            <p style="margin-top: 15px;">
                {'推荐银行将快速处理您的申请。' if approval_odds >= 70 else '建议补充完整财务文件以提高批准率。'}
            </p>
        </div>
        """
        
        # 7. 产品推荐
        html += build_product_recommendation_section(products, top_n=5)
        
        # 8. 改进建议（如果BRR较高）
        if brr_grade >= 6 or dscr < 1.50:
            html += f"""
            <div class="report-section">
                <h2>💡 改进建议 | Improvement Recommendations</h2>
                <strong>提升贷款批准率的建议：</strong>
                <ul style="margin-top: 15px; line-height: 1.8;">
                    {"<li>提高DSCR至1.50以上（增加营运利润或降低债务）</li>" if dscr < 1.50 else ""}
                    {"<li>改善现金流管理，降低波动率至20%以下</li>" if cashflow_variance > 0.30 else ""}
                    {"<li>提升CTOS SME评分（保持良好还款记录）</li>" if ctos_sme_score < 700 else ""}
                    <li>考虑CGC（Credit Guarantee Corporation）担保计划</li>
                    <li>提供额外抵押品或担保人</li>
                </ul>
            </div>
            """
        
        # 9. 最终决策
        html += build_final_decision_section(
            is_eligible=(max_loan_amount > 0),
            max_loan_amount=max_loan_amount,
            max_tenure=120,
            estimated_emi=None
        )
        
        # 10. 数据增强摘要（如果有）
        if enriched_data:
            html += LoanReportBuilder._build_data_enrichment_section(enriched_data)
        
        # 报告底部
        html += build_report_footer()
        
        return html
    
    @staticmethod
    def _build_data_enrichment_section(enriched_data: Dict) -> str:
        """构建数据增强摘要段落"""
        auto_filled = enriched_data.get("auto_filled_fields", [])
        
        if not auto_filled:
            return ""
        
        html = """
        <div class="report-section">
            <h2>🔍 数据采集摘要 | Data Enrichment Summary</h2>
            <p style="margin-bottom: 15px;">
                以下字段通过智能数据采集系统自动补全：
            </p>
            <table class="info-table">
        """
        
        for field_info in auto_filled:
            field_name = field_info.get("field", "N/A")
            source = field_info.get("source", "系统默认值")
            confidence = field_info.get("confidence", 0)
            
            confidence_color = "#00FF7F" if confidence >= 0.80 else "#FFD700" if confidence >= 0.60 else "#FFA500"
            
            html += f"""
                <tr>
                    <td><strong>{field_name}</strong></td>
                    <td>
                        来源: {source}<br>
                        <span style="color: {confidence_color};">置信度: {confidence:.0%}</span>
                    </td>
                </tr>
            """
        
        html += """
            </table>
            <p style="margin-top: 15px; font-size: 12px; color: #999;">
                * 自动补全字段可能影响评估结果，建议核对准确性
            </p>
        </div>
        """
        
        return html
