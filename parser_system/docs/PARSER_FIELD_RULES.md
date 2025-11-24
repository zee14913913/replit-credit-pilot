# DocParser 7家银行解析规则
## 为 Cheok Jun Yoon 客户创建的信用卡账单解析模版

---

## 📋 需要创建的7个Parser

| # | 银行名称 | Parser名称 | 示例PDF文件 |
|---|---------|-----------|------------|
| 1 | AmBank | `AMBANK` | 1_AMBANK.pdf |
| 2 | AmBank Islamic | `AMBANK_ISLAMIC` | 2_AMBANK_ISLAMIC.pdf |
| 3 | Standard Chartered | `STANDARD_CHARTERED` | 3_STANDARD_CHARTERED.pdf |
| 4 | UOB | `UOB` | 4_UOB.pdf |
| 5 | Hong Leong Bank | `HONG_LEONG` | 5_HONG_LEONG.pdf |
| 6 | OCBC | `OCBC` | 6_OCBC.pdf |
| 7 | HSBC | `HSBC` | 7_HSBC.pdf |

---

## 🎯 每个Parser必须提取的字段（标准化）

### 基本信息字段
```
1. bank_name          - 银行名称（固定值）
2. card_number        - 卡号后4位
3. statement_date     - 账单日期（YYYY-MM-DD）
4. statement_period   - 账单周期（YYYY-MM）
5. cardholder_name    - 持卡人姓名
```

### 账户余额字段
```
6. previous_balance   - 上期结余（Previous Balance）
7. total_credit       - 总贷项（Credits / Payments）
8. total_debit        - 总借项（Purchases / Debits）
9. current_balance    - 本期结余（Current Balance）
10. minimum_payment   - 最低还款额
11. payment_due_date  - 缴款截止日期
```

### 交易明细字段（Table格式）
```
12. transactions      - 交易列表（Table）
    - date           - 交易日期
    - description    - 交易描述
    - amount         - 金额
    - type           - 类型（DR/CR）
```

---

## 🏦 每家银行的特殊规则

### 1. AmBank (6354)
- **卡号字段**: 卡号后4位显示为 "xxxx 6354"
- **日期格式**: DD/MM/YYYY
- **特殊字段**: 
  - `reward_points` - 奖励积分
  - `cashback_earned` - 现金回赠

### 2. AmBank Islamic (9902)
- **卡号字段**: 卡号后4位显示为 "xxxx 9902"
- **日期格式**: DD/MM/YYYY
- **特殊字段**:
  - `zakat_amount` - Zakat金额（如有）
  - `hibah_rate` - Hibah利率（如有）

### 3. Standard Chartered (1237)
- **卡号字段**: 卡号后4位显示为 "xxxx 1237"
- **日期格式**: DD MMM YYYY
- **特殊字段**:
  - `bonus_points` - 奖励积分
  - `annual_fee` - 年费（如有）

### 4. UOB (3530/8387)
- **卡号字段**: 可能是 3530 或 8387
- **日期格式**: DD/MM/YYYY
- **特殊字段**:
  - `uni_dollars` - UNI$ 积分
  - `interest_charged` - 利息收费

### 5. Hong Leong Bank (3964)
- **卡号字段**: 卡号后4位显示为 "xxxx 3964"
- **日期格式**: DD/MM/YYYY
- **特殊字段**:
  - `rewards_earned` - 累积奖赏
  - `late_payment_fee` - 滞纳金（如有）

### 6. OCBC (3506)
- **卡号字段**: 卡号后4位显示为 "xxxx 3506"
- **日期格式**: DD MMM YYYY
- **特殊字段**:
  - `ocbc_rewards` - OCBC奖励积分
  - `forex_charges` - 外汇手续费（如有）

### 7. HSBC (0034)
- **卡号字段**: 卡号后4位显示为 "xxxx 0034"
- **日期格式**: DD MMM YYYY
- **特殊字段**:
  - `rewards_points` - RewardCash积分
  - `service_fee` - 服务费（如有）

---

## 📊 交易分类规则（INFINITE GZ专用）

### Owner vs INFINITE 分类规则
解析后需要根据以下规则分类交易：

#### 自动分类为 INFINITE 的交易：
```
1. 描述包含以下关键词之一：
   - "on behalf"
   - "behalf of"
   - "for client"
   - "client request"
   - "payment for"
   - "on behalf of client"
   - "payment on behalf"

2. 描述包含7家INFINITE供应商之一：
   - 7SL
   - DINAS
   - RAUB SYC HAINAN
   - AI SMART TECH
   - HUAWEI
   - PASAR RAYA
   - PUCHONG HERBS
```

#### 自动分类为 Owner 的交易：
```
1. 描述包含客户/公司名称：
   - "CHEOK JUN YOON"
   - "INFINITE GZ"
   
2. 描述完全空白（Blank Description）

3. 不符合上述INFINITE规则的所有其他交易
```

#### 1%供应商费用规则：
```
- INFINITE供应商交易金额的1%计入Owner账户
- 同时记录在 miscellaneous_fee 字段
- 例如：INFINITE消费 RM 1000
  → Owner记录: +RM 10 (1%手续费)
  → miscellaneous_fee: RM 10
```

---

## 🔧 DocParser配置建议

### 1. 创建Parser时选择模版
- **推荐模版**: "Bank Statement" 或 "Blank Template"
- **文档类型**: PDF

### 2. Parsing Rules设置
- **使用Table Parser**: 提取交易明细
- **使用Text Anchor**: 定位固定字段（如卡号、余额）
- **使用Regex Pattern**: 提取日期和金额

### 3. 输出格式设置
- **Primary Format**: JSON
- **Date Format**: YYYY-MM-DD (统一格式)
- **Number Format**: Decimal (保留2位小数)

### 4. Webhook设置（可选）
```
Webhook URL: https://[your-repl-url]/api/docparser/webhook
Method: POST
Format: JSON
```

---

## ✅ 验证清单

创建每个Parser后，请验证：

- [ ] Parser名称正确
- [ ] 示例PDF上传成功
- [ ] 所有必需字段都能提取
- [ ] Table格式的交易明细正确
- [ ] 日期格式统一为 YYYY-MM-DD
- [ ] 金额格式正确（无货币符号）
- [ ] Parser ID已记录

---

## 📝 Parser ID记录表

创建完成后，请记录每个Parser的ID：

| 银行 | Parser名称 | Parser ID | 状态 |
|------|-----------|-----------|------|
| AmBank | AMBANK | `_____________` | ⬜ 待创建 |
| AmBank Islamic | AMBANK_ISLAMIC | `_____________` | ⬜ 待创建 |
| Standard Chartered | STANDARD_CHARTERED | `_____________` | ⬜ 待创建 |
| UOB | UOB | `_____________` | ⬜ 待创建 |
| Hong Leong | HONG_LEONG | `_____________` | ⬜ 待创建 |
| OCBC | OCBC | `_____________` | ⬜ 待创建 |
| HSBC | HSBC | `_____________` | ⬜ 待创建 |

---

## 🎯 下一步

1. ✅ 示例PDF已准备 → `./docparser_templates/sample_pdfs/`
2. ⬜ 在DocParser中创建7个Parser
3. ⬜ 配置字段提取规则
4. ⬜ 记录7个Parser ID
5. ⬜ 更新系统配置文件

完成后，系统将自动：
- 上传PDF → 调用对应银行的Parser → 自动解析 → 分类入库
