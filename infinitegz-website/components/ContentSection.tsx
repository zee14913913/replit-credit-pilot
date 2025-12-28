'use client'

import { useScrollAnimation } from '../hooks/useScrollAnimation'
import { useLanguage } from '@/contexts/LanguageContext'

export default function ContentSection() {
  const { t } = useLanguage()
  const { ref: sectionRef, isVisible } = useScrollAnimation(0.1)
  
  return (
    <section 
      id="solutions" 
      ref={sectionRef as any}
      className="min-h-screen flex items-center py-16 sm:py-32 bg-background snap-section"
    >
      <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl space-y-16 sm:space-y-32">
        {/* 主标题区 */}
        <div className={`max-w-3xl mx-auto text-center space-y-8 transition-all duration-700 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
          <div className="mono-tag text-secondary">
            {t.home.content.tag}
          </div>
          
          <h2 className="text-3xl tracking-tight md:text-4xl lg:text-5xl text-primary">
            {t.home.content.title}
          </h2>
          
          <p className="text-secondary text-base md:text-lg leading-relaxed">
            {t.home.content.description}
          </p>
        </div>

        {/* 特性网格 */}
        <div className="relative grid gap-16 md:grid-cols-4">
          {t.home.content.features.map((feature, index) => (
            <div 
              key={index} 
              className={`space-y-4 transition-all duration-700 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}
              style={{ transitionDelay: `${(index + 2) * 100}ms` }}
            >
              <h3 className="text-xl font-normal text-primary mono-tag">
                {feature.title}
              </h3>
              <p className="text-sm text-secondary leading-relaxed">
                {feature.description}
              </p>
            </div>
          ))}
        </div>

        {/* CreditPilot 详细说明 */}
        <div className="max-w-4xl mx-auto space-y-12 py-16">
          <h3 className="text-2xl md:text-3xl tracking-tight text-primary">
            {t.home.content.detailsTitle}
          </h3>
          
          <div className="space-y-8 text-secondary">
            {t.home.content.details.map((detail, idx) => (
              <div key={idx} className="space-y-3">
                <h4 className="text-primary font-normal mono-tag text-base">
                  {detail.title}
                </h4>
                <p className="text-sm md:text-base leading-relaxed">
                  {detail.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
