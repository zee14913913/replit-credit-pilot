'use client'

import { useScrollAnimation } from '../hooks/useScrollAnimation'
import { useLanguage } from '@/contexts/LanguageContext'

export default function NewsSection() {
  const { t } = useLanguage()
  const { ref: sectionRef, isVisible } = useScrollAnimation(0.1)
  
  return (
    <section 
      id="resources" 
      ref={sectionRef as any}
      className="min-h-screen flex items-center py-16 sm:py-32 bg-background border-t border-primary/10 snap-section"
    >
      <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl space-y-16">
        {/* Section 标题 */}
        <div className={`space-y-4 ${isVisible ? 'animate-on-scroll' : 'opacity-0'}`}>
          <div className="mono-tag text-secondary">
            {t.home.news.tag}
          </div>
          <h2 className="text-3xl tracking-tight md:text-4xl lg:text-5xl text-primary max-w-2xl">
            {t.home.news.title}
          </h2>
          <p className="text-secondary text-base md:text-lg max-w-2xl">
            {t.home.news.description}
          </p>
        </div>

        {/* 新闻网格 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 lg:gap-12">
          {t.home.news.items.map((item, index) => (
            <article
              key={index}
              className={`group space-y-4 cursor-pointer ${isVisible ? 'animate-on-scroll' : 'opacity-0'} delay-${(index + 1) * 100}`}
            >
              {/* 日期和分类 */}
              <div className="flex items-center justify-between">
                <span className="mono-tag text-xs text-secondary">
                  {item.date}
                </span>
                <span className="mono-tag text-xs text-secondary/50 px-2 py-0.5 border border-primary/10 rounded-full">
                  {item.category}
                </span>
              </div>

              {/* 标题 */}
              <h3 className="text-xl md:text-2xl font-normal tracking-tight text-primary group-hover:text-secondary transition-colors duration-150">
                {item.title}
              </h3>

              {/* 描述 */}
              <p className="text-sm text-secondary leading-relaxed">
                {item.description}
              </p>

              {/* 阅读更多链接 */}
              <div className="pt-2">
                <span className="mono-tag text-xs text-primary/50 group-hover:text-primary transition-colors duration-150 inline-flex items-center gap-2">
                  {t.common.readMore}
                  <svg className="w-4 h-4 transform group-hover:translate-x-1 transition-transform duration-150" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </span>
              </div>
            </article>
          ))}
        </div>

        {/* 查看全部按钮 */}
        <div className="text-center pt-8">
          <button className="btn-xai">
            {t.common.viewAll}
          </button>
        </div>
      </div>
    </section>
  )
}
