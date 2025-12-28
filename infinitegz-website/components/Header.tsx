'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useLanguage } from '@/contexts/LanguageContext'
import LanguageSwitcher from './LanguageSwitcher'

export default function Header() {
  const [scrolled, setScrolled] = useState(false)
  const { t } = useLanguage()

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20)
    }
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <header className="fixed inset-x-0 top-0 z-50 duration-200">
      {/* 渐变遮罩 - 滚动时显示 */}
      <div 
        className={`pointer-events-none absolute inset-x-0 h-32 bg-gradient-to-b from-black duration-200 lg:h-24 lg:from-black/75 transition-opacity ${
          scrolled ? 'opacity-100' : 'opacity-0'
        }`}
      />
      
      {/* 背景模糊层 */}
      <div 
        className={`bg-background/25 fixed inset-x-0 top-0 backdrop-blur transition-opacity duration-200 ${
          scrolled ? 'opacity-100' : 'opacity-0'
        }`}
        style={{ height: '78px' }}
      />

      {/* 主导航 */}
      <div className="relative">
        <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl">
          <div className="flex items-center justify-between gap-4 py-4 duration-200" style={{ height: '78px' }}>
            {/* Logo */}
            <Link href="/" className="text-primary font-mono text-xl tracking-tight hover:opacity-80 transition-opacity">
              INFINITE GZ
            </Link>

            {/* 导航菜单 - 桌面版 */}
            <div className="hidden lg:flex flex-grow gap-1 ml-3">
              <Link 
                href="/" 
                className="nav-link-glow"
                style={{
                  color: 'rgb(245, 245, 245)',
                  textShadow: '0 0 8px rgba(255, 255, 255, 0.3)'
                }}
              >
                {t.nav.home}
              </Link>
              <Link 
                href="/creditpilot" 
                className="nav-link-glow"
                style={{
                  color: 'rgb(245, 245, 245)',
                  textShadow: '0 0 8px rgba(255, 255, 255, 0.3)'
                }}
              >
                {t.nav.creditpilot}
              </Link>
              <Link 
                href="/solutions" 
                className="nav-link-glow"
                style={{
                  color: 'rgb(245, 245, 245)',
                  textShadow: '0 0 8px rgba(255, 255, 255, 0.3)'
                }}
              >
                {t.nav.solutions}
              </Link>
              <Link 
                href="/advisory" 
                className="nav-link-glow"
                style={{
                  color: 'rgb(245, 245, 245)',
                  textShadow: '0 0 8px rgba(255, 255, 255, 0.3)'
                }}
              >
                {t.nav.advisory}
              </Link>
              <Link 
                href="/company" 
                className="nav-link-glow"
                style={{
                  color: 'rgb(245, 245, 245)',
                  textShadow: '0 0 8px rgba(255, 255, 255, 0.3)'
                }}
              >
                {t.nav.company}
              </Link>
              <Link 
                href="/news" 
                className="nav-link-glow"
                style={{
                  color: 'rgb(245, 245, 245)',
                  textShadow: '0 0 8px rgba(255, 255, 255, 0.3)'
                }}
              >
                {t.nav.news}
              </Link>
              <Link 
                href="/resources" 
                className="nav-link-glow"
                style={{
                  color: 'rgb(245, 245, 245)',
                  textShadow: '0 0 8px rgba(255, 255, 255, 0.3)'
                }}
              >
                {t.nav.resources}
              </Link>
              <Link 
                href="/careers" 
                className="nav-link-glow"
                style={{
                  color: 'rgb(245, 245, 245)',
                  textShadow: '0 0 8px rgba(255, 255, 255, 0.3)'
                }}
              >
                {t.nav.careers}
              </Link>
            </div>

            {/* CTA 按钮和语言切换 */}
            <div className="flex gap-2 items-center">
              <LanguageSwitcher />
              <Link 
                href="https://portal.infinitegz.com" 
                className="btn-xai hidden lg:inline-flex"
              >
                {t.common.getStarted}
              </Link>
              
              {/* 移动菜单按钮 */}
              <button 
                className="btn-xai lg:hidden aspect-square px-3"
                aria-label="Menu"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}
