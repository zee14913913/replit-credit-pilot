"""
SFTP 客户端模块
负责建立 SFTP 连接和文件上传
"""
import os
import json
import paramiko
import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class SFTPClient:
    """SFTP 客户端，管理与 SQL ACC ERP Edition 的连接"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化 SFTP 客户端
        
        Args:
            config: SFTP配置字典，如果为None则从环境变量SFTP_CONFIG读取
        """
        if config is None:
            config_str = os.getenv("SFTP_CONFIG")
            if not config_str:
                raise ValueError("SFTP_CONFIG environment variable not set")
            config = json.loads(config_str)
        
        self.host = config.get("host")
        self.port = config.get("port", 22)
        self.username = config.get("username")
        self.password = config.get("password")
        self.remote_base_dir = config.get("remote_dir", "C:/ERP_IMPORTS")
        self.use_key_auth = config.get("use_key_auth", False)
        self.private_key_path = config.get("private_key_path", "")
        self.verify_host_key = config.get("verify_host_key", True)  # 默认启用host key验证
        self.known_hosts_path = config.get("known_hosts_path", os.path.expanduser("~/.ssh/known_hosts"))
        
        # 验证必需配置
        if not all([self.host, self.username]):
            raise ValueError("SFTP config missing required fields: host, username")
        
        if not self.use_key_auth and not self.password:
            raise ValueError("Password required when use_key_auth is False")
        
        logger.info(f"✅ SFTP Client initialized for {self.username}@{self.host}:{self.port}")
    
    @contextmanager
    def get_connection(self):
        """
        获取 SFTP 连接（上下文管理器）
        
        使用方法:
            with client.get_connection() as sftp:
                sftp.put(local_path, remote_path)
        
        Yields:
            paramiko.SFTPClient: SFTP连接对象
        """
        transport = None
        sftp = None
        
        try:
            # 建立 SSH transport
            transport = paramiko.Transport((self.host, self.port))
            
            # 启动客户端（不进行认证，只获取host key）
            transport.start_client()
            
            # 🔒 安全性：SSH host key验证（防止中间人攻击）
            if self.verify_host_key:
                # 加载known_hosts文件
                host_keys = paramiko.HostKeys()
                if os.path.exists(self.known_hosts_path):
                    try:
                        host_keys.load(self.known_hosts_path)
                        logger.debug(f"Loaded host keys from: {self.known_hosts_path}")
                    except Exception as e:
                        logger.error(f"❌ Failed to load known_hosts: {e}")
                        raise
                
                # 获取服务器host key
                server_key = transport.get_remote_server_key()
                
                # 🔒 使用 lookup() 方法支持 hashed entries
                # lookup() 返回 dict: {key_type: PKey}
                lookup_candidates = [
                    self.host,
                    f"[{self.host}]:{self.port}",
                ]
                
                stored_key_map = None
                for candidate in lookup_candidates:
                    stored_key_map = host_keys.lookup(candidate)
                    if stored_key_map:
                        logger.debug(f"Found stored keys for: {candidate}")
                        break
                
                # 🔒 严格模式：未知主机必须拒绝
                if stored_key_map is None:
                    error_msg = (
                        f"❌ Host key verification failed: {self.host}:{self.port} not found in known_hosts.\n"
                        f"Known_hosts file: {self.known_hosts_path}\n"
                        f"To fix this, add the server key (works with both hashed and unhashed entries):\n"
                        f"  ssh-keyscan -p {self.port} {self.host} >> {self.known_hosts_path}\n"
                        f"Or manually connect once via SSH to add the key:\n"
                        f"  ssh -p {self.port} {self.username}@{self.host}\n"
                        f"Or disable host key verification (NOT RECOMMENDED) by setting verify_host_key=false."
                    )
                    logger.error(error_msg)
                    raise paramiko.SSHException(error_msg)
                
                # 从字典中获取与服务器 key 类型匹配的 key
                server_key_type = server_key.get_name()
                stored_key = stored_key_map.get(server_key_type)
                
                if stored_key is None:
                    error_msg = (
                        f"❌ Host key type mismatch: server presented {server_key_type}, "
                        f"but known_hosts has {list(stored_key_map.keys())}. "
                        f"Update known_hosts with the correct key type."
                    )
                    logger.error(error_msg)
                    raise paramiko.SSHException(error_msg)
                
                # 验证 key 是否匹配
                if stored_key.asbytes() != server_key.asbytes():
                    error_msg = (
                        f"❌ Host key mismatch for {self.host}:{self.port}! "
                        f"Possible MITM attack detected. "
                        f"Server presented key fingerprint: {server_key.get_base64()}\n"
                        f"Stored key fingerprint: {stored_key.get_base64()}\n"
                        f"Remove the old key and re-add the correct one."
                    )
                    logger.error(error_msg)
                    raise paramiko.SSHException(error_msg)
                
                logger.info(f"✅ Host key verified successfully for {self.host}:{self.port} ({server_key_type})")
            
            # 在同一个transport session上进行认证
            if self.use_key_auth and self.private_key_path:
                # 使用私钥认证
                private_key = paramiko.RSAKey.from_private_key_file(self.private_key_path)
                transport.auth_publickey(self.username, private_key)
                logger.info(f"🔑 Connected using SSH key authentication")
            else:
                # 使用密码认证
                transport.auth_password(self.username, self.password)
                logger.info(f"🔑 Connected using password authentication")
            
            # 创建 SFTP 客户端
            sftp = paramiko.SFTPClient.from_transport(transport)
            logger.info(f"✅ SFTP connection established to {self.host}")
            
            yield sftp
            
        except paramiko.AuthenticationException as e:
            logger.error(f"❌ SFTP authentication failed: {e}")
            raise
        except paramiko.SSHException as e:
            logger.error(f"❌ SFTP SSH error: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ SFTP connection error: {e}")
            raise
        finally:
            # 清理连接
            if sftp:
                sftp.close()
                logger.debug("SFTP client closed")
            if transport:
                transport.close()
                logger.debug("SSH transport closed")
    
    def upload_file(self, local_path: str, remote_path: str) -> Dict[str, Any]:
        """
        上传单个文件到远程服务器
        
        Args:
            local_path: 本地文件路径
            remote_path: 远程文件路径
        
        Returns:
            Dict包含上传结果:
                - success: bool
                - message: str
                - file_size: int (可选)
                - duration: float (可选)
        """
        import time
        
        # 验证本地文件存在
        if not os.path.exists(local_path):
            return {
                "success": False,
                "message": f"Local file not found: {local_path}"
            }
        
        # 获取文件大小
        file_size = os.path.getsize(local_path)
        
        try:
            start_time = time.time()
            
            with self.get_connection() as sftp:
                # 确保远程目录存在
                remote_dir = os.path.dirname(remote_path)
                self._ensure_remote_dir(sftp, remote_dir)
                
                # 上传文件
                sftp.put(local_path, remote_path)
                
                duration = time.time() - start_time
                
                logger.info(f"✅ Uploaded: {local_path} → {remote_path} ({file_size} bytes, {duration:.2f}s)")
                
                return {
                    "success": True,
                    "message": f"File uploaded successfully: {os.path.basename(local_path)}",
                    "file_size": file_size,
                    "duration": duration
                }
                
        except Exception as e:
            logger.error(f"❌ Upload failed: {local_path} | Error: {e}")
            return {
                "success": False,
                "message": f"Upload failed: {str(e)}",
                "error": str(e)
            }
    
    def _ensure_remote_dir(self, sftp: paramiko.SFTPClient, remote_dir: str):
        """
        确保远程目录存在，不存在则创建
        
        Args:
            sftp: SFTP客户端
            remote_dir: 远程目录路径
        """
        try:
            sftp.stat(remote_dir)
            logger.debug(f"Remote dir exists: {remote_dir}")
        except FileNotFoundError:
            # 目录不存在，递归创建
            parent_dir = os.path.dirname(remote_dir)
            if parent_dir and parent_dir != remote_dir:
                self._ensure_remote_dir(sftp, parent_dir)
            
            sftp.mkdir(remote_dir)
            logger.info(f"📁 Created remote directory: {remote_dir}")
    
    def test_connection(self) -> Dict[str, Any]:
        """
        测试 SFTP 连接
        
        Returns:
            Dict包含测试结果:
                - success: bool
                - message: str
                - server_info: dict (可选)
        """
        try:
            with self.get_connection() as sftp:
                # 尝试列出根目录
                try:
                    sftp.listdir('.')
                except:
                    pass
                
                return {
                    "success": True,
                    "message": f"Successfully connected to {self.host}",
                    "server_info": {
                        "host": self.host,
                        "port": self.port,
                        "username": self.username
                    }
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}",
                "error": str(e)
            }
    
    def get_payload_remote_path(self, payload_type: str) -> str:
        """
        根据数据类型获取远程目标路径（防止路径遍历攻击）
        
        Args:
            payload_type: 数据类型（sales, suppliers, payments等）
        
        Returns:
            远程目录路径
        """
        # 🔒 安全性：严格白名单验证（防止路径注入）
        allowed_types = {
            "sales", "suppliers", "payments", "customers",
            "bank", "payroll", "loan"
        }
        
        if payload_type not in allowed_types:
            raise ValueError(
                f"Invalid payload_type: {payload_type}. "
                f"Allowed types: {allowed_types}"
            )
        
        # 构造路径（使用posixpath确保Linux路径格式）
        import posixpath
        remote_path = posixpath.join(self.remote_base_dir, payload_type)
        
        # 🔒 安全性：规范化路径并验证不超出base_dir
        normalized = posixpath.normpath(remote_path)
        if not normalized.startswith(self.remote_base_dir):
            raise SecurityError(
                f"Path traversal detected: {payload_type} would escape base directory"
            )
        
        return normalized + "/"


class SecurityError(Exception):
    """安全相关错误"""
    pass
