# 新闻内容管理指南 / News Content Management Guide

## 📋 概述 / Overview

新闻内容现在通过 JSON 文件管理，支持自动三语切换。

News content is now managed through a JSON file with automatic trilingual support.

---

## 📁 文件位置 / File Location

**新闻数据文件 / News Data File:**
```
data/news.json
```

**加载器文件 / Loader File:**
```
lib/newsLoader.ts
```

---

## ✏️ 如何添加新闻 / How to Add News

### 方法1：直接编辑 JSON 文件 (推荐)

1. 打开 `data/news.json`
2. 在 `items` 数组中添加新条目：

```json
{
  "id": "news-007",
  "date": "2024-12",
  "title": {
    "en": "Your English Title",
    "zh": "你的中文标题",
    "ms": "Tajuk Bahasa Melayu Anda"
  },
  "category": {
    "en": "Category",
    "zh": "分类",
    "ms": "Kategori"
  },
  "description": {
    "en": "English description",
    "zh": "中文描述",
    "ms": "Penerangan Bahasa Melayu"
  }
}
```

3. 保存文件
4. 重启开发服务器或重新构建：`npm run build`

---

## 🔄 自动化流程 / Automated Workflow

### 当前流程：
1. ✅ **添加新闻** - 编辑 `data/news.json`
2. ✅ **自动加载** - 页面自动读取 JSON
3. ✅ **自动切换** - 根据语言选择显示对应翻译
4. ❌ **自动翻译** - 目前需要手动提供三语翻译

### 未来优化（可选实现）：

#### 选项A：使用翻译API自动翻译
```bash
# 只需提供英文，自动翻译为中文和马来文
npm run translate-news
```

#### 选项B：集成CMS系统
- Strapi / Sanity / Contentful
- 提供管理界面
- 支持自动翻译
- 版本控制

#### 选项C：使用数据库
- MongoDB / PostgreSQL
- 动态更新
- 无需重新部署

---

## 📝 新闻类别参考 / News Categories Reference

| 英文 (EN) | 中文 (ZH) | 马来文 (MS) |
|-----------|-----------|-------------|
| Milestone | 里程碑 | Pencapaian |
| Product | 产品 | Produk |
| Case Study | 案例研究 | Kajian Kes |
| Partnership | 合作 | Perkongsian |
| Recognition | 荣誉 | Pengiktirafan |
| Growth | 增长 | Pertumbuhan |
| Policy Update | 政策更新 | Kemas Kini Dasar |
| Financial Tips | 财务提示 | Petua Kewangan |
| Guide | 指南 | Panduan |

---

## 🔧 技术架构 / Technical Architecture

```
用户访问 /news 页面
    ↓
NewsPage 组件加载
    ↓
调用 getNews(language)
    ↓
从 data/news.json 读取数据
    ↓
根据当前语言筛选翻译
    ↓
渲染新闻卡片
```

### API Functions:

```typescript
// 获取指定语言的新闻列表
getNews(language: 'en' | 'zh' | 'ms'): LocalizedNewsItem[]

// 获取所有新闻（含所有语言版本）
getAllNews(): NewsItem[]

// 根据ID获取单条新闻
getNewsById(id: string, language: 'en' | 'zh' | 'ms'): LocalizedNewsItem | null
```

---

## ✅ 优势 / Advantages

1. **✓ 自动三语切换** - 无需修改代码
2. **✓ 集中管理** - 所有新闻在一个文件
3. **✓ 类型安全** - TypeScript 类型检查
4. **✓ 易于维护** - JSON 格式简单易读
5. **✓ 无需数据库** - 静态部署友好
6. **✓ 版本控制** - Git 追踪所有变更

---

## 🚀 下一步优化建议 / Next Steps

### 优先级 High:
- [ ] 添加自动翻译脚本（使用 Google Translate API）
- [ ] 添加新闻详情页面
- [ ] 添加日期格式化

### 优先级 Medium:
- [ ] 添加分类筛选功能
- [ ] 添加搜索功能
- [ ] 添加分页

### 优先级 Low:
- [ ] 集成 CMS 系统
- [ ] 添加图片支持
- [ ] RSS 订阅

---

## 📞 需要帮助？ / Need Help?

如果遇到问题，请检查：
1. JSON 格式是否正确（使用 JSON 验证器）
2. 所有必需字段是否存在（id, date, title, category, description）
3. 每个字段是否包含三种语言（en, zh, ms）
4. ID 是否唯一

---

**最后更新 / Last Updated:** 2024-12-27
