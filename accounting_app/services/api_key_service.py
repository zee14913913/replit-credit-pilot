"""
Phase 2-2 Task 5: API密钥生成和管理服务

核心功能：
1. 安全随机生成API密钥
2. SHA-256哈希存储（绝不存储明文）
3. 密钥前缀标识（sk_live_/sk_test_）
4. 密钥验证和权限检查
"""
import secrets
import hashlib
import string
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import logging

logger = logging.getLogger(__name__)


class APIKeyService:
    """API密钥管理服务"""
    
    # 密钥格式配置
    KEY_PREFIX_LIVE = "sk_live_"
    KEY_PREFIX_TEST = "sk_test_"
    KEY_LENGTH = 32  # 密钥随机部分长度
    HASH_ALGORITHM = "sha256"
    
    def __init__(self, db_url: Optional[str] = None):
        """初始化服务"""
        self.db_url = db_url or os.environ.get('DATABASE_URL')
        if not self.db_url:
            raise ValueError("DATABASE_URL not configured")
    
    def _get_connection(self):
        """获取数据库连接"""
        if not self.db_url:
            raise ValueError("DATABASE_URL not configured")
        return psycopg2.connect(self.db_url)
    
    # ========== 密钥生成 ==========
    
    def generate_api_key(self, environment: str = "live") -> tuple[str, str, str]:
        """
        生成新的API密钥
        
        **安全要求：**
        1. 使用secrets模块生成加密安全的随机字符串
        2. 返回明文密钥（仅此一次显示给用户）
        3. 同时返回SHA-256哈希用于存储
        4. 返回前缀用于快速查找
        
        Args:
            environment: "live" 或 "test"
        
        Returns:
            tuple: (明文密钥, 密钥前缀, SHA-256哈希)
            
        Example:
            key, prefix, hash = generate_api_key("live")
            # key: "sk_live_abc123...xyz" (显示给用户，仅此一次)
            # prefix: "sk_live_abc123" (存储，用于快速查找)
            # hash: "a1b2c3..." (存储，用于验证)
        """
        # 1. 选择前缀
        if environment == "live":
            prefix_base = self.KEY_PREFIX_LIVE
        elif environment == "test":
            prefix_base = self.KEY_PREFIX_TEST
        else:
            raise ValueError(f"Invalid environment: {environment}. Must be 'live' or 'test'")
        
        # 2. 生成加密安全的随机字符串
        # 使用secrets.token_urlsafe确保密码学安全性
        random_part = secrets.token_urlsafe(self.KEY_LENGTH)
        
        # 3. 组合完整密钥（明文）
        full_key = f"{prefix_base}{random_part}"
        
        # 4. 提取前缀（前12个字符用于快速查找）
        key_prefix = full_key[:12]  # sk_live_abc or sk_test_abc
        
        # 5. 生成SHA-256哈希（用于存储）
        key_hash = hashlib.sha256(full_key.encode('utf-8')).hexdigest()
        
        return full_key, key_prefix, key_hash
    
    def hash_api_key(self, api_key: str) -> str:
        """
        对API密钥进行SHA-256哈希
        
        Args:
            api_key: 明文API密钥
        
        Returns:
            str: SHA-256哈希（64字符十六进制）
        """
        return hashlib.sha256(api_key.encode('utf-8')).hexdigest()
    
    # ========== 密钥创建 ==========
    
    def create_api_key(
        self,
        user_id: int,
        company_id: int,
        name: str,
        permissions: List[str],
        environment: str = "live",
        rate_limit: int = 100,
        expires_in_days: Optional[int] = None,
        created_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        创建新的API密钥
        
        **重要：仅在此处返回明文密钥，之后仅存储哈希！**
        
        Args:
            user_id: 用户ID
            company_id: 公司ID
            name: 密钥名称
            permissions: 权限列表
            environment: "live" 或 "test"
            rate_limit: 每分钟请求限制
            expires_in_days: 多少天后过期（None表示永不过期）
            created_by: 创建人ID
        
        Returns:
            dict: {
                "id": 密钥ID,
                "api_key": 明文密钥（仅此一次返回！），
                "key_prefix": 前缀,
                "name": 名称,
                "environment": 环境,
                "permissions": 权限列表,
                "created_at": 创建时间
            }
        """
        # 1. 生成密钥（明文、前缀、哈希）
        api_key_plaintext, key_prefix, key_hash = self.generate_api_key(environment)
        
        # 2. 计算过期时间
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now() + timedelta(days=expires_in_days)
        
        # 3. 存储到数据库（仅存储哈希！）
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    INSERT INTO api_keys (
                        user_id, company_id, key_hash, key_prefix,
                        name, environment, permissions, rate_limit,
                        expires_at, created_by, is_active
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE
                    )
                    RETURNING id, name, environment, permissions, created_at
                """, (
                    user_id, company_id, key_hash, key_prefix,
                    name, environment, permissions, rate_limit,
                    expires_at, created_by or user_id
                ))
                
                result = cursor.fetchone()
                
                if not result:
                    raise Exception("Failed to create API key")
                
                conn.commit()
                
                logger.info(
                    f"API密钥创建成功: id={result['id']}, "
                    f"user_id={user_id}, company_id={company_id}, "
                    f"environment={environment}"
                )
                
                # 4. 返回结果（包含明文密钥，仅此一次！）
                return {
                    "id": result["id"],
                    "api_key": api_key_plaintext,  # ⚠️ 明文密钥，仅此一次返回
                    "key_prefix": key_prefix,
                    "name": result["name"],
                    "environment": result["environment"],
                    "permissions": result["permissions"],
                    "created_at": result["created_at"].isoformat()
                }
        
        except Exception as e:
            conn.rollback()
            logger.error(f"创建API密钥失败: {e}")
            raise
        finally:
            conn.close()
    
    # ========== 密钥验证 ==========
    
    def verify_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """
        验证API密钥并返回关联信息
        
        Args:
            api_key: 明文API密钥
        
        Returns:
            dict 或 None: 如果密钥有效返回密钥信息，否则返回None
        """
        # 1. 计算哈希
        key_hash = self.hash_api_key(api_key)
        
        # 2. 查询数据库
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT 
                        ak.id, ak.user_id, ak.company_id,
                        ak.name, ak.environment, ak.permissions,
                        ak.rate_limit, ak.expires_at, ak.is_active,
                        u.username, u.role, c.company_name
                    FROM api_keys ak
                    JOIN users u ON ak.user_id = u.id
                    JOIN companies c ON ak.company_id = c.id
                    WHERE ak.key_hash = %s
                """, (key_hash,))
                
                result = cursor.fetchone()
                
                if not result:
                    logger.warning("API密钥验证失败: 密钥不存在")
                    return None
                
                # 3. 检查是否激活
                if not result['is_active']:
                    logger.warning(f"API密钥验证失败: 密钥已被撤销 (id={result['id']})")
                    return None
                
                # 4. 检查是否过期
                if result['expires_at'] and datetime.now() > result['expires_at']:
                    logger.warning(f"API密钥验证失败: 密钥已过期 (id={result['id']})")
                    return None
                
                # 5. 更新最后使用时间
                cursor.execute("""
                    UPDATE api_keys
                    SET last_used_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (result['id'],))
                conn.commit()
                
                logger.info(f"API密钥验证成功: id={result['id']}, user={result['username']}")
                
                return dict(result)
        
        except Exception as e:
            logger.error(f"验证API密钥时出错: {e}")
            return None
        finally:
            conn.close()
    
    # ========== 密钥管理 ==========
    
    def list_api_keys(
        self,
        user_id: Optional[int] = None,
        company_id: Optional[int] = None,
        include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        列出API密钥
        
        Args:
            user_id: 按用户ID筛选
            company_id: 按公司ID筛选
            include_inactive: 是否包含已撤销的密钥
        
        Returns:
            List[dict]: 密钥列表（不包含哈希和明文）
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = """
                    SELECT 
                        id, user_id, company_id, key_prefix,
                        name, environment, permissions, rate_limit,
                        expires_at, is_active, last_used_at, last_used_ip,
                        created_at, created_by, revoked_at, revoked_by, revoked_reason
                    FROM api_keys
                    WHERE 1=1
                """
                params = []
                
                if user_id:
                    query += " AND user_id = %s"
                    params.append(user_id)
                
                if company_id:
                    query += " AND company_id = %s"
                    params.append(company_id)
                
                if not include_inactive:
                    query += " AND is_active = TRUE"
                
                query += " ORDER BY created_at DESC"
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                return [dict(row) for row in results]
        
        finally:
            conn.close()
    
    def revoke_api_key(
        self,
        key_id: int,
        revoked_by: int,
        reason: str
    ) -> bool:
        """
        撤销API密钥
        
        Args:
            key_id: 密钥ID
            revoked_by: 撤销人ID
            reason: 撤销原因
        
        Returns:
            bool: 是否成功撤销
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE api_keys
                    SET 
                        is_active = FALSE,
                        revoked_at = CURRENT_TIMESTAMP,
                        revoked_by = %s,
                        revoked_reason = %s
                    WHERE id = %s AND is_active = TRUE
                    RETURNING id
                """, (revoked_by, reason, key_id))
                
                result = cursor.fetchone()
                conn.commit()
                
                if result:
                    logger.info(f"API密钥已撤销: id={key_id}, by={revoked_by}, reason={reason}")
                    return True
                else:
                    logger.warning(f"撤销API密钥失败: 密钥不存在或已被撤销 (id={key_id})")
                    return False
        
        except Exception as e:
            conn.rollback()
            logger.error(f"撤销API密钥时出错: {e}")
            raise
        finally:
            conn.close()
