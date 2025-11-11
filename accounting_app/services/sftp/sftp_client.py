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
            
            # 认证
            if self.use_key_auth and self.private_key_path:
                # 使用私钥认证
                private_key = paramiko.RSAKey.from_private_key_file(self.private_key_path)
                transport.connect(username=self.username, pkey=private_key)
                logger.info(f"🔑 Connected using SSH key authentication")
            else:
                # 使用密码认证
                transport.connect(username=self.username, password=self.password)
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
        根据数据类型获取远程目标路径
        
        Args:
            payload_type: 数据类型（sales, suppliers, payments等）
        
        Returns:
            远程目录路径
        """
        # 路径映射（防止路径注入）
        path_mapping = {
            "sales": f"{self.remote_base_dir}/sales/",
            "suppliers": f"{self.remote_base_dir}/suppliers/",
            "payments": f"{self.remote_base_dir}/payments/",
            "customers": f"{self.remote_base_dir}/customers/",
            "bank": f"{self.remote_base_dir}/bank/",
            "payroll": f"{self.remote_base_dir}/payroll/",
            "loan": f"{self.remote_base_dir}/loan/",
        }
        
        if payload_type not in path_mapping:
            raise ValueError(f"Invalid payload_type: {payload_type}")
        
        return path_mapping[payload_type]
