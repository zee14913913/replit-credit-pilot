"""
AI日报邮件推送模块
功能：每天早上08:10自动发送AI日报到管理员邮箱
V2企业智能版：优先使用SendGrid API（生产级稳定性）
"""
import os
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Content
    import requests as req_lib
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False
    print("⚠️ SendGrid库未安装，将使用SMTP备用方案")


def get_sendgrid_credentials():
    """
    获取SendGrid凭据（优先使用环境变量）
    返回: (api_key, from_email)
    """
    # 直接使用环境变量中的API Key（用户已在Secrets中配置）
    api_key = os.getenv("SENDGRID_API_KEY")
    
    # 发件人邮箱：优先使用SENDGRID_FROM_EMAIL，否则使用ADMIN_EMAIL
    from_email = os.getenv("SENDGRID_FROM_EMAIL")
    if not from_email:
        from_email = os.getenv("ADMIN_EMAIL")
    
    return (api_key, from_email)


def send_ai_report_email():
    """
    发送最新的AI日报到管理员邮箱
    V2企业智能版：优先使用SendGrid API
    
    返回:
        str: 发送状态消息
    """
    try:
        # 连接数据库获取最新日报
        db = sqlite3.connect('db/smart_loan_manager.db')
        db.row_factory = sqlite3.Row
        cursor = db.cursor()
        
        cursor.execute("""
            SELECT response, created_at FROM ai_logs
            WHERE query LIKE 'AI日报%'
            ORDER BY created_at DESC LIMIT 1
        """)
        
        latest = cursor.fetchone()
        db.close()
        
        if not latest:
            print("❌ AI日报邮件推送：无日报可发送")
            return "❌ 无日报可发送"
        
        # 获取收件人邮箱
        recipient_email = os.getenv("ADMIN_EMAIL")
        if not recipient_email:
            print("⚠️ AI日报邮件推送：未配置ADMIN_EMAIL环境变量")
            return "⚠️ 未配置管理员邮箱"
        
        # 获取SendGrid凭据（包含验证过的发件人邮箱）
        sendgrid_api_key, sendgrid_from_email = get_sendgrid_credentials()
        use_sendgrid = SENDGRID_AVAILABLE and sendgrid_api_key and sendgrid_from_email
        
        if use_sendgrid:
            print(f"✅ 使用SendGrid发送（发件人: {sendgrid_from_email}）")
        
        # 构建邮件内容
        report_date = latest['created_at'].split("T")[0] if "T" in latest['created_at'] else latest['created_at'].split(" ")[0]
        
        # 创建HTML邮件
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: #fff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h1 {{ color: #ff007f; border-bottom: 3px solid #ff007f; padding-bottom: 10px; }}
                .date {{ color: #666; font-size: 14px; margin-bottom: 20px; }}
                .report {{ line-height: 1.8; color: #333; white-space: pre-wrap; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #888; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📊 CreditPilot AI 财务日报</h1>
                <div class="date">📅 报告日期: {report_date}</div>
                <div class="report">{latest['response']}</div>
                <div class="footer">
                    <p>本邮件由 CreditPilot 智能财务系统自动生成</p>
                    <p>© 2025 CreditPilot - Smart Credit & Loan Manager</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # 创建纯文本备用内容
        text_body = f"""
📊 CreditPilot AI 财务日报

📅 报告日期: {report_date}

{latest['response']}

---
本邮件由 CreditPilot 智能财务系统自动生成
© 2025 CreditPilot - Smart Credit & Loan Manager
        """
        
        # ===========================================
        # 优先方案：SendGrid API（企业级稳定性）
        # ===========================================
        if use_sendgrid:
            try:
                # 使用SendGrid验证过的发件人邮箱
                message = Mail(
                    from_email=sendgrid_from_email,
                    to_emails=recipient_email,
                    subject=f"📊 CreditPilot AI财务日报 - {report_date}",
                    plain_text_content=text_body,
                    html_content=html_body
                )
                
                sg = SendGridAPIClient(sendgrid_api_key)
                response = sg.send(message)
                
                success_msg = f"✅ AI日报邮件已通过SendGrid发送到 {recipient_email}"
                print(f"\n{'='*60}")
                print(success_msg)
                print(f"📧 SendGrid状态码: {response.status_code}")
                print(f"📤 发件人: {sendgrid_from_email}")
                print(f"📥 收件人: {recipient_email}")
                print(f"{'='*60}\n")
                return success_msg
                
            except Exception as sg_error:
                error_msg = f"⚠️ SendGrid发送失败: {str(sg_error)}"
                print(error_msg)
                print("尝试使用SMTP备用方案...")
                use_sendgrid = False  # 降级到SMTP
        
        # ===========================================
        # 备用方案：SMTP（当SendGrid不可用时）
        # ===========================================
        if not use_sendgrid:
            # 创建邮件消息
            msg = MIMEMultipart('alternative')
            msg["Subject"] = f"📊 CreditPilot AI财务日报 - {report_date}"
            msg["From"] = f"CreditPilot AI <{recipient_email}>"
            msg["To"] = recipient_email
            
            # 添加纯文本和HTML版本
            msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
            msg.attach(MIMEText(html_body, 'html', 'utf-8'))
            
            smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
            smtp_port = int(os.getenv("SMTP_PORT", "587"))
            smtp_user = os.getenv("SMTP_USER", recipient_email)
            smtp_password = os.getenv("SMTP_PASSWORD", os.getenv("ADMIN_PASSWORD", ""))
            
            if not smtp_password:
                print("⚠️ AI日报邮件推送：未配置SMTP密码")
                return "⚠️ 未配置SMTP密码（需要SMTP_PASSWORD或ADMIN_PASSWORD）"
            
            try:
                smtp = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
                smtp.starttls()
                smtp.login(smtp_user, smtp_password)
                smtp.sendmail(msg["From"], [recipient_email], msg.as_string())
                smtp.quit()
                
                success_msg = f"✅ AI日报邮件已通过SMTP发送到 {recipient_email}"
                print(f"\n{'='*60}")
                print(success_msg)
                print(f"{'='*60}\n")
                return success_msg
                
            except smtplib.SMTPAuthenticationError:
                error_msg = "❌ SMTP认证失败，请检查邮箱密码"
                print(f"⚠️ {error_msg}")
                return error_msg
                
            except Exception as smtp_error:
                error_msg = f"❌ SMTP发送失败: {str(smtp_error)}"
                print(f"⚠️ {error_msg}")
                return error_msg
        
    except Exception as e:
        error_msg = f"❌ 邮件发送失败: {str(e)}"
        print(f"⚠️ {error_msg}")
        import traceback
        traceback.print_exc()
        return error_msg


# 支持直接运行测试
if __name__ == "__main__":
    print("🧪 测试AI日报邮件发送...")
    result = send_ai_report_email()
    print(f"\n结果: {result}")
