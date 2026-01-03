# Credit Card Statement Post-processing Pipeline

Google Document AI 后处理系统 - 将 Document AI 的 JSON 输出转换为统一的大表格结构

## 📋 系统功能

### 核心功能
1. ✅ **字段提取** - 从 Document AI JSON 中提取 16 个标准字段
2. ✅ **格式标准化** - 日期统一为 YYYY-MM-DD，金额转 float
3. ✅ **CR/DR 自动修正** - 智能识别并修正 Credit/Debit 分类错误
4. ✅ **余额验证** - 数学校验：`previous_balance + sum(DR) - sum(CR) = current_balance`
5. ✅ **交易扁平化** - 将嵌套的交易表格转换为行记录
6. ✅ **CSV/JSON 输出** - 支持多种输出格式
7. ✅ **API Endpoint** - 提供 RESTful API 供前端调用

### 支持的16个字段
```
1.  bank_name
2.  customer_name
3.  ic_no
4.  card_type
5.  card_no
6.  credit_limit
7.  statement_date
8.  payment_due_date
9.  previous_balance
10. current_balance
11. minimum_payment
12. transaction_date
13. transaction_description
14. amount_CR
15. amount_DR
16. earned_point
```

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install fastapi uvicorn pydantic python-multipart
```

### 2. 运行示例（本地测试）
```bash
python main.py
```

### 3. 启动 API 服务器
```bash
python api/server.py
```
或
```bash
uvicorn api.server:app --reload --port 8001
```

服务器启动后访问：
- API 文档：http://localhost:8001/docs
- 健康检查：http://localhost:8001/health

## 📖 使用示例

### 示例1：Python 脚本调用
```python
from main import StatementProcessor

# 初始化处理器
processor = StatementProcessor()

# Document AI JSON 输入
doc_ai_json = {
    "entities": [
        {"type": "bank_name", "mentionText": "AMBANK"},
        {"type": "customer_name", "mentionText": "CHEOK JUN YOON"},
        {"type": "card_no", "mentionText": "4031 4899 9530 6354"},
        {"type": "statement_date", "mentionText": "28 OCT 25"},
        {"type": "current_balance", "mentionText": "RM15,062.57"},
        {
            "type": "line_item",
            "properties": [
                {"type": "date", "mentionText": "27 SEP 25"},
                {"type": "description", "mentionText": "Shopee Malaysia"},
                {"type": "amount", "mentionText": "16.39 CR"}
            ]
        }
    ]
}

# 处理
result = processor.process(doc_ai_json)

# 保存输出
processor.save_to_json(result, 'output/statement.json')
processor.save_to_csv(result, 'output/statement.csv')
```

### 示例2：API 调用（curl）
```bash
curl -X POST "http://localhost:8001/parse" \
  -H "Content-Type: application/json" \
  -d '{
    "document_ai_json": {
      "entities": [
        {"type": "bank_name", "mentionText": "AMBANK"}
      ]
    },
    "output_format": "json"
  }'
```

### 示例3：批量处理
```python
from main import StatementProcessor

processor = StatementProcessor()

# 批量处理41个账单
statements = [...]  # 41 个 Document AI JSON

results = []
for doc_ai_json in statements:
    result = processor.process(doc_ai_json)
    results.append(result)

# 合并所有账单到一个大 CSV
all_rows = []
for result in results:
    rows = processor.flatten_to_rows(result)
    all_rows.extend(rows)

# 保存
import csv
with open('all_statements.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(all_rows)
```

## 🔧 系统架构

```
├── main.py                    # 主处理器
├── utils/
│   ├── extract.py            # Document AI JSON 提取
│   ├── normalize.py          # 字段标准化（日期、金额、卡号）
│   └── crdr_fix.py           # CR/DR 自动修正 + 余额验证
├── api/
│   └── server.py             # FastAPI 服务器
└── output/                   # 输出目录（自动创建）
```

## 📊 输出格式

### JSON 输出格式
```json
{
  "bank_name": "AMBANK",
  "customer_name": "CHEOK JUN YOON",
  "card_no": "4031 4899 9530 6354",
  "statement_date": "2025-10-28",
  "payment_due_date": "2025-11-17",
  "current_balance": 15062.57,
  "minimum_payment": 1501.88,
  "transactions": [
    {
      "transaction_date": "2025-09-27",
      "transaction_description": "Shopee Malaysia",
      "amount_CR": 16.39,
      "amount_DR": 0.0
    }
  ],
  "validation": {
    "is_valid": true,
    "calculated_balance": 15062.57,
    "difference": 0.0
  },
  "metadata": {
    "total_transactions": 12,
    "auto_corrected_count": 2
  }
}
```

### CSV 输出格式
每条交易一行，包含所有16个字段：

| bank_name | customer_name | card_no | statement_date | transaction_date | transaction_description | amount_CR | amount_DR |
|-----------|---------------|---------|----------------|------------------|-------------------------|-----------|-----------|
| AMBANK    | CHEOK JUN YOON| 4031... | 2025-10-28     | 2025-09-27       | Shopee Malaysia         | 16.39     | 0.00      |

## 🧪 CR/DR 自动修正逻辑

系统会自动识别并修正错误的 Credit/Debit 分类：

### 规则1：Payment/Refund → CR
如果描述包含：`payment`, `refund`, `rebate`, `returned`  
→ 应该归类为 **CR (Credit)**

### 规则2：Purchase/Fee → DR
如果描述包含：`purchase`, `interest`, `charge`, `fee`, `lazada`, `shopee`  
→ 应该归类为 **DR (Debit)**

### 规则3：自动修正
如果检测到逻辑矛盾（例如：描述是"Payment Received"但被标记为DR），系统会：
- 自动交换 CR 和 DR 的值
- 添加标记：`_auto_corrected: true`
- 记录原因：`_correction_reason: "Payment/Refund should be CR"`

## 🔍 余额验证

系统会自动验证账单余额的一致性：

**公式**：
```
previous_balance + sum(amount_DR) - sum(amount_CR) = current_balance
```

**验证结果**：
```json
{
  "is_valid": true,
  "calculated_balance": 15062.57,
  "actual_balance": 15062.57,
  "difference": 0.0,
  "total_dr": 547.08,
  "total_cr": 0.0,
  "message": "Balance verified"
}
```

## 🌐 API Endpoints

### 1. 解析单个账单
```
POST /parse
```

### 2. 批量解析
```
POST /parse/batch
```

### 3. 下载 CSV
```
POST /parse/csv
```

### 4. 余额验证
```
POST /validate
```

### 5. 健康检查
```
GET /health
```

完整 API 文档：启动服务器后访问 http://localhost:8001/docs

## 🛠️ 技术栈

- **Python 3.9+**
- **FastAPI** - API 框架
- **Pydantic** - 数据验证
- **Uvicorn** - ASGI 服务器

## 📝 注意事项

1. **Document AI JSON 格式要求**：
   - 必须包含 `entities` 数组
   - 每个 entity 需要有 `type` 和 `mentionText` 字段
   
2. **日期格式支持**：
   - DD MMM YY (例: 28 OCT 25)
   - DD MMM YYYY (例: 16 SEP 2025)
   - DD/MM/YYYY
   - YYYY-MM-DD

3. **金额格式处理**：
   - 自动去除 RM 标记
   - 自动去除逗号
   - 支持 CR/DR 标记

4. **性能**：
   - 单个账单处理时间：< 100ms
   - 41个账单批量处理：< 5s

## 🔐 安全建议

- 生产环境部署时，限制 CORS 域名
- 使用 HTTPS
- 添加 API 密钥验证
- 遮罩敏感信息（卡号、IC号）

## 📞 支持

如有问题，请检查：
1. Document AI JSON 格式是否正确
2. API 服务器是否正常运行（访问 /health）
3. 查看日志输出

---

**CreditPilot System v1.0**  
*Built for Malaysian Credit Card Statement Processing*
