# 🧪 Card Optimizer API 测试指南

## 📋 测试文件说明

| 文件 | 用途 |
|------|------|
| `Card_Optimizer_API_Tests.postman_collection.json` | Postman 测试集合（8个完整测试用例） |
| `test_data_seed.json` | 测试数据种子文件（5个场景） |
| `README_API_TESTING.md` | 本文档 - 测试指南 |

---

## 🚀 快速开始（Replit环境）

### 1️⃣ 导入 Postman Collection

```bash
# 方式1：在 Postman 中导入
File → Import → 选择 Card_Optimizer_API_Tests.postman_collection.json

# 方式2：使用 curl 直接测试（无需 Postman）
# 见下方 cURL 示例
```

### 2️⃣ 配置环境变量

在 Postman 中设置以下变量（或直接修改 collection 中的变量）：

```json
{
  "base_url": "https://<your-replit-url>",
  "customer_id": "CJY001"
}
```

**获取你的 Replit URL：**
- 点击 Replit 右上角的 "Open in new tab" 
- 复制浏览器地址栏的 URL（例如：`https://abc123.replit.dev`）

### 3️⃣ 按顺序执行测试

建议按以下顺序执行测试：

```
1. Get Customer Cards (获取卡片数据)
   ↓
2. Generate Plan (生成优化方案) → 记下返回的 plan_id
   ↓
3. Confirm Plan (确认方案) → 使用上一步的 plan_id
   ↓
4. Import Supplier Transaction (测试手续费拆分)
   ↓
5. Monthly Summary (验证对账)
   ↓
6. Audit Logs (检查审计追踪)
```

---

## 🧪 测试场景详解

### ✅ 场景1：正常刷卡优化

**请求：**
```bash
POST /api/card-optimizer/generate-plan
{
  "customer_id": "CJY001",
  "expected_amount": 5000.00,
  "expected_date": "2025-12-01"
}
```

**验证点：**
- ✅ 返回 `plan_id`（格式：PLAN-YYYYMMDD-CUSTOMER-XXXXX）
- ✅ 每张卡有 `score`、`free_days`、`risk_level`
- ✅ `free_days ≥ 50` 的卡排名靠前
- ✅ 所有卡 `risk_level = LOW`

**预期响应：**
```json
{
  "status": "success",
  "plan_id": "PLAN-20251112-CJY001-12345",
  "recommended_cards": [
    {
      "card_id": 2,
      "bank_name": "CIMB",
      "score": 8.5,
      "free_days": 51,
      "risk_level": "LOW"
    }
  ]
}
```

---

### ⚠️ 场景2：高风险检测

**请求：**
```bash
POST /api/card-optimizer/generate-plan
{
  "customer_id": "CJY001",
  "expected_amount": 15000.00,  # 超大金额触发风险
  "expected_date": "2025-11-15"
}
```

**验证点：**
- ✅ 利用率 >90% 的卡标记为 `EXTREME`
- ✅ `high_risk_cards` 数组不为空
- ✅ 返回警告消息

**预期响应：**
```json
{
  "status": "warning",
  "message": "检测到高风险卡片",
  "high_risk_cards": [
    {
      "card_id": 1,
      "risk_level": "EXTREME",
      "utilization_rate": 0.95,
      "warning": "利用率过高，建议还款后再使用"
    }
  ]
}
```

---

### 💰 场景3：手续费拆分验证

**请求：**
```bash
POST /api/accounting/import-transaction
{
  "customer_id": "CJY001",
  "card_id": 1,
  "transaction_date": "2025-11-12",
  "description": "7SL TECH SDN BHD",
  "amount": 1000.00,
  "type": "DEBIT",
  "merchant_category": "supplier"
}
```

**数据库验证（需在 Replit Shell 中执行）：**
```bash
sqlite3 db/smart_loan_manager.db "SELECT id, description, amount, account_type, is_fee_split FROM transactions WHERE customer_code='CJY001' ORDER BY id DESC LIMIT 2;"
```

**预期结果：**
```
id | description        | amount | account_type      | is_fee_split
---+--------------------+--------+-------------------+-------------
2  | 7SL TECH - 手续费1% | 10.00  | owner_expense     | true
1  | 7SL TECH SDN BHD   | 990.00 | infinite_expense  | false
```

---

### 📊 场景4：月度对账验证

**请求：**
```bash
GET /api/accounting/monthly-summary?customer_id=CJY001&month=2025-11
```

**验证公式：**
```
closing_balance = opening_balance + total_credits - total_debits
diff = abs(closing_balance - statement_closing_balance)
PASS if diff ≤ 0.01
```

**预期响应：**
```json
{
  "customer_id": "CJY001",
  "month": "2025-11",
  "total_infinite_expenses": 5940.00,
  "total_owner_fees": 60.00,
  "total_owner_expenses": 50.00,
  "closing_balance": 6050.00,
  "diff": 0.00,
  "status": "balanced"
}
```

---

### 📝 场景5：审计日志验证

**请求：**
```bash
GET /api/audit/logs?module=card_optimizer&limit=10
```

**验证点：**
- ✅ `action_type` 包含 `generate_plan`、`confirm_plan`
- ✅ `entity_type = card_optimizer_plan`
- ✅ 包含 `user_id`、`timestamp`、`description`

---

## 🔧 cURL 测试示例（无需 Postman）

### 生成优化方案
```bash
curl -X POST http://localhost:5000/api/card-optimizer/generate-plan \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CJY001",
    "expected_amount": 5000.00,
    "expected_date": "2025-12-01"
  }'
```

### 确认方案（记得替换 plan_id）
```bash
curl -X POST http://localhost:5000/api/card-optimizer/confirm-plan \
  -H "Content-Type: application/json" \
  -d '{
    "plan_id": "PLAN-20251112-CJY001-12345",
    "selected_card_id": 2,
    "consent_confirmed": true
  }'
```

---

## 📈 测试通过标准

### ✅ 完整测试检查清单

- [ ] **API 可访问性**
  - [ ] 所有8个端点返回 200/400/404（非 500）
  - [ ] 错误响应包含清晰的错误消息

- [ ] **数据完整性**
  - [ ] Generate Plan 创建 `card_optimizer_plans` 记录
  - [ ] Confirm Plan 创建 `card_risk_consents` 记录
  - [ ] Import Transaction 创建手续费拆分交易（2条记录）

- [ ] **业务逻辑**
  - [ ] 免息期计算正确（≥50天优先）
  - [ ] 风险评估准确（利用率阈值 80%/90%）
  - [ ] 手续费拆分正确（1% merchant fee）

- [ ] **对账准确性**
  - [ ] 月度余额 diff ≤ 0.01
  - [ ] Owner + GZ 账目平衡

- [ ] **审计追踪**
  - [ ] 所有关键操作被记录到 audit_logs
  - [ ] 日志包含完整的上下文信息

---

## 🐛 常见问题排查

### 问题1：404 Not Found
```
解决方案：
1. 检查 Flask workflows 是否正常运行
2. 确认 API Blueprint 已注册（查看启动日志）
3. 验证 URL 路径是否正确
```

### 问题2：Customer not found
```
解决方案：
1. 先创建测试客户（使用前端或直接插入数据库）
2. 或修改 customer_id 为已存在的客户
```

### 问题3：手续费未拆分
```
解决方案：
1. 确认 merchant_category = "supplier"
2. 检查 owner_infinite_classifier.py 是否被调用
3. 查看 transactions 表的 is_fee_split 字段
```

---

## 📌 下一步

测试通过后，可以进行：

1. **前端开发** - 创建 Card Optimizer UI 界面
2. **集成到账本** - 在 Credit Cards 页面添加 Optimizer Tab
3. **报表增强** - 月度报表中显示 Owner/GZ 分账明细

---

## 🆘 需要帮助？

如遇到任何问题，请检查：
1. Replit Shell 日志（`refresh_all_logs`）
2. 数据库状态（SQLite Browser）
3. API 响应的详细错误消息

**测试愉快！** 🎉
