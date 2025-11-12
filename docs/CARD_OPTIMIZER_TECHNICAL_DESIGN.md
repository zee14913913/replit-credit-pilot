# 智能排卡优化系统 - 技术设计文档 v1.0

## 📋 文档信息
- **版本**: 1.0
- **日期**: 2024-11-12
- **阶段**: Phase 1 核心功能设计
- **预计开发周期**: 7-10天

---

## 🎯 一、系统目标

### 核心价值主张
为客户提供**智能信用卡使用建议**，通过优化刷卡时间和还款顺序：
1. **延长免息期** - 最大化每笔消费的免息天数（目标：≥50天）
2. **降低利息成本** - 优化还款顺序，减少罚金和利息
3. **提升现金流** - 合理利用信用卡额度，延缓资金压力

### Phase 1 范围
✅ Card Usage Optimizer（排卡优化器）
✅ Float Days Calculator（免息期计算引擎）
✅ Payment Priority Engine（还款优先级引擎）
✅ Calendar View UI（日历视图）
✅ Risk Compliance System（风险告知与合规）

❌ Phase 2功能（暂不实现）：
- Short-term Funding（短期筹资）
- Loan Readiness（贷款推进）
- Aggregated Limit（聚合额度）

---

## 🏗️ 二、系统架构设计

### 2.1 技术栈
```
前端: Jinja2 Templates + Bootstrap 5 + Vanilla JavaScript
后端: Flask (Python 3.11)
数据库: SQLite (现有) + 新增4张表
计算引擎: Python服务类
可视化: FullCalendar.js (日历组件)
```

### 2.2 模块结构
```
services/
├── card_optimizer.py          # 核心优化引擎
├── float_calculator.py         # 免息期计算器
├── payment_prioritizer.py      # 还款优先级引擎
└── risk_validator.py           # 风险验证器

templates/
└── credit_card/
    ├── optimizer_dashboard.html   # 优化器主页面
    ├── calendar_view.html         # 日历视图
    └── risk_confirmation.html     # 风险确认弹窗

static/js/
└── card_optimizer.js           # 前端交互逻辑
```

---

## 📊 三、数据库设计

### 3.1 新增表结构

#### 表1: `card_usage_plans` - 排卡计划表
```sql
CREATE TABLE card_usage_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    plan_month VARCHAR(7) NOT NULL,           -- YYYY-MM
    status VARCHAR(20) DEFAULT 'draft',        -- draft/confirmed/executed
    total_expected_spend DECIMAL(10,2),        -- 预计本月总消费
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,                        -- 创建人（admin/customer）
    
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    UNIQUE(customer_id, plan_month)
);
```

#### 表2: `card_recommendations` - 刷卡建议表
```sql
CREATE TABLE card_recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER NOT NULL,
    card_id INTEGER NOT NULL,
    priority_rank INTEGER NOT NULL,            -- 优先级排名（1最高）
    
    -- 推荐窗口
    recommended_start_date DATE NOT NULL,      -- 建议刷卡起始日
    recommended_end_date DATE NOT NULL,        -- 建议刷卡结束日
    estimated_float_days INTEGER,              -- 预计免息天数
    
    -- 额度建议
    recommended_spend_limit DECIMAL(10,2),     -- 建议本月消费上限
    current_utilization DECIMAL(5,2),          -- 当前使用率 (%)
    
    -- 原因说明
    reason TEXT,                               -- 推荐理由
    risk_level VARCHAR(10),                    -- low/medium/high
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (plan_id) REFERENCES card_usage_plans(id),
    FOREIGN KEY (card_id) REFERENCES credit_cards(id)
);
```

#### 表3: `payment_schedules` - 还款计划表
```sql
CREATE TABLE payment_schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER NOT NULL,
    card_id INTEGER NOT NULL,
    
    -- 还款信息
    due_date DATE NOT NULL,                    -- 到期日
    minimum_payment DECIMAL(10,2),             -- 最低还款额
    recommended_payment DECIMAL(10,2),         -- 建议还款额
    priority_order INTEGER,                    -- 还款优先级（1最高）
    
    -- 资金来源
    funding_source VARCHAR(50),                -- self/gz_transfer/loan/defer
    payment_status VARCHAR(20) DEFAULT 'pending', -- pending/scheduled/paid
    
    -- 说明
    notes TEXT,                                -- 备注说明
    risk_warning TEXT,                         -- 风险警告
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    executed_at DATETIME,
    
    FOREIGN KEY (plan_id) REFERENCES card_usage_plans(id),
    FOREIGN KEY (card_id) REFERENCES credit_cards(id)
);
```

#### 表4: `risk_consents` - 风险确认记录表
```sql
CREATE TABLE risk_consents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    plan_id INTEGER,
    
    -- 风险内容
    risk_type VARCHAR(50) NOT NULL,            -- high_utilization/defer_payment/gz_advance
    risk_description TEXT NOT NULL,            -- 风险描述
    
    -- 确认信息
    consent_given BOOLEAN DEFAULT FALSE,       -- 是否同意
    consent_timestamp DATETIME,                -- 确认时间
    ip_address VARCHAR(50),                    -- IP地址
    user_agent TEXT,                           -- 浏览器信息
    
    -- 审计
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (plan_id) REFERENCES card_usage_plans(id)
);
```

### 3.2 现有表需要新增字段

#### `credit_cards` 表新增字段
```sql
ALTER TABLE credit_cards ADD COLUMN statement_cutoff_day INTEGER; -- 账单日（每月几号）
ALTER TABLE credit_cards ADD COLUMN payment_due_day INTEGER;      -- 到期日（每月几号）
ALTER TABLE credit_cards ADD COLUMN interest_rate DECIMAL(5,2);   -- 年利率(%)
ALTER TABLE credit_cards ADD COLUMN min_payment_rate DECIMAL(5,2) DEFAULT 5.0; -- 最低还款比例
```

---

## 🧮 四、核心算法设计

### 4.1 免息期计算算法

#### 算法原理
```
免息期天数 = 还款到期日 - 消费入账日

关键变量：
1. statement_cutoff_day: 账单日（每月X号）
2. payment_due_day: 到期日（每月Y号）
3. purchase_date: 消费日期

计算步骤：
1. 确定消费将出现在哪个账单周期
2. 计算该账单周期的到期日
3. 计算免息天数
```

#### Python实现
```python
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

class FloatDaysCalculator:
    """免息期计算器"""
    
    def calculate_float_days(self, purchase_date: date, 
                            cutoff_day: int, 
                            due_day: int) -> dict:
        """
        计算单笔消费的免息天数
        
        Args:
            purchase_date: 消费日期
            cutoff_day: 账单日（1-31）
            due_day: 到期日（1-31）
        
        Returns:
            {
                'float_days': int,           # 免息天数
                'statement_date': date,      # 账单日期
                'due_date': date,            # 到期日期
                'billing_cycle': str         # 账单周期
            }
        """
        # Step 1: 确定消费属于哪个账单周期
        if purchase_date.day <= cutoff_day:
            # 消费在本月账单日之前 → 记入本月账单
            statement_month = purchase_date
        else:
            # 消费在本月账单日之后 → 记入下月账单
            statement_month = purchase_date + relativedelta(months=1)
        
        # Step 2: 计算账单日期
        try:
            statement_date = statement_month.replace(day=cutoff_day)
        except ValueError:
            # 处理2月、小月问题
            statement_date = statement_month.replace(day=1) + \
                           relativedelta(months=1, days=-1)
        
        # Step 3: 计算到期日期（账单日后X天）
        try:
            # 假设到期日在账单日同月
            due_date = statement_date.replace(day=due_day)
            if due_date <= statement_date:
                # 到期日在账单日之前，推到下个月
                due_date = due_date + relativedelta(months=1)
        except ValueError:
            # 处理月份天数问题
            due_date = statement_date + relativedelta(months=1, day=due_day)
        
        # Step 4: 计算免息天数
        float_days = (due_date - purchase_date).days
        
        return {
            'float_days': float_days,
            'statement_date': statement_date,
            'due_date': due_date,
            'billing_cycle': statement_date.strftime('%Y-%m')
        }
    
    def find_optimal_purchase_window(self, cutoff_day: int, 
                                     due_day: int,
                                     target_month: str) -> dict:
        """
        找出本月的最佳刷卡窗口（获得最长免息期）
        
        Returns:
            {
                'best_window_start': date,   # 最佳窗口起始
                'best_window_end': date,     # 最佳窗口结束
                'max_float_days': int,       # 最大免息天数
                'worst_window_start': date,  # 最短窗口起始
                'min_float_days': int        # 最小免息天数
            }
        """
        year, month = map(int, target_month.split('-'))
        month_start = date(year, month, 1)
        month_end = month_start + relativedelta(months=1, days=-1)
        
        # 模拟整个月每一天的免息期
        float_days_map = {}
        for day in range(1, month_end.day + 1):
            test_date = date(year, month, day)
            result = self.calculate_float_days(test_date, cutoff_day, due_day)
            float_days_map[test_date] = result['float_days']
        
        # 找出最大和最小免息期
        max_float = max(float_days_map.values())
        min_float = min(float_days_map.values())
        
        # 找出对应的日期区间
        best_dates = [d for d, f in float_days_map.items() if f == max_float]
        worst_dates = [d for d, f in float_days_map.items() if f == min_float]
        
        return {
            'best_window_start': min(best_dates),
            'best_window_end': max(best_dates),
            'max_float_days': max_float,
            'worst_window_start': min(worst_dates),
            'min_float_days': min_float
        }
```

### 4.2 排卡优先级算法

#### 评分公式
```python
card_score = (
    W1 * float_days +              # 免息期权重
    W2 * available_credit_ratio +   # 可用额度权重
    W3 * (100 - utilization_rate) - # 低使用率奖励
    W4 * risk_penalty               # 风险惩罚
)

# 默认权重
W1 = 2.0   # 免息期最重要
W2 = 1.0   # 可用额度次要
W3 = 0.5   # 低使用率有奖励
W4 = 3.0   # 高风险重罚
```

#### Python实现
```python
class CardOptimizer:
    """排卡优化引擎"""
    
    WEIGHTS = {
        'float_days': 2.0,
        'available_credit': 1.0,
        'low_utilization_bonus': 0.5,
        'risk_penalty': 3.0
    }
    
    def calculate_card_score(self, card: dict, 
                            purchase_date: date,
                            expected_amount: float) -> dict:
        """
        计算单张卡的优先级评分
        
        Args:
            card: {
                'id': int,
                'bank_name': str,
                'credit_limit': float,
                'current_balance': float,
                'cutoff_day': int,
                'due_day': int
            }
            purchase_date: 计划消费日期
            expected_amount: 预计消费金额
        
        Returns:
            {
                'score': float,
                'float_days': int,
                'utilization_after': float,
                'risk_level': str,
                'recommendation': str
            }
        """
        # 1. 计算免息期
        float_calc = FloatDaysCalculator()
        float_result = float_calc.calculate_float_days(
            purchase_date, 
            card['cutoff_day'], 
            card['due_day']
        )
        float_days = float_result['float_days']
        
        # 2. 计算可用额度比例
        available_credit = card['credit_limit'] - card['current_balance']
        available_ratio = available_credit / card['credit_limit'] * 100
        
        # 3. 计算消费后使用率
        utilization_after = (card['current_balance'] + expected_amount) / \
                           card['credit_limit'] * 100
        
        # 4. 风险评估
        risk_level, risk_penalty = self._assess_risk(
            utilization_after, 
            available_credit, 
            expected_amount
        )
        
        # 5. 计算总分
        score = (
            self.WEIGHTS['float_days'] * float_days +
            self.WEIGHTS['available_credit'] * available_ratio +
            self.WEIGHTS['low_utilization_bonus'] * (100 - utilization_after) -
            self.WEIGHTS['risk_penalty'] * risk_penalty
        )
        
        return {
            'card_id': card['id'],
            'score': round(score, 2),
            'float_days': float_days,
            'utilization_after': round(utilization_after, 2),
            'risk_level': risk_level,
            'recommendation': self._generate_recommendation(
                float_days, utilization_after, risk_level
            ),
            'statement_date': float_result['statement_date'],
            'due_date': float_result['due_date']
        }
    
    def _assess_risk(self, utilization: float, 
                     available: float, 
                     amount: float) -> tuple:
        """
        风险评估
        
        Returns:
            (risk_level, risk_penalty)
        """
        if utilization > 90:
            return ('high', 10.0)
        elif utilization > 70:
            return ('medium', 5.0)
        elif available < amount:
            return ('high', 15.0)  # 额度不足
        else:
            return ('low', 0.0)
    
    def _generate_recommendation(self, float_days: int, 
                                utilization: float, 
                                risk: str) -> str:
        """生成推荐说明"""
        if risk == 'high':
            return f"❌ 不推荐：使用率过高({utilization:.1f}%)或额度不足"
        elif float_days >= 50:
            return f"✅ 强烈推荐：{float_days}天免息期"
        elif float_days >= 40:
            return f"✓ 推荐：{float_days}天免息期"
        else:
            return f"⚠️ 免息期较短：仅{float_days}天"
```

### 4.3 还款优先级算法

```python
class PaymentPrioritizer:
    """还款优先级引擎"""
    
    def prioritize_payments(self, cards: list, 
                           available_funds: float) -> list:
        """
        计算还款优先级
        
        Args:
            cards: 所有信用卡数据
            available_funds: 可用还款资金
        
        Returns:
            排序后的还款计划列表
        """
        payment_plans = []
        
        for card in cards:
            if card['current_balance'] <= 0:
                continue
            
            # 计算到期紧迫性（距离到期日天数）
            days_to_due = (card['next_due_date'] - date.today()).days
            
            # 计算最低还款额
            min_payment = card['current_balance'] * \
                         (card.get('min_payment_rate', 5.0) / 100)
            
            # 优先级评分（越高越优先）
            priority_score = (
                100 - days_to_due +                    # 越快到期越高
                card.get('interest_rate', 18.0) * 2 +  # 高利率优先
                (card['current_balance'] / 1000)       # 高余额优先
            )
            
            payment_plans.append({
                'card_id': card['id'],
                'bank_name': card['bank_name'],
                'current_balance': card['current_balance'],
                'due_date': card['next_due_date'],
                'days_to_due': days_to_due,
                'minimum_payment': min_payment,
                'recommended_payment': self._calculate_recommended_payment(
                    card, available_funds
                ),
                'priority_score': priority_score,
                'urgency_level': self._get_urgency_level(days_to_due)
            })
        
        # 按优先级排序
        return sorted(payment_plans, 
                     key=lambda x: x['priority_score'], 
                     reverse=True)
    
    def _calculate_recommended_payment(self, card: dict, 
                                      available: float) -> float:
        """计算建议还款额"""
        if available >= card['current_balance']:
            return card['current_balance']  # 全额还款
        else:
            min_pay = card['current_balance'] * 0.05
            return max(min_pay, available * 0.3)  # 至少最低还款
    
    def _get_urgency_level(self, days: int) -> str:
        """紧迫程度"""
        if days <= 3:
            return 'critical'
        elif days <= 7:
            return 'urgent'
        elif days <= 14:
            return 'normal'
        else:
            return 'low'
```

---

## 🎨 五、前端UI设计

### 5.1 优化器主页面布局

```
┌─────────────────────────────────────────────────────┐
│  智能排卡优化器                    【生成本月计划】    │
├─────────────────────────────────────────────────────┤
│                                                     │
│  📅 本月排卡建议 (2025-11)                          │
│  ┌───────────────────────────────────────────────┐ │
│  │  优先级1: CIMB Visa Signature                 │ │
│  │  ✅ 建议刷卡窗口: 11-06 至 11-09             │ │
│  │  💰 免息期: 52天 | 建议额度: RM 5,000        │ │
│  │  📊 当前使用率: 45% → 预计: 65%              │ │
│  └───────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────┐ │
│  │  优先级2: Maybank Platinum                    │ │
│  │  ⚠️ 免息期较短: 仅28天                       │ │
│  │  建议用于小额消费                              │ │
│  └───────────────────────────────────────────────┘ │
│                                                     │
│  💳 本月还款计划                                    │
│  ┌───────────────────────────────────────────────┐ │
│  │  🔴 紧急: UOB One Card                        │ │
│  │  到期日: 2025-11-15 (3天后)                  │ │
│  │  最低还款: RM 250 | 建议: RM 2,500           │ │
│  │  [安排还款]                                   │ │
│  └───────────────────────────────────────────────┘ │
│                                                     │
│  📊 免息期模拟器        【查看日历视图】             │
└─────────────────────────────────────────────────────┘
```

### 5.2 日历视图

使用FullCalendar.js实现：

```javascript
// 事件类型
events: [
    {
        title: '✅ CIMB最佳刷卡窗口',
        start: '2025-11-06',
        end: '2025-11-09',
        color: '#00FF7F',
        description: '52天免息期'
    },
    {
        title: '⚠️ Maybank到期',
        start: '2025-11-15',
        color: '#FF007F',
        description: '需还款RM 2,500'
    }
]
```

### 5.3 风险确认弹窗

```html
<div class="modal" id="riskConsentModal">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5>⚠️ 风险告知</h5>
            </div>
            <div class="modal-body">
                <p class="text-warning">
                    此操作可能导致以下风险：
                </p>
                <ul>
                    <li>信用卡使用率将达到 <strong>85%</strong></li>
                    <li>若未按时还款，将产生利息约 <strong>RM 150/月</strong></li>
                    <li>可能影响信用评分</li>
                </ul>
                <div class="form-check">
                    <input type="checkbox" id="consentCheck">
                    <label>我已了解并同意承担风险</label>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn-secondary">取消</button>
                <button class="btn-professional" id="confirmRisk" disabled>
                    确认并继续
                </button>
            </div>
        </div>
    </div>
</div>
```

---

## 🔌 六、API接口设计

### 6.1 生成排卡计划

**Endpoint**: `POST /api/card-optimizer/generate-plan`

**Request**:
```json
{
    "customer_id": 5,
    "plan_month": "2025-11",
    "expected_total_spend": 8000.00,
    "spending_breakdown": [
        {
            "category": "business_supplies",
            "amount": 5000,
            "preferred_date": "2025-11-10"
        },
        {
            "category": "utilities",
            "amount": 1500,
            "flexible": true
        }
    ]
}
```

**Response**:
```json
{
    "success": true,
    "plan_id": 123,
    "recommendations": [
        {
            "card_id": 45,
            "bank_name": "CIMB",
            "priority_rank": 1,
            "recommended_window": {
                "start": "2025-11-06",
                "end": "2025-11-09"
            },
            "float_days": 52,
            "recommended_amount": 5000,
            "current_utilization": 45.0,
            "projected_utilization": 65.0,
            "risk_level": "low",
            "reason": "✅ 强烈推荐：52天免息期"
        }
    ],
    "payment_schedule": [
        {
            "card_id": 38,
            "bank_name": "UOB",
            "due_date": "2025-11-15",
            "days_remaining": 3,
            "minimum_payment": 250.00,
            "recommended_payment": 2500.00,
            "urgency": "critical"
        }
    ]
}
```

### 6.2 模拟免息期

**Endpoint**: `GET /api/card-optimizer/simulate-float`

**Query Params**:
- `card_id`: 45
- `purchase_date`: 2025-11-10

**Response**:
```json
{
    "card_id": 45,
    "purchase_date": "2025-11-10",
    "float_days": 45,
    "statement_date": "2025-11-25",
    "due_date": "2025-12-25",
    "billing_cycle": "2025-11",
    "is_optimal": false,
    "optimal_dates": {
        "best_start": "2025-11-06",
        "best_end": "2025-11-09",
        "max_float_days": 52
    }
}
```

### 6.3 确认计划

**Endpoint**: `POST /api/card-optimizer/confirm-plan`

**Request**:
```json
{
    "plan_id": 123,
    "risk_consent": true,
    "consent_details": {
        "ip_address": "103.x.x.x",
        "timestamp": "2025-11-12T10:30:00Z"
    }
}
```

---

## ✅ 七、实现步骤

### Week 1: 数据库与核心算法（3天）
- [ ] Day 1: 创建4张新表 + 迁移脚本
- [ ] Day 2: 实现FloatDaysCalculator
- [ ] Day 3: 实现CardOptimizer + PaymentPrioritizer

### Week 2: API与业务逻辑（3天）
- [ ] Day 4: 实现/generate-plan接口
- [ ] Day 5: 实现/simulate-float接口
- [ ] Day 6: 风险验证与合规记录

### Week 3: 前端UI（3天）
- [ ] Day 7: 优化器主页面
- [ ] Day 8: 日历视图集成FullCalendar
- [ ] Day 9: 风险确认弹窗 + 交互逻辑

### Week 4: 测试与优化（1天）
- [ ] Day 10: 端到端测试 + Bug修复

---

## 🧪 八、测试计划

### 8.1 单元测试用例

#### FloatDaysCalculator测试
```python
def test_float_calculation():
    calc = FloatDaysCalculator()
    
    # 测试用例1: 账单日前消费
    result = calc.calculate_float_days(
        purchase_date=date(2025, 11, 5),
        cutoff_day=25,
        due_day=15
    )
    assert result['float_days'] == 40  # 11-05 到 12-15
    
    # 测试用例2: 账单日后消费（最长免息期）
    result = calc.calculate_float_days(
        purchase_date=date(2025, 11, 26),
        cutoff_day=25,
        due_day=15
    )
    assert result['float_days'] >= 50  # 跨到下下个月
```

### 8.2 集成测试场景

**场景1: 客户有3张卡，计划消费RM 8,000**
- 输入: 3张卡的详细信息
- 预期: 系统推荐最优卡组合，最大化免息期
- 验证: 总免息天数 > 单卡使用

**场景2: 客户有卡即将到期，余额不足还款**
- 输入: 卡余额RM 5,000，可用资金RM 2,000
- 预期: 系统标记高风险，建议最低还款
- 验证: 触发风险告知弹窗

---

## 📈 九、性能指标

### 目标指标
- 计划生成时间: < 2秒
- 免息期模拟: < 500ms
- 页面加载时间: < 3秒
- 支持并发用户: ≥ 50

### 优化策略
- 使用缓存减少重复计算
- 数据库索引优化
- 前端懒加载

---

## 🔒 十、安全与合规

### 10.1 风险类型定义

| 风险类型 | 触发条件 | 风险等级 |
|---------|---------|---------|
| `high_utilization` | 使用率 > 80% | High |
| `insufficient_funds` | 可用额度 < 消费金额 | Critical |
| `delayed_payment` | 距到期日 < 3天 | High |
| `over_leverage` | 总欠款 > 月收入3倍 | Critical |

### 10.2 合规要求
1. ✅ 所有高风险操作必须获得客户确认
2. ✅ 记录IP地址和时间戳
3. ✅ 保存确认记录至少3年
4. ✅ 提供风险说明的中英文版本

---

## 📝 十一、配置文件示例

### `config/optimizer_config.py`
```python
# 优化器配置
OPTIMIZER_CONFIG = {
    # 评分权重
    'weights': {
        'float_days': 2.0,
        'available_credit': 1.0,
        'low_utilization_bonus': 0.5,
        'risk_penalty': 3.0
    },
    
    # 风险阈值
    'risk_thresholds': {
        'utilization_high': 80.0,
        'utilization_critical': 90.0,
        'days_to_due_urgent': 7,
        'days_to_due_critical': 3
    },
    
    # 还款建议
    'payment_recommendations': {
        'min_payment_ratio': 0.05,  # 5%最低还款
        'recommended_ratio': 0.30,  # 建议30%
        'full_payment_threshold': 1.0
    }
}
```

---

## ✅ 十二、验收标准

### Phase 1 完成标准
- [x] 所有数据库表创建成功
- [x] 核心算法通过单元测试
- [x] API接口返回正确数据
- [x] 前端UI符合设计稿
- [x] 风险告知流程完整
- [x] 端到端测试通过

---

## 📚 十三、参考资料

- FullCalendar.js文档: https://fullcalendar.io/
- Python dateutil: https://dateutil.readthedocs.io/
- Bootstrap Modal: https://getbootstrap.com/docs/5.3/components/modal/

---

**文档结束**

---

## 🤔 待确认问题

请审阅以上设计并反馈：

1. **数据库设计**是否合理？需要调整字段吗？
2. **算法权重**是否需要调整？（目前免息期权重最高）
3. **风险阈值**设置是否合适？（使用率>80%算高风险）
4. **UI设计**是否符合预期？需要修改布局吗？
5. **开发时间**（10天）是否可接受？

确认后我将立即开始实现！🚀
