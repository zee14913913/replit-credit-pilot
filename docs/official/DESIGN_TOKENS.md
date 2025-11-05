# CreditPilot Design Tokens

**INFINITE GZ SDN. BHD.**  
**版本**: v2.0  
**最后更新**: 2025-11-05

本文档定义了 CreditPilot 系统的所有设计令牌（Design Tokens），确保品牌一致性和开发效率。

---

## 🎨 品牌颜色（Brand Colors）

### **主色调**
```css
--hot-pink:   #FF007F    /* Hot Pink 主色 - 按钮、链接、强调 */
--dark-purple:#322446    /* 深紫 - 卡片、边框、次色 */
--deep-black: #1A1323    /* 深底色 - 页面背景 */
```

### **辅助颜色**
```css
--snow-white: #FFFFFF    /* 莹白色 - 文字、图标 */
--elephant:   #4A4A4A    /* 大象深灰 - 次要文字 */
--light-gray: #CCCCCC    /* 浅灰 - 辅助文字 */
```

### **透明度变体**
```css
--pink-20:    #FF007F33  /* 20% 透明粉 - 边框 */
--pink-40:    #FF007F66  /* 40% 透明粉 - 悬停 */
--purple-40:  #32244666  /* 40% 透明紫 - 边框 */
```

---

## 📝 字体规范（Typography）

### **字重（Font Weights）**
```css
--fw-regular: 400        /* 正文 */
--fw-medium:  500        /* 次要标题 */
--fw-semi:    600        /* 卡片标题 */
--fw-bold:    700        /* 页面标题 */
--fw-black:   800        /* 超大标题 */
```

### **字号（Font Sizes）**
```css
--fs-xxs: 11px          /* 最小 - 角标、提示 */
--fs-xs:  12px          /* 小号 - 辅助信息 */
--fs-sm:  13px          /* 正文小号 - 表格、列表 */
--fs-md:  15px          /* 标准 - 卡片标题、按钮 */
--fs-lg:  18px          /* 大号 - 区块标题 */
--fs-xl:  22px          /* 超大 - 页面副标题 */
--fs-xxl: 28px          /* 巨大 - 页面主标题、得分 */
```

### **行高（Line Heights）**
```css
--lh-tight: 1.2         /* 紧凑 - 标题 */
--lh-normal: 1.45       /* 标准 - 正文 */
--lh-relax: 1.65        /* 宽松 - 长段落 */
```

---

## 🧩 工具类（Utility Classes）

### **颜色工具类**

#### **文字颜色**
```html
<span class="text-pink">Hot Pink文字</span>
<span class="text-purple">深紫文字</span>
<span class="text-white">白色文字</span>
<span class="text-elephant">深灰文字</span>
<span class="text-light">浅灰文字</span>
```

#### **背景颜色**
```html
<div class="bg-pink">粉色背景</div>
<div class="bg-purple">紫色背景</div>
<div class="bg-black">黑色背景</div>
```

#### **边框颜色**
```html
<div class="border-pink">粉色边框</div>
<div class="border-pink-20">20%透明粉边框</div>
<div class="border-purple">紫色边框</div>
```

---

### **排版工具类**

#### **字重**
```html
<p class="fw-400">正常粗细 (400)</p>
<p class="fw-500">中等粗细 (500)</p>
<p class="fw-600">半粗 (600)</p>
<p class="fw-700">粗体 (700)</p>
<p class="fw-800">超粗 (800)</p>
```

#### **字号**
```html
<p class="fs-xxs">超小字号 (11px)</p>
<p class="fs-xs">小字号 (12px)</p>
<p class="fs-sm">正文小号 (13px)</p>
<p class="fs-md">标准字号 (15px)</p>
<p class="fs-lg">大字号 (18px)</p>
<p class="fs-xl">超大字号 (22px)</p>
<p class="fs-xxl">巨大字号 (28px)</p>
```

#### **行高**
```html
<p class="lh-tight">紧凑行高 (1.2)</p>
<p class="lh-normal">标准行高 (1.45)</p>
<p class="lh-relax">宽松行高 (1.65)</p>
```

#### **文本转换**
```html
<p class="tt-upper">UPPERCASE 全大写</p>
<p class="tt-cap">Capitalize 首字母大写</p>
<p class="tt-normal">normal case 正常</p>
```

#### **文本溢出**
```html
<p class="ellipsis">超长文字会自动显示省略号...</p>
```

---

## 🎯 组件样式（Components）

### **卡片（Card）**
```html
<div class="card">
  <div class="card-title">卡片标题</div>
  <p>卡片内容</p>
</div>
```

**CSS定义**：
```css
.card {
  background: linear-gradient(180deg, #322446, #281a3a);
  border: 1px solid #FF007F33;
  border-radius: 14px;
  padding: 18px;
  box-shadow: 0 6px 22px rgba(0, 0, 0, .25);
}
```

---

### **按钮（Button）**

#### **标准按钮**
```html
<button class="btn">普通按钮</button>
<button class="btn primary">主要按钮</button>
<button class="btn ghost">幽灵按钮</button>
```

#### **带工具类的按钮**
```html
<button class="btn primary fw-600 fs-md">粗体中号按钮</button>
<button class="btn tt-upper">UPPERCASE BUTTON</button>
```

---

### **徽章 & 标签**

```html
<span class="badge">徽章</span>
<span class="tag">标签</span>
```

---

## 📐 布局系统（Layout）

### **容器**
```html
<div class="container">
  <!-- 最大宽度 1200px，自动居中 -->
</div>
```

### **网格**
```html
<!-- 两列网格 -->
<div class="grid grid-cols-2">
  <div>左列</div>
  <div>右列</div>
</div>

<!-- 三列网格 -->
<div class="grid grid-cols-3">
  <div>列1</div>
  <div>列2</div>
  <div>列3</div>
</div>
```

---

## 💡 使用示例

### **示例1: 页面标题**
```html
<h1 class="fs-xxl fw-800 text-pink tt-upper ellipsis">
  INFINITE GZ SDN. BHD.
</h1>
<p class="text-elephant fs-sm">Smart Credit & Loan Manager</p>
```

### **示例2: 卡片组件**
```html
<div class="card">
  <div class="card-title tt-upper ellipsis">
    Loans Intelligence Center
  </div>
  <p class="fs-sm text-light lh-normal">
    最新更新：2025-11-06
  </p>
  
  <button class="btn primary fw-600 fs-md">
    Add to Compare
  </button>
  <button class="btn" style="margin-left:8px;">
    Export CSV
  </button>
</div>
```

### **示例3: 数据展示**
```html
<div class="kv">
  <div class="text-light">APR利率：</div>
  <div class="text-pink fw-700">3.75%</div>
  
  <div class="text-light">DSR得分：</div>
  <div class="text-white fw-700">96.25</div>
</div>
```

---

## 🔧 文件位置

**主文件**: `accounting_app/static/css/brand.css`

**引用方式**:
```html
<link rel="stylesheet" href="/static/css/brand.css">
```

---

## 📊 设计原则

### **1. 一致性优先**
- 所有颜色使用 CSS 变量，不要硬编码
- 字号使用预定义的 `--fs-*` 变量
- 间距使用 8px 倍数（8, 12, 16, 24...）

### **2. 性能优化**
- 工具类使用 `!important` 确保优先级
- 减少嵌套选择器
- 合理使用 CSS Grid 和 Flexbox

### **3. 响应式设计**
- 移动端自动切换单列布局
- 字号在小屏幕适当缩小
- 保持触摸目标 ≥ 44px

---

## 🎨 品牌应用场景

| 颜色 | 用途 | 示例 |
|------|------|------|
| Hot Pink (#FF007F) | 主要按钮、链接、强调文字 | "Add to Compare"按钮 |
| Dark Purple (#322446) | 卡片背景、边框、次要按钮 | 贷款产品卡片 |
| Deep Black (#1A1323) | 页面背景 | 全局背景 |
| Snow White (#FFFFFF) | 主要文字、图标 | 正文内容 |
| Elephant (#4A4A4A) | 次要文字、说明 | "最后更新时间" |
| Light Gray (#CCCCCC) | 辅助文字、禁用状态 | 表单占位符 |

---

## 📞 联系方式

**设计系统维护**: INFINITE GZ SDN. BHD. 技术团队  
**更新频率**: 每季度审查  
**反馈渠道**: support@infinitegz.com

---

© INFINITE GZ SDN. BHD. 版权所有
