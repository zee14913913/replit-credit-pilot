'use client'

import Link from 'next/link'
import { useScrollAnimation } from '../hooks/useScrollAnimation'
import { useLanguage } from '@/contexts/LanguageContext'

export default function ProductCards() {
  const { t } = useLanguage()
  const { elementRef: sectionRef, isVisible } = useScrollAnimation({ threshold: 0.1, triggerOnce: true })
  
  // 产品图标
  const productIcons = [
    // CreditPilot - 智能分析
    <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>,
    // Loan Advisory - 专家指导
    <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
    </svg>,
    // Digitalization - 数字化转型
    <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
    </svg>
  ]
  
  return (
    <section 
      id="products" 
      ref={sectionRef as any}
      className="min-h-screen flex items-center py-16 sm:py-32 bg-background snap-section relative"
    >
      {/* 顶部激光分隔线 */}
      <div className="absolute top-0 left-0 right-0">
        <div className="laser-divider"></div>
      </div>
      
      <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl space-y-16 sm:space-y-24">
        {/* Section 标题 - 简化 */}
        <div className={`text-center space-y-6 transition-all duration-700 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
          <div className="mono-tag text-secondary text-sm">
            {t.home.products.tag}
          </div>
          
          <h2 className="text-3xl tracking-tight md:text-4xl lg:text-5xl text-primary max-w-3xl mx-auto">
            {t.home.products.title}
          </h2>
        </div>

        {/* 产品卡片网格 - 视觉化 */}
        <div className="grid gap-8 lg:grid-cols-3">
          {t.home.products.items.map((product, index) => (
            <div
              key={index}
              className={`card-3d group relative flex flex-col items-center text-center space-y-8 p-10 rounded-2xl border border-primary/5 hover:border-primary/20 hover:bg-gradient-to-b from-secondary/5 via-transparent to-transparent transition-all duration-700 ${
                isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
              }`}
              style={{ transitionDelay: `${index * 100}ms` }}
            >
              {/* 图标 */}
              <div className="relative w-20 h-20 icon-pulse">
                <div className="absolute inset-0 rounded-full bg-gradient-to-br from-primary/10 to-secondary/5 backdrop-blur-xl"></div>
                <div className="absolute inset-0 flex items-center justify-center text-primary/60">
                  {productIcons[index]}
                </div>
              </div>

              {/* 内容 */}
              <div className="space-y-6 flex-grow">
                {/* 标签 */}
                <div className="mono-tag text-secondary text-xs">
                  {product.tag}
                </div>

                {/* 标题 */}
                <h3 className="text-2xl md:text-3xl font-normal tracking-tight text-primary">
                  {product.title}
                </h3>

                {/* 描述 - 简化 */}
                <p className="text-secondary text-base leading-loose max-w-xs mx-auto">
                  {product.description}
                </p>
              </div>

              {/* CTA 按钮 */}
              <Link
                href={product.linkUrl}
                className="btn-xai w-full justify-center group-hover:bg-primary group-hover:text-background transition-all duration-300"
              >
                {product.linkText}
              </Link>
            </div>
          ))}
        </div>
      </div>
      
      {/* 底部激光分隔线 */}
      <div className="absolute bottom-0 left-0 right-0">
        <div className="laser-divider"></div>
      </div>
    </section>
  )
}
