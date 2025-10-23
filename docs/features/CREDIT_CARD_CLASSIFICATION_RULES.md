# 信用卡交易分类规则文档

## 📊 分类架构总览

信用卡交易采用**两级分类系统**：
1. **主分类** (transaction_type): `payment` vs `purchase`
2. **子分类** (transaction_subtype): 根据交易性质的详细分类

---

## 🔍 主分类规则

### 1️⃣ Payment (付款/还款) - `transaction_type = 'payment'`

**识别方法**：
- ✅ 交易描述包含以下关键词之一：
  ```
  'payment', 'bayaran', 'pembayaran', 'paid', 'pay'
  'transfer', 'pemindahan', 'autopay', 'auto-pay'
  'online payment', 'atm payment', 'bank transfer'
  'cash deposit', 'cheque deposit', 'giro'
  'direct debit', 'auto debit', 'fpx', 'duitnow'
  ```
- ✅ 金额为负数 (amount < 0)
- ✅ PDF中标记有 `CR` 标识 (Alliance Bank格式)

**作用**：减少信用卡欠款

---

### 2️⃣ Purchase (消费) - `transaction_type = 'purchase'`

**识别方法**：
- ✅ 不符合 Payment 条件的所有交易
- ✅ 金额为正数 (amount > 0)
- ✅ PDF中无 `CR` 标识

**作用**：增加信用卡欠款

---

## 🎯 子分类规则 (transaction_subtype)

### **Payment 的子分类**

#### 1. Owner Credit (客户本人付款) - `owner_credit`

**识别方法**：
- ✅ 交易描述包含以下关键词：
  ```
  'owner', 'self', 'own account', 'my account'
  'principal', 'cardholder', 'pemegang kad'
  ```
- ✅ 或者不包含第三方标识：`'third party'`, `'3rd party'`, `'pihak ketiga'`

**示例**：
```
"PAYMENT - THANK YOU"
"ONLINE PAYMENT BY CARDHOLDER"
"AUTO DEBIT FROM MY ACCOUNT"
```

**特征**：
- `payment_user = 'Owner'`
- 客户自己的还款

---

#### 2. 3rd Party Credit (第三方付款) - `3rd_party_credit`

**识别方法**：
- ✅ 交易描述包含：`'third party'`, `'3rd party'`, `'pihak ketiga'`
- ✅ 或能从描述中提取付款人姓名

**姓名提取规则**：
```
FROM <PAYER_NAME>
BY <PAYER_NAME>
PEMBAYARAN OLEH <PAYER_NAME>
```

**示例**：
```
"PAYMENT FROM JOHN DOE"
"PAYMENT BY COMPANY ABC"
"3RD PARTY PAYMENT"
```

**特征**：
- `payment_user` = 提取的姓名或 `'3rd Party'`
- 他人代为还款

---

### **Purchase 的子分类**

#### 1. Supplier Debit (供应商消费) - `supplier_debit` ⭐

**7个特定供应商**（需收取1%手续费）：
```
1. 7SL (7SL SDN BHD)
2. Dinas (DINAS餐厅)
3. Raub Syc Hainan (Raub餐厅)
4. Ai Smart Tech (AI Smart Tech)
5. Huawei (华为)
6. Pasar Raya (超市)
7. Puchong Herbs (草药店)
```

**识别方法**：
- ✅ 交易描述包含上述供应商名称（不区分大小写）

**示例**：
```
"PAYMENT TO 7SL SDN BHD"
"AI SMART TECH SHAH ALAM MYS" → RM 4,299.00
"HUAWEI TECHNOLOGIES"
"DINAS RESTAURANT"
```

**特征**：
- `supplier_fee = amount × 1%`
- 需要向供应商开具发票
- **这是INFINITE公司的业务合作伙伴**

---

#### 2. Shop Debit (商店/公用事业) - `shop_debit`

**3个商家类型**：
```
1. Shopee (网购平台)
2. Lazada (网购平台)
3. TNB (国家能源公司 - 水电费)
```

**识别方法**：
- ✅ 交易描述包含上述商家名称（不区分大小写）

**示例**：
```
"SHOPEE MALAYSIA"
"LAZADA ONLINE SHOPPING"
"TNB UTILITY BILL PAYMENT"
```

**特征**：
- `supplier_fee = 0`
- 普通商店消费

---

#### 3. Others Debit (其他消费) - `others_debit`

**识别方法**：
- ✅ 所有不属于上述两类的消费

**示例**：
```
"STARBUCKS COFFEE"
"PETRONAS PETROL STATION"
"AEON MALL"
"INSTL OLYLIFE INTERNATIONAL 21 OF 24" (分期付款)
"INTEREST FOR INSTALMENT" (分期利息)
"CC SERVICE TAX(SST ID:W10-1808-32000842)" (服务税)
```

**特征**：
- `supplier_fee = 0`
- 一般消费

---

## 💰 手续费计算规则

### Supplier Fee (供应商手续费)

**适用对象**：仅限7个特定供应商的 `supplier_debit` 交易

**计算公式**：
```
supplier_fee = transaction_amount × 1%
```

**示例**：
```
AI SMART TECH - RM 4,299.00
→ supplier_fee = RM 42.99

7SL SDN BHD - RM 10,000.00
→ supplier_fee = RM 100.00
```

**特殊情况**：
- 可以在数据库中为特定供应商设置不同的费率
- 默认费率：1%

---

## 🏢 INFINITE业务逻辑 (高级分类)

### LedgerClassifier 系统

这是一个更高级的分类系统，用于识别与INFINITE公司相关的交易。

#### 1. INFINITE供应商识别

**方法**：通过数据库中的 `supplier_aliases` 表动态识别

**供应商别名示例**：
```
7sl → 7SL SDN BHD
dinas → DINAS餐厅
raub → Raub Syc Hainan
ai smart → AI Smart Tech
huawei → 华为
pasar raya → Pasar Raya
puchong herbs → Puchong Herbs
```

**返回值**：
- `(True, "7SL SDN BHD")` - 如果是INFINITE供应商
- `(False, None)` - 如果不是

---

#### 2. 付款人分类

**三种付款类型**：

##### A. Customer (客户本名付款)
- 客户使用自己的名字付款
- 检查 `payer_aliases` 表中的客户别名

##### B. Company (公司KENG CHOW付款)
- 通过公司账户付款
- 检查公司名称别名：`KENG CHOW SDN BHD`

##### C. INFINITE (INFINITE公司付款)
- 默认类型
- 所有不匹配上述两种的付款

**示例**：
```
"PAYMENT BY CHANG CHOON CHOW" → customer (客户本名)
"PAYMENT BY KENG CHOW SDN BHD" → company (公司)
"PAYMENT FROM ACCOUNT 1234" → infinite (INFINITE)
```

---

#### 3. 转账收款人识别

**用途**：识别储蓄账户转账给特定客户的交易

**方法**：通过 `transfer_recipient_aliases` 表识别

**示例**：
```
"TRANSFER TO CHANG CHOON CHOW" → ✅ Customer transfer
"TRANSFER TO KENG CHOW" → ✅ Customer transfer
"TRANSFER TO OTHER PERSON" → ❌ Not customer transfer
```

---

## 📊 实际案例分析

### Chang Choon Chow - Alliance Bank (12个月，83笔交易)

#### 交易分布：
```
Purchase (消费): 83笔 → RM 95,433.01
  ├─ Supplier Debit: 待统计
  ├─ Shop Debit: 待统计
  └─ Others Debit: 待统计

Payment (还款): 0笔 → RM 0.00
```

#### 实际交易示例及分类：

| 日期 | 描述 | 金额 | 主分类 | 子分类 | 手续费 |
|------|------|------|--------|--------|--------|
| 2025-07-30 | AI SMART TECH SHAH ALAM MYS | RM 4,299.00 | purchase | **supplier_debit** | **RM 42.99** |
| 2025-07-13 | INSTL FC - 36MTHS @ 3.99% P.A. 12 OF 36 | RM 638.63 | purchase | others_debit | RM 0.00 |
| 2025-07-13 | INTEREST FOR INSTALMENT | RM 107.84 | purchase | others_debit | RM 0.00 |
| 2025-08-12 | INSTL OLYLIFE INTERNATIONAL 21 OF 24 | RM 183.33 | purchase | others_debit | RM 0.00 |
| 2025-08-09 | CC SERVICE TAX(SST ID:W10-1808-32000842) | RM 25.00 | purchase | others_debit | RM 0.00 |
| 2025-08-01 | PAYMENT - THANK YOU | RM 746.47 | **payment** | **owner_credit** | RM 0.00 |

---

## 🔄 分类流程图

```
交易
  │
  ├─ 包含 payment 关键词？或 amount < 0？或 有CR标记？
  │   │
  │   ├─ YES → Payment (还款)
  │   │        │
  │   │        ├─ 包含 owner 关键词？或 无3rd party标记？
  │   │        │   │
  │   │        │   ├─ YES → owner_credit (客户本人付款)
  │   │        │   └─ NO → 3rd_party_credit (第三方付款)
  │   │
  │   └─ NO → Purchase (消费)
  │            │
  │            ├─ 包含7个供应商名称之一？
  │            │   │
  │            │   ├─ YES → supplier_debit (供应商消费)
  │            │   │         [计算1%手续费]
  │            │   │
  │            │   └─ NO → 包含 Shopee/Lazada/TNB？
  │            │           │
  │            │           ├─ YES → shop_debit (商店消费)
  │            │           └─ NO → others_debit (其他消费)
```

---

## 💡 关键要点总结

### 1. **两级分类系统**
- **主分类**：payment vs purchase（影响欠款计算）
- **子分类**：5种详细类型（影响手续费和报表）

### 2. **7个特定供应商最重要**
- 这些是INFINITE的业务合作伙伴
- **必须**计算1%手续费
- 需要生成发票

### 3. **自动识别规则**
- 基于关键词匹配
- 可通过数据库动态添加新别名
- 支持中英文关键词

### 4. **金额符号**
- 负数 = payment (减少欠款)
- 正数 = purchase (增加欠款)

### 5. **Alliance Bank特殊标记**
- `CR` = Credit = Payment (还款)
- 无 `CR` = Debit = Purchase (消费)

---

## 🗄️ 数据库表结构

### 相关配置表：

1. **supplier_aliases** - 供应商别名
   ```sql
   CREATE TABLE supplier_aliases (
       id INTEGER PRIMARY KEY,
       supplier_name TEXT,
       alias TEXT,
       is_active INTEGER DEFAULT 1
   )
   ```

2. **payer_aliases** - 付款人别名
   ```sql
   CREATE TABLE payer_aliases (
       id INTEGER PRIMARY KEY,
       customer_id INTEGER,
       payer_type TEXT,  -- 'customer' or 'company'
       alias TEXT,
       is_active INTEGER DEFAULT 1
   )
   ```

3. **supplier_fee_config** - 供应商费率配置
   ```sql
   CREATE TABLE supplier_fee_config (
       id INTEGER PRIMARY KEY,
       supplier_name TEXT,
       fee_percentage REAL DEFAULT 1.0,
       is_active INTEGER DEFAULT 1
   )
   ```

4. **transfer_recipient_aliases** - 转账收款人别名
   ```sql
   CREATE TABLE transfer_recipient_aliases (
       id INTEGER PRIMARY KEY,
       customer_id INTEGER,
       recipient_name TEXT,
       alias TEXT,
       is_active INTEGER DEFAULT 1
   )
   ```

---

*最后更新: 2025-10-22*
*版本: v1.0 - 信用卡分类规则*
