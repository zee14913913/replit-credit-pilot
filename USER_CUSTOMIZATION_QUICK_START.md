# 🎨 快速自定义指南

**3分钟学会改CreditPilot外观**

---

## 📝 改哪个文件？

```
accounting_app/static/css/brand.css
```

---

## 🎯 最常改的3件事

### **1. 换主题颜色**

打开 `brand.css`，找到这段：
```css
:root {
  --hot-pink:#FF007F;       /* 主色 */
  --dark-purple:#322446;    /* 次色 */
  --deep-black:#1A1323;     /* 背景 */
}
```

**改成你想要的颜色**，保存即可！

---

### **2. 改标题大小**

在HTML中添加类名：
```html
<!-- 小标题 -->
<h3 class="fs-18">标题</h3>

<!-- 大标题 -->
<h1 class="fs-28 fw-800">标题</h1>

<!-- 超大标题 -->
<h1 class="fs-28 fw-800 text-pink upper">标题</h1>
```

---

### **3. 改按钮样式**

```html
<!-- 普通按钮 -->
<button class="btn">按钮</button>

<!-- 粉色主按钮 -->
<button class="btn primary">按钮</button>

<!-- 透明线框按钮 -->
<button class="btn ghost">按钮</button>
```

---

## 🚀 常用类速查

| 类名 | 效果 |
|------|------|
| `fs-14` | 14px字号 |
| `fs-18` | 18px字号 |
| `fs-28` | 28px字号 |
| `fw-700` | 粗体 |
| `fw-800` | 超粗 |
| `text-pink` | 粉色文字 |
| `upper` | 英文大写 |
| `ellipsis` | 单行省略 |

---

## 💡 完整示例

```html
<div class="card">
  <div class="title fs-22 fw-800 text-pink upper">
    Loans Center
  </div>
  <p class="fs-14 text-light">
    最新产品推荐
  </p>
  <button class="btn primary fw-600">
    查看详情
  </button>
</div>
```

---

## 🔧 改完没效果？

1. **Replit**: 点击 Stop → Run
2. **浏览器**: 按 `Ctrl + Shift + R` 强制刷新

---

**详细文档**: 查看 `docs/official/DESIGN_CUSTOMIZATION_GUIDE.md`

© INFINITE GZ SDN. BHD.
