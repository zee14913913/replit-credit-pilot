"""
Flask Session解析器 - Phase 2-2 Task 8

功能：在FastAPI中解析和验证Flask session cookie
支持：itsdangerous签名验证、session数据提取、用户认证
"""
import os
import logging
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status

logger = logging.getLogger(__name__)

# ========== Flask Session Parser ==========

class FlaskSessionParser:
    """
    Flask Session解析器
    
    解析Flask使用itsdangerous库创建的session cookie
    """
    
    def __init__(self, secret_key: Optional[str] = None):
        """
        初始化session解析器
        
        Args:
            secret_key: Flask应用的SECRET_KEY（默认从环境变量获取）
        """
        self.secret_key = secret_key or os.environ.get('SECRET_KEY')
        
        if not self.secret_key:
            logger.warning("⚠️ SECRET_KEY未设置，Flask session验证将失败")
            self.serializer = None
            return
        
        # 延迟导入itsdangerous（避免未安装时启动失败）
        try:
            from itsdangerous import URLSafeTimedSerializer
            from itsdangerous.serializer import Serializer
            from flask.json.tag import TaggedJSONSerializer
            import hashlib
            
            # Flask兼容配置：使用TaggedJSONSerializer + HMAC + SHA1
            # 参考：flask.sessions.SecureCookieSessionInterface
            self.serializer = URLSafeTimedSerializer(
                secret_key=self.secret_key,
                salt='cookie-session',  # Flask默认session salt
                serializer=TaggedJSONSerializer(),  # Flask使用TaggedJSON序列化器
                signer_kwargs={
                    'key_derivation': 'hmac',  # Flask默认使用HMAC派生密钥
                    'digest_method': hashlib.sha1  # Flask默认使用SHA1摘要
                }
            )
        except ImportError as e:
            logger.warning(f"⚠️ Flask session依赖库缺失: {e}")
            self.serializer = None
    
    def parse_session_cookie(self, cookie_value: str) -> Optional[Dict[str, Any]]:
        """
        解析Flask session cookie
        
        Args:
            cookie_value: session cookie的值
        
        Returns:
            dict: Session数据，失败返回None
        """
        if not self.serializer:
            logger.error("Session解析器未初始化（可能缺少SECRET_KEY或itsdangerous库）")
            return None
        
        try:
            # 解析并验证session签名
            session_data = self.serializer.loads(cookie_value)
            logger.debug(f"✅ Flask session解析成功: keys={list(session_data.keys())}")
            return session_data
        
        except Exception as e:
            logger.warning(f"Flask session解析失败: {e}")
            return None
    
    def extract_user_from_session(self, session_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        从session中提取用户信息
        
        Flask session通常包含：
        - user_id: 用户ID
        - username: 用户名（可选）
        - role: 角色（可选）
        - company_id: 公司ID（可选）
        
        Args:
            session_data: 解析后的session数据
        
        Returns:
            dict: 用户信息 {'user_id': int, 'username': str, ...}
        """
        user_id = session_data.get('user_id')
        
        if not user_id:
            logger.warning("Session中缺少user_id字段")
            return None
        
        return {
            'user_id': user_id,
            'username': session_data.get('username'),
            'role': session_data.get('role'),
            'company_id': session_data.get('company_id')
        }


# ========== FastAPI Session依赖 ==========

# 全局session解析器实例
flask_session_parser = FlaskSessionParser()


async def parse_flask_session_from_request(request: Request) -> Optional[Dict[str, Any]]:
    """
    从FastAPI Request中解析Flask session
    
    使用方法：
    ```python
    @router.get("/protected")
    async def protected_route(
        session_data: Optional[Dict] = Depends(parse_flask_session_from_request)
    ):
        if not session_data:
            raise HTTPException(401, "No valid session")
        user_id = session_data['user_id']
        ...
    ```
    
    Args:
        request: FastAPI Request对象
    
    Returns:
        dict: Session数据（包含user_id等），失败返回None
    """
    # 1. 提取session cookie
    session_cookie = request.cookies.get('session')
    
    if not session_cookie:
        logger.debug("请求中不包含session cookie")
        return None
    
    # 2. 解析session
    session_data = flask_session_parser.parse_session_cookie(session_cookie)
    
    if not session_data:
        logger.warning("Session cookie解析失败或签名无效")
        return None
    
    # 3. 提取用户信息
    user_info = flask_session_parser.extract_user_from_session(session_data)
    
    if not user_info:
        logger.warning("Session中缺少用户信息")
        return None
    
    logger.info(f"✅ Flask session验证成功: user_id={user_info['user_id']}, username={user_info.get('username')}")
    
    return user_info


async def require_flask_session(request: Request) -> Dict[str, Any]:
    """
    强制要求Flask session（无session则返回401错误）
    
    使用方法：
    ```python
    @router.get("/protected")
    async def protected_route(
        session_data: Dict = Depends(require_flask_session)
    ):
        user_id = session_data['user_id']
        ...
    ```
    
    Args:
        request: FastAPI Request对象
    
    Returns:
        dict: Session数据（包含user_id等）
    
    Raises:
        HTTPException: 401 如果session无效或缺失
    """
    session_data = await parse_flask_session_from_request(request)
    
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No valid Flask session. Please login first.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return session_data
