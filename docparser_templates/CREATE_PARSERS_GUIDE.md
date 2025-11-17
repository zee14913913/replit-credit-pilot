# 🚀 DocParser自动创建7个银行Parser - 操作指南

## ⚠️ 重要说明
由于DocParser不支持API自动创建Parser，我已经为您准备好所有材料，您只需要**复制粘贴**即可完成。

---

## 📁 已准备好的材料

| 文件/文件夹 | 说明 |
|------------|------|
| `sample_pdfs/` | 7个示例PDF文件（已命名好） |
| `PARSER_FIELD_RULES.md` | 详细的字段提取规则 |
| 本文档 | 一步步操作指南 |

---

## 🎯 创建Parser的3个步骤（每个银行重复7次）

### 第1步：打开DocParser并创建新Parser
1. 打开浏览器访问: https://app.docparser.com
2. 登录您的账户
3. 点击右上角 **"Create Document Parser"** 按钮
4. 选择模版: **"Bank Statement"** （或 "Blank Template"）
5. 点击 **"Create Parser"**

### 第2步：设置Parser名称并上传示例
| 银行 | Parser名称（复制这个） | 上传文件 |
|------|---------------------|---------|
| AmBank | `AMBANK` | 1_AMBANK.pdf |
| AmBank Islamic | `AMBANK_ISLAMIC` | 2_AMBANK_ISLAMIC.pdf |
| Standard Chartered | `STANDARD_CHARTERED` | 3_STANDARD_CHARTERED.pdf |
| UOB | `UOB` | 4_UOB.pdf |
| Hong Leong | `HONG_LEONG` | 5_HONG_LEONG.pdf |
| OCBC | `OCBC` | 6_OCBC.pdf |
| HSBC | `HSBC` | 7_HSBC.pdf |

1. 在 **"Parser Name"** 输入框中，复制粘贴上面对应的名称
2. 点击 **"Upload Document"** 按钮
3. 选择对应的示例PDF文件上传
4. 等待上传完成

### 第3步：配置字段提取规则（自动设置）
DocParser会自动识别银行账单的常见字段。您需要确保以下字段存在：

**必需字段（如果没有，手动添加）：**
- `statement_date` - 账单日期
- `card_number` - 卡号后4位
- `previous_balance` - 上期结余
- `current_balance` - 本期结余
- `transactions` - 交易明细表（Table格式）

**配置交易明细表：**
1. 找到PDF中的交易记录表格
2. 点击表格，DocParser会自动识别
3. 确保包含以下列：
   - `date` - 日期
   - `description` - 描述
   - `amount` - 金额

4. 点击 **"Save"** 保存配置

### 第4步：记录Parser ID
1. 创建完成后，进入Parser设置页面
2. 点击左侧菜单的 **"Settings"** → **"API"**
3. 复制 **Parser ID**（类似：mwekrupomwekrupo）
4. 记录到下面的表格中

---

## 📝 Parser ID记录表（填写这个！）

| 序号 | 银行 | Parser名称 | Parser ID | 完成 |
|------|------|-----------|-----------|------|
| 1 | AmBank | AMBANK | `_____________` | ⬜ |
| 2 | AmBank Islamic | AMBANK_ISLAMIC | `_____________` | ⬜ |
| 3 | Standard Chartered | STANDARD_CHARTERED | `_____________` | ⬜ |
| 4 | UOB | UOB | `_____________` | ⬜ |
| 5 | Hong Leong | HONG_LEONG | `_____________` | ⬜ |
| 6 | OCBC | OCBC | `_____________` | ⬜ |
| 7 | HSBC | HSBC | `_____________` | ⬜ |

---

## ⏱️ 预计时间
- 每个Parser: 3-5分钟
- 总共7个: **25-35分钟**

---

## ✅ 完成后
将7个Parser ID告诉我，我会自动配置系统！

系统将自动实现：
```
客户上传PDF → 自动识别银行 → 调用对应Parser → 解析数据 → 分类入库
```

---

## 🆘 遇到问题？

### 问题1：找不到 "Create Document Parser" 按钮
**解决**: 确保您已登录DocParser账户，按钮在页面右上角

### 问题2：上传PDF失败
**解决**: 确保PDF文件小于10MB，格式正确

### 问题3：无法找到Parser ID
**解决**: 进入Parser → Settings → API，Parser ID就在页面顶部

### 问题4：字段提取不准确
**解决**: 不用担心！我们后续可以手动调整字段位置

---

## 💡 温馨提示
- 创建Parser时不需要100%完美，后续可以随时调整
- 示例PDF文件都在 `./docparser_templates/sample_pdfs/` 文件夹中
- 完成一个就勾选一个，避免重复创建

开始吧！💪
