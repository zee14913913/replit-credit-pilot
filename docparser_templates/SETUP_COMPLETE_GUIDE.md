# 🎯 DocParser完整设置指南

## 总结：您只需做3件事（5分钟）

1. **创建1个Parser**（2分钟）
2. **配置6个字段**（2分钟）
3. **复制Parser ID**（30秒）

系统会自动处理其他所有事情！

---

## 📝 详细步骤

### 步骤1：登录DocParser

访问：https://app.docparser.com

### 步骤2：创建Parser

点击 **"Create Document Parser"**

填写：
- **Name**: `CreditPilot_Malaysia`
- **Type**: Bank Statement

### 步骤3：上传示例PDF

从这些文件中任选1个上传：

```
docparser_templates/sample_pdfs/1_AMBANK.pdf  ← 推荐这个
或者其他任何一个都可以
```

### 步骤4：配置6个字段（核心步骤）

在DocParser界面上，**用鼠标点击PDF上的数字**，然后输入字段名：

| 点击PDF上的什么 | 输入字段名 | 示例值 |
|----------------|-----------|--------|
| 卡号后4位 | `card_number` | 6354 |
| 账单日期 | `statement_date` | 2025-06-01 |
| Previous Balance | `previous_balance` | 861.17 |
| Total Purchases | `total_debit` | 8147.54 |
| Total Payments | `total_credit` | 0.00 |
| Current Balance | `current_balance` | 9008.71 |

**提示**：
- 字段名必须完全一致（包括大小写）
- 点击数字后会出现输入框
- 输入字段名后按回车保存

### 步骤5：保存并测试

点击 **"Test Parser"** 确认提取正确

### 步骤6：获取Parser ID

1. 点击 **Settings** → **API**
2. 复制 **Parser ID**（类似：`odnzsomkbyeh`）
3. 保存到环境变量：

```bash
export DOCPARSER_PARSER_ID=你的Parser_ID
```

---

## ✅ 配置验证

运行测试：

```bash
python3 test_docparser_integration.py
```

应该看到：

```
✅ 上传成功，文档ID: xxx
✅ 解析完成（耗时5秒）
✅ 识别银行: AMBANK
```

---

## 🎉 完成！

配置完成后，系统支持：

✅ **上传任意银行的PDF** → 自动识别银行
✅ **批量上传42个PDF** → 自动分类归档
✅ **零手动操作** → 完全自动化

---

## 📊 为什么只需要1个Parser？

### 传统方案（不推荐）
- 需要创建7个Parser（每个银行1个）
- 上传PDF时需要手动选择Parser
- 新增银行需要创建新Parser

### 我们的方案（智能）
- 只需1个通用Parser
- **AI自动识别**银行名称（从PDF文本中）
- 新增银行无需任何配置

---

## ❓ 常见问题

### Q: 我配置错了怎么办？
**A**: 点击 "Edit Parsing Rules" 重新调整字段位置即可

### Q: 字段名必须一样吗？
**A**: 是的，必须完全一致（包括大小写和下划线）

### Q: 如果识别错误怎么办？
**A**: 系统会提示，您可以手动选择正确的银行

---

需要帮助？运行 `python3 test_docparser_integration.py` 查看详细错误信息！
