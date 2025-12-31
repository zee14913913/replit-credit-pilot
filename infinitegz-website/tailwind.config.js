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
        // X.AI 纯黑风格
        background: '#000000', // 纯黑背景
        primary: '#FFFFFF', // 主文字颜色
        secondary: '#A1A1AA', // 次要文字颜色 - zinc-400
        'border-color': 'rgba(63, 63, 70, 0.5)', // 边框颜色 - zinc-700
        'hover-bg': 'rgba(63, 63, 70, 0.3)', // Hover 背景
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