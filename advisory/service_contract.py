"""
服务合同生成器
生成授权同意合同（双方签字）
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from db.database import get_db
from datetime import datetime
import json
import os

class ServiceContract:
    
    def __init__(self, output_folder='static/uploads/contracts'):
        self.output_folder = output_folder
        os.makedirs(output_folder, exist_ok=True)
    
    def generate_authorization_contract(self, customer_id, suggestion_id, consultation_request_id):
        """
        生成授权同意合同
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 获取客户信息
            cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
            customer = dict(cursor.fetchone())
            
            # 获取优化建议
            cursor.execute('SELECT * FROM financial_optimization_suggestions WHERE id = ?', (suggestion_id,))
            suggestion = dict(cursor.fetchone())
            suggestion_details = json.loads(suggestion['suggestion_details'])
            
            # 获取咨询记录
            cursor.execute('SELECT * FROM consultation_requests WHERE id = ?', (consultation_request_id,))
            consultation = dict(cursor.fetchone())
            
            # 生成合同编号
            contract_number = f"INF-{customer_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # 创建PDF
            filename = f"Contract_{contract_number}.pdf"
            filepath = os.path.join(self.output_folder, filename)
            
            doc = SimpleDocTemplate(filepath, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
            story = []
            styles = getSampleStyleSheet()
            
            # 标题样式
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=20,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            
            # 内容样式
            body_style = ParagraphStyle(
                'BodyText',
                parent=styles['Normal'],
                fontSize=11,
                alignment=TA_JUSTIFY,
                spaceAfter=12,
                leading=16
            )
            
            # 合同标题
            story.append(Paragraph("<b>财务优化服务授权同意书</b>", title_style))
            story.append(Paragraph("<b>FINANCIAL OPTIMIZATION SERVICE AUTHORIZATION AGREEMENT</b>", title_style))
            story.append(Spacer(1, 0.3*inch))
            
            # 合同编号和日期
            story.append(Paragraph(f"<b>合同编号 Contract No.:</b> {contract_number}", styles['Normal']))
            story.append(Paragraph(f"<b>日期 Date:</b> {datetime.now().strftime('%Y-%m-%d')}", styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
            
            # 甲方乙方信息
            parties_data = [
                ['<b>甲方 Party A (客户 Client)</b>', '<b>乙方 Party B (服务商 Service Provider)</b>'],
                [f"姓名 Name: {customer['name']}", '公司 Company: INFINITE GZ SDN BHD'],
                [f"IC号码 IC No.: {customer.get('ic_number', 'N/A')}", '注册号 Reg No.: 202501234567'],
                [f"联系电话 Phone: {customer.get('phone', 'N/a')}", '联系电话 Phone: +60 12-345-6789'],
                [f"电邮 Email: {customer.get('email', 'N/A')}", '电邮 Email: infinitegz.reminder@gmail.com']
            ]
            
            parties_table = Table(parties_data, colWidths=[3*inch, 3*inch])
            parties_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('PADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(parties_table)
            story.append(Spacer(1, 0.3*inch))
            
            # 服务内容
            story.append(Paragraph("<b>一、服务内容 SERVICE SCOPE</b>", styles['Heading2']))
            
            service_type = "债务整合优化" if suggestion['suggestion_type'] == 'debt_consolidation' else "信用卡优化"
            service_desc = f"""
            乙方将为甲方提供<b>{service_type}</b>服务，具体包括：<br/>
            1. 分析甲方当前财务状况<br/>
            2. 制定优化方案并实施<br/>
            3. 协助甲方完成相关手续<br/>
            4. 提供后续跟进服务
            """
            story.append(Paragraph(service_desc, body_style))
            story.append(Spacer(1, 0.2*inch))
            
            # 优化方案对比
            story.append(Paragraph("<b>二、优化方案对比 OPTIMIZATION COMPARISON</b>", styles['Heading2']))
            
            comparison_data = [
                ['<b>项目 Item</b>', '<b>现状 Current</b>', '<b>优化后 Optimized</b>'],
                ['年度成本/收益<br/>Annual Cost/Benefit', 
                 f"RM {suggestion['current_cost']:.2f}", 
                 f"RM {suggestion['optimized_cost']:.2f}"],
                ['<b>年度节省/赚取<br/>Annual Savings/Earnings</b>', 
                 '', 
                 f"<b>RM {suggestion['estimated_savings']:.2f}</b>"]
            ]
            
            comparison_table = Table(comparison_data, colWidths=[2.5*inch, 1.75*inch, 1.75*inch])
            comparison_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8f4f8')),
                ('PADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(comparison_table)
            story.append(Spacer(1, 0.3*inch))
            
            # 费用与分成
            story.append(Paragraph("<b>三、费用与分成 FEES AND PROFIT SHARING</b>", styles['Heading2']))
            
            fee_amount = suggestion['estimated_savings'] * 0.5
            fee_text = f"""
            <b>3.1 成功费用原则 Success-Based Fee Principle:</b><br/>
            • 如果乙方未能为甲方节省或赚取任何金额，乙方<b>不收取分毫费用</b>。<br/>
            • If Party B fails to save or earn any amount for Party A, <b>NO FEE</b> will be charged.<br/>
            <br/>
            <b>3.2 利润分成 Profit Sharing:</b><br/>
            • 甲方实际节省/赚取金额：<b>RM {suggestion['estimated_savings']:.2f}</b><br/>
            • 分成比例：<b>50% / 50%</b><br/>
            • 甲方保留：<b>RM {suggestion['estimated_savings'] * 0.5:.2f}</b><br/>
            • 乙方服务费：<b>RM {fee_amount:.2f}</b><br/>
            <br/>
            <b>3.3 支付条款 Payment Terms:</b><br/>
            • 服务费将在优化方案完成并确认节省/赚取金额后支付。<br/>
            • Service fee will be paid after the optimization is completed and savings/earnings are confirmed.
            """
            story.append(Paragraph(fee_text, body_style))
            story.append(Spacer(1, 0.3*inch))
            
            # 服务流程
            story.append(Paragraph("<b>四、服务流程 SERVICE PROCESS</b>", styles['Heading2']))
            process_text = f"""
            <b>4.1</b> 甲方授权乙方代表其办理相关财务优化手续。<br/>
            <b>4.2</b> 乙方将在获得甲方授权后开始实施优化方案。<br/>
            <b>4.3</b> 优化方案实施过程中，乙方将及时向甲方汇报进展。<br/>
            <b>4.4</b> 方案完成后，双方共同确认实际节省/赚取金额。<br/>
            <b>4.5</b> 确认金额后，甲方支付约定的服务费用。
            """
            story.append(Paragraph(process_text, body_style))
            story.append(Spacer(1, 0.3*inch))
            
            # 双方权利义务
            story.append(Paragraph("<b>五、双方权利与义务 RIGHTS AND OBLIGATIONS</b>", styles['Heading2']))
            rights_text = f"""
            <b>5.1 甲方权利 Party A's Rights:</b><br/>
            • 有权了解优化方案的详细内容和实施进度<br/>
            • 有权在确认实际节省/赚取金额后才支付费用<br/>
            • 如未产生节省/赚取，有权拒绝支付任何费用<br/>
            <br/>
            <b>5.2 乙方义务 Party B's Obligations:</b><br/>
            • 尽最大努力为甲方争取最优方案<br/>
            • 确保所有操作符合法律法规<br/>
            • 只有在为甲方创造实际价值后才收取费用<br/>
            • 对甲方信息严格保密
            """
            story.append(Paragraph(rights_text, body_style))
            story.append(Spacer(1, 0.3*inch))
            
            # 签名栏
            story.append(Spacer(1, 0.5*inch))
            story.append(Paragraph("<b>六、签名确认 SIGNATURES</b>", styles['Heading2']))
            story.append(Spacer(1, 0.2*inch))
            
            signature_data = [
                ['<b>甲方签名 Party A Signature</b>', '<b>乙方签名 Party B Signature</b>'],
                ['', ''],
                ['', ''],
                [f"姓名 Name: {customer['name']}", '姓名 Name: ___________________'],
                [f"日期 Date: {datetime.now().strftime('%Y-%m-%d')}", f"日期 Date: {datetime.now().strftime('%Y-%m-%d')}"]
            ]
            
            sig_table = Table(signature_data, colWidths=[3*inch, 3*inch], rowHeights=[0.3*inch, 0.8*inch, 0.3*inch, 0.3*inch, 0.3*inch])
            sig_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('PADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(sig_table)
            
            # 生成PDF
            doc.build(story)
            
            # 保存到数据库
            cursor.execute('''
                INSERT INTO service_contracts
                (customer_id, suggestion_id, consultation_request_id, contract_number, 
                 service_type, total_savings, our_fee_50_percent, contract_file_path, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending_signature')
            ''', (
                customer_id,
                suggestion_id,
                consultation_request_id,
                contract_number,
                suggestion['suggestion_type'],
                suggestion['estimated_savings'],
                fee_amount,
                filepath
            ))
            
            contract_id = cursor.lastrowid
            conn.commit()
            
            return {
                'contract_id': contract_id,
                'contract_number': contract_number,
                'filepath': filepath,
                'filename': filename,
                'total_savings': suggestion['estimated_savings'],
                'our_fee': fee_amount,
                'customer_gets': suggestion['estimated_savings'] * 0.5
            }
    
    def sign_contract(self, contract_id, signed_by='customer'):
        """
        合同签字
        
        Args:
            contract_id: 合同ID
            signed_by: 'customer' 或 'company'
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            if signed_by == 'customer':
                cursor.execute('''
                    UPDATE service_contracts
                    SET customer_signed = 1,
                        customer_signed_date = ?
                    WHERE id = ?
                ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), contract_id))
            else:
                cursor.execute('''
                    UPDATE service_contracts
                    SET company_signed = 1,
                        company_signed_date = ?
                    WHERE id = ?
                ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), contract_id))
            
            # 检查是否双方都已签字
            cursor.execute('''
                SELECT customer_signed, company_signed
                FROM service_contracts
                WHERE id = ?
            ''', (contract_id,))
            
            result = cursor.fetchone()
            
            if result['customer_signed'] and result['company_signed']:
                # 双方都签字了，更新状态为已生效
                cursor.execute('''
                    UPDATE service_contracts
                    SET status = 'active'
                    WHERE id = ?
                ''', (contract_id,))
                
                # 更新建议状态为服务中
                cursor.execute('''
                    UPDATE financial_optimization_suggestions
                    SET status = 'in_service'
                    WHERE id = (SELECT suggestion_id FROM service_contracts WHERE id = ?)
                ''', (contract_id,))
            
            conn.commit()
            
            return {
                'contract_id': contract_id,
                'signed_by': signed_by,
                'both_signed': result['customer_signed'] and result['company_signed']
            }


# 便捷函数
def generate_contract(customer_id, suggestion_id, consultation_id):
    """生成授权合同"""
    contract_gen = ServiceContract()
    return contract_gen.generate_authorization_contract(customer_id, suggestion_id, consultation_id)

def sign_service_contract(contract_id, signer='customer'):
    """签署合同"""
    contract_gen = ServiceContract()
    return contract_gen.sign_contract(contract_id, signer)
