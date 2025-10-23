# 信用卡优化推荐系统 - 设计文档

## 系统目标

基于客户的实际消费习惯，从马来西亚所有银行的信用卡产品库中，推荐**利益最大化**的信用卡组合，并计算**年度节省金额**。

---

## 数据需求

### 信用卡产品数据库字段（从Excel/CSV提取）

**必须字段：**
1. **bank_name** - 银行名称（如：Maybank, CIMB, Public Bank）
2. **card_name** - 信用卡名称（如：Maybank 2 Cards, CIMB Visa Signature）
3. **annual_fee** - 年费（RM）
4. **cashback_rate** - 现金返还率（%）或固定金额
5. **category_bonuses** - 分类奖励（如：Dining 5%, Groceries 3%）
6. **min_income** - 最低收入要求（RM）
7. **rewards_type** - 奖励类型（Cashback/Points/Miles）
8. **welcome_bonus** - 迎新奖励（RM）

**可选字段：**
9. **max_cashback_monthly** - 每月最高返现上限（RM）
10. **cashback_cap_annual** - 年度返现上限（RM）
11. **fuel_discount** - 油费折扣（%）
12. **insurance_coverage** - 保险覆盖
13. **airport_lounge** - 机场贵宾室次数
14. **free_supplementary_cards** - 免费附属卡数量
15. **interest_free_period** - 免息期（天）

---

## 数据库表结构

### 1. credit_card_products（信用卡产品库）

```sql
CREATE TABLE IF NOT EXISTS credit_card_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bank_name TEXT NOT NULL,
    card_name TEXT NOT NULL,
    card_type TEXT,  -- Visa/Mastercard/Amex
    
    -- 费用
    annual_fee REAL DEFAULT 0,
    supplementary_card_fee REAL DEFAULT 0,
    
    -- 返现/奖励
    rewards_type TEXT,  -- cashback/points/miles
    cashback_rate REAL DEFAULT 0,  -- 基础返现率%
    max_cashback_monthly REAL,  -- 月返现上限
    max_cashback_annual REAL,   -- 年返现上限
    welcome_bonus REAL DEFAULT 0,
    
    -- 分类奖励（JSON格式）
    category_bonuses TEXT,  -- {"dining": 5, "groceries": 3, "petrol": 8}
    
    -- 申请要求
    min_income REAL,
    citizenship_requirement TEXT,  -- MY/Foreigner/Both
    age_min INTEGER DEFAULT 21,
    age_max INTEGER DEFAULT 65,
    
    -- 其他福利
    fuel_discount REAL DEFAULT 0,
    airport_lounge_visits INTEGER DEFAULT 0,
    insurance_coverage TEXT,
    interest_free_days INTEGER DEFAULT 20,
    
    -- 特色功能
    features TEXT,  -- JSON: ["contactless", "virtual_card", "installment_plan"]
    promotions TEXT,  -- 当前促销活动
    
    -- 数据管理
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(bank_name, card_name)
)
```

### 2. customer_card_recommendations（客户推荐记录）

```sql
CREATE TABLE IF NOT EXISTS customer_card_recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    card_product_id INTEGER NOT NULL,
    
    -- 推荐理由
    recommendation_score REAL,  -- 0-100分
    match_reason TEXT,
    
    -- 收益计算
    estimated_annual_cashback REAL,  -- 预计年返现
    estimated_annual_savings REAL,   -- 年度节省（vs现有卡）
    current_card_annual_cost REAL,   -- 现有卡年成本
    recommended_card_annual_benefit REAL,  -- 推荐卡年收益
    
    -- 基于客户数据
    based_on_spending_pattern TEXT,  -- JSON: {"dining": 2000, "groceries": 1500}
    
    -- 状态
    status TEXT DEFAULT 'pending',  -- pending/accepted/rejected/implemented
    recommended_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    implemented_at TIMESTAMP,
    
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (card_product_id) REFERENCES credit_card_products(id)
)
```

---

## 推荐算法

### Step 1: 客户消费分析

**从交易数据提取：**
```python
customer_spending_pattern = {
    "Food & Dining": 2500,      # RM/月
    "Groceries": 1200,
    "Transport": 800,
    "Shopping": 1500,
    "Bills & Utilities": 600,
    "Entertainment": 400,
    "Travel": 1000,
    "Others": 500
}

total_monthly_spending = 8500  # RM
```

### Step 2: 卡片匹配与评分

**评分维度（100分制）：**

1. **返现/奖励匹配度（40分）**
   - 主要消费类别的返现率
   - 月度上限是否足够
   - 年度上限检查

2. **费用成本（20分）**
   - 年费成本
   - 附属卡费用
   - 净收益 = 返现 - 年费

3. **福利价值（20分）**
   - 机场贵宾室
   - 保险覆盖
   - 免息期
   - 油费折扣

4. **申请可行性（20分）**
   - 收入符合度
   - 年龄符合
   - 公民身份

**评分公式：**
```python
score = (
    cashback_match_score * 0.4 +
    cost_efficiency_score * 0.2 +
    benefits_value_score * 0.2 +
    eligibility_score * 0.2
) * 100
```

### Step 3: 收益计算

**示例：**
```python
# 客户现有卡
current_card = {
    "name": "Maybank Visa Classic",
    "annual_fee": 150,
    "cashback_rate": 0.2,  # 0.2%
    "monthly_spending": 8500
}

annual_cashback_current = 8500 * 12 * 0.002 = RM 204
annual_cost_current = 150
net_benefit_current = 204 - 150 = RM 54

# 推荐卡
recommended_card = {
    "name": "CIMB Visa Signature",
    "annual_fee": 288,
    "cashback_rates": {
        "dining": 0.10,  # 10%
        "groceries": 0.05,  # 5%
        "others": 0.005  # 0.5%
    }
}

annual_cashback_recommended = (
    2500 * 12 * 0.10 +  # Dining: RM 3,000
    1200 * 12 * 0.05 +  # Groceries: RM 720
    4800 * 12 * 0.005   # Others: RM 288
) = RM 4,008

annual_cost_recommended = 288
net_benefit_recommended = 4008 - 288 = RM 3,720

# 年度节省
annual_savings = 3720 - 54 = RM 3,666  ✅
```

---

## 推荐引擎模块

### 文件结构

```
advisory/
├── card_recommendation_engine.py    # 核心推荐引擎
├── card_product_loader.py           # Excel/CSV导入
├── spending_analyzer.py             # 消费模式分析
└── benefit_calculator.py            # 收益计算器
```

### API端点

```python
# 1. 导入信用卡产品数据
POST /admin/import-credit-cards
- Upload Excel/CSV
- Parse and validate
- Insert into credit_card_products

# 2. 为客户推荐信用卡
GET /api/customer/<id>/card-recommendations
- Analyze spending pattern
- Match best cards
- Calculate savings
- Return top 5 recommendations

# 3. 对比现有卡 vs 推荐卡
GET /api/customer/<id>/card-comparison
- Current card benefits
- Recommended card benefits
- Side-by-side comparison
- Annual savings

# 4. 接受推荐
POST /api/customer/<id>/accept-recommendation/<rec_id>
- Update status to 'accepted'
- Generate application guide
- Track implementation
```

---

## 集成到月度对比报告

### 报告新增章节：

**第4页：信用卡优化建议**

```
┌─────────────────────────────────────────────────┐
│  💳 信用卡优化分析                               │
├─────────────────────────────────────────────────┤
│                                                 │
│  您当前使用：                                    │
│  • Maybank Visa Classic                        │
│  • 年费：RM 150                                │
│  • 基础返现：0.2%                              │
│  • 年度返现：RM 204                            │
│  • 净收益：RM 54                               │
│                                                 │
├─────────────────────────────────────────────────┤
│  我们为您推荐：                                  │
│                                                 │
│  🏆 第1名：CIMB Visa Signature                 │
│  ✅ 匹配度：95分                                │
│  💰 年度返现：RM 4,008                          │
│  📊 净收益：RM 3,720                            │
│  💵 年度节省：RM 3,666 ⬆️                       │
│                                                 │
│  推荐理由：                                      │
│  • 餐饮10%返现（您月均消费RM 2,500）           │
│  • 杂货5%返现（您月均消费RM 1,200）            │
│  • 无返现上限                                   │
│  • 免费6次机场贵宾室                            │
│                                                 │
├─────────────────────────────────────────────────┤
│  🥈 第2名：Public Bank Visa Infinite           │
│  💵 年度节省：RM 3,200                          │
│                                                 │
│  🥉 第3名：Hong Leong Wise Platinum            │
│  💵 年度节省：RM 2,800                          │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## 实施步骤

### Phase 1: 数据导入（立即执行）

1. ✅ **接收Excel/CSV文件**
2. ✅ **创建数据库表** `credit_card_products`
3. ✅ **解析并导入数据**
4. ✅ **数据验证**（必填字段检查）

### Phase 2: 推荐引擎开发（1-2天）

5. ✅ **消费模式分析器** `spending_analyzer.py`
6. ✅ **卡片匹配算法** `card_recommendation_engine.py`
7. ✅ **收益计算器** `benefit_calculator.py`

### Phase 3: UI集成（1天）

8. ✅ **客户Dashboard显示推荐**
9. ✅ **对比页面** Current vs Recommended
10. ✅ **月度报告集成**

### Phase 4: 测试与优化（1天）

11. ✅ **算法测试**（真实客户数据）
12. ✅ **收益计算验证**
13. ✅ **UI/UX优化**

---

## 成功指标

1. **推荐准确度**：>90%客户认为推荐合理
2. **节省金额**：平均年度节省 >RM 2,000/客户
3. **转化率**：>30%客户接受推荐并换卡
4. **系统响应**：推荐生成 <2秒

---

## 竞争优势

**vs 传统银行顾问：**
- ✅ 数据驱动（基于实际消费）
- ✅ 全市场对比（不限单一银行）
- ✅ 自动化分析（无人工偏见）
- ✅ 持续优化（每月更新）

**vs 信用卡比较网站：**
- ✅ 个性化推荐（非通用排行榜）
- ✅ 精准收益计算（基于客户数据）
- ✅ 一站式服务（分析+推荐+实施）

---

## 收费模式（建议）

**利润分享模式：**
- 免费分析和推荐
- 客户成功换卡后，收取**年度节省金额的10%**作为服务费
- 例如：节省RM 3,666，收费RM 366.60

**或固定服务费：**
- 推荐报告：RM 50/次
- 申请协助：RM 200/卡
- 包年服务：RM 500（无限推荐+优先申请）

---

## 下一步

等待您上传Excel/CSV文件后，我们将立即开始：
1. 数据导入到数据库
2. 开发推荐引擎
3. 集成到现有系统
4. 测试并上线

**预计完成时间：2-3天**
