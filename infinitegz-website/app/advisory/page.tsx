'use client'

import Header from '@/components/Header'
import Footer from '@/components/Footer'
import ScrollProgress from '@/components/ScrollProgress'
import Link from 'next/link'
import { useLanguage } from '@/contexts/LanguageContext'

export default function AdvisoryPage() {
  const { t } = useLanguage()
  
  return (
    <>
      <ScrollProgress />
      <main className="min-h-screen bg-[rgb(10,10,10)]">
        <Header />
        
        {/* Hero Section */}
        <section className="relative pb-px">
          <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl flex h-full flex-col justify-center">
            <div className="relative z-20 text-center space-y-8">
              <div className="mono-tag text-secondary text-sm">
                [ {t.advisory.hero.tag} ]
              </div>
              
              <h1 className="text-primary mx-auto max-w-4xl text-balance text-5xl leading-tight tracking-tight md:text-7xl md:leading-tight lg:text-8xl lg:leading-tight">
                {t.advisory.hero.title}
              </h1>
              
              <p className="text-secondary mx-auto max-w-3xl text-lg md:text-xl leading-relaxed">
                {t.advisory.hero.description}
              </p>
              
              <div className="flex flex-wrap items-center justify-center gap-4 pt-8">
                <Link 
                  href="https://portal.infinitegz.com/advisory" 
                  className="relative isolate inline-flex shrink-0 items-center justify-center border font-mono text-base/6 uppercase tracking-widest gap-x-3 px-6 py-3 sm:text-sm border-[--btn-border] bg-[--btn-bg] text-[--btn-text] hover:border-[--btn-hover] hover:bg-[--btn-hover] rounded-full [--btn-bg:theme(colors.primary)] [--btn-border:theme(colors.primary)] [--btn-hover:theme(colors.primary/80%)] [--btn-text:theme(colors.background)]"
                >
                  <span>{t.common.bookConsultation}</span>
                </Link>
                <Link 
                  href="https://wa.me/60123456789" 
                  className="relative isolate inline-flex shrink-0 items-center justify-center border font-mono text-base/6 uppercase tracking-widest gap-x-3 px-6 py-3 sm:text-sm border-[--btn-border] bg-[--btn-bg] text-[--btn-text] hover:bg-[--btn-hover] rounded-full [--btn-bg:transparent] [--btn-border:theme(colors.primary/25%)] [--btn-hover:theme(colors.secondary/20%)] [--btn-text:theme(colors.primary)]"
                >
                  <span>{t.common.whatsappUs}</span>
                </Link>
              </div>
            </div>
          
      {/* 底部激光分隔线 */}
      <div className="absolute bottom-0 left-0 right-0">
        <div className="laser-divider"></div>
      </div>
          </div>
        </section>

        {/* 8 Services Section */}
        <section className="py-16 sm:py-32 relative">
          <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl space-y-16 sm:space-y-32">
            <div className="space-y-12">
              <div className="mono-tag flex items-center gap-2 text-sm text-secondary">
                <span>[</span> <span>{t.advisory.services.tag}</span> <span>]</span>
              </div>
              <h2 className="text-balance text-3xl tracking-tight md:text-5xl lg:text-6xl text-primary max-w-3xl">
                {t.advisory.services.title}
              </h2>
            </div>

            <div className="grid lg:grid-cols-3 gap-px bg-border">
              {t.advisory.services.items.map((service, index) => (
                <div 
                  key={index}
                  className="group relative flex h-full flex-col space-y-4 p-8 bg-background from-secondary/10 via-transparent to-transparent hover:bg-gradient-to-b transition-all"
                >
                  <div className="border-primary/10 pointer-events-none absolute inset-0 isolate z-10 border opacity-0 group-hover:opacity-100">
                    <div className="bg-primary absolute -left-1 -top-1 z-10 size-2 -translate-x-px -translate-y-px"></div>
                    <div className="bg-primary absolute -right-1 -top-1 z-10 size-2 -translate-y-px translate-x-px"></div>
                    <div className="bg-primary absolute -bottom-1 -left-1 z-10 size-2 -translate-x-px translate-y-px"></div>
                    <div className="bg-primary absolute -bottom-1 -right-1 z-10 size-2 translate-x-px translate-y-px"></div>
                  </div>
                  
                  <div className="mono-tag text-xs text-secondary relative z-20">
                    {service.num}
                  </div>
                  
                  <h3 className="text-2xl text-primary group-hover:text-primary/90 transition-colors relative z-20">
                    {service.title}
                  </h3>
                  
                  <p className="text-secondary text-sm leading-relaxed group-hover:text-primary/80 transition-colors relative z-20">
                    {service.description}
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

        {/* Key Benefits */}
        <section className="py-16 sm:py-32 relative">
          <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl space-y-16">
            <div className="space-y-8 text-center">
              <div className="mono-tag inline-flex items-center gap-2 text-sm text-secondary">
                <span>[</span> <span>{t.advisory.benefits.tag}</span> <span>]</span>
              </div>
              <h2 className="text-balance text-3xl tracking-tight md:text-5xl text-primary mx-auto max-w-3xl">
                {t.advisory.benefits.title}
              </h2>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
              {t.advisory.benefits.items.map((benefit, index) => (
                <div key={index} className="p-6 border border-border rounded-lg space-y-4">
                  <div className="text-4xl">{benefit.icon}</div>
                  <h3 className="text-xl text-primary">{benefit.title}</h3>
                  <p className="text-secondary text-sm">{benefit.description}</p>
                </div>
              ))}
            </div>
          
      {/* 底部激光分隔线 */}
      <div className="absolute bottom-0 left-0 right-0">
        <div className="laser-divider"></div>
      </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-16 sm:py-32">
          <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl">
            <div className="border border-border rounded-2xl p-8 sm:p-16 text-center space-y-8 bg-gradient-to-b from-secondary/5 to-transparent">
              <h2 className="text-3xl sm:text-5xl text-primary max-w-3xl mx-auto">
                {t.advisory.cta.title}
              </h2>
              <p className="text-secondary text-lg max-w-2xl mx-auto">
                {t.advisory.cta.description}
              </p>
              <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
                <Link 
                  href="https://portal.infinitegz.com/advisory" 
                  className="relative isolate inline-flex shrink-0 items-center justify-center border font-mono text-base/6 uppercase tracking-widest gap-x-3 px-6 py-3 sm:text-sm border-[--btn-border] bg-[--btn-bg] text-[--btn-text] hover:border-[--btn-hover] hover:bg-[--btn-hover] rounded-full [--btn-bg:theme(colors.primary)] [--btn-border:theme(colors.primary)] [--btn-hover:theme(colors.primary/80%)] [--btn-text:theme(colors.background)]"
                >
                  <span>{t.common.bookConsultation}</span>
                </Link>
                <Link 
                  href="https://wa.me/60123456789" 
                  className="relative isolate inline-flex shrink-0 items-center justify-center border font-mono text-base/6 uppercase tracking-widest gap-x-3 px-6 py-3 sm:text-sm border-[--btn-border] bg-[--btn-bg] text-[--btn-text] hover:bg-[--btn-hover] rounded-full [--btn-bg:transparent] [--btn-border:theme(colors.primary/25%)] [--btn-hover:theme(colors.secondary/20%)] [--btn-text:theme(colors.primary)]"
                >
                  <span>{t.common.whatsappUs}</span>
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
