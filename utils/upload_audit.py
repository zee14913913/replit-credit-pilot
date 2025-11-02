"""
Phase 2-3 Task 2: Flask上传审计助手
将Flask (5000)的上传事件POST到FastAPI (8000)的审计日志

设计原则：
- ✅ 异步调用，不阻塞上传流程
- ✅ 失败不影响上传（只记录错误日志）
- ✅ 记录完整上下文信息（IP、UA、customer等）
"""
import requests
import os
from typing import Optional, Dict, Any
from flask import request
import logging

logger = logging.getLogger(__name__)

# FastAPI审计端点地址
AUDIT_API_URL = "http://localhost:8000/api/audit-logs/upload-event"


def get_client_ip() -> Optional[str]:
    """
    获取客户端真实IP地址
    优先从X-Forwarded-For获取（Replit/nginx代理环境）
    """
    if request.environ.get('HTTP_X_FORWARDED_FOR'):
        # X-Forwarded-For可能包含多个IP，取第一个
        return request.environ.get('HTTP_X_FORWARDED_FOR').split(',')[0].strip()
    return request.environ.get('REMOTE_ADDR')


def get_user_agent() -> Optional[str]:
    """获取客户端User-Agent"""
    return request.environ.get('HTTP_USER_AGENT')


def record_upload_event(
    customer_id: Optional[int] = None,
    customer_code: Optional[str] = None,
    customer_name: Optional[str] = None,
    company_id: Optional[int] = None,
    upload_type: str = "unknown",
    filename: str = "",
    file_size: int = 0,
    file_path: Optional[str] = None,
    session_user: Optional[str] = None,
    success: bool = True,
    error_message: Optional[str] = None,
    additional_info: Optional[Dict[str, Any]] = None
) -> bool:
    """
    记录Flask上传事件到FastAPI审计日志
    
    Args:
        customer_id: 客户ID
        customer_code: 客户代码（如Be_rich_KP）
        customer_name: 客户姓名
        company_id: 公司ID（如果有）
        upload_type: 上传类型（credit_card_statement, savings_statement, receipt等）
        filename: 文件名
        file_size: 文件大小（字节）
        file_path: 文件保存路径
        session_user: Flask session中的用户信息
        success: 上传是否成功
        error_message: 错误信息（如果失败）
        additional_info: 其他附加信息
    
    Returns:
        bool: 审计日志是否记录成功（失败不影响上传）
    """
    try:
        # 提取客户端信息
        ip_address = get_client_ip()
        user_agent = get_user_agent()
        
        # 构建审计事件数据
        event_data = {
            "customer_id": customer_id,
            "customer_code": customer_code,
            "customer_name": customer_name,
            "company_id": company_id,
            "upload_type": upload_type,
            "filename": filename,
            "file_size": file_size,
            "file_path": file_path,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "session_user": session_user,
            "success": success,
            "error_message": error_message,
            "additional_info": additional_info
        }
        
        # POST到FastAPI审计端点
        response = requests.post(
            AUDIT_API_URL,
            json=event_data,
            timeout=2  # 2秒超时，避免阻塞
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Upload event recorded: {upload_type} - {filename} (audit_log_id={result.get('audit_log_id')})")
            return True
        else:
            logger.warning(f"⚠️ Audit API returned status {response.status_code}: {response.text}")
            return False
    
    except requests.exceptions.Timeout:
        # 超时不影响上传
        logger.warning(f"⚠️ Audit API timeout (non-blocking): {upload_type} - {filename}")
        return False
    
    except Exception as e:
        # 任何异常都不影响上传流程
        logger.error(f"❌ Failed to record upload event (non-blocking): {e}")
        return False


def record_upload_event_async(
    customer_id: Optional[int] = None,
    customer_code: Optional[str] = None,
    customer_name: Optional[str] = None,
    company_id: Optional[int] = None,
    upload_type: str = "unknown",
    filename: str = "",
    file_size: int = 0,
    file_path: Optional[str] = None,
    session_user: Optional[str] = None,
    success: bool = True,
    error_message: Optional[str] = None,
    additional_info: Optional[Dict[str, Any]] = None
):
    """
    异步记录上传事件（后台线程）
    完全不阻塞上传流程
    
    **Architect Fix**: 在启动后台线程前，同步提取IP/UA
    避免 RuntimeError: Working outside of request context
    
    用法：
        record_upload_event_async(
            customer_id=1,
            upload_type='credit_card_statement',
            filename='maybank_jan.pdf',
            file_size=524288
        )
    """
    from threading import Thread
    
    # Phase 2-3 Task 2 Bug Fix: 
    # 在主线程（request context内）同步提取IP和UA
    # 避免在后台线程中访问thread-local的Flask request对象
    try:
        captured_ip = get_client_ip()
        captured_ua = get_user_agent()
    except:
        # 如果不在Flask request上下文中（如测试），使用None
        captured_ip = None
        captured_ua = None
    
    # 在后台线程中执行审计记录，传入已提取的IP/UA
    def _worker():
        try:
            # 提取客户端信息 - 使用已捕获的值
            ip_address = captured_ip
            user_agent = captured_ua
            
            # 构建审计事件数据
            event_data = {
                "customer_id": customer_id,
                "customer_code": customer_code,
                "customer_name": customer_name,
                "company_id": company_id,
                "upload_type": upload_type,
                "filename": filename,
                "file_size": file_size,
                "file_path": file_path,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "session_user": session_user,
                "success": success,
                "error_message": error_message,
                "additional_info": additional_info
            }
            
            # POST到FastAPI审计端点
            response = requests.post(
                AUDIT_API_URL,
                json=event_data,
                timeout=2  # 2秒超时，避免阻塞
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Upload event recorded: {upload_type} - {filename} (audit_log_id={result.get('audit_log_id')})")
            else:
                logger.warning(f"⚠️ Audit API returned status {response.status_code}: {response.text}")
        
        except requests.exceptions.Timeout:
            logger.warning(f"⚠️ Audit API timeout (non-blocking): {upload_type} - {filename}")
        
        except Exception as e:
            logger.error(f"❌ Failed to record upload event (non-blocking): {e}")
    
    thread = Thread(target=_worker)
    thread.daemon = True  # 守护线程，不阻塞主进程退出
    thread.start()
