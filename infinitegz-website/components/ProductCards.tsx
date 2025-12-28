'use client'

import Link from 'next/link'
import { useScrollAnimation } from '../hooks/useScrollAnimation'
import { useLanguage } from '@/contexts/LanguageContext'

export default function ProductCards() {
  const { t } = useLanguage()
  const { ref: sectionRef, isVisible } = useScrollAnimation(0.1)
  
  return (
    <section 
      id="products" 
      ref={sectionRef as any}
      className="min-h-screen flex items-center py-16 sm:py-32 bg-background snap-section"
    >
      <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl space-y-16 sm:space-y-32">
        {/* Section 标题 */}
        <div className={`space-y-12 transition-all duration-700 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
          <div className="mono-tag flex items-center gap-2">
            <span className="text-secondary">{t.home.products.tag}</span>
          </div>
          
          <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
            <div className="max-w-2xl space-y-12">
              <h2 className="text-balance text-3xl tracking-tight md:text-4xl lg:text-5xl text-primary">
                {t.home.products.title}
              </h2>
            </div>
          </div>
        </div>

        {/* 产品卡片网格 - X.AI + Ethnocare 风格 */}
        <div className="grid gap-0 lg:grid-cols-3 lg:-space-x-px">
          {t.home.products.items.map((product, index) => (
            <div
              key={index}
              className={`card-3d group relative flex h-full flex-col space-y-4 px-0 py-10 lg:p-8 border-t border-primary/10 lg:border-l lg:border-t-0 hover:bg-gradient-to-b from-secondary/10 via-transparent to-transparent transition-all duration-700 ${
                isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
              }`}
              style={{ transitionDelay: `${index * 100}ms` }}
            >
              {/* 悬停边框效果 */}
              <div className="border-primary/10 pointer-events-none absolute inset-0 isolate z-10 border opacity-0 group-hover:opacity-100 hidden lg:block transition-opacity duration-200" />
              
              {/* 左上角装饰点 */}
              <div className="bg-primary absolute -left-1 -top-1 z-10 size-2 -translate-x-px -translate-y-px opacity-0 group-hover:opacity-100 transition-opacity duration-200 hidden lg:block" />

              {/* 内容 */}
              <div className="relative z-20 space-y-6">
                {/* 标签 */}
                <div className="mono-tag text-secondary">
                  {product.tag}
                </div>

                {/* 标题 */}
                <h3 className="text-2xl md:text-3xl font-normal tracking-tight text-primary">
                  {product.title}
                </h3>

                {/* 描述 */}
                <p className="text-secondary text-sm md:text-base leading-relaxed">
                  {product.description}
                </p>

                {/* 特性列表 */}
                <ul className="space-y-3">
                  {product.features.map((feature, idx) => (
                    <li key={idx} className="flex items-start gap-3 text-sm text-secondary">
                      <span className="mt-1.5 size-1 shrink-0 rounded-full bg-primary/50" />
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>

                {/* CTA 按钮 */}
                <div className="pt-4">
                  <Link
                    href={product.linkUrl}
                    className="btn-xai"
                  >
                    {product.linkText}
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
