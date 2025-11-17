"""
配置文件加载器
从 settings.json 加载配置，支持环境变量替换
"""
import json
import os
import re
from pathlib import Path
from typing import Any, Dict


class SettingsLoader:
    """配置加载器"""
    
    def __init__(self, config_path: str = "config/settings.json"):
        self.config_path = Path(config_path)
        self._settings = None
    
    def load(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            raw_config = json.load(f)
        
        self._settings = self._replace_env_vars(raw_config)
        return self._settings
    
    def _replace_env_vars(self, obj: Any) -> Any:
        """递归替换环境变量"""
        if isinstance(obj, dict):
            return {k: self._replace_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._replace_env_vars(item) for item in obj]
        elif isinstance(obj, str):
            return self._replace_env_var_in_string(obj)
        else:
            return obj
    
    def _replace_env_var_in_string(self, value: str) -> str:
        """替换字符串中的环境变量 ${VAR_NAME}"""
        pattern = r'\$\{([^}]+)\}'
        
        def replacer(match):
            env_var = match.group(1)
            return os.getenv(env_var, match.group(0))
        
        return re.sub(pattern, replacer, value)
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值（支持点号分隔的嵌套键）"""
        if self._settings is None:
            self.load()
        
        keys = key.split('.')
        value = self._settings
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_pdf_upload_config(self) -> Dict[str, Any]:
        """获取PDF上传配置"""
        return self.get('pdf_upload', {})
    
    def get_google_ai_config(self) -> Dict[str, Any]:
        """获取Google Document AI配置"""
        return self.get('google_document_ai', {})
    
    def get_database_config(self) -> Dict[str, Any]:
        """获取数据库配置"""
        return self.get('database', {})
    
    def get_notification_config(self) -> Dict[str, Any]:
        """获取通知配置"""
        return self.get('notifications', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return self.get('logging', {})
    
    def validate_required_env_vars(self) -> Dict[str, bool]:
        """验证必需的环境变量"""
        required_vars = [
            'GOOGLE_CLOUD_PROJECT_ID',
            'DOCUMENT_AI_PROCESSOR_ID',
            'SMTP_HOST',
            'SMTP_PORT',
            'SMTP_USERNAME',
            'SMTP_PASSWORD',
            'SMTP_FROM_EMAIL'
        ]
        
        status = {}
        for var in required_vars:
            status[var] = os.getenv(var) is not None
        
        return status
    
    def create_directories(self):
        """创建必要的目录"""
        directories = [
            self.get('pdf_upload.upload_directory'),
            self.get('pdf_upload.temp_directory'),
            self.get('database.auto_backup.backup_directory'),
            Path(self.get('logging.file_path')).parent,
            'credentials'
        ]
        
        for directory in directories:
            if directory:
                Path(directory).mkdir(parents=True, exist_ok=True)


# 全局配置实例
settings = SettingsLoader()


def get_settings() -> SettingsLoader:
    """获取配置实例"""
    return settings


if __name__ == '__main__':
    # 测试配置加载
    config = SettingsLoader()
    config.load()
    config.create_directories()
    
    print("="*80)
    print("配置加载测试")
    print("="*80)
    
    print("\n📁 PDF上传配置:")
    print(f"   最大文件大小: {config.get('pdf_upload.max_file_size_mb')} MB")
    print(f"   上传目录: {config.get('pdf_upload.upload_directory')}")
    
    print("\n🤖 Google Document AI配置:")
    print(f"   项目ID: {config.get('google_document_ai.project_id')}")
    print(f"   位置: {config.get('google_document_ai.location')}")
    
    print("\n💾 数据库配置:")
    print(f"   类型: {config.get('database.type')}")
    print(f"   文件路径: {config.get('database.file_path')}")
    print(f"   自动备份: {config.get('database.auto_backup.enabled')}")
    
    print("\n📧 通知配置:")
    print(f"   邮件提醒: {config.get('notifications.email.enabled')}")
    print(f"   提醒时间: {config.get('notifications.reminders.daily_time')}")
    
    print("\n📝 日志配置:")
    print(f"   日志级别: {config.get('logging.level')}")
    print(f"   日志文件: {config.get('logging.file_path')}")
    
    print("\n🔐 环境变量验证:")
    env_status = config.validate_required_env_vars()
    for var, exists in env_status.items():
        status = "✅" if exists else "❌"
        print(f"   {status} {var}")
    
    print("\n✅ 配置加载完成")
    print("="*80)
