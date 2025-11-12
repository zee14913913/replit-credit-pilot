"""
AI日报邮件推送模块
功能：每天早上08:10自动发送AI日报到管理员邮箱
"""
import os
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


def send_ai_report_email():
    """
    发送最新的AI日报到管理员邮箱
    
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
        
        # 获取管理员邮箱
        admin_email = os.getenv("ADMIN_EMAIL")
        if not admin_email:
            print("⚠️ AI日报邮件推送：未配置ADMIN_EMAIL环境变量")
            return "⚠️ 未配置管理员邮箱"
        
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
        
        # 创建邮件消息
        msg = MIMEMultipart('alternative')
        msg["Subject"] = f"📊 CreditPilot AI财务日报 - {report_date}"
        msg["From"] = f"CreditPilot AI <{admin_email}>"
        msg["To"] = admin_email
        
        # 添加纯文本和HTML版本
        msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
        
        # 发送邮件（使用Gmail SMTP作为示例）
        # 注意：生产环境建议使用SendGrid或其他专业邮件服务
        smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER", admin_email)
        smtp_password = os.getenv("SMTP_PASSWORD", os.getenv("ADMIN_PASSWORD", ""))
        
        if not smtp_password:
            print("⚠️ AI日报邮件推送：未配置SMTP密码")
            return "⚠️ 未配置SMTP密码（需要SMTP_PASSWORD或ADMIN_PASSWORD）"
        
        try:
            smtp = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
            smtp.starttls()
            smtp.login(smtp_user, smtp_password)
            smtp.sendmail(msg["From"], [admin_email], msg.as_string())
            smtp.quit()
            
            success_msg = f"✅ AI日报邮件已发送到 {admin_email}"
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
