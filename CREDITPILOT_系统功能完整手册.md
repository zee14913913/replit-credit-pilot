# CreditPilot 系统功能完整手册

**版本**: V2025.11  
**更新日期**: 2025-11-24  
**适用对象**: 马来西亚银行客户财务管理

---

## 📋 目录

1. [系统概述](#系统概述)
2. [核心功能模块](#核心功能模块)
3. [信用卡计算引擎详细说明](#信用卡计算引擎详细说明)
4. [PDF解析系统](#pdf解析系统)
5. [贷款评估系统](#贷款评估系统)
6. [交易分类规则](#交易分类规则)
7. [月度账本引擎](#月度账本引擎)
8. [AI智能助手](#ai智能助手)
9. [报告中心](#报告中心)
10. [系统设置与配置](#系统设置与配置)

---

## 系统概述

### 什么是CreditPilot？

**CreditPilot** 是为马来西亚银行客户打造的**企业级SaaS财务管理平台**，专注于：
- ✅ **100%数据准确性** - 绝对不使用估算值或默认值
- ✅ **智能自动化** - AI驱动的财务分析和建议
- ✅ **多银行支持** - 支持13家马来西亚主流银行
- ✅ **双语界面** - 中英文完整支持

### 核心价值

| 功能 | 为客户做什么 | 客户获益 |
|------|-------------|---------|
| **信用卡管理** | 自动处理PDF账单，精确计算Owner和INFINITE两条财务线 | 节省80%手工记账时间 |
| **贷款评估** | 基于CTOS数据评估贷款资格，匹配804个贷款产品 | 找到最优贷款方案 |
| **交易分类** | 自动识别供应商交易，区分个人和公司支出 | 清晰的财务分账 |
| **AI助手** | 24/7财务问答，每日自动生成财务报告 | 专业财务顾问服务 |
| **Excel报告** | 一键生成专业格式Excel报告 | 直接用于会计和报税 |

---

## 核心功能模块

### 1. DASHBOARD（仪表板）

**功能**：
- 财务概览一目了然
- 实时显示总资产、总负债、净值
- 信用卡使用率图表
- 近期交易快速查看

**操作方式**：
1. 登录后自动显示仪表板
2. 点击任意卡片进入详细页面
3. 图表支持鼠标悬停查看数据

---

### 2. CUSTOMERS（客户管理）

**功能**：
- 管理客户基本信息
- 记录月收入、联系方式
- 设置个人和公司账户信息

**客户信息包含**：
```yaml
基本信息:
  - 姓名（中英文）
  - 身份证号（IC No）
  - 电话、邮箱
  - 月收入

银行账户:
  - 个人账户名称 + 账号
  - 公司账户名称 + 账号
```

**操作方式**：
1. Admin/Accountant角色：访问 `/admin/customers`
2. 点击"新增客户"填写信息
3. 编辑/删除客户资料

---

### 3. CREDIT CARDS（信用卡管理）

**功能**：
- 管理客户的所有信用卡
- 上传并解析PDF账单
- 自动计算Owner和INFINITE两条财务线
- 查看每月交易明细

**支持的银行**（13家）：
1. AmBank / AmBank Islamic
2. UOB
3. HSBC
4. Standard Chartered
5. Hong Leong Bank
6. OCBC
7. Alliance Bank
8. Public Bank
9. Maybank
10. CIMB
11. RHB
12. BSN
13. Affin Bank

**操作流程**：
```
Step 1: 添加信用卡
  → 选择银行
  → 输入卡号、持卡人姓名
  → 设置信用额度

Step 2: 上传PDF账单
  → 拖拽PDF文件 或 点击上传
  → 系统自动解析（5秒内完成）
  → 提取全部交易记录

Step 3: 查看计算结果
  → Owner's Expenses（客户个人支出）
  → GZ's Expenses（INFINITE公司支出）
  → Owner's Payment（客户还款）
  → GZ's Payment（INFINITE还款）
  → 最终余额（Owner + INFINITE分别显示）
```

---

## 信用卡计算引擎详细说明

### 计算原理

**核心规则**：将信用卡账单分为**Owner（客户）**和**INFINITE GZ（公司）**两条独立财务线。

### 第1轮计算（6个基础项目）

| 项目 | 英文 | 计算公式 | 说明 |
|------|------|----------|------|
| 1 | Owner's Expenses | SUM(所有非Suppliers的DR交易) | 客户个人消费 |
| 2 | GZ's Expenses | SUM(所有Suppliers的DR交易) | INFINITE公司采购 |
| 3 | Owner's Payment | SUM(客户自己的CR还款) | 客户还款金额 |
| 4 | GZ's Payment1 | 所有CR - Owner's Payment | INFINITE第1次还款 |
| 5 | Owner's OS Bal | Previous Balance + Owner's Expenses - Owner's Payment | 客户欠款余额 |
| 6 | GZ's OS Bal | Previous Balance + GZ's Expenses - GZ's Payment1 | INFINITE欠款余额（第1轮） |

### 第2轮计算（GZ's Payment2）

**计算内容**：从9个GZ银行账户转账到客户银行账户的金额

**9个GZ银行账户组合**：
```
1. Tan Zee Liang @ GX Bank
2. Yeo Chee Wang @ Maybank
3. Yeo Chee Wang @ GX Bank
4. Yeo Chee Wang @ UOB
5. Yeo Chee Wang @ OCBC
6. Teo Yok Chu @ OCBC
7. Infinite GZ Sdn Bhd @ Hong Leong Bank
8. Ai Smart Tech @ Public Bank
9. Ai Smart Tech @ Alliance Bank
```

**识别规则**：
- 银行名称 + 持卡人名称 **双重精确匹配**
- 支持银行别名：Hong Leong = HLB，Public Bank = PBB，Alliance Bank = Alliance

### 最终计算

```
8. FINAL Owner OS Bal = Owner's OS Bal（第1轮）
9. FINAL GZ OS Bal = GZ's OS Bal（第1轮）- GZ's Payment2
```

### ⚠️ 重要特性

1. **允许负数余额** - 表示客户多还了钱（CR余额）
2. **100%精确计算** - 使用Decimal类型，避免浮点数误差
3. **双重验证** - 4层验证系统确保数据完整性

---

## PDF解析系统

### 本地Fallback Parser

**特点**：
- ✅ **零外部API成本** - 完全本地解析
- ✅ **100%交易提取** - 保证不丢失任何交易
- ✅ **13家银行支持** - 覆盖马来西亚主流银行

### 解析步骤

```yaml
Step 1: PDF文件验证
  - 检查文件格式（PDF）
  - 检查文件大小（<10MB）
  - 检查页数（<50页）

Step 2: 提取关键字段（8个）
  - Statement Date（账单日期）
  - Due Date（还款截止日期）
  - Statement Total（账单总额）
  - Minimum Payment（最低还款额）
  - Previous Balance（上月余额）
  - Credit Limit（信用额度）
  - Card Number（卡号）
  - Card Holder Name（持卡人姓名）

Step 3: 提取交易记录
  - 智能多列布局检测
  - 独立DR/CR列解析
  - 日期、描述、金额三元组验证

Step 4: 数据验证
  - 验证DR/CR双列存在
  - 验证日期格式
  - 验证金额合计
  - 验证4个关键字段必须存在
```

### 🔒 **100%数据质量保证**

**客户明确要求**：
> "所有4个关键字段（Statement Date, Due Date, Statement Total, Minimum Payment）必须从PDF直接提取，绝对不允许估算、计算或使用默认值！"

**实施策略**：
- ❌ 禁止使用估算值
- ❌ 禁止使用计算值
- ❌ 禁止使用默认值
- ✅ 只接受PDF原始数据
- ✅ 提取失败则标记为"需要重新上传"

---

## 交易分类规则

### 7个Suppliers（INFINITE供应商）

**完整名单**：
```
1. 7SL
2. Dinas
3. Raub Syc Hainan
4. Ai Smart Tech
5. HUAWEI
6. PasarRaya
7. Puchong Herbs
```

### 分类逻辑

#### DR交易（消费）

```python
IF 描述包含任意Supplier名称:
    → "GZ's Expenses"（INFINITE公司采购）
ELSE:
    → "Owner's Expenses"（客户个人消费）
```

#### CR交易（还款）

```python
# Rule 1: 客户姓名识别
IF 描述包含客户姓名:
    → "Owner's Payment"（客户还款）

# Rule 2: 空描述处理
ELIF 描述为空:
    → "Owner's Payment"（默认为客户还款）

# Rule 3: 排除法
ELSE:
    → "GZ's Payment"（INFINITE还款）
```

### 模糊匹配

**相似度阈值**：98%

**示例**：
- "7-ELEVEN" ≈ "7SL" ✅
- "DINAS RAUB" ≈ "Dinas" ✅
- "AI SMART TECHNOLOGY" ≈ "Ai Smart Tech" ✅

---

## 月度账本引擎

### 功能

为每张信用卡生成月度账本，分别追踪：
1. **Customer Ledger**（客户账本）
2. **INFINITE Ledger**（INFINITE账本）

### 计算逻辑

```yaml
每个月:
  开始余额: 上月结束余额（滚动余额）
  
  本月支出:
    Customer Spend: SUM(Owner's Expenses)
    INFINITE Spend: SUM(GZ's Expenses)
  
  本月还款:
    Customer Payments: SUM(Owner's Payment)
    INFINITE Payments: SUM(GZ's Payment1 + GZ's Payment2)
  
  结束余额:
    Customer Balance = 开始余额 + Customer Spend - Customer Payments
    INFINITE Balance = 开始余额 + INFINITE Spend - INFINITE Payments
```

### 滚动余额规则

**第一个月**：
```python
IF stmt_prev_balance != 0:
    # 使用PDF中的Previous Balance作为起点
    Customer起始余额 = stmt_prev_balance
    INFINITE起始余额 = 0
```

**后续月份**：
```python
Customer起始余额 = 上月Customer结束余额
INFINITE起始余额 = 上月INFINITE结束余额
```

### 验证机制

```python
# 验证stmt_prev_balance是否匹配
IF |stmt_prev_balance - (上月Customer余额 + 上月INFINITE余额)| > 0.01:
    ⚠️ 警告：余额不匹配，请检查
```

---

## 贷款评估系统（CREDITPILOT双引擎）

### 支持的评估标准

#### Legacy引擎（传统标准）
- **DSR** (Debt Service Ratio) - 债务偿还比率
- **DSCR** (Debt Service Coverage Ratio) - 债务偿还覆盖率

#### Modern引擎（现代标准）
- **DTI** (Debt-to-Income) - 债务收入比
- **FOIR** (Fixed Obligation to Income Ratio) - 固定债务收入比
- **CCRIS** - 中央信贷参考信息系统
- **BRR** (Basic Risk Rating) - 基础风险评级

### 数据源

**独家CTOS数据**：
- ✅ Personal CTOS Report（个人信用报告）
- ✅ Company CTOS Report（公司信用报告）
- ✅ 债务承诺数据（Debt Commitment）

### 评估流程

```yaml
Step 1: 上传CTOS报告
  - 个人CTOS（Personal）
  - 公司CTOS（Company）

Step 2: 系统自动提取
  - 月收入（Monthly Income）
  - 现有债务（Existing Commitments）
  - 信用评分（Credit Score）
  - 违约记录（Default History）

Step 3: 风险评级计算
  等级:
    - AAA: 优秀（违约概率<1%）
    - AA: 良好（违约概率1-3%）
    - A: 可接受（违约概率3-5%）
    - BBB: 一般（违约概率5-10%）
    - BB: 较差（违约概率10-20%）
    - B: 差（违约概率>20%）

Step 4: 产品匹配
  从804个贷款产品中筛选:
    - 银行要求匹配
    - 利率最优
    - 审批概率高
    - 贷款额度符合
```

### 804个贷款产品

**覆盖银行**（12+家）：
- Maybank, CIMB, Public Bank, Hong Leong Bank
- RHB, AmBank, UOB, HSBC, Standard Chartered
- OCBC, Alliance Bank, Affin Bank, BSN
- + 其他金融机构

**产品类型**：
1. Personal Loan（个人贷款）
2. Home Loan（房屋贷款）
3. Car Loan（汽车贷款）
4. Business Loan（商业贷款）
5. SME Financing（中小企业融资）

---

## AI智能助手 V3

### 功能

**多提供商AI架构**：
- 主要：Perplexity AI（sonar模型）
- 备用：OpenAI（gpt-4o-mini）
- 自动故障转移

### 能力

| 功能 | 说明 | 使用场景 |
|------|------|---------|
| **实时网络搜索** | 获取最新金融信息 | 查询当前利率、汇率 |
| **财务问答** | 24/7智能回答 | "我本月花了多少钱？" |
| **跨模块分析** | 综合分析所有财务数据 | 现金流预测、异常检测 |
| **每日财务报告** | 自动生成每日摘要 | 邮件发送财务概览 |
| **信用卡推荐** | 基于消费习惯推荐 | 找到最适合的信用卡 |
| **贷款建议** | 债务整合、重组建议 | 降低利息支出 |

### 使用方式

```
方式1: 浮动聊天框
  - 点击右下角AI图标
  - 输入问题
  - 获得即时答案

方式2: 语音助手
  - 点击麦克风图标
  - 语音提问
  - 语音回答

方式3: 每日报告
  - 设置：Admin → 通知设置
  - 选择：每日财务报告
  - 时间：每天早上8点自动发送
```

---

## 报告中心（Report Center）

### 可生成的报告

#### 1. 月度信用卡报告

**内容**：
- 每月消费总额（Owner + INFINITE）
- 分类支出统计（餐饮、购物、交通等）
- 还款记录
- 余额变化趋势图

**格式**：Excel（专业格式）/ PDF / CSV

#### 2. 年度财务报告

**内容**：
- 年度总收入
- 年度总支出
- 按月趋势图
- 分类占比饼图

#### 3. CTOS报告

**内容**：
- Personal CTOS PDF
- Company CTOS PDF
- 债务承诺清单
- 信用评分历史

#### 4. 贷款匹配报告

**内容**：
- 推荐贷款产品（Top 10）
- 利率比较表
- 审批概率评估
- 节省利息计算

### Excel专业格式标准（13项）

```yaml
1. 标题行格式:
   - 字体: Arial Bold 12pt
   - 背景色: CreditPilot Pink (#FFB6C1)
   - 文字颜色: Deep Brown (#3E2723)

2. 数据行格式:
   - 奇数行: 白色背景
   - 偶数行: 浅灰色背景（#F5F5F5）

3. 列宽自动调整

4. 货币格式: "RM 1,234.56"

5. 日期格式: "DD-MMM-YY" (例: 28-OCT-25)

6. 边框: 全表格线

7. 冻结首行

8. 页眉/页脚:
   - 左: 客户名称
   - 中: 报告标题
   - 右: 生成日期

9. 打印设置:
   - 页面: A4横向
   - 边距: 窄边距
   - 居中: 水平 + 垂直

10. 小计行:
    - 字体: Bold
    - 背景色: 浅黄色

11. 总计行:
    - 字体: Bold 14pt
    - 背景色: CreditPilot Pink
    - 双线边框

12. 图表（如果有）:
    - 样式: 简约现代
    - 颜色: CreditPilot配色

13. 数据验证:
    - 金额列: 数字格式检查
    - 日期列: 日期格式检查
```

---

## 系统设置与配置

### 用户角色权限（RBAC）

| 角色 | 权限 | 可访问功能 |
|------|------|----------|
| **Admin** | 完全控制 | 所有功能 + 用户管理 |
| **Accountant** | 财务管理 | 除用户管理外的所有功能 |
| **Customer** | 查看自己数据 | 仅个人财务数据 |
| **Unauthenticated** | 无权限 | 仅登录页 |

### 颜色系统（3色规则）

**严格遵守**：
```yaml
主色1: Black (#000000)
  用途: 主背景

主色2: Hot Pink (#FF007F)
  用途: 收入、贷项、高亮、按钮

主色3: Dark Purple (#322446)
  用途: 支出、借项、边框
```

**禁止**：
- ❌ 修改全局CSS
- ❌ 使用!important覆盖
- ❌ 添加其他颜色

### 通知设置

#### 支持的通知渠道

```yaml
1. In-App通知:
   - 实时弹窗
   - 通知中心

2. Email通知:
   - SendGrid发送
   - 每日/每周摘要
   - 重要提醒

3. SMS通知:
   - Twilio发送
   - 高优先级提醒
   - 验证码
```

#### 可配置的通知类型

```yaml
财务提醒:
  - 账单到期提醒（Due Date前3天）
  - 信用卡额度预警（使用率>80%）
  - 异常交易检测（单笔>RM5000）

系统通知:
  - PDF解析完成
  - 报告生成完成
  - 数据导出完成

AI助手:
  - 每日财务报告
  - 每周财务总结
  - 每月推荐报告
```

### 数据备份

**自动备份**：
- 频率：每天凌晨2点
- 保留：最近30天备份
- 位置：`lee_e_kai_data/database_backup/`

**手动备份**：
- Admin → 系统设置 → 数据备份
- 一键导出所有数据（SQLite + 附件）

### SFTP ERP自动化

**功能**：每10分钟自动导出7类财务数据到SQL ACC ERP系统

**导出内容**：
```yaml
1. 客户主数据（Customers）
2. 信用卡数据（Credit Cards）
3. 交易记录（Transactions）
4. 月度账本（Monthly Ledger）
5. 供应商发票（Supplier Invoices）
6. CTOS报告（CTOS Reports）
7. 审计日志（Audit Logs）
```

**配置**：
```yaml
SFTP服务器:
  Host: {ERP_HOST}
  Port: 22
  Username: {SFTP_USER}
  Password: {SFTP_PASSWORD}

导出格式: CSV（UTF-8编码）
导出路径: /import/{table_name}_{YYYYMMDD_HHMMSS}.csv
```

---

## 常见问题（FAQ）

### Q1: 如何确保数据100%准确？
**A**: 
1. 所有关键字段从PDF直接提取，不使用估算
2. 4层验证系统检查数据完整性
3. Decimal精度计算避免浮点数误差
4. 双重验证：系统计算 vs PDF原始值

### Q2: 支持哪些银行？
**A**: 支持13家马来西亚主流银行：
- AmBank, UOB, HSBC, Standard Chartered
- Hong Leong, OCBC, Alliance, Public Bank
- Maybank, CIMB, RHB, BSN, Affin

### Q3: 如何区分Owner和INFINITE交易？
**A**: 
- **DR交易**: 根据7个Supplier名称自动分类
- **CR交易**: 根据客户姓名和GZ银行账户识别
- **模糊匹配**: 98%相似度智能识别

### Q4: PDF解析失败怎么办？
**A**:
1. 检查PDF格式（非扫描件）
2. 检查PDF大小（<10MB）
3. 使用VBA备用解析器
4. 联系技术支持

### Q5: 如何获得贷款推荐？
**A**:
1. 上传Personal + Company CTOS报告
2. 系统自动评估资格
3. 查看推荐产品（804个产品库）
4. 导出对比报告

---

## 技术支持

**文档位置**: `/docs/`
**系统架构**: `replit.md`
**API文档**: `API_ENDPOINTS_SUMMARY.md`

**联系方式**:
- Email: support@creditpilot.my
- 在线客服: 点击右下角AI助手

---

**© 2025 CreditPilot - Enterprise-Grade Financial Management Platform**
