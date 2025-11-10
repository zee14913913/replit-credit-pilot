# Replit 特殊指示：防止幻想数据和遗漏的终极提示词

---

## 直接给 Replit 的指示（复制粘贴版本）

```
【重要通知】我已经多次发现你在以下方面失败：

1. ❌ 添加假数据 - 你看到"信用卡"就编造"年费50RM"，而网页根本没这个信息
2. ❌ 浅层抓取 - 你只看了列表页有"10个产品"就填10，根本没点进每个产品的详情页
3. ❌ 中途放弃 - 看到复杂网站就用"数据库中的典型值"替代真实数据
4. ❌ 遗忘指示 - 刚开始还记得"12个字段都要提取"，到第20家公司时就开始跳字段
5. ❌ 留空字段 - 某些字段难提取你就不填了，留一片空白

这次我要求你【必须】做到以下这些，不能妥协：

【第一步】启动时声明
- 在最开始打印：🔴 STRICT MODE ACTIVATED
- 打印每条规则，确认理解
- 如果你想偷懒，立即停止并报错

【第二步】对每家公司明确打印
========== COMPANY 1/67 ==========
Company: Affin Bank
URL: https://...
Status: STARTING
- 列表页: [寻找...]
- 已找到产品数: [X个]
- 逐个提取详情: [1/X] → [2/X] → ...
- 完成统计：提取了X个产品，Y个字段

【第三步】对每个产品逐字段打印
  Product: Affin Gold Card
  - COMPANY: Affin Bank ✅
  - LOAN_TYPE: Credit Card ✅
  - REQUIRED_DOC: [寻找中...] → [网页找到：IC + 薪资单] ✅
  - FEATURES: [寻找中...] → [No DATA FOUND] ⚠️（真的没有，不是我偷懒）
  - ... (12个字段全部打印状态)

【第四步】12个字段的强制提取规则
每个字段必须尝试3种方法才能放弃：

REQUIRED_DOC:
  1️⃣ 寻找"Required Documents"关键词 → [成功/失败]
  2️⃣ 寻找文档列表(ul/ol) → [成功/失败]
  3️⃣ 寻找表格里的"Document"列 → [成功/失败]
  
  结果：[如果都失败，填[NO DATA FOUND]]

FEATURES:
  1️⃣ 寻找"Features"关键词 → [成功/失败]
  2️⃣ 寻找"Key Features"或符号列表 → [成功/失败]
  3️⃣ 寻找规格框(spec box)内容 → [成功/失败]
  
  结果：[如果都失败，填[NO DATA FOUND]]

... (以此类推12个字段)

【第五步】绝对禁止的行为
❌ 不许留空格
❌ 不许写"通常银行有..."这类推断
❌ 不许用"同类产品数据库里的数据"
❌ 不许因为"太复杂"就跳过某家公司
❌ 不许因为"字段难找"就省略
❌ 不许看一半就换产品类别

✅ 必须做到：
✅ 每个字段都是从HTML tag里提取的真实数据
✅ 找不到就明确标记[NO DATA FOUND]
✅ 每个产品都进详情页，不是只看列表
✅ 每家公司都按顺序完全完成
✅ 中间保存进度，防止遗忘
✅ 完成后输出统计：X个公司、Y个产品、Z%的[NO DATA FOUND]比率

【第六步】质量检查清单（完成后必须做）
✅ 检查1：总行数 > 100行（如果<100说明抓得太少）
✅ 检查2：[NO DATA FOUND]比率 < 20%（如果>30%说明方法不对）
✅ 检查3：每家公司至少有1个产品（如果=0说明跳过了）
✅ 检查4：没有两行完全相同的内容（说明是复制粘贴的假数据）
✅ 检查5：随机打印5个产品样本，让我手动验证
```

---

## 配合脚本使用的检查代码

将这段代码加到你的 Python 脚本开头：

```python
# ========== 反自作聪明 模块 ==========

STRICT_MODE = {
    'NO_SYNTHESIS': True,         # 禁止合成数据
    'NO_DEFAULTS': True,          # 禁止用默认值
    'NO_EMPTY_CELLS': True,       # 禁止空单元格
    'FORCE_DETAIL_PAGES': True,   # 强制进详情页
    'VERIFY_EACH_FIELD': True,    # 每字段都检查
    'AUDIT_TRAIL': True,          # 审计每一步
    'PREVENT_HALLUCINATION': True # 防止幻想数据
}

def validate_strict_mode():
    """启动时验证"""
    print("\n" + "="*80)
    print("🔴 STRICT MODE ACTIVATED - NO COMPROMISE")
    print("="*80)
    for key, value in STRICT_MODE.items():
        status = "✅ ON" if value else "❌ OFF"
        print(f"  {key}: {status}")
    print("="*80 + "\n")

def field_is_invalid(value):
    """检查字段是否无效（空、猜测、默认值等）"""
    if value is None:
        return True
    if value == '':
        return True
    if str(value).lower() in ['n/a', 'na', 'unknown', 'tbd', '待定', 'null']:
        return True
    # 检查是否是明显的合成/猜测数据
    typical_synthesis = [
        'usually', 'typically', 'generally', 'most banks',
        'as per industry standard', 'similar products',
        '通常', '一般', '大部分', '业界标准'
    ]
    for pattern in typical_synthesis:
        if pattern.lower() in str(value).lower():
            print(f"  🚨 WARNING: Possible synthesized data detected: {value[:50]}")
            return True
    return False

def enforce_all_fields(product_data):
    """强制所有字段都有有效值"""
    required_fields = [
        'COMPANY', 'LOAN_TYPE', 'REQUIRED_DOC', 'FEATURES', 'BENEFITS',
        'FEES_CHARGES', 'TENURE', 'RATE', 'APPLICATION_FORM',
        'PRODUCT_DISCLOSURE', 'TERMS_CONDITIONS', 'BORROWER_PREFERENCE'
    ]
    
    for field in required_fields:
        if field not in product_data or field_is_invalid(product_data.get(field)):
            product_data[field] = '[NO DATA FOUND]'
    
    return product_data

def audit_extraction_step(step_name, success, details):
    """审计每一步"""
    status = "✅" if success else "⚠️"
    print(f"    {status} {step_name}: {details}")

# 在主函数开始时调用
validate_strict_mode()
```

---

## 针对 Replit 的特殊语言（防止它理解成建议）

### ❌ 不要这样说（Replit会当成"可选"）：
```
"建议你进详情页抓取数据"
"通常情况下应该检查所有字段"
"如果可能的话，标记NO DATA FOUND"
```

### ✅ 要这样说（强制性）：
```
【强制性要求】MUST进详情页抓取，不是"建议"
【致命错误】如果任何字段为空，程序会崩溃并显示：FATAL ERROR
【不可妥协】如果字段找不到，MUST标记[NO DATA FOUND]，没有其他选项
【终止条件】如果检测到幻想数据，程序会自动停止并生成错误报告
```

---

## 最后的检查清单（在把脚本给Replit前确认）

- [ ] 代码中有`validate_strict_mode()`函数，在最开始调用
- [ ] 代码中有`enforce_all_fields()`函数，在每个产品完成后调用
- [ ] 代码中有详细的打印/日志，展示每一步的过程
- [ ] 代码中对每个字段都有3个备选提取方法
- [ ] 代码中有进度文件(`progress.json`)，定期保存状态
- [ ] 代码中有审计日志(`audit.json`)，记录每一步
- [ ] 代码中有最终的质量检查报告
- [ ] 代码中禁止使用`continue`跳过，每个产品必须处理完
- [ ] 代码中没有任何"if complex then use_default"的逻辑
- [ ] 指示中至少出现3次"不许"、"禁止"、"必须"这类强制性词汇

---

## 如果 Replit 还是作梗怎么办？

如果Replit仍然：
- 留空字段
- 添加假数据  
- 跳过某家公司
- 中途遗忘指示

**直接指示它：**
```
【Replit，停止】我发现你又在添加合成数据。
这次我要你：
1. 立即停止当前任务
2. 显示到目前为止提取的所有产品（CSV格式）
3. 逐行检查是否有[NO DATA FOUND]标记
4. 如果有任何空字段，程序必须报错：ERROR_EMPTY_FIELD
5. 继续时，每提取1个产品就暂停并显示日志，让我确认

如果你不按这个做，我就把任务改为手动逐行验证。
```

重点是：**让Replit知道你会查证**，它就不敢作梗了。
