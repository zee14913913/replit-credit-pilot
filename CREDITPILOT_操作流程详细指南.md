# CreditPilot 操作流程详细指南

**版本**: V2025.11  
**更新日期**: 2025-11-24  
**适用对象**: 系统操作员、客户服务人员

---

## 📋 目录

1. [系统登录流程](#系统登录流程)
2. [客户注册与管理](#客户注册与管理)
3. [信用卡账单处理完整流程](#信用卡账单处理完整流程)
4. [交易分类与审核](#交易分类与审核)
5. [月度账本生成](#月度账本生成)
6. [贷款评估完整流程](#贷款评估完整流程)
7. [报告生成与导出](#报告生成与导出)
8. [AI助手使用指南](#ai助手使用指南)
9. [常见问题处理](#常见问题处理)
10. [数据备份与恢复](#数据备份与恢复)

---

## 系统登录流程

### 步骤1: 访问系统

```
URL: https://your-domain.replit.app
或
URL: https://creditpilot.my
```

### 步骤2: 输入登录凭证

```yaml
Admin/Accountant登录:
  邮箱: admin@creditpilot.my
  密码: ********
  角色: Admin（管理员）或 Accountant（会计）

Customer登录:
  邮箱: customer@example.com
  密码: ********
  角色: Customer（客户）
```

### 步骤3: 双因素认证（如果启用）

```yaml
Step 1: 接收SMS验证码
Step 2: 输入6位数验证码
Step 3: 点击"验证"
```

### 步骤4: 进入仪表板

```
登录成功后自动跳转到:
  - Admin/Accountant → /admin/dashboard
  - Customer → /customers/{customer_id}
```

---

## 客户注册与管理

### 创建新客户（完整流程）

#### Step 1: 进入客户管理页面

```
路径: Dashboard → Customers → "新增客户"按钮
URL: /admin/customers/create
```

#### Step 2: 填写基本信息

```yaml
必填字段:
  姓名（中文）: 李二凯
  姓名（英文）: LEE E KAI
  身份证号: 900101-01-1234
  电话: +60123456789
  邮箱: lee.ekai@example.com

可选字段:
  月收入: RM 8,000.00
  地址: Kuala Lumpur, Malaysia
```

#### Step 3: 设置银行账户

```yaml
个人账户:
  账户名称: LEE E KAI
  银行: Maybank
  账户号: 1234567890123

公司账户（如果有）:
  账户名称: INFINITE GZ SDN BHD
  银行: Hong Leong Bank
  账户号: 0987654321098
```

#### Step 4: 系统自动生成客户代码

```
格式: {姓名缩写}_{顺序号}
示例: LEE_EK_009
```

#### Step 5: 保存并确认

```
点击"保存"按钮
→ 系统验证数据
→ 生成审计日志
→ 跳转到客户详情页
```

---

### 编辑现有客户

```yaml
Step 1: 客户列表 → 找到客户 → 点击"编辑"
Step 2: 修改需要更新的字段
Step 3: 点击"保存更改"
Step 4: 系统记录修改历史（Audit Log）
```

---

## 信用卡账单处理完整流程

### 流程概览

```
┌─────────────┐
│ 1. 添加信用卡 │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 2. 上传PDF账单│
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 3. 自动解析  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 4. 交易分类  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 5. 执行计算  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 6. 查看结果  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 7. 导出报告  │
└─────────────┘
```

---

### 详细步骤

#### Step 1: 添加信用卡

**路径**: Customers → 选择客户 → Credit Cards → "添加信用卡"

**填写信息**:
```yaml
必填:
  银行名称: [从下拉列表选择]
    - AmBank
    - UOB
    - HSBC
    - Standard Chartered
    - Hong Leong Bank
    - OCBC
    - Alliance Bank
    - Public Bank
    - Maybank
    - CIMB
    - RHB
    - BSN
    - Affin Bank
  
  卡号（后4位）: 1234
  持卡人姓名: LEE E KAI
  信用额度: RM 15,000.00
  卡类型: Visa / MasterCard

可选:
  卡片昵称: "主卡"
  有效期: 12/26
```

**点击"保存"**:
```
→ 系统生成卡片ID
→ 状态设为"Active"
→ 跳转到卡片详情页
```

---

#### Step 2: 上传PDF账单

**路径**: Credit Cards → 选择卡片 → "上传账单"

**上传方式**:
```yaml
方式1: 拖拽上传
  - 将PDF文件拖到上传区域
  - 支持多文件（最多10个）

方式2: 点击上传
  - 点击"选择文件"按钮
  - 浏览并选择PDF
  - 点击"上传"

方式3: 批量上传（高级）
  - 选择多个PDF文件
  - 系统自动按文件名排序
  - 批量解析
```

**文件要求**:
```yaml
格式: PDF（非扫描件优先）
大小: < 10MB
页数: < 50页
命名: 建议格式 YYYY-MM_BankName.pdf
      例: 2025-10_AmBank.pdf
```

---

#### Step 3: 自动解析（系统后台）

**解析进度**:
```
1. 文件验证 .............. [✓] 0.5秒
2. 提取关键字段 .......... [✓] 1.5秒
3. 提取交易记录 .......... [✓] 2.0秒
4. 验证数据完整性 ........ [✓] 0.5秒
5. 保存到数据库 .......... [✓] 0.5秒

总计: 约5秒完成
```

**提取的字段**:
```yaml
关键字段（必须）:
  ✓ Statement Date: 2025-10-28
  ✓ Due Date: 2025-11-17
  ✓ Statement Total: RM 15,062.57
  ✓ Minimum Payment: RM 1,501.88

可选字段:
  ✓ Previous Balance: RM 14,515.49
  ✓ Credit Limit: RM 15,000.00
  ✓ Card Number: **** 1234
  ✓ Card Holder: LEE E KAI

交易记录:
  ✓ 提取了156笔交易
  ✓ DR交易: 145笔
  ✓ CR交易: 11笔
```

**解析失败处理**:
```yaml
如果解析失败:
  1. 系统显示错误信息
  2. 标记为"待处理"状态
  3. 提供备用解析选项:
     - VBA Excel解析器
     - 手动输入
     - 联系技术支持
```

---

#### Step 4: 交易分类

**自动分类规则**:
```yaml
DR交易（消费）:
  IF 描述包含Supplier名称:
    → 分类为 "GZ's Expenses"
    → 标记供应商: 7SL / Dinas / Ai Smart Tech
  ELSE:
    → 分类为 "Owner's Expenses"

CR交易（还款）:
  IF 描述包含客户姓名:
    → 分类为 "Owner's Payment"
  ELIF 描述为空:
    → 分类为 "Owner's Payment"（默认）
  ELSE:
    → 分类为 "GZ's Payment"
```

**手动审核交易**:
```yaml
Step 1: 查看分类结果
  路径: Statement Details → Transactions Tab

Step 2: 筛选需要审核的交易
  - 未分类交易（Unassigned）
  - 低置信度交易（Confidence < 80%）

Step 3: 手动调整分类
  - 点击交易行
  - 修改Category下拉框
  - 保存更改

Step 4: 批量调整（如果需要）
  - 勾选多个交易
  - 批量操作 → 修改分类
  - 确认更改
```

---

#### Step 5: 执行计算

**自动计算**:
```
上传完成后系统自动执行：
1. 第1轮计算（6个基础项目）
2. 第2轮计算（GZ's Payment2）
3. 最终计算（Final Balances）
```

**手动重新计算**:
```yaml
场景: 交易分类调整后需要重新计算

Step 1: Statement Details → "重新计算"按钮
Step 2: 系统提示"确认重新计算?"
Step 3: 点击"确认"
Step 4: 等待计算完成（约2秒）
Step 5: 查看更新后的结果
```

**计算验证**:
```yaml
系统自动验证:
  ✓ 交易合计 ≈ Statement Total（±5%）
  ✓ Minimum Payment ≤ Statement Total
  ✓ Previous Balance + 本月交易 ≈ Statement Total
  ✓ Owner's OS Bal + GZ's OS Bal ≈ Total Outstanding

验证失败处理:
  - 显示警告消息
  - 高亮不匹配的字段
  - 提供修正建议
```

---

#### Step 6: 查看结果

**计算结果页面**:
```yaml
第1轮计算结果:
  ┌────────────────────────────┬──────────────┐
  │ Owner's Expenses           │ RM 8,547.08  │
  │ GZ's Expenses              │ RM 5,968.41  │
  │ Owner's Payment            │ RM 8,000.00  │
  │ GZ's Payment1              │ RM 0.00      │
  │ Owner's OS Bal (Round 1)   │ RM 15,062.57 │
  │ GZ's OS Bal (Round 1)      │ RM 6,483.90  │
  └────────────────────────────┴──────────────┘

第2轮计算结果:
  ┌────────────────────────────┬──────────────┐
  │ GZ's Payment2              │ RM 3,500.00  │
  └────────────────────────────┴──────────────┘

最终结果:
  ┌────────────────────────────┬──────────────┐
  │ FINAL Owner OS Bal         │ RM 15,062.57 │
  │ FINAL GZ OS Bal            │ RM 2,983.90  │
  │ TOTAL Outstanding Balance  │ RM 18,046.47 │
  └────────────────────────────┴──────────────┘
```

**交易明细查看**:
```yaml
Tab 1: All Transactions（全部交易）
  - 显示所有156笔交易
  - 按日期排序
  - 可筛选DR/CR

Tab 2: Owner's Expenses（Owner支出）
  - 显示客户个人消费
  - 合计: RM 8,547.08

Tab 3: GZ's Expenses（INFINITE支出）
  - 显示INFINITE公司采购
  - 合计: RM 5,968.41
  - 按供应商分组

Tab 4: Payments（还款）
  - Owner's Payment: RM 8,000.00
  - GZ's Payment: RM 3,500.00
```

---

#### Step 7: 导出报告

**导出选项**:
```yaml
格式1: Excel（专业格式）
  - 13项专业格式标准
  - CreditPilot官方配色
  - 包含所有交易明细
  - 自动计算公式
  - 图表可视化

格式2: PDF
  - A4横向打印
  - 包含公司Logo
  - 专业排版
  - 适合客户查看

格式3: CSV
  - 纯数据导出
  - 适合数据分析
  - Excel兼容
```

**导出步骤**:
```yaml
Step 1: Statement Details → "导出"按钮
Step 2: 选择导出格式
Step 3: 点击"生成报告"
Step 4: 等待生成（约5-10秒）
Step 5: 点击"下载"
Step 6: 保存到本地
```

---

## 交易分类与审核

### 批量分类流程

```yaml
Step 1: 选择账单
  路径: Credit Cards → Statement → Transactions

Step 2: 应用筛选条件
  - 筛选: Unassigned（未分类）
  - 日期范围: 2025-10-01 to 2025-10-31
  - 金额范围: > RM 100

Step 3: 全选或多选交易
  - 点击表头复选框 = 全选
  - 或逐个勾选需要分类的交易

Step 4: 批量操作
  操作: 修改分类
  新分类: Owner's Expenses
  确认: 是

Step 5: 系统自动更新
  - 更新交易记录
  - 重新计算账单
  - 记录审计日志
```

---

### 异常交易处理

```yaml
场景1: 金额异常大（> RM 5,000）

检测规则:
  IF 单笔交易 > RM 5,000:
    → 标记为"异常"
    → 发送通知给Admin

处理流程:
  Step 1: 查看异常交易列表
  Step 2: 核实交易真实性
  Step 3: 确认分类
  Step 4: 添加备注说明
  Step 5: 标记为"已审核"

---

场景2: 供应商名称模糊匹配失败

检测规则:
  IF 描述与Supplier相似度 < 80%:
    → 标记为"待审核"

处理流程:
  Step 1: 手动查看描述
  Step 2: 判断是否为Supplier
  Step 3: 如果是 → 手动标记为"GZ's Expenses"
  Step 4: 如果否 → 标记为"Owner's Expenses"
  Step 5: 系统学习记录（未来自动识别）

---

场景3: CR交易无法确定付款来源

检测规则:
  IF CR交易 AND 描述不含客户名 AND 描述不含GZ银行:
    → 标记为"待审核"

处理流程:
  Step 1: 查询银行记录确认
  Step 2: 核对客户或INFINITE银行账户流水
  Step 3: 确认付款来源
  Step 4: 手动分类为"Owner's Payment"或"GZ's Payment"
```

---

## 月度账本生成

### 自动生成流程

```yaml
触发条件:
  - 每月上传第一个账单时自动创建
  - 或手动触发"生成月度账本"

Step 1: 系统检查
  - 检查当月是否已有账本
  - 检查上月账本余额

Step 2: 计算期初余额
  - Customer期初 = 上月Customer结束余额
  - INFINITE期初 = 上月INFINITE结束余额

Step 3: 汇总本月数据
  - Customer Spend = SUM(Owner's Expenses)
  - INFINITE Spend = SUM(GZ's Expenses)
  - Customer Payments = SUM(Owner's Payment)
  - INFINITE Payments = SUM(GZ's Payment1 + GZ's Payment2)

Step 4: 计算滚动余额
  - Customer余额 = 期初 + Spend - Payments
  - INFINITE余额 = 期初 + Spend - Payments

Step 5: 保存月度账本
  - monthly_ledger表（Customer）
  - infinite_monthly_ledger表（INFINITE）

Step 6: 生成月度摘要
  - 创建PDF报告
  - 发送邮件通知
```

---

### 查看月度账本

```yaml
路径: Reports → Monthly Ledger

视图1: 月度列表
  ┌──────────┬──────────┬──────────┬──────────┬──────────┐
  │ 月份     │ 期初余额 │ 本月消费 │ 本月还款 │ 滚动余额 │
  ├──────────┼──────────┼──────────┼──────────┼──────────┤
  │ 2025-10  │  8,000   │ 14,515   │  8,000   │ 14,515   │
  │ 2025-11  │ 14,515   │ 15,063   │ 11,500   │ 18,078   │
  │ 2025-12  │ 18,078   │ 12,450   │  9,000   │ 21,528   │
  └──────────┴──────────┴──────────┴──────────┴──────────┘

视图2: 趋势图
  - 余额变化趋势线图
  - 消费vs还款柱状图
  - 累计余额面积图

视图3: 对比分析
  - Customer vs INFINITE余额对比
  - 月度支出占比饼图
  - 还款率计算
```

---

## 贷款评估完整流程

### 流程概览

```
┌─────────────┐
│1. 上传CTOS报告│
└──────┬──────┘
       │
       ▼
┌─────────────┐
│2. 自动提取数据│
└──────┬──────┘
       │
       ▼
┌─────────────┐
│3. 计算DSR/DTI│
└──────┬──────┘
       │
       ▼
┌─────────────┐
│4. 风险评级  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│5. 产品匹配  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│6. 生成推荐报告│
└─────────────┘
```

---

### 详细步骤

#### Step 1: 上传CTOS报告

**路径**: Loans → Evaluate → "上传CTOS报告"

**上传内容**:
```yaml
Personal CTOS:
  - 文件名: CTOS_Personal_LEE_E_KAI.pdf
  - 包含: 个人信用评分、债务清单

Company CTOS（如果有）:
  - 文件名: CTOS_Company_INFINITE_GZ.pdf
  - 包含: 公司信用、公司债务
```

**上传后系统自动**:
```
1. OCR提取文本 ............ [✓]
2. 识别关键数据 ............ [✓]
3. 保存到数据库 ............ [✓]
```

---

#### Step 2: 自动提取数据

**Personal CTOS提取**:
```yaml
基本信息:
  ✓ IC Number: 900101-01-1234
  ✓ Full Name: LEE E KAI
  ✓ Age: 35岁
  ✓ Employment Status: Employed

信用数据:
  ✓ Credit Score: 720分（Good）
  ✓ Total Debt: RM 350,000
  ✓ Monthly Commitment: RM 4,500

债务明细:
  ✓ Home Loan: RM 300,000（月供RM 2,500）
  ✓ Car Loan: RM 50,000（月供RM 800）
  ✓ Credit Cards: RM 18,000（最低还款RM 1,200）
```

**Company CTOS提取**:
```yaml
公司信息:
  ✓ Company Name: INFINITE GZ SDN BHD
  ✓ Registration No: 202301234567
  ✓ Business Type: Trading

信用数据:
  ✓ Company Credit Score: 680分
  ✓ Company Debt: RM 500,000
  ✓ Directors: 2人
```

---

#### Step 3: 计算财务比率

**DSR（Debt Service Ratio）计算**:
```
DSR = 月供总额 / 月收入
    = RM 4,500 / RM 8,000
    = 0.5625
    = 56.25%

标准: 
  ✓ Excellent: < 30%
  ✓ Good: 30-40%
  ✓ Fair: 40-50%
  ⚠️ High: 50-60%  ← 当前
  ❌ Very High: > 60%
```

**DTI（Debt-to-Income）计算**:
```
DTI = 总债务 / 年收入
    = RM 350,000 / (RM 8,000 × 12)
    = RM 350,000 / RM 96,000
    = 3.65

标准:
  ✓ Excellent: < 2.0
  ✓ Good: 2.0-3.0
  ✓ Fair: 3.0-4.0  ← 当前
  ⚠️ High: 4.0-5.0
  ❌ Very High: > 5.0
```

**CCRIS风险评分**:
```
因素:
  ✓ 还款历史: 无逾期（+100分）
  ✓ 信用使用率: 60%（-20分）
  ✓ 账户年龄: 8年（+30分）
  ✓ 新增申请: 3个月内1次（-10分）

总分: 720 / 850
等级: Good
```

---

#### Step 4: 风险评级

**综合风险评分**:
```yaml
评分项目:
  1. CTOS Credit Score: 720分 → 得分85/100
  2. DSR比率: 56.25% → 得分60/100
  3. DTI比率: 3.65 → 得分70/100
  4. 还款历史: 无逾期 → 得分100/100
  5. 就业稳定性: 5年+ → 得分90/100

加权平均:
  总分 = (85×30% + 60×25% + 70×20% + 100×15% + 90×10%)
       = 76.5分

风险等级:
  90-100分: AAA（优秀）
  80-89分: AA（良好）
  70-79分: A（可接受） ← 当前
  60-69分: BBB（一般）
  50-59分: BB（较差）
  < 50分: B（差）
```

---

#### Step 5: 产品匹配

**筛选条件**:
```yaml
基于评估结果筛选:
  ✓ 风险等级 = A
  ✓ 月收入 = RM 8,000
  ✓ DSR = 56.25%
  ✓ 贷款需求 = RM 50,000（示例）

匹配规则:
  1. 银行接受风险等级A或更低
  2. 最低月收入 ≤ RM 8,000
  3. 最大DSR ≥ 56.25%
  4. 贷款额度范围: RM 10,000 - RM 100,000
```

**匹配结果（Top 10产品）**:
```yaml
Rank 1: Maybank Personal Loan
  - 利率: 3.88% - 5.88%
  - 额度: RM 10,000 - RM 150,000
  - 期限: 1年 - 7年
  - 手续费: 0.5%
  - 审批概率: 85%

Rank 2: CIMB Personal Loan
  - 利率: 3.99% - 6.20%
  - 额度: RM 5,000 - RM 100,000
  - 期限: 1年 - 5年
  - 手续费: 1.0%
  - 审批概率: 80%

Rank 3: Public Bank Personal Loan
  - 利率: 4.15% - 6.50%
  - 额度: RM 10,000 - RM 120,000
  - 期限: 1年 - 7年
  - 手续费: 0.75%
  - 审批概率: 75%

... 还有7个产品
```

---

#### Step 6: 生成推荐报告

**报告内容**:
```yaml
第1部分: 客户财务概览
  - 月收入
  - 现有债务
  - DSR/DTI比率
  - 信用评分

第2部分: 风险评估结果
  - 综合风险等级
  - 各项评分明细
  - 改善建议

第3部分: 推荐产品列表（Top 10）
  - 产品对比表
  - 利率比较图
  - 月供计算
  - 节省利息估算

第4部分: 申请指南
  - 所需文件清单
  - 申请流程
  - 注意事项
  - 联系方式
```

**导出格式**:
```yaml
Excel版本:
  - 专业格式
  - 包含计算公式
  - 可编辑

PDF版本:
  - A4打印
  - 适合提交银行
  - 专业排版
```

---

## 报告生成与导出

### 月度信用卡报告

**路径**: Reports → Monthly Card Report

**生成步骤**:
```yaml
Step 1: 选择参数
  客户: LEE E KAI
  卡片: AmBank Islamic
  月份: 2025-10
  格式: Excel / PDF / CSV

Step 2: 点击"生成报告"

Step 3: 系统处理（约10秒）
  - 汇总交易数据
  - 执行计算
  - 生成图表
  - 应用专业格式

Step 4: 下载报告
```

**报告包含**:
```yaml
Sheet 1: 账单摘要
  - 关键指标
  - Owner vs INFINITE对比
  - 图表可视化

Sheet 2: 交易明细
  - 全部156笔交易
  - 按日期排序
  - 分类标签

Sheet 3: 分类统计
  - Owner's Expenses明细
  - GZ's Expenses明细（按供应商）
  - 还款记录

Sheet 4: 计算详情
  - 第1轮计算结果
  - 第2轮计算结果
  - 最终余额
```

---

### 年度财务报告

**路径**: Reports → Annual Financial Report

**生成步骤**:
```yaml
Step 1: 选择参数
  客户: LEE E KAI
  年份: 2025
  包含卡片: 全部 / 选定卡片

Step 2: 点击"生成年度报告"

Step 3: 系统汇总12个月数据
  - 总收入
  - 总支出
  - 净现金流
  - 月度趋势

Step 4: 生成图表
  - 月度支出柱状图
  - 分类占比饼图
  - 余额趋势线图

Step 5: 下载报告（Excel/PDF）
```

---

## AI助手使用指南

### 日常财务问答

**使用方式**:
```yaml
方式1: 浮动聊天窗
  - 点击右下角AI图标
  - 输入问题
  - 获得即时答案

方式2: 语音助手
  - 点击麦克风图标
  - 语音提问
  - 语音回答
```

**示例对话**:
```
用户: "我本月花了多少钱?"

AI: 根据您2025年11月的信用卡账单，您的支出如下：
    - Owner个人支出: RM 8,547.08
    - INFINITE公司支出: RM 5,968.41
    - 总计: RM 14,515.49

用户: "哪个类别花得最多?"

AI: 您本月支出最多的3个类别是：
    1. 餐饮娱乐: RM 3,245.60（22%）
    2. 购物: RM 2,890.45（20%）
    3. 交通: RM 1,567.80（11%）

用户: "我应该申请哪种贷款?"

AI: 根据您的财务状况（月收入RM 8,000，DSR 56.25%），
    我推荐以下3个产品：
    1. Maybank Personal Loan（3.88%利率）
    2. CIMB Personal Loan（3.99%利率）
    3. Public Bank Personal Loan（4.15%利率）
    
    我已生成详细对比报告，请查看"贷款评估"页面。
```

---

### 每日财务报告

**设置方式**:
```yaml
Step 1: Admin → 通知设置
Step 2: 启用"每日财务报告"
Step 3: 设置发送时间: 08:00 AM
Step 4: 选择接收方式: Email / SMS / In-App
Step 5: 保存设置
```

**报告内容示例**:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  CreditPilot 每日财务报告
  2025-11-24 星期日
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 今日概览:
  • 新增交易: 5笔
  • 今日支出: RM 456.80
  • 本月累计: RM 8,547.08
  • 剩余预算: RM 1,452.92

💳 信用卡使用:
  • AmBank Islamic: 87% (RM 13,050 / RM 15,000)
  • ⚠️ 接近信用额度上限

📅 即将到期:
  • AmBank账单到期: 2025-11-17（7天后）
  • 最低还款: RM 1,501.88

💡 AI建议:
  • 建议本周减少非必要支出
  • 考虑申请账单分期降低月供

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 常见问题处理

### 问题1: PDF解析失败

**原因**:
- PDF是扫描件（图片格式）
- PDF已加密
- PDF格式不标准

**解决方案**:
```yaml
方案1: 使用VBA备用解析器
  Step 1: 下载VBA模板
  Step 2: 在Excel中打开PDF
  Step 3: 运行VBA宏
  Step 4: 生成JSON文件
  Step 5: 上传JSON到系统

方案2: 手动输入
  Step 1: 手动输入4个关键字段
  Step 2: 手动输入交易记录
  Step 3: 系统执行计算

方案3: 联系技术支持
  邮箱: support@creditpilot.my
  提供PDF样本以更新解析器
```

---

### 问题2: 计算结果不正确

**检查清单**:
```yaml
Step 1: 验证4个关键字段
  ✓ Statement Date正确?
  ✓ Statement Total正确?
  ✓ Previous Balance正确?
  ✓ Minimum Payment正确?

Step 2: 验证交易分类
  ✓ 所有交易已分类?
  ✓ Supplier识别正确?
  ✓ 客户名称匹配?

Step 3: 重新计算
  点击"重新计算"按钮

Step 4: 如果仍然错误
  导出数据并联系技术支持
```

---

### 问题3: 无法登录

**解决步骤**:
```yaml
Step 1: 确认网络连接

Step 2: 检查邮箱/密码
  - 大小写正确?
  - 空格?

Step 3: 重置密码
  - 点击"忘记密码"
  - 输入注册邮箱
  - 查收重置邮件
  - 设置新密码

Step 4: 清除浏览器缓存
  - Ctrl + Shift + Delete
  - 清除Cookie和缓存

Step 5: 联系Admin
  请求重置账户
```

---

## 数据备份与恢复

### 自动备份

**备份计划**:
```yaml
频率: 每天凌晨2:00 AM
保留: 最近30天
位置: lee_e_kai_data/database_backup/
格式: SQLite数据库文件 + 附件ZIP
```

**备份内容**:
```yaml
1. 数据库:
   - smart_loan_manager.db
   - 所有表数据

2. 附件:
   - PDF账单
   - Excel报告
   - CTOS报告
   - 证据文件

3. 配置:
   - 系统设置
   - 用户权限
   - API密钥
```

---

### 手动备份

**操作步骤**:
```yaml
Step 1: Admin → 系统设置 → 数据备份
Step 2: 点击"立即备份"
Step 3: 等待备份完成（约1-2分钟）
Step 4: 下载备份文件
Step 5: 保存到安全位置
```

---

### 数据恢复

**恢复流程**:
```yaml
⚠️ 警告: 恢复数据会覆盖当前所有数据！

Step 1: Admin → 系统设置 → 数据恢复
Step 2: 上传备份文件
Step 3: 确认恢复点
Step 4: 输入Admin密码确认
Step 5: 点击"开始恢复"
Step 6: 等待恢复完成（约5分钟）
Step 7: 系统自动重启
Step 8: 重新登录验证数据
```

---

**© 2025 CreditPilot - 操作流程详细指南**
