'use client'

import Header from '@/components/Header'
import Footer from '@/components/Footer'
import ScrollProgress from '@/components/ScrollProgress'
import Link from 'next/link'
import { useLanguage } from '@/contexts/LanguageContext'

export default function SolutionsPage() {
  const { t } = useLanguage()
  
  return (
    <>
      <ScrollProgress />
      <main className="min-h-screen bg-[rgb(10,10,10)]">
        <Header />
        
        {/* Hero Section */}
        <section className="relative pb-px min-h-screen">
          {/* Video Background - z-0 */}
          <div className="absolute inset-0 z-0 overflow-hidden bg-black">
            <video
              autoPlay
              loop
              muted
              playsInline
              preload="auto"
              className="w-full h-full object-cover opacity-50"
            >
              <source src="/videos/solutions-hero-bg.mp4" type="video/mp4" />
              您的浏览器不支持视频播放
            </video>
          </div>
          
          {/* Gradient Overlay - z-10 轻微底部渐变 */}
          <div className="absolute inset-0 z-10 bg-gradient-to-b from-black/10 via-transparent to-black/50"></div>

          {/* Content - z-20 */}
          <div className="relative z-20 mx-auto w-full px-4 lg:px-6 xl:max-w-7xl flex min-h-screen flex-col justify-center">
            <div className="py-20 text-center">
              <hgroup className="space-y-8">
                <div className="mono-tag text-secondary text-sm">
                  [ {t.solutions.hero.tag} ]
                </div>
                
                <h1 className="text-primary mx-auto max-w-4xl text-balance text-5xl leading-tight tracking-tight md:text-7xl md:leading-tight lg:text-8xl lg:leading-tight">
                  {t.solutions.hero.title}
                </h1>
                
                <p className="text-secondary mx-auto max-w-3xl text-lg md:text-xl leading-relaxed">
                  {t.solutions.hero.description}
                </p>
                
                <div className="flex flex-wrap items-center justify-center gap-4 pt-8">
                  <Link 
                    href="https://portal.infinitegz.com" 
                    className="relative isolate inline-flex shrink-0 items-center justify-center border font-mono text-base/6 uppercase tracking-widest gap-x-3 px-6 py-3 sm:text-sm border-[--btn-border] bg-[--btn-bg] text-[--btn-text] hover:border-[--btn-hover] hover:bg-[--btn-hover] rounded-full [--btn-bg:theme(colors.primary)] [--btn-border:theme(colors.primary)] [--btn-hover:theme(colors.primary/80%)] [--btn-text:theme(colors.background)]"
                  >
                    <span>{t.common.getStarted}</span>
                  </Link>
                  <Link 
                    href="/creditpilot" 
                    className="relative isolate inline-flex shrink-0 items-center justify-center border font-mono text-base/6 uppercase tracking-widest gap-x-3 px-6 py-3 sm:text-sm border-[--btn-border] bg-[--btn-bg] text-[--btn-text] hover:bg-[--btn-hover] rounded-full [--btn-bg:transparent] [--btn-border:theme(colors.primary/25%)] [--btn-hover:theme(colors.secondary/20%)] [--btn-text:theme(colors.primary)]"
                  >
                    <span>{t.common.explore}</span>
                  </Link>
                </div>
              </hgroup>
            </div>
          </div>
          
          {/* 底部激光分隔线 - z-30 */}
          <div className="absolute bottom-0 left-0 right-0 z-30">
            <div className="laser-divider"></div>
          </div>
        </section>

        {/* Product Cards Section */}
        <section className="py-16 sm:py-24 relative">
          <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl">
            <div className="grid lg:grid-cols-3 gap-px bg-border">
              
              {t.solutions.products.map((product, index) => (
                <Link 
                  key={index}
                  href={index === 0 ? '/creditpilot' : index === 1 ? '/advisory' : '/resources'} 
                  className={`group bg-background p-8 sm:p-12 hover:bg-secondary/5 transition-colors ${index > 0 ? 'border-t lg:border-t-0 lg:border-l border-border' : ''}`}
                >
                  <div className="space-y-6">
                    <div className="mono-tag text-xs text-secondary">[ {product.tag} ]</div>
                    <h2 className="text-3xl sm:text-4xl text-primary group-hover:text-primary/80 transition-colors">
                      {product.title}
                    </h2>
                    <p className="text-secondary text-base leading-relaxed">
                      {product.description}
                    </p>
                    <div className="flex items-center gap-2 text-sm text-primary">
                      <span>{product.linkText}</span>
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
                      </svg>
                    </div>
                  </div>
                </Link>
              ))}

            </div>
          
      {/* 底部激光分隔线 */}
      <div className="absolute bottom-0 left-0 right-0">
        <div className="laser-divider"></div>
      </div>
          </div>
        </section>

        {/* Core Business Details */}
        <section className="py-16 sm:py-32 relative">
          <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl space-y-16 sm:space-y-24">
            <div className="space-y-8">
              <div className="mono-tag flex items-center gap-2 text-sm text-secondary">
                <span>[</span> <span>{t.solutions.coreBusiness.tag}</span> <span>]</span>
              </div>
              <h2 className="text-balance text-3xl tracking-tight md:text-5xl lg:text-6xl text-primary max-w-3xl">
                {t.solutions.coreBusiness.title}
              </h2>
              <p className="text-secondary text-lg max-w-2xl">
                {t.solutions.coreBusiness.description}
              </p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
              {t.solutions.coreBusiness.features.map((feature, index) => (
                <div key={index} className="space-y-4 p-6 border border-border rounded-lg">
                  <div className="text-5xl">{feature.icon}</div>
                  <h3 className="text-xl text-primary">{feature.title}</h3>
                  <p className="text-secondary text-sm">
                    {feature.description}
                  </p>
                </div>
              ))}
            </div>
          
      {/* 底部激光分隔线 */}
      <div className="absolute bottom-0 left-0 right-0">
        <div className="laser-divider"></div>
      </div>
          </div>
        </section>

        {/* 8 Complementary Services */}
        <section className="py-16 sm:py-32 relative">
          <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl space-y-16 sm:space-y-24">
            <div className="space-y-8">
              <div className="mono-tag flex items-center gap-2 text-sm text-secondary">
                <span>[</span> <span>{t.solutions.complementaryServices.tag}</span> <span>]</span>
              </div>
              <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-8">
                <div className="max-w-3xl space-y-4">
                  <h2 className="text-balance text-3xl tracking-tight md:text-5xl lg:text-6xl text-primary">
                    {t.solutions.complementaryServices.title}
                  </h2>
                  <p className="text-secondary text-lg">
                    {t.solutions.complementaryServices.description}
                  </p>
                </div>
                <Link 
                  href="/advisory" 
                  className="relative isolate inline-flex shrink-0 items-center justify-center border font-mono text-base/6 uppercase tracking-widest gap-x-3 px-6 py-3 sm:text-sm border-[--btn-border] bg-[--btn-bg] text-[--btn-text] hover:bg-[--btn-hover] rounded-full [--btn-bg:transparent] [--btn-border:theme(colors.primary/25%)] [--btn-hover:theme(colors.secondary/20%)] [--btn-text:theme(colors.primary)]"
                >
                  <span>{t.common.viewDetails}</span>
                </Link>
              </div>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-px bg-border">
              {t.solutions.complementaryServices.items.map((service, index) => {
                // 第1项（财务优化）和第8项（信用卡管理）使用链接
                const isFinancialOptimization = service.num === '01';
                const isCreditCard = service.num === '08';
                
                if (isFinancialOptimization) {
                  return (
                    <Link 
                      key={index}
                      href="/financial-optimization"
                      className="bg-background p-6 sm:p-8 space-y-4 hover:bg-secondary/5 transition-colors group cursor-pointer"
                    >
                      <div className="mono-tag text-xs text-secondary">{service.num}</div>
                      <h3 className="text-lg text-primary group-hover:text-accent transition-colors">{service.title}</h3>
                      <p className="text-sm text-secondary leading-relaxed">{service.description}</p>
                      <div className="flex items-center gap-2 text-xs text-primary pt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        <span>{t.common.viewDetails}</span>
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-3 h-3">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
                        </svg>
                      </div>
                    </Link>
                  );
                }
                
                if (isCreditCard) {
                  return (
                    <Link 
                      key={index}
                      href="/credit-card-management"
                      className="bg-background p-6 sm:p-8 space-y-4 hover:bg-secondary/5 transition-colors group cursor-pointer"
                    >
                      <div className="mono-tag text-xs text-secondary">{service.num}</div>
                      <h3 className="text-lg text-primary group-hover:text-accent transition-colors">{service.title}</h3>
                      <p className="text-sm text-secondary leading-relaxed">{service.description}</p>
                      <div className="flex items-center gap-2 text-xs text-primary pt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        <span>{t.common.viewDetails}</span>
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-3 h-3">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
                        </svg>
                      </div>
                    </Link>
                  );
                }
                
                // 其他7项保持原样
                return (
                  <div key={index} className="bg-background p-6 sm:p-8 space-y-4 hover:bg-secondary/5 transition-colors">
                    <div className="mono-tag text-xs text-secondary">{service.num}</div>
                    <h3 className="text-lg text-primary">{service.title}</h3>
                    <p className="text-sm text-secondary leading-relaxed">{service.description}</p>
                  </div>
                );
              })}
            </div>
          
      {/* 底部激光分隔线 */}
      <div className="absolute bottom-0 left-0 right-0">
        <div className="laser-divider"></div>
      </div>
          </div>
        </section>

        {/* Pricing Model */}
        <section className="py-16 sm:py-32 relative">
          <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl space-y-16 sm:space-y-24">
            <div className="space-y-8">
              <div className="mono-tag flex items-center gap-2 text-sm text-secondary">
                <span>[</span> <span>{t.solutions.pricing.tag}</span> <span>]</span>
              </div>
              <h2 className="text-balance text-3xl tracking-tight md:text-5xl lg:text-6xl text-primary max-w-3xl">
                {t.solutions.pricing.title}
              </h2>
            </div>

            <div className="grid lg:grid-cols-3 gap-8">
              {t.solutions.pricing.models.map((model, index) => (
                <div key={index} className={`space-y-6 p-8 sm:p-12 rounded-lg transition-colors ${index === 1 ? 'border-2 border-primary/20 bg-primary/5' : 'border border-border hover:border-primary/30'}`}>
                  <div className="mono-tag text-xs text-secondary">[ {model.tag} ]</div>
                  <h3 className="text-3xl text-primary">{model.title}</h3>
                  <div className="text-6xl font-light text-primary">{model.price}</div>
                  <p className="text-secondary leading-relaxed">
                    {model.description}
                  </p>
                  <ul className="space-y-3 text-sm text-secondary">
                    {model.features.map((feature, fIndex) => (
                      <li key={fIndex} className="flex items-start gap-2">
                        <span className="text-primary">•</span>
                        <span>{feature}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          
      {/* 底部激光分隔线 */}
      <div className="absolute bottom-0 left-0 right-0">
        <div className="laser-divider"></div>
      </div>
          </div>
        </section>

        {/* Target Customers */}
        <section className="py-16 sm:py-32 relative">
          <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl space-y-16 sm:space-y-24">
            <div className="space-y-8">
              <div className="mono-tag flex items-center gap-2 text-sm text-secondary">
                <span>[</span> <span>{t.solutions.targetCustomers.tag}</span> <span>]</span>
              </div>
              <h2 className="text-balance text-3xl tracking-tight md:text-5xl lg:text-6xl text-primary max-w-3xl">
                {t.solutions.targetCustomers.title}
              </h2>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
              {t.solutions.targetCustomers.customers.map((customer, index) => (
                <div key={index} className="space-y-4 p-6 border border-border rounded-lg">
                  <div className="text-4xl">{customer.icon}</div>
                  <h3 className="text-xl text-primary">{customer.title}</h3>
                  <p className="text-secondary text-sm">
                    {customer.description}
                  </p>
                </div>
              ))}
            </div>
          
      {/* 底部激光分隔线 */}
      <div className="absolute bottom-0 left-0 right-0">
        <div className="laser-divider"></div>
      </div>
          </div>
        </section>

        {/* Call to Action */}
        <section className="py-16 sm:py-32">
          <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl">
            <div className="border border-border rounded-2xl p-8 sm:p-16 text-center space-y-8 bg-gradient-to-b from-secondary/5 to-transparent">
              <h2 className="text-3xl sm:text-5xl text-primary max-w-3xl mx-auto">
                {t.solutions.cta.title}
              </h2>
              <p className="text-secondary text-lg max-w-2xl mx-auto">
                {t.solutions.cta.description}
              </p>
              <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
                <Link 
                  href="https://portal.infinitegz.com" 
                  className="relative isolate inline-flex shrink-0 items-center justify-center border font-mono text-base/6 uppercase tracking-widest gap-x-3 px-6 py-3 sm:text-sm border-[--btn-border] bg-[--btn-bg] text-[--btn-text] hover:border-[--btn-hover] hover:bg-[--btn-hover] rounded-full [--btn-bg:theme(colors.primary)] [--btn-border:theme(colors.primary)] [--btn-hover:theme(colors.primary/80%)] [--btn-text:theme(colors.background)]"
                >
                  <span>{t.common.getStarted}</span>
                </Link>
                <Link 
                  href="https://wa.me/60123456789" 
                  className="relative isolate inline-flex shrink-0 items-center justify-center border font-mono text-base/6 uppercase tracking-widest gap-x-3 px-6 py-3 sm:text-sm border-[--btn-border] bg-[--btn-bg] text-[--btn-text] hover:bg-[--btn-hover] rounded-full [--btn-bg:transparent] [--btn-border:theme(colors.primary/25%)] [--btn-hover:theme(colors.secondary/20%)] [--btn-text:theme(colors.primary)]"
                >
                  <span>{t.common.contactUs}</span>
                </Link>
              </div>
            </div>
          
      {/* 底部激光分隔线 */}
      <div className="absolute bottom-0 left-0 right-0">
        <div className="laser-divider"></div>
      </div>
          </div>
        </section>

        <Footer />
      </main>
    </>
  )
}
