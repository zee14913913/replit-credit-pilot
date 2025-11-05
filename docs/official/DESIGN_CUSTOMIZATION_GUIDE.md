# CreditPilot 外观自定义指南

**INFINITE GZ SDN. BHD.**  
**版本**: v1.0  
**最后更新**: 2025-11-05

本指南帮助您自己动手修改 CreditPilot 的外观样式，无需等待开发团队。

---

## 🎨 一次上手：3步改外观

### **步骤1: 编辑 brand.css**

打开文件：`accounting_app/static/css/brand.css`

**核心配置（调色台）**：
```css
:root {
  /* —— 颜色总开关：改这里就能全站换色 —— */
  --hot-pink:#FF007F;       /* 主色：按钮/高亮 */
  --dark-purple:#322446;    /* 次色：卡片底色/描边 */
  --deep-black:#1A1323;     /* 页面背景 */
  --snow-white:#FFFFFF;     /* 正文白 */
  --elephant:#4A4A4A;       /* 大象深灰（次要文字） */
  --light-gray:#CCCCCC;     /* 浅灰（提示/边框） */

  /* —— 字重/字号常量 —— */
  --fw-400:400; --fw-600:600; --fw-700:700; --fw-800:800;
  --fs-12:12px; --fs-14:14px; --fs-15:15px; --fs-18:18px; --fs-22:22px; --fs-28:28px;
}
```

**想换主题？** 只改 `:root` 里的 6 个颜色变量即可！

---

### **步骤2: 确保CSS已引入**

在 `templates/base.html` 的 `<head>` 中确认有这行：
```html
<link rel="stylesheet" href="/static/css/brand.css">
```

**注意**：这行要放在其他CSS后面（后加载=后覆盖）

---

### **步骤3: 使用工具类**

在HTML中直接添加类名，立即生效！

---

## 🧩 常用组件速查

### **卡片组件**
```html
<div class="card">
  <div class="title fs-18 fw-800">Loans Intelligence Center</div>
  <p class="meta ellipsis">产品列表 / 偏好情报 / DSR 试算</p>
  
  <div style="display:flex; gap:8px; flex-wrap:wrap">
    <a class="btn">Open Portal</a>
    <a class="btn primary upper">Open Compare</a>
    <a class="btn ghost text-pink">Export CSV</a>
  </div>
</div>
```

**效果**：
- 深紫渐变背景
- 粉色描边
- 标题自动大写（英文）
- 单行省略

---

### **按钮样式**

```html
<!-- 普通按钮 -->
<a class="btn">Next</a>

<!-- 主按钮（粉色） -->
<a class="btn primary">Add to Compare</a>

<!-- 线框按钮（透明底） -->
<a class="btn ghost">Cancel</a>

<!-- 英文大写按钮 -->
<a class="btn primary upper">SAVE</a>
```

---

### **文字颜色**

```html
<p class="text-pink">粉色文字</p>
<p class="text-elephant">深灰文字</p>
<p class="text-light">浅灰文字</p>
```

---

### **字号和粗细**

```html
<!-- 字号 -->
<h1 class="fs-28">超大标题 (28px)</h1>
<h2 class="fs-22">大标题 (22px)</h2>
<h3 class="fs-18">中标题 (18px)</h3>
<p class="fs-14">正文 (14px)</p>

<!-- 粗细 -->
<p class="fw-400">正常 (400)</p>
<p class="fw-600">半粗 (600)</p>
<p class="fw-700">粗体 (700)</p>
<p class="fw-800">超粗 (800)</p>

<!-- 组合使用 -->
<h1 class="fs-28 fw-800 text-pink upper">
  INFINITE GZ SDN. BHD.
</h1>
```

---

### **文本效果**

```html
<!-- 英文自动大写 -->
<p class="upper">creditpilot → CREDITPILOT</p>

<!-- 单行省略 -->
<p class="ellipsis">超长文字会自动显示省略号...</p>
```

---

## 📋 工具类速查表

### **颜色类**
| 类名 | 效果 |
|------|------|
| `.text-pink` | 粉色文字 |
| `.text-elephant` | 深灰文字 |
| `.text-light` | 浅灰文字 |
| `.border-pink` | 粉色边框 |
| `.border-purple` | 紫色边框 |

### **字号类**
| 类名 | 大小 | 用途 |
|------|------|------|
| `.fs-12` | 12px | 最小字号 |
| `.fs-14` | 14px | 正文 |
| `.fs-18` | 18px | 卡片标题 |
| `.fs-22` | 22px | 区块标题 |
| `.fs-28` | 28px | 页面主标题 |

### **字重类**
| 类名 | 粗细 | 用途 |
|------|------|------|
| `.fw-400` | 400 | 正常 |
| `.fw-600` | 600 | 半粗 |
| `.fw-700` | 700 | 粗体 |
| `.fw-800` | 800 | 超粗 |

### **效果类**
| 类名 | 效果 |
|------|------|
| `.upper` | 英文大写 |
| `.ellipsis` | 单行省略 |

---

## 🎯 6个常见需求

### **1. 改字体大小和粗细**
```html
<!-- 原来 -->
<h3>标题</h3>

<!-- 改后 -->
<h3 class="fs-22 fw-800">标题</h3>
```

---

### **2. 英文自动大写**
```html
<h1 class="upper">CreditPilot</h1>
<!-- 显示为: CREDITPILOT -->
```

---

### **3. 长标题自动省略**
```html
<div class="title ellipsis">
  非常非常长的贷款产品名称会自动显示省略号
</div>
```

---

### **4. 改卡片背景**

**方法1**: 修改 CSS 变量
```css
:root {
  --dark-purple: #your-color;  /* 改这里 */
}
```

**方法2**: 覆盖样式
```css
.card {
  background: #your-color;  /* 纯色背景 */
}
```

---

### **5. 改文字颜色**
```html
<p class="text-pink">粉色强调</p>
<p class="text-elephant">灰色次要</p>
```

---

### **6. 改边框颜色**
```html
<div class="card border-pink">更亮的粉边</div>
<div class="card border-purple">稳重的紫边</div>
```

---

## 🚀 批量提亮捷径（可选）

如果旧页面没有使用 `.card` 类，添加这段JS自动转换：

在 `templates/base.html` 底部添加：
```html
<script>
(function(){
  ['.panel','.box','.widget','.tile','.section','.module'].forEach(sel=>{
    document.querySelectorAll(sel).forEach(el=>{
      if(!el.classList.contains('card')) el.classList.add('card');
      const h = el.querySelector('h1,h2,h3');
      if(h && !h.classList.contains('title')) h.classList.add('title');
    });
  });
})();
</script>
```

---

## 🔧 常见问题

### **Q1: 改了CSS但没效果？**

**解决方法**：
1. **重启服务**: 在Replit点击 Stop → Run
2. **强制刷新**: 浏览器按 `Ctrl + Shift + R` (Mac: `Cmd + Shift + R`)
3. **检查路径**: 确认 `/static/css/brand.css` 路径正确
4. **检查引入**: 确认 base.html 已引入CSS文件

---

### **Q2: 内联样式太强，覆盖不了？**

添加 `!important`：
```css
.my-class {
  color: var(--hot-pink) !important;
}
```

---

### **Q3: 如何临时禁用某个样式？**

注释掉对应的类：
```html
<!-- 原来 -->
<div class="card border-pink">

<!-- 临时禁用 border-pink -->
<div class="card">
```

---

## 📦 "口袋卡" - 复制即用

```html
<!-- 标准卡片 -->
<div class="card">
  <div class="title fs-18 fw-800 upper ellipsis">标题</div>
  <p class="meta">说明文字</p>
  <a class="btn primary">主按钮</a>
</div>

<!-- 高亮卡片 -->
<div class="card border-pink">
  <div class="title text-pink">强调标题</div>
  <a class="btn primary upper">ACTION</a>
</div>

<!-- 数据展示 -->
<div class="kv">
  <div class="text-light">APR利率：</div>
  <div class="text-pink fw-700">3.75%</div>
</div>
```

---

## 🎨 主题配色参考

### **当前主题（INFINITE GZ）**
```css
--hot-pink:   #FF007F
--dark-purple:#322446
--deep-black: #1A1323
```

### **备选主题（示例）**
```css
/* 科技蓝 */
--hot-pink:   #00D9FF
--dark-purple:#1A2332
--deep-black: #0A0E14

/* 专业绿 */
--hot-pink:   #00FF88
--dark-purple:#1E3A32
--deep-black: #0F1A14
```

---

## 📞 需要帮助？

如果您需要更复杂的定制，请联系技术团队：
- **邮箱**: support@infinitegz.com
- **文档**: 参考 `DESIGN_TOKENS.md`

---

© INFINITE GZ SDN. BHD. 版权所有
