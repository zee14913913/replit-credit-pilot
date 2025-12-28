'use client'

import { useState, useEffect, useRef } from 'react'
import Link from 'next/link'
import { useLanguage } from '@/contexts/LanguageContext'

export default function Hero() {
  const [currentSlide, setCurrentSlide] = useState(0)
  const [scrollY, setScrollY] = useState(0)
  const { t } = useLanguage()
  const heroRef = useRef<HTMLElement>(null)

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % 3)
    }, 5000)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    const handleScroll = () => {
      if (heroRef.current) {
        const rect = heroRef.current.getBoundingClientRect()
        const scrollProgress = Math.max(0, -rect.top / window.innerHeight)
        setScrollY(scrollProgress)
      }
    }

    window.addEventListener('scroll', handleScroll, { passive: true })
    handleScroll()
    
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <section 
      ref={heroRef}
      className="relative h-screen flex items-center justify-center snap-section overflow-hidden"
    >
      {/* 纯墨黑背景 */}
      <div className="absolute inset-0 bg-background"></div>

      {/* 内容容器 */}
      <div className="relative z-10 mx-auto w-full px-4 lg:px-6 xl:max-w-7xl flex flex-col" style={{ minHeight: 'calc(100vh - 78px)', paddingTop: '78px' }}>
        <div className="flex-grow flex items-center justify-center py-16 sm:py-32">
          <div className="w-full max-w-4xl space-y-12">
            {/* 顶部图标 + 标签 */}
            <div className="flex flex-col items-center gap-8 animate-fadeIn">
              {/* 动态图标 */}
              <div className="relative w-20 h-20 icon-pulse">
                <div className="absolute inset-0 rounded-full bg-gradient-to-br from-primary/20 to-secondary/10 backdrop-blur-xl"></div>
                <div className="absolute inset-0 flex items-center justify-center">
                  <svg className="w-10 h-10 text-primary/80" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
              </div>
              
              <Link 
                href="https://portal.infinitegz.com" 
                className="btn-xai mono-tag"
              >
                {t.common.useCreditPilot}
              </Link>
            </div>

            {/* 主标题 - 更大更突出 */}
            <div className="text-center space-y-6 animate-fadeIn delay-100">
              <h1 className="text-5xl leading-tight tracking-tight md:text-6xl md:leading-tight lg:text-7xl lg:leading-tight xl:text-8xl xl:leading-tight">
                <span className="inline-block bg-gradient-to-r from-secondary via-primary to-secondary bg-clip-text text-transparent py-2 whitespace-pre-line font-bold">
                  {t.home.hero.title}
                </span>
              </h1>
              
              {/* 简短的副标题 - 减少文字 */}
              <p className="text-secondary text-lg md:text-xl max-w-2xl mx-auto leading-relaxed font-light">
                {t.home.hero.description}
              </p>
            </div>

            {/* CTA 按钮 - 更突出 */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-fadeIn delay-200">
              <Link 
                href="https://portal.infinitegz.com" 
                className="btn-xai btn-xai-primary whitespace-nowrap min-w-[180px] text-base py-3"
              >
                {t.common.getStarted}
              </Link>
              <Link 
                href="#products" 
                className="btn-xai whitespace-nowrap min-w-[180px] text-base py-3"
              >
                {t.common.learnMore}
              </Link>
            </div>

            {/* 轮播指示器 */}
            <div className="flex justify-center gap-2 pt-4 animate-fadeIn delay-300">
              {[0, 1, 2].map((index) => (
                <button
                  key={index}
                  onClick={() => setCurrentSlide(index)}
                  className={`h-0.5 rounded-full transition-all duration-200 ${
                    currentSlide === index 
                      ? 'bg-primary w-8' 
                      : 'bg-primary/25 w-2'
                  }`}
                  aria-label={`Go to slide ${index + 1}`}
                />
              ))}
            </div>
          </div>
        </div>
      </div>
      
      {/* 底部激光分隔线 */}
      <div className="absolute bottom-0 left-0 right-0 z-20">
        <div className="laser-divider"></div>
      </div>
    </section>
  )
}
