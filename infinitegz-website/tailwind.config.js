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
        // 高级墨黑色系统
        background: 'rgb(5, 5, 8)', // 主背景 - 深邃墨黑带微蓝
        primary: 'rgb(255, 255, 255)', // 主文字颜色
        secondary: 'rgb(180, 185, 195)', // 次要文字颜色 - 银灰色
        'border-color': 'rgba(192, 192, 192, 0.2)', // 边框颜色 - 银色
        'hover-bg': 'rgba(192, 192, 192, 0.1)', // Hover 背景 - 银色光泽
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