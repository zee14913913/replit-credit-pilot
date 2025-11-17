"""
邮件和SMS通知服务
支持Twilio SMS和SendGrid邮件发送
"""
import os
import logging
from typing import Optional
from twilio.rest import Client as TwilioClient

# 导入统一配色系统
from config.colors import COLORS

logger = logging.getLogger(__name__)


class EmailNotificationService:
    """
    统一的邮件和SMS通知服务
    """
    
    def __init__(self):
        """初始化Twilio和SendGrid客户端"""
        # Twilio配置（从环境变量读取）
        self.twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_phone_number = os.getenv('TWILIO_PHONE_NUMBER')
        
        # SendGrid配置
        self.sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
        self.from_email = os.getenv('NOTIFICATION_FROM_EMAIL', 'notifications@gzloans.com')
        
        # 初始化Twilio客户端
        if self.twilio_account_sid and self.twilio_auth_token:
            try:
                self.twilio_client = TwilioClient(
                    self.twilio_account_sid, 
                    self.twilio_auth_token
                )
                logger.info("✅ Twilio客户端初始化成功")
            except Exception as e:
                logger.warning(f"⚠️ Twilio客户端初始化失败: {e}")
                self.twilio_client = None
        else:
            self.twilio_client = None
            logger.info("ℹ️ Twilio凭据未配置，SMS功能不可用")
    
    def send_sms(
        self, 
        to_phone: str, 
        message: str
    ) -> bool:
        """
        发送SMS通知
        
        Args:
            to_phone: 接收者手机号（国际格式，如+60123456789）
            message: 短信内容
            
        Returns:
            bool: 是否发送成功
        """
        if not self.twilio_client:
            logger.warning("❌ Twilio客户端未初始化，无法发送SMS")
            return False
        
        if not self.twilio_phone_number:
            logger.warning("❌ Twilio发送号码未配置")
            return False
        
        try:
            # 发送SMS
            sms = self.twilio_client.messages.create(
                body=message,
                from_=self.twilio_phone_number,
                to=to_phone
            )
            
            logger.info(f"✅ SMS发送成功 (SID: {sms.sid}) → {to_phone}")
            return True
            
        except Exception as e:
            logger.error(f"❌ SMS发送失败 → {to_phone}: {e}")
            return False
    
    def send_email(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str,
        plain_content: Optional[str] = None
    ) -> bool:
        """
        发送邮件通知
        
        Args:
            to_email: 接收者邮箱
            subject: 邮件主题
            html_content: HTML格式邮件内容
            plain_content: 纯文本邮件内容（可选）
            
        Returns:
            bool: 是否发送成功
        """
        if not self.sendgrid_api_key:
            logger.warning("❌ SendGrid API Key未配置，无法发送邮件")
            return False
        
        try:
            # 使用SendGrid发送邮件
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Content
            
            # 构建邮件
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )
            
            # 如果提供了纯文本内容，添加到邮件
            if plain_content:
                message.content = [
                    Content("text/plain", plain_content),
                    Content("text/html", html_content)
                ]
            
            # 发送邮件
            sg = SendGridAPIClient(self.sendgrid_api_key)
            response = sg.send(message)
            
            logger.info(f"✅ 邮件发送成功 (状态码: {response.status_code}) → {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 邮件发送失败 → {to_email}: {e}")
            return False
    
    def send_notification(
        self,
        notification_type: str,
        title: str,
        message: str,
        user_email: Optional[str] = None,
        user_phone: Optional[str] = None,
        send_email: bool = True,
        send_sms: bool = False
    ) -> dict:
        """
        发送多渠道通知
        
        Args:
            notification_type: 通知类型（upload_success, upload_failure等）
            title: 通知标题
            message: 通知内容
            user_email: 用户邮箱
            user_phone: 用户手机号
            send_email: 是否发送邮件
            send_sms: 是否发送SMS
            
        Returns:
            dict: 发送结果 {'email': bool, 'sms': bool}
        """
        result = {
            'email': False,
            'sms': False
        }
        
        # 发送邮件
        if send_email and user_email:
            html_content = self._generate_email_html(
                notification_type, 
                title, 
                message
            )
            result['email'] = self.send_email(
                to_email=user_email,
                subject=title,
                html_content=html_content,
                plain_content=message
            )
        
        # 发送SMS
        if send_sms and user_phone:
            # SMS内容需要简短
            sms_message = f"{title}\n{message[:150]}"
            result['sms'] = self.send_sms(
                to_phone=user_phone,
                message=sms_message
            )
        
        return result
    
    def _generate_email_html(
        self, 
        notification_type: str, 
        title: str, 
        message: str
    ) -> str:
        """
        生成专业的HTML邮件模板
        
        Args:
            notification_type: 通知类型
            title: 标题
            message: 消息内容
            
        Returns:
            str: HTML邮件内容
        """
        # 根据通知类型选择颜色主题 - 从统一配置加载
        color_map = {
            'upload_success': COLORS.core.hot_pink,  # Hot Pink
            'upload_failure': COLORS.status.error,   # Error Red
            'admin_alert': COLORS.core.dark_purple,  # Dark Purple
            'system': '#6C757D'  # Gray (neutral, not in core palette)
        }
        
        primary_color = color_map.get(notification_type, COLORS.core.hot_pink)
        
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background-color: {COLORS.core.black};">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: {COLORS.core.black};">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #1a1a1a; border-radius: 12px; overflow: hidden; box-shadow: 0 8px 24px rgba(255, 0, 127, 0.2);">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, {primary_color} 0%, {COLORS.core.dark_purple} 100%); padding: 30px; text-align: center;">
                            <h1 style="color: {COLORS.core.white}; margin: 0; font-size: 24px; font-weight: 700;">GZ财务会计系统</h1>
                            <p style="color: rgba(255, 255, 255, 0.8); margin: 8px 0 0 0; font-size: 14px;">银行月结单智能管理平台</p>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px 30px;">
                            <h2 style="color: {primary_color}; margin: 0 0 20px 0; font-size: 20px; font-weight: 600;">{title}</h2>
                            <div style="color: #cccccc; line-height: 1.6; white-space: pre-line;">{message}</div>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #0a0a0a; padding: 20px 30px; text-align: center; border-top: 1px solid rgba(255, 0, 127, 0.2);">
                            <p style="color: #666666; margin: 0; font-size: 12px;">
                                © 2025 GZ财务会计系统 | 企业级银行贷款合规解决方案
                            </p>
                            <p style="color: #666666; margin: 8px 0 0 0; font-size: 12px;">
                                此邮件由系统自动发送，请勿直接回复
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
        return html


# 全局单例
email_notification_service = EmailNotificationService()
