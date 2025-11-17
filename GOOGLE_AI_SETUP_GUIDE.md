# Google Document AI 认证设置指南

## ⚠️ 重要：Google Document AI需要Service Account认证

Google Document AI **不支持简单的API Key**，必须使用**Service Account JSON文件**进行认证。

---

## 📋 两个选择

### 选项A：完成Google Cloud设置（需要15分钟）

如果您想继续使用Google Document AI，需要完成以下步骤：

#### 1. 创建Service Account

1. 访问：https://console.cloud.google.com/iam-admin/serviceaccounts
2. 选择您的项目：`famous-tre...`（您的GOOGLE_PROJECT_ID）
3. 点击 **"CREATE SERVICE ACCOUNT"**
4. 填写：
   - Name: `document-ai-service`
   - Role: **Document AI API User**
5. 点击 **"CREATE KEY"**
6. 选择 **JSON** 格式
7. 下载JSON文件

#### 2. 上传JSON到Replit

1. 在Replit项目中创建 `service_account.json` 文件
2. 将下载的JSON内容粘贴进去

#### 3. 设置环境变量

```bash
export GOOGLE_APPLICATION_CREDENTIALS=service_account.json
```

或者将JSON内容设置为Secret：
```
GOOGLE_SERVICE_ACCOUNT_JSON = {完整JSON内容}
```

#### 4. 测试

```bash
python3 test_google_ai.py
```

---

### 选项B：改用DocParser（推荐⭐，仅需5分钟）

**更简单、更快、更可靠的方案**

#### 为什么推荐DocParser？

| 对比项 | Google Document AI | DocParser |
|--------|-------------------|-----------|
| **认证复杂度** | ❌ 需要Service Account JSON | ✅ 仅需API Key（已设置） |
| **设置时间** | ⚠️ 15-30分钟 | ✅ 5分钟 |
| **准确度** | 98-99.9% | 95-99% |
| **维护成本** | 需要管理JSON密钥 | 零维护 |
| **月成本** | 基本免费（<1000页） | $49-$99 |

#### DocParser设置（5分钟）

1. 访问 https://app.docparser.com
2. 创建1个Parser
3. 配置6个字段（用鼠标点击PDF）
4. 复制Parser ID到环境变量

详细步骤：
```bash
cat docparser_templates/VISUAL_GUIDE.txt
```

---

## 🎯 我的建议

### 如果您：

**✅ 想快速上线** → 选择DocParser
- 我已准备好所有材料
- 您只需5分钟配置
- 立即可用

**⚠️ 已有GCP Service Account** → 继续Google AI
- 提供Service Account JSON
- 我帮您完成集成

**❓ 不确定** → 先用DocParser
- 快速验证概念
- 之后可切换到Google AI

---

## 💡 推荐方案：DocParser

**原因**：
1. ✅ 您的API Key已经设置好（DOCPARSER_API_KEY）
2. ✅ 我已准备好所有代码和指南
3. ✅ 95-99%准确度足够满足需求
4. ✅ 5分钟即可上线

**下一步**：
```bash
# 查看可视化设置指南
cat docparser_templates/VISUAL_GUIDE.txt

# 配置完成后测试
python3 test_docparser_integration.py
```

---

## ❓ 您的决定

请告诉我：

**A. 提供Google Service Account JSON**
   - 我帮您完成Google AI集成

**B. 改用DocParser**（推荐）
   - 5分钟上线，我已准备好一切

**C. 暂停，先了解更多**
   - 我详细解释两者区别
