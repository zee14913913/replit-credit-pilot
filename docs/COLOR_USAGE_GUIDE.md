# CreditPilot Color Usage Guide

**Official Color Standards for the Entire System**

Version: 2.0.0  
Last Updated: 2025-11-17  
Status: **MANDATORY** for all development

---

## 📌 Core Principle

**CreditPilot uses a MINIMAL 3-COLOR PALETTE ONLY for Web UI.**

This is not a suggestion - it's a **mandatory requirement** enforced by code review and automated checks.

---

## 🎨 The Official 3-Color Palette

### 1. Black (#000000)
- **Purpose**: Primary background color
- **Usage**: All page backgrounds, dark mode base
- **Python**: `COLORS.core.black`
- **CSS**: `var(--color-black)`

### 2. Hot Pink (#FF007F)
- **Purpose**: Primary accent color
- **Usage**: Buttons, links, revenue, income, credits, highlights
- **Python**: `COLORS.core.hot_pink`
- **CSS**: `var(--color-hot-pink)`

### 3. Dark Purple (#322446)
- **Purpose**: Secondary accent color
- **Usage**: Borders, expenses, debits, secondary buttons
- **Python**: `COLORS.core.dark_purple`
- **CSS**: `var(--color-dark-purple)`

### 4. White (#FFFFFF)
- **Purpose**: Primary text color
- **Usage**: Text on dark backgrounds
- **Python**: `COLORS.core.white`
- **CSS**: `var(--color-white)`

---

## ✅ Status Colors (Functional Only)

These are the ONLY non-core colors allowed in Web UI:

| Color | Hex | Purpose | Python | CSS |
|-------|-----|---------|--------|-----|
| **Success** | #00ff87 | Success messages, 'Excellent' grade | `COLORS.status.success` | `var(--color-success)` |
| **Warning** | #ffcc00 | Warning messages, 'Good' grade | `COLORS.status.warning` | `var(--color-warning)` |
| **Error** | #ff4444 | Error messages, 'Poor' grade | `COLORS.status.error` | `var(--color-error)` |
| **Info** | #1e40af | Informational messages | `COLORS.status.info` | `var(--color-info)` |

---

## 📁 Excel Report Colors (Separate System)

Excel reports use a **different color scheme** optimized for printing:

| Color | Hex | Purpose |
|-------|-----|---------|
| **Main Pink** | #FFB6C1 | Headers, highlights |
| **Deep Brown** | #3E2723 | Text, borders |
| **Pure White** | #FFFFFF | Backgrounds |

**Important**: These colors are ONLY for Excel reports, never for Web UI!

---

## 🚫 Prohibited Colors (DEPRECATED)

These colors are **NO LONGER ALLOWED**:

| Color | Hex | Old Usage | Replacement |
|-------|-----|-----------|-------------|
| **Silver** | #C0C0C0 | Galaxy Theme | → `var(--color-hot-pink)` |
| **Gold** | #D4AF37 | Loan system accent | → `var(--color-hot-pink)` |
| **Gold (alt)** | #FFD700 | Loan highlights | → `var(--color-hot-pink)` |
| **Orange-red** | #FF5722 | Monthly reports | → `var(--color-hot-pink)` |
| **Orange** | #FF7043 | Email templates | → `var(--color-hot-pink)` |

---

## 💻 Usage in Different File Types

### Python Files (.py)

**❌ WRONG** (Hardcoded colors):
```python
COLOR_BLACK = colors.HexColor('#000000')
COLOR_HOT_PINK = colors.HexColor('#FF007F')
primary_color = '#FF007F'
```

**✅ CORRECT** (Import from config):
```python
from config.colors import COLORS

COLOR_BLACK = colors.HexColor(COLORS.core.black)
COLOR_HOT_PINK = colors.HexColor(COLORS.core.hot_pink)
primary_color = COLORS.core.hot_pink
```

**Shortcuts Available**:
```python
from config.colors import COLOR_BLACK, COLOR_HOT_PINK, COLOR_DARK_PURPLE
```

---

### CSS Files (.css)

**Step 1**: Import color variables at the top of your CSS file:
```css
@import url('/static/css/colors.css');
```

**Step 2**: Use CSS variables

**❌ WRONG** (Hardcoded):
```css
.button {
  background: #FF007F;
  border: 1px solid #322446;
  color: #FFFFFF;
}
```

**✅ CORRECT** (CSS variables):
```css
.button {
  background: var(--color-hot-pink);
  border: var(--border-primary);
  color: var(--color-white);
}
```

**Predefined Classes** (Use these when possible):
```css
.btn-primary    /* Hot pink button */
.btn-secondary  /* Dark purple button */
.btn-dark       /* Black button with pink border */
.btn-outline    /* Transparent with pink border */

.card-primary   /* Black card with purple border */
.card-accent    /* Black card with pink border */

.badge-success  /* Green success badge */
.badge-warning  /* Yellow warning badge */
.badge-error    /* Red error badge */
```

---

### HTML Templates (.html)

**Step 1**: Include color stylesheet in `<head>`:
```html
<link rel="stylesheet" href="/static/css/colors.css">
```

**Step 2**: Use CSS variables in inline styles

**❌ WRONG** (Hardcoded):
```html
<div style="background: #000000; color: #FF007F;">
  <h1 style="color: #FF007F;">Title</h1>
</div>
```

**✅ CORRECT** (CSS variables):
```html
<div style="background: var(--color-black); color: var(--color-hot-pink);">
  <h1 style="color: var(--color-hot-pink);">Title</h1>
</div>
```

**Better** (Use classes):
```html
<div class="card-accent">
  <h1 class="text-accent">Title</h1>
</div>
```

---

## 🎯 Common Scenarios

### Scenario 1: Creating a New Button

**Wrong Approach**:
```css
.my-button {
  background: #FF007F;
  color: white;
}
```

**Right Approach**:
```html
<button class="btn-primary">Click Me</button>
```

Or if custom styling needed:
```css
.my-button {
  background: var(--color-hot-pink);
  color: var(--color-white);
  /* Add your custom spacing, sizing, etc. */
}
```

---

### Scenario 2: Email Template Colors

**Wrong Approach**:
```python
html = f"""
<body style="background: #FF5722;">
  <h1 style="color: #FF7043;">Title</h1>
</body>
"""
```

**Right Approach**:
```python
from config.colors import COLORS

html = f"""
<body style="background: {COLORS.core.hot_pink};">
  <h1 style="color: {COLORS.core.white};">Title</h1>
</body>
"""
```

---

### Scenario 3: PDF Report Colors

**Wrong Approach**:
```python
title_color = colors.HexColor('#FF007F')
```

**Right Approach**:
```python
from config.colors import COLORS
from reportlab.lib import colors

title_color = colors.HexColor(COLORS.core.hot_pink)
```

---

### Scenario 4: Conditional Colors

**Wrong Approach**:
```python
if status == 'success':
    color = '#00ff87'
elif status == 'error':
    color = '#ff4444'
```

**Right Approach**:
```python
from config.colors import COLORS

if status == 'success':
    color = COLORS.status.success
elif status == 'error':
    color = COLORS.status.error
```

---

## 🔍 Automated Compliance Checking

Run the color compliance checker regularly:

```bash
# Check all files
python3 scripts/check_color_compliance.py

# Check specific directory
python3 scripts/check_color_compliance.py --path static/css

# Generate detailed report
python3 scripts/check_color_compliance.py --detailed
```

The script will:
- ✅ Scan all .py, .css, and .html files
- ✅ Find hardcoded hex color values
- ✅ Identify deprecated colors
- ✅ Provide fix recommendations

---

## 📋 Checklist for New Features

Before submitting code for review:

- [ ] No hardcoded hex colors in Python files
- [ ] No hardcoded hex colors in CSS files
- [ ] No hardcoded hex colors in HTML files
- [ ] All colors imported from `config.colors` (Python)
- [ ] All colors use CSS variables (CSS/HTML)
- [ ] No deprecated colors (gold, silver, orange-red)
- [ ] Color compliance check passes: `python3 scripts/check_color_compliance.py`

---

## ❓ FAQ

### Q: Can I add a new color for a special feature?

**A:** No. Use the existing 3-color palette. If absolutely necessary, propose the change to the team and update `config/colors.json` first.

### Q: What about gradients?

**A:** Use predefined gradients:
- Python: `COLORS.gradients.primary_gradient`
- CSS: `var(--gradient-primary)`

### Q: What about hover states?

**A:** Use predefined hover colors:
- CSS: `var(--color-hot-pink-hover)`, `var(--color-dark-purple-hover)`

### Q: Can I use opacity/transparency?

**A:** Yes! You can use `rgba()` or opacity:
```css
background: rgba(255, 0, 127, 0.5);  /* Hot pink at 50% opacity */
opacity: 0.8;
```

But prefer CSS variables with opacity:
```css
background: var(--color-hot-pink);
opacity: 0.5;
```

### Q: What about chart colors?

**A:** For charts/graphs, use:
1. Primary: Hot pink (#FF007F)
2. Secondary: Dark purple (#322446)
3. Success: Success green (#00ff87)
4. Warning: Warning yellow (#ffcc00)
5. Error: Error red (#ff4444)

---

## 🚨 Enforcement

**This is not optional.**

- ❌ Pull requests with hardcoded colors will be **rejected**
- ❌ Code review will check for compliance
- ✅ Automated checks run on every commit
- ✅ CI/CD pipeline includes color compliance validation

---

## 📚 Related Documentation

- **Color Configuration**: `config/colors.json`
- **Python Color Module**: `config/colors.py`
- **CSS Variables**: `static/css/colors.css`
- **Compliance Checker**: `scripts/check_color_compliance.py`
- **Color Audit Report**: `docs/color_audit_report.md`

---

## 💡 Questions?

If you need help with color implementation:
1. Check this guide first
2. Run `python3 config/colors.py` to see all available colors
3. Run `python3 scripts/check_color_compliance.py` to check your code
4. Ask the development team

---

**Remember**: Consistent colors = Professional brand = Happy customers! 🎨✨
