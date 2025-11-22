#!/usr/bin/env python3
import os
import json
from datetime import datetime

def backup_env_vars():
    """备份环境变量配置（不含敏感值）"""
    print("="*60)
    print("💾 环境变量备份")
    print("="*60)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 需要追踪的环境变量（只记录是否存在，不记录值）
    env_vars = [
        'GOOGLE_PROJECT_ID',
        'GOOGLE_PROCESSOR_ID',
        'GOOGLE_LOCATION',
        'GOOGLE_SERVICE_ACCOUNT_JSON',
        'DOCPARSER_API_KEY',
        'DOCPARSER_PARSER_ID',
        'SECRET_KEY',
        'DATABASE_URL',
        'FLASK_ENV',
        'FLASK_DEBUG'
    ]
    
    backup_data = {
        'timestamp': datetime.now().isoformat(),
        'environment_variables': {}
    }
    
    configured = 0
    missing = 0
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # 只记录变量存在，不记录实际值
            backup_data['environment_variables'][var] = {
                'configured': True,
                'length': len(value) if value else 0
            }
            print(f"✅ {var}: 已配置 ({len(value)} 字符)")
            configured += 1
        else:
            backup_data['environment_variables'][var] = {
                'configured': False,
                'length': 0
            }
            print(f"⚠️ {var}: 未配置")
            missing += 1
    
    # 保存到文件
    filename = f"logs/env_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 备份文件: {filename}")
    print(f"📊 已配置: {configured}, 未配置: {missing}\n")
    
    return 0 if missing == 0 else 1

if __name__ == "__main__":
    import sys
    sys.exit(backup_env_vars())
