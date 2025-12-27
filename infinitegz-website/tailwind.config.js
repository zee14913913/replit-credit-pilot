/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // X.AI 精确颜色
        background: 'rgb(10, 10, 10)', // 主背景 - 非纯黑
        primary: 'rgb(255, 255, 255)', // 主文字颜色
        secondary: 'rgb(125, 129, 135)', // 次要文字颜色
        'border-color': 'rgba(255, 255, 255, 0.25)', // 边框颜色 - 25% 透明
        'hover-bg': 'rgba(125, 129, 135, 0.2)', // Hover 背景 - 20% 透明
      },
      fontFamily: {
        sans: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'Liberation Mono', 'Courier New', 'monospace'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'Liberation Mono', 'Courier New', 'monospace'],
      },
      fontSize: {
        'xai-sm': ['14px', { lineHeight: '1.5' }],
        'xai-base': ['16px', { lineHeight: '24px' }],
        'xai-h2': ['36px', { lineHeight: '40px' }],
        'xai-hero': ['5rem', { lineHeight: '5rem' }],
      },
      spacing: {
        '128': '128px', // Section padding (py-32)
        '78': '78px', // Header height
      },
      borderRadius: {
        'full': '9999px',
      },
      transitionDuration: {
        '150': '150ms',
        '200': '200ms',
      },
      letterSpacing: {
        'widest': '0.1em',
      },
    },
  },
  plugins: [],
}