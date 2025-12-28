# Hero Banner 视频使用说明

## 如何添加视频背景

### 方法 1：修改代码中的 videoUrl

打开 `components/Hero.tsx`，找到第 16 行：

```typescript
const videoUrl = '' // 留空表示不显示视频
```

改为：

```typescript
const videoUrl = '/videos/hero-bg.mp4' // 你的视频路径
```

或使用外部 URL：

```typescript
const videoUrl = 'https://your-cdn.com/video.mp4'
```

### 方法 2：视频文件放置位置

1. 在项目根目录创建 `public/videos` 文件夹
2. 将视频文件放入该文件夹，例如：
   - `public/videos/hero-bg.mp4`
3. 在代码中引用：`const videoUrl = '/videos/hero-bg.mp4'`

### 视频要求

**推荐规格：**
- 分辨率：1920x1080 或更高（支持超大屏）
- 格式：MP4 (H.264)
- 时长：10-30秒（循环播放）
- 文件大小：< 10MB（优化加载速度）

**编码建议：**
```bash
# 使用 ffmpeg 优化视频
ffmpeg -i input.mp4 -vcodec h264 -acodec aac -b:v 2M output.mp4
```

### 功能特性

✅ **自动播放** - 页面加载后自动播放
✅ **循环播放** - 视频结束后自动重播
✅ **静音播放** - 默认静音（符合浏览器自动播放策略）
✅ **全屏覆盖** - object-cover 确保填满整个屏幕
✅ **响应式** - 适配所有屏幕尺寸
✅ **视频遮罩** - 渐变黑色遮罩确保文字可读
✅ **播放/暂停** - 右下角控制按钮

### 视频遮罩调整

如果视频太亮影响文字阅读，可以调整遮罩透明度：

```tsx
{/* 在 Hero.tsx 第 66-68 行 */}
<div className="absolute inset-0 bg-gradient-to-b 
  from-black/60    // 顶部遮罩 (0-100，数字越大越暗)
  via-black/40     // 中间遮罩
  to-black/70      // 底部遮罩
"></div>
```

### 添加视频封面图（Poster）

```typescript
poster="/videos/poster.jpg" // 视频加载前显示的封面
```

封面图应该是视频的第一帧或代表性画面。

### 性能优化建议

1. **使用 CDN** - 将视频托管到 CDN 加快加载
2. **提供多种格式** - 支持 WebM 作为备选
   ```tsx
   <source src={videoUrl} type="video/mp4" />
   <source src={videoUrl.replace('.mp4', '.webm')} type="video/webm" />
   ```
3. **懒加载** - 仅在首屏时加载视频
4. **压缩视频** - 保持文件小于 10MB

### 示例视频源

**免费视频资源：**
- Pexels: https://www.pexels.com/videos/
- Pixabay: https://pixabay.com/videos/
- Coverr: https://coverr.co/

**推荐主题：**
- 金融/数据可视化
- 办公场景
- 科技感动画
- 抽象图形

### 禁用视频

如果不想使用视频，保持 `videoUrl = ''` 即可，页面会显示纯墨黑背景。

---

**注意事项：**
- 视频会自动循环播放
- 移动设备上会自动适配
- 视频加载失败会显示墨黑背景
- 播放/暂停按钮位于右下角
