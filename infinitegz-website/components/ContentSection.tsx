'use client'

import { useScrollAnimation } from '../hooks/useScrollAnimation'
import { useLanguage } from '@/contexts/LanguageContext'

export default function ContentSection() {
  const { t } = useLanguage()
  const { elementRef: sectionRef, isVisible } = useScrollAnimation({ threshold: 0.1, triggerOnce: true })
  
  // 特性图标
  const featureIcons = [
    <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>,
    <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
    </svg>,
    <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
    </svg>,
    <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
    </svg>
  ]
  
  return (
    <section 
      id="solutions" 
      ref={sectionRef as any}
      className="min-h-screen flex items-center py-16 sm:py-32 bg-background snap-section relative"
    >
      {/* 顶部激光分隔线 */}
      <div className="absolute top-0 left-0 right-0">
        <div className="laser-divider"></div>
      </div>
      
      <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl space-y-16 sm:space-y-24">
        {/* 主标题区 - 简化 */}
        <div className={`text-center space-y-6 transition-all duration-700 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
          <div className="mono-tag text-secondary text-sm">
            {t.home.content.tag}
          </div>
          
          <h2 className="text-3xl tracking-tight md:text-4xl lg:text-5xl text-primary max-w-3xl mx-auto">
            {t.home.content.title}
          </h2>
        </div>

        {/* 特性网格 - 图标化 */}
        <div className="grid gap-12 md:grid-cols-2 lg:grid-cols-4 max-w-6xl mx-auto">
          {t.home.content.features.map((feature, index) => (
            <div 
              key={index} 
              className={`flex flex-col items-center text-center space-y-4 transition-all duration-700 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}
              style={{ transitionDelay: `${(index + 1) * 100}ms` }}
            >
              {/* 图标 */}
              <div className="relative w-16 h-16 icon-pulse">
                <div className="absolute inset-0 rounded-full bg-gradient-to-br from-primary/10 to-secondary/5"></div>
                <div className="absolute inset-0 flex items-center justify-center text-primary/60">
                  {featureIcons[index]}
                </div>
              </div>
              
              {/* 标题 */}
              <h3 className="text-lg font-normal text-primary mono-tag">
                {feature.title}
              </h3>
              
              {/* 描述 - 缩短 */}
              <p className="text-sm text-secondary leading-relaxed">
                {feature.description.split('.')[0]}.
              </p>
            </div>
          ))}
        </div>

        {/* 统计数据展示 - 添加视觉吸引力 */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-8 max-w-5xl mx-auto py-12">
          <div className="text-center space-y-2">
            <div className="text-4xl md:text-5xl font-bold text-primary number-glow">100%</div>
            <div className="text-sm text-secondary mono-tag">Legal & Licensed</div>
          </div>
          <div className="text-center space-y-2">
            <div className="text-4xl md:text-5xl font-bold text-primary number-glow">8+</div>
            <div className="text-sm text-secondary mono-tag">Services Included</div>
          </div>
          <div className="text-center space-y-2">
            <div className="text-4xl md:text-5xl font-bold text-primary number-glow">0</div>
            <div className="text-sm text-secondary mono-tag">Upfront Fees</div>
          </div>
          <div className="text-center space-y-2">
            <div className="text-4xl md:text-5xl font-bold text-primary number-glow">24/7</div>
            <div className="text-sm text-secondary mono-tag">Support Available</div>
          </div>
        </div>
      </div>
      
      {/* 底部激光分隔线 */}
      <div className="absolute bottom-0 left-0 right-0">
        <div className="laser-divider"></div>
      </div>
    </section>
  )
}
