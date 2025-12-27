# INFINITE GZ Website

A modern, dark-themed corporate website for INFINITE GZ SDN BHD, inspired by the design aesthetics of x.ai.

## 🎨 Design Features

- **Dark Theme**: Pure black background with silver/white text for maximum contrast
- **Minimalist Layout**: Clean, breathable design with ample whitespace
- **Smooth Animations**: Fade-in, slide-up effects on scroll
- **Responsive Design**: Mobile-first approach, works on all screen sizes
- **Hero Carousel**: Placeholder for rotating images/videos (5-second intervals)

## 🚀 Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Styling**: Tailwind CSS
- **Language**: TypeScript
- **Animations**: Framer Motion

## 📦 Installation

```bash
npm install
```

## 🔧 Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the site.

## 🏗️ Build

```bash
npm run build
npm start
```

## 📁 Project Structure

```
infinitegz-website/
├── app/
│   ├── layout.tsx       # Root layout with metadata
│   ├── page.tsx         # Homepage
│   └── globals.css      # Global styles
├── components/
│   ├── Header.tsx       # Navigation header
│   ├── Hero.tsx         # Hero section with carousel
│   ├── ProductCards.tsx # Three main product cards
│   ├── ContentSection.tsx # Content and features
│   ├── NewsSection.tsx  # Latest news grid
│   └── Footer.tsx       # Footer with links
├── public/              # Static assets
└── package.json
```

## 🎯 Key Sections

1. **Header**: Fixed navigation with logo, menu, and CTA button
2. **Hero**: Full-screen hero with animated background carousel
3. **Product Cards**: CreditPilot, Loan Advisory, Digitalization services
4. **Content Section**: Features and benefits explanation
5. **News Section**: Latest updates and articles grid
6. **Footer**: Multiple link columns and contact CTAs

## 🔗 Placeholder Links

All external links currently point to placeholder URLs:
- Portal: `https://portal.infinitegz.com`
- WhatsApp: `https://wa.me/60123456789`

Update these in the respective component files before deployment.

## 📝 Customization

### Colors
Edit `tailwind.config.js` to modify the color scheme:
```js
colors: {
  'infinitegz-black': '#000000',
  'infinitegz-dark': '#0a0a0a',
  'infinitegz-gray': '#1a1a1a',
  'infinitegz-light-gray': '#2a2a2a',
  'infinitegz-white': '#ffffff',
  'infinitegz-silver': '#e5e5e5',
  'infinitegz-accent': '#f0f0f0',
}
```

### Content
- Update business content in component files
- Replace placeholder images in `public/` folder
- Modify news items in `NewsSection.tsx`

## 🚀 Deployment

Deploy to Vercel:
```bash
vercel
```

Or push to GitHub and connect to Vercel for automatic deployments.

## 📄 License

© 2024 INFINITE GZ SDN BHD. All rights reserved.
