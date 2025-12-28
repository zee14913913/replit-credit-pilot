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

  // Ethnocare 风格的视差滚动效果
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
      className="relative h-screen flex items-center justify-center border-b border-primary/10 snap-section overflow-hidden"
    >
      {/* 纯墨黑背景 - 无渐变 */}
      <div className="absolute inset-0 bg-background"></div>

      {/* 内容容器 - 固定定位不受视差影响 */}
      <div className="relative z-10 mx-auto w-full px-4 lg:px-6 xl:max-w-7xl flex flex-col" style={{ minHeight: 'calc(100vh - 78px)', paddingTop: '78px' }}>
        <div className="flex-grow flex items-center justify-center py-16 sm:py-32">
          <div className="w-full max-w-3xl space-y-8">
            {/* 顶部标签按钮 */}
            <div className="flex justify-center animate-fadeIn">
              <Link 
                href="https://portal.infinitegz.com" 
                className="btn-xai mono-tag"
              >
                {t.common.useCreditPilot}
              </Link>
            </div>

            {/* 主标题 - 渐变文字效果 */}
            <div className="text-center space-y-4 animate-fadeIn delay-100">
              <h1 className="text-4xl leading-tight tracking-tight md:text-5xl md:leading-tight lg:text-6xl lg:leading-tight xl:text-[5rem] xl:leading-tight min-h-[8rem] md:min-h-[10rem] lg:min-h-[12rem] flex items-center justify-center">
                <span className="inline-block bg-gradient-to-r from-secondary to-primary bg-clip-text text-transparent py-2 whitespace-pre-line">
                  {t.home.hero.title}
                </span>
              </h1>
            </div>

            {/* 副标题 */}
            <p className="text-center text-secondary text-base md:text-xl max-w-2xl mx-auto leading-relaxed animate-fadeIn delay-200">
              {t.home.hero.description}
            </p>

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

        {/* 底部 CTA 区域 */}
        <div className="relative z-10 pb-4 pt-4 lg:min-h-[160px] lg:py-10 animate-fadeIn delay-400">
          <div className="flex flex-col md:flex-row items-start md:items-end justify-between gap-6 w-full">
            {/* 描述文本 - 固定宽度容器 */}
            <div className="w-full md:max-w-2xl flex-shrink-0">
              <p className="text-secondary text-sm md:text-base leading-relaxed">
                {t.home.hero.bottomDescription}
              </p>
            </div>
            
            {/* 按钮组 - 固定宽度容器 */}
            <div className="w-full md:w-auto flex flex-col sm:flex-row items-stretch sm:items-center gap-3 flex-shrink-0">
              <Link 
                href="https://portal.infinitegz.com" 
                className="btn-xai hidden lg:inline-flex whitespace-nowrap min-w-[140px] justify-center"
              >
                {t.common.getStarted}
              </Link>
              <Link 
                href="#products" 
                className="btn-xai whitespace-nowrap min-w-[140px] justify-center"
              >
                {t.common.learnMore}
              </Link>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
