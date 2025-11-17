# 配置文件说明

## 文件结构

```
config/
├── settings.json          # 主配置文件
├── settings_loader.py     # 配置加载器
└── README.md             # 本说明文件
```

## settings.json 配置说明

### 1. PDF 上传设置 (`pdf_upload`)

```json
{
  "max_file_size_mb": 10,           // 最大文件大小（MB）
  "allowed_mime_types": [...],      // 允许的MIME类型
  "upload_directory": "./uploads/statements",  // 上传目录
  "temp_directory": "./uploads/temp"          // 临时目录
}
```

### 2. Google Document AI 配置 (`google_document_ai`)

```json
{
  "project_id": "${GOOGLE_CLOUD_PROJECT_ID}",      // 项目ID（从环境变量）
  "processor_id": "${DOCUMENT_AI_PROCESSOR_ID}",   // 处理器ID（从环境变量）
  "location": "us",                                // API位置
  "api_credentials_path": "./credentials/google-cloud-key.json"
}
```

**环境变量要求**：
- `GOOGLE_CLOUD_PROJECT_ID` - Google Cloud项目ID
- `DOCUMENT_AI_PROCESSOR_ID` - Document AI处理器ID

### 3. 数据库设置 (`database`)

```json
{
  "type": "SQLite",
  "file_path": "./data/creditpilot.db",
  "auto_backup": {
    "enabled": true,
    "schedule": "0 2 * * *",        // Cron表达式：每日凌晨2点
    "retention_days": 30            // 备份保留30天
  }
}
```

### 4. 通知设置 (`notifications`)

```json
{
  "email": {
    "enabled": true,
    "smtp_host": "${SMTP_HOST}",     // SMTP服务器（从环境变量）
    "smtp_port": "${SMTP_PORT}",     // SMTP端口
    "smtp_username": "${SMTP_USERNAME}",
    "smtp_password": "${SMTP_PASSWORD}"
  },
  "reminders": {
    "daily_time": "09:00",           // 每日提醒时间
    "advance_days": [3, 7, 14]       // 提前提醒天数
  }
}
```

**环境变量要求**：
- `SMTP_HOST` - SMTP服务器地址
- `SMTP_PORT` - SMTP端口（如587）
- `SMTP_USERNAME` - SMTP用户名
- `SMTP_PASSWORD` - SMTP密码
- `SMTP_FROM_EMAIL` - 发件人邮箱

### 5. 日志设置 (`logging`)

```json
{
  "level": "INFO",                  // 日志级别：DEBUG, INFO, WARNING, ERROR
  "file_path": "./logs/system.log", // 日志文件路径
  "rotation": {
    "enabled": true,
    "when": "daily",                // 每日轮转
    "retention_days": 30            // 保留30天
  }
}
```

## 使用方法

### 基础用法

```python
from config.settings_loader import get_settings

# 获取配置实例
settings = get_settings()
settings.load()

# 读取配置
max_size = settings.get('pdf_upload.max_file_size_mb')
project_id = settings.get('google_document_ai.project_id')
```

### 快捷方法

```python
# 获取特定模块配置
pdf_config = settings.get_pdf_upload_config()
db_config = settings.get_database_config()
```

### 创建必要目录

```python
settings.create_directories()  # 自动创建所有必要目录
```

### 验证环境变量

```python
env_status = settings.validate_required_env_vars()
for var, exists in env_status.items():
    print(f"{var}: {'✅' if exists else '❌'}")
```

## 环境变量设置

在Replit Secrets中添加以下环境变量：

### Google Document AI
- `GOOGLE_CLOUD_PROJECT_ID` = `famous-tree-468019-b9`
- `DOCUMENT_AI_PROCESSOR_ID` = `您的处理器ID`

### SMTP邮件
- `SMTP_HOST` = `smtp.gmail.com`
- `SMTP_PORT` = `587`
- `SMTP_USERNAME` = `您的邮箱`
- `SMTP_PASSWORD` = `您的密码`
- `SMTP_FROM_EMAIL` = `noreply@creditpilot.com`

## 注意事项

1. **环境变量替换**：配置文件中的 `${VAR_NAME}` 会自动替换为环境变量值
2. **目录自动创建**：调用 `create_directories()` 会创建所有必要目录
3. **配置验证**：使用 `validate_required_env_vars()` 检查环境变量是否完整
4. **安全性**：敏感信息（密码、密钥）必须通过环境变量设置，不要写在配置文件中

## 测试配置

```bash
# 运行配置测试
python3 config/settings_loader.py
```

输出示例：
```
================================================================================
配置加载测试
================================================================================

📁 PDF上传配置:
   最大文件大小: 10 MB
   上传目录: ./uploads/statements

🤖 Google Document AI配置:
   项目ID: famous-tree-468019-b9
   位置: us

✅ 配置加载完成
================================================================================
```
