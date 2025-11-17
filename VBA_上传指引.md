# VBA PDF解析强制规范 - INFINITE GZ系统

## 🔒 强制执行规则

**生效日期**: 2025-01-17  
**配置文件**: `config/pdf_parser_config.py`  
**当前模式**: `PARSER_MODE = VBA_ONLY`

---

## ✅ 允许的上传方式

### 1️⃣ VBA单文件上传（推荐）
- **端点**: `/api/upload/vba-json`
- **方法**: POST
- **格式**: JSON
- **流程**:
  1. Windows Excel + VBA解析PDF
  2. 生成标准化JSON
  3. POST到API端点

### 2️⃣ VBA批量上传
- **端点**: `/api/upload/vba-batch`
- **方法**: POST
- **格式**: JSON数组
- **流程**: 同上，支持多文件批量

### 3️⃣ 手动OCR备用（仅管理员）
- **条件**: VBA不可用时
- **触发**: 管理员手动操作
- **工具**: pytesseract

---

## ❌ 禁止的操作

| 操作 | 状态 | 原因 |
|------|------|------|
| 直接上传PDF自动解析 | ❌ **已禁用** | 准确度低、成本高 |
| 跳过VBA直接入库 | ❌ **禁止** | 违反数据规范 |
| 前端PDF上传触发解析 | ❌ **已拦截** | 系统强制VBA |

---

## 🔄 标准工作流程

```
┌─────────────────┐
│   PDF Account   │
│     Statement   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Excel Client   │
│  (Windows VBA)  │
└────────┬────────┘
         │ VBA解析
         ▼
┌─────────────────┐
│  Standard JSON  │
└────────┬────────┘
         │ API上传
         ▼
┌─────────────────┐
│ Replit Backend  │
│  (SQLite DB)    │
└─────────────────┘
```

---

## 📋 JSON标准格式

### 信用卡账单JSON示例

```json
{
  "document_type": "credit_card",
  "account_info": {
    "owner_name": "CHEOK JUN YOON",
    "bank": "HSBC",
    "card_last_4": "0034",
    "card_type": "PLATINUM",
    "statement_date": "2025-10-13",
    "card_limit": 50000.00,
    "previous_balance": 15000.00,
    "closing_balance": 18500.00
  },
  "transactions": [
    {
      "date": "2025-10-01",
      "description": "SHOPEE PAYMENT",
      "amount": 1500.00,
      "type": "debit",
      "category": "Online Shopping"
    }
  ],
  "summary": {
    "total_debits": 18500.00,
    "total_credits": 0.00,
    "transaction_count": 45
  }
}
```

---

## 🛡️ 系统拦截机制

### 批量上传路由 (`/batch/upload/<customer_id>`)

```python
# app.py line 1053-1069
if not is_direct_pdf_allowed():
    return jsonify({
        'success': False,
        'message': '❌ PDF直接上传已禁用。请使用VBA客户端解析后上传JSON数据。',
        'guidance': get_upload_guidance('zh'),
        'vba_endpoints': {
            'single': '/api/upload/vba-json',
            'batch': '/api/upload/vba-batch'
        }
    }), 403
```

---

## 📊 配置详情

### `config/pdf_parser_config.py`

```python
# 当前强制执行的解析策略
PARSER_MODE = ParserPriority.VBA_ONLY

# 允许的上传方式
ALLOWED_UPLOAD_METHODS = {
    'vba_json': True,           # ✅ VBA JSON上传（主要方式）
    'vba_batch': True,          # ✅ VBA批量上传
    'direct_pdf': False,        # ❌ 禁止直接PDF
    'ocr_manual': True,         # ✅ 管理员手动OCR
}
```

---

## 🎯 为什么强制VBA？

### ✅ VBA优势
- ✅ **准确度高**: Excel原生解析，100%准确
- ✅ **成本低**: 客户端处理，节省服务器资源
- ✅ **标准化**: JSON格式统一，易于维护
- ✅ **可控**: 客户端验证，减少错误

### ❌ 直接PDF解析的问题
- ❌ **OCR不准确**: 扫描版PDF识别错误率高
- ❌ **成本高**: 服务器资源消耗大
- ❌ **不可控**: 各银行PDF格式不统一
- ❌ **难维护**: 需要为每家银行写解析器

---

## 🔧 开发者注意事项

### 新增上传功能时

1. **必须检查配置**:
   ```python
   from config.pdf_parser_config import is_direct_pdf_allowed
   
   if not is_direct_pdf_allowed():
       return error_response()
   ```

2. **必须使用VBA端点**:
   - `/api/upload/vba-json`
   - `/api/upload/vba-batch`

3. **禁止绕过检查**:
   - 不能修改 `ALLOWED_UPLOAD_METHODS`
   - 不能删除拦截代码
   - 必须经过VBA客户端

---

## 📞 技术支持

如遇到问题：

1. **VBA客户端问题** → 检查Excel宏设置
2. **JSON格式错误** → 参考上方标准格式
3. **API上传失败** → 查看audit日志
4. **特殊情况** → 联系管理员手动OCR

---

## 📝 更新日志

| 日期 | 版本 | 变更 |
|------|------|------|
| 2025-01-17 | v1.0 | 初始版本，强制VBA_ONLY模式 |

---

**本规范为INFINITE GZ系统强制执行，不可绕过。**
