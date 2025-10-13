"""
自动化月结报表生成和发送系统
- 每月30号：自动生成所有客户的月度报表
- 每月1号：批量发送报表给所有客户
"""

import os
from datetime import datetime, timedelta
from db.database import get_db, log_audit
from report.galaxy_report_generator import GalaxyMonthlyReportGenerator
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication


class MonthlyReportScheduler:
    """自动化月结报表调度器"""
    
    def __init__(self):
        self.report_generator = GalaxyMonthlyReportGenerator()
        self.admin_email = os.environ.get('ADMIN_EMAIL', '')
        self.admin_password = os.environ.get('ADMIN_PASSWORD', '')
    
    def generate_all_customer_reports(self):
        """
        每月30号执行：为所有客户生成上月的月度报表
        """
        today = datetime.now()
        
        # 计算上个月的年月
        if today.month == 1:
            target_year = today.year - 1
            target_month = 12
        else:
            target_year = today.year
            target_month = today.month - 1
        
        print(f"🌌 开始生成所有客户的月度报表：{target_year}-{target_month}")
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 获取所有客户
            cursor.execute('SELECT id, name, email FROM customers')
            customers = cursor.fetchall()
            
            success_count = 0
            fail_count = 0
            
            for customer in customers:
                try:
                    # 检查该客户该月是否有账单数据
                    cursor.execute('''
                        SELECT COUNT(*) as count
                        FROM statements s
                        JOIN credit_cards c ON s.card_id = c.id
                        WHERE c.customer_id = ?
                        AND strftime('%Y', s.statement_date) = ?
                        AND strftime('%m', s.statement_date) = ?
                    ''', (customer['id'], str(target_year), f"{target_month:02d}"))
                    
                    result = cursor.fetchone()
                    if result and result['count'] > 0:
                        # 生成报表
                        pdf_path = self.report_generator.generate_customer_monthly_report_galaxy(
                            customer['id'], 
                            target_year, 
                            target_month
                        )
                        
                        if pdf_path:
                            success_count += 1
                            print(f"  ✅ {customer['name']} - 报表生成成功")
                            log_audit('monthly_report_auto_generated', customer['id'], 
                                    f'自动生成{target_year}-{target_month}月度报表')
                        else:
                            fail_count += 1
                            print(f"  ⚠️ {customer['name']} - 报表生成失败")
                    else:
                        print(f"  ⏭️ {customer['name']} - 该月无账单数据")
                
                except Exception as e:
                    fail_count += 1
                    print(f"  ❌ {customer['name']} - 错误: {str(e)}")
            
            print(f"\n📊 报表生成完成！成功: {success_count}, 失败: {fail_count}")
            
            # 记录系统日志
            log_audit('batch_report_generation', 0, 
                     f'{target_year}-{target_month}月度报表批量生成: 成功{success_count}, 失败{fail_count}')
        
        return {
            'success': success_count,
            'failed': fail_count,
            'year': target_year,
            'month': target_month
        }
    
    def send_reports_to_all_customers(self):
        """
        每月1号执行：发送上月报表给所有客户
        """
        today = datetime.now()
        
        # 计算上个月的年月
        if today.month == 1:
            target_year = today.year - 1
            target_month = 12
        else:
            target_year = today.year
            target_month = today.month - 1
        
        print(f"📧 开始发送月度报表邮件：{target_year}-{target_month}")
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 获取该月所有生成的报表
            cursor.execute('''
                SELECT mr.*, c.name as customer_name, c.email
                FROM monthly_reports mr
                JOIN customers c ON mr.customer_id = c.id
                WHERE mr.report_year = ? AND mr.report_month = ?
                AND mr.pdf_path IS NOT NULL
            ''', (target_year, target_month))
            
            reports = cursor.fetchall()
            
            sent_count = 0
            fail_count = 0
            
            for report in reports:
                try:
                    if report['email'] and '@' in report['email']:
                        # 发送邮件
                        success = self._send_report_email(
                            customer_name=report['customer_name'],
                            customer_email=report['email'],
                            pdf_path=report['pdf_path'],
                            year=target_year,
                            month=target_month
                        )
                        
                        if success:
                            sent_count += 1
                            print(f"  ✅ {report['customer_name']} ({report['email']}) - 邮件发送成功")
                            
                            # 更新发送状态
                            cursor.execute('''
                                UPDATE monthly_reports 
                                SET email_sent = 1, email_sent_date = ?
                                WHERE id = ?
                            ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), report['id']))
                            
                            log_audit('monthly_report_sent', report['customer_id'], 
                                    f'{target_year}-{target_month}月度报表已发送至{report["email"]}')
                        else:
                            fail_count += 1
                            print(f"  ❌ {report['customer_name']} - 邮件发送失败")
                    else:
                        print(f"  ⚠️ {report['customer_name']} - 无有效邮箱")
                        fail_count += 1
                
                except Exception as e:
                    fail_count += 1
                    print(f"  ❌ {report['customer_name']} - 错误: {str(e)}")
            
            conn.commit()
            
            print(f"\n📧 邮件发送完成！成功: {sent_count}, 失败: {fail_count}")
            
            # 记录系统日志
            log_audit('batch_report_email_sent', 0, 
                     f'{target_year}-{target_month}月度报表批量发送: 成功{sent_count}, 失败{fail_count}')
        
        return {
            'sent': sent_count,
            'failed': fail_count,
            'year': target_year,
            'month': target_month
        }
    
    def _send_report_email(self, customer_name, customer_email, pdf_path, year, month):
        """发送月度报表邮件"""
        try:
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = self.admin_email
            msg['To'] = customer_email
            msg['Subject'] = f'🌌 您的{year}年{month}月信用卡月度报表 - Infinite GZ Financial'
            
            # 邮件正文（HTML格式）
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; background: linear-gradient(135deg, #FF7043 0%, #FF5722 100%); padding: 40px;">
                <div style="max-width: 600px; margin: 0 auto; background: #FFFFFF; border-radius: 16px; overflow: hidden; box-shadow: 0 8px 20px rgba(0,0,0,0.2);">
                    <!-- Header -->
                    <div style="background: linear-gradient(135deg, #FF7043 0%, #FF5722 100%); padding: 30px; text-align: center;">
                        <h1 style="color: #FFFFFF; margin: 0; font-size: 28px; font-weight: 900;">🌌 月度财务报表</h1>
                        <p style="color: rgba(255,255,255,0.95); margin: 10px 0 0 0; font-size: 16px; font-weight: 700;">
                            {year}年{month}月 银河主题专业报表
                        </p>
                    </div>
                    
                    <!-- Content -->
                    <div style="padding: 40px;">
                        <p style="font-size: 16px; color: #2C2416; font-weight: 700;">尊敬的 {customer_name}，</p>
                        
                        <p style="font-size: 14px; color: #333333; line-height: 1.8;">
                            您好！您的 <strong>{year}年{month}月</strong> 信用卡消费月度报表已经生成。
                            请查看附件中的详细分析报告。
                        </p>
                        
                        <div style="background: #FFF3E0; border-left: 4px solid #FF7043; padding: 20px; margin: 30px 0; border-radius: 8px;">
                            <h3 style="color: #FF5722; margin: 0 0 15px 0; font-size: 18px;">📊 本月报表包含：</h3>
                            <ul style="color: #333333; margin: 0; padding-left: 20px; line-height: 2;">
                                <li>✨ 所有信用卡完整交易明细</li>
                                <li>📈 消费分类统计分析</li>
                                <li>💰 优化方案和节省建议</li>
                                <li>🎯 DSR债务比率计算</li>
                                <li>🌟 50/50利润分成收益展示</li>
                            </ul>
                        </div>
                        
                        <p style="font-size: 14px; color: #333333; line-height: 1.8;">
                            如果您对报表有任何疑问，或希望了解更多优化建议，欢迎随时联系我们的专业财务顾问团队。
                        </p>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <p style="font-size: 18px; color: #FF5722; font-weight: 900; margin: 0;">
                                💡 发现节省机会？立即申请咨询！
                            </p>
                        </div>
                        
                        <p style="font-size: 12px; color: #999999; margin-top: 30px; padding-top: 20px; border-top: 1px solid #EEEEEE;">
                            此邮件由 Infinite GZ Financial 系统自动发送<br>
                            如有问题请联系: {self.admin_email}
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_body, 'html'))
            
            # 附加PDF文件
            if os.path.exists(pdf_path):
                with open(pdf_path, 'rb') as f:
                    pdf_attachment = MIMEApplication(f.read(), _subtype='pdf')
                    pdf_attachment.add_header('Content-Disposition', 'attachment', 
                                            filename=f'{customer_name}_{year}_{month}_月度报表.pdf')
                    msg.attach(pdf_attachment)
            
            # 发送邮件
            if self.admin_email and self.admin_password:
                with smtplib.SMTP('smtp.gmail.com', 587) as server:
                    server.starttls()
                    server.login(self.admin_email, self.admin_password)
                    server.send_message(msg)
                return True
            else:
                print("  ⚠️ 邮件配置未设置（需要ADMIN_EMAIL和ADMIN_PASSWORD环境变量）")
                return False
        
        except Exception as e:
            print(f"  ❌ 发送邮件失败: {str(e)}")
            return False
    
    def test_report_generation(self, customer_id=None):
        """测试报表生成功能"""
        if customer_id:
            # 测试单个客户
            today = datetime.now()
            target_year = today.year if today.month > 1 else today.year - 1
            target_month = today.month - 1 if today.month > 1 else 12
            
            pdf_path = self.report_generator.generate_customer_monthly_report_galaxy(
                customer_id, target_year, target_month
            )
            return pdf_path is not None
        else:
            # 测试所有客户
            return self.generate_all_customer_reports()
    
    def test_email_sending(self):
        """测试邮件发送功能"""
        return self.send_reports_to_all_customers()


# 更新monthly_reports表结构（添加邮件发送字段）
def init_monthly_reports_email_fields():
    """初始化月度报表邮件字段"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 检查是否需要添加email_sent字段
        cursor.execute("PRAGMA table_info(monthly_reports)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'email_sent' not in columns:
            cursor.execute('''
                ALTER TABLE monthly_reports 
                ADD COLUMN email_sent INTEGER DEFAULT 0
            ''')
        
        if 'email_sent_date' not in columns:
            cursor.execute('''
                ALTER TABLE monthly_reports 
                ADD COLUMN email_sent_date TEXT
            ''')
        
        conn.commit()


# 初始化表字段
init_monthly_reports_email_fields()
