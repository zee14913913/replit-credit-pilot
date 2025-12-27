'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useLanguage } from '@/contexts/LanguageContext'

export default function Hero() {
  const [currentSlide, setCurrentSlide] = useState(0)
  const { t } = useLanguage()

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % 3)
    }, 5000)
    return () => clearInterval(timer)
  }, [])

  return (
    <section className="relative h-screen flex items-center justify-center border-b border-primary/10 snap-section">
      {/* 背景渐变占位符 - 轮播区域 */}
      <div className="absolute inset-0 overflow-hidden bg-background">
        <div className="relative w-full h-full">
          <div className={`absolute inset-0 transition-opacity duration-1000 ${currentSlide === 0 ? 'opacity-20' : 'opacity-0'}`}>
            <div className="w-full h-full bg-gradient-to-br from-blue-900/30 to-purple-900/30"></div>
          </div>
          <div className={`absolute inset-0 transition-opacity duration-1000 ${currentSlide === 1 ? 'opacity-20' : 'opacity-0'}`}>
            <div className="w-full h-full bg-gradient-to-br from-purple-900/30 to-pink-900/30"></div>
          </div>
          <div className={`absolute inset-0 transition-opacity duration-1000 ${currentSlide === 2 ? 'opacity-20' : 'opacity-0'}`}>
            <div className="w-full h-full bg-gradient-to-br from-green-900/30 to-blue-900/30"></div>
          </div>
        </div>
      </div>

      {/* 内容容器 */}
      <div className="relative z-10 mx-auto w-full px-4 lg:px-6 xl:max-w-7xl flex flex-col" style={{ minHeight: 'calc(100vh - 78px)', paddingTop: '78px' }}>
        <div className="flex-grow flex items-center justify-center py-16 sm:py-32">
          <div className="w-full max-w-3xl space-y-8">
            {/* 顶部标签按钮 */}
            <div className="flex justify-center">
              <Link 
                href="https://portal.infinitegz.com" 
                className="btn-xai mono-tag"
              >
                {t.common.useCreditPilot}
              </Link>
            </div>

            {/* 主标题 - 渐变文字效果 */}
            <div className="text-center space-y-4">
              <h1 className="text-4xl leading-[2.25rem] tracking-tight md:text-[5rem] md:leading-[5rem]">
                <span className="inline-block bg-gradient-to-r from-secondary to-primary bg-clip-text text-transparent py-2">
                  {t.home.hero.title}
                </span>
              </h1>
            </div>

            {/* 副标题 */}
            <p className="text-center text-secondary text-base md:text-xl max-w-2xl mx-auto leading-relaxed">
              {t.home.hero.description}
            </p>

            {/* 轮播指示器 */}
            <div className="flex justify-center gap-2 pt-4">
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
        <div className="relative z-10 flex items-end justify-between gap-6 pb-4 pt-4 lg:min-h-[160px] lg:py-10">
          <div className="flex flex-col items-end gap-6 sm:gap-8 md:flex-row lg:gap-12 w-full">
            <div className="max-w-2xl">
              <p className="text-secondary text-sm md:text-base leading-relaxed">
                {t.home.hero.bottomDescription}
              </p>
            </div>
            
            <div className="flex flex-col items-end gap-3 sm:flex-row ml-auto">
              <Link 
                href="https://portal.infinitegz.com" 
                className="btn-xai hidden lg:inline-flex whitespace-nowrap"
              >
                {t.common.getStarted}
              </Link>
              <Link 
                href="#products" 
                className="btn-xai whitespace-nowrap"
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
