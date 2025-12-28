'use client'

import { usePathname } from 'next/navigation'
import { useEffect, useState } from 'react'

// 页面配置
const pageConfig: Record<string, { name: string; color: string; gradient: string }> = {
  '/': {
    name: 'Home',
    color: 'rgb(59, 130, 246)', // blue
    gradient: 'from-blue-500 via-cyan-500 to-blue-500'
  },
  '/creditpilot': {
    name: 'CreditPilot',
    color: 'rgb(16, 185, 129)', // green
    gradient: 'from-green-500 via-emerald-500 to-green-500'
  },
  '/advisory': {
    name: 'Advisory',
    color: 'rgb(139, 92, 246)', // purple
    gradient: 'from-purple-500 via-violet-500 to-purple-500'
  },
  '/solutions': {
    name: 'Solutions',
    color: 'rgb(236, 72, 153)', // pink
    gradient: 'from-pink-500 via-rose-500 to-pink-500'
  },
  '/company': {
    name: 'Company',
    color: 'rgb(251, 146, 60)', // orange
    gradient: 'from-orange-500 via-amber-500 to-orange-500'
  },
  '/news': {
    name: 'News',
    color: 'rgb(234, 179, 8)', // yellow
    gradient: 'from-yellow-500 via-amber-500 to-yellow-500'
  },
  '/resources': {
    name: 'Resources',
    color: 'rgb(6, 182, 212)', // cyan
    gradient: 'from-cyan-500 via-teal-500 to-cyan-500'
  },
  '/careers': {
    name: 'Careers',
    color: 'rgb(168, 85, 247)', // violet
    gradient: 'from-violet-500 via-purple-500 to-violet-500'
  },
  '/loan-matcher': {
    name: 'Loan Matcher',
    color: 'rgb(14, 165, 233)', // sky
    gradient: 'from-sky-500 via-blue-500 to-sky-500'
  },
  '/loan-analyzer': {
    name: 'Loan Analyzer',
    color: 'rgb(244, 63, 94)', // rose
    gradient: 'from-rose-500 via-pink-500 to-rose-500'
  }
}

export default function PageIndicator() {
  const pathname = usePathname()
  const [isVisible, setIsVisible] = useState(false)
  const config = pageConfig[pathname] || pageConfig['/']

  useEffect(() => {
    // 淡入动画
    const timer = setTimeout(() => setIsVisible(true), 100)
    return () => clearTimeout(timer)
  }, [pathname])

  return (
    <div
      className={`
        fixed top-24 right-6 z-40
        transition-all duration-500 ease-out
        ${isVisible ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-8'}
      `}
    >
      {/* 主容器 */}
      <div className="relative">
        {/* 外层发光圆环 - 流动效果 */}
        <div className="absolute inset-0 -m-1">
          <div
            className={`
              w-full h-full rounded-full
              bg-gradient-to-r ${config.gradient}
              animate-spin-slow
              opacity-50 blur-sm
            `}
            style={{
              animationDuration: '3s'
            }}
          />
        </div>
        
        {/* 中层圆环 - 脉冲效果 */}
        <div className="absolute inset-0">
          <div
            className="w-full h-full rounded-full animate-ping-slow"
            style={{
              backgroundColor: config.color,
              opacity: 0.2,
              animationDuration: '2s'
            }}
          />
        </div>

        {/* 内层圆环 - 主体 */}
        <div
          className="
            relative w-16 h-16 rounded-full
            bg-gradient-to-br from-background/90 to-background/70
            backdrop-blur-md
            border-2
            flex items-center justify-center
            shadow-lg
          "
          style={{
            borderColor: config.color,
            boxShadow: `0 0 20px ${config.color}40, 0 0 40px ${config.color}20`
          }}
        >
          {/* 页面名称首字母 */}
          <div
            className="
              text-2xl font-bold font-mono
              transition-all duration-300
            "
            style={{
              color: config.color,
              textShadow: `0 0 10px ${config.color}80`
            }}
          >
            {config.name.charAt(0)}
          </div>
        </div>
      </div>
    </div>
  )
}
