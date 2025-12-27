# 三语切换功能使用说明

## 已完成的功能

### 1. 基础架构
- ✅ 语言上下文 (LanguageContext)
- ✅ 翻译文件 (translations.ts)
- ✅ 语言切换器组件 (LanguageSwitcher)
- ✅ Header 导航多语言支持

### 2. 支持的语言
- 🇬🇧 English (en)
- 🇨🇳 中文 (zh)
- 🇲🇾 Bahasa Malaysia (ms)

### 3. 已完成翻译的内容
- 导航菜单 (所有8个链接)
- 常用按钮文本 (Get Started, Learn More, etc.)
- 所有页面的基础内容结构

## 如何在页面中使用

### 示例：更新任何页面使用翻译

```typescript
'use client';

import { useLanguage } from '@/contexts/LanguageContext';

export default function SomePage() {
  const { t } = useLanguage();

  return (
    <div>
      <h1>{t.solutions.hero.title}</h1>
      <p>{t.solutions.hero.description}</p>
      <button>{t.common.getStarted}</button>
    </div>
  );
}
```

## 下一步需要做的事情

为了完全实现三语切换，需要将现有页面改为使用翻译：

### 需要更新的页面
1. ❌ /app/page.tsx (首页)
2. ❌ /app/solutions/page.tsx
3. ❌ /app/creditpilot/page.tsx
4. ❌ /app/advisory/page.tsx
5. ❌ /app/company/page.tsx
6. ❌ /app/news/page.tsx
7. ❌ /app/resources/page.tsx
8. ❌ /app/careers/page.tsx

### 更新步骤
1. 添加 'use client' 指令
2. 导入 useLanguage hook
3. 将所有硬编码文本替换为 t.xxx.xxx
4. 测试所有三种语言的显示效果

## 当前状态
- ✅ Header 导航已完成三语支持
- ✅ 语言切换器已添加到 Header
- ⏳ 页面内容等待更新

