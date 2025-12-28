'use client'

import Header from '@/components/Header'
import Footer from '@/components/Footer'
import ScrollProgress from '@/components/ScrollProgress'
import Link from 'next/link'
import { useLanguage } from '@/contexts/LanguageContext'

export default function CreditPilotPage() {
  const { t } = useLanguage()
  
  return (
    <>
      <ScrollProgress />
      <main className="min-h-screen bg-[rgb(10,10,10)]">
        <Header />
        
        {/* Hero Section */}
        <section className="relative pb-px">
          <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl flex h-full flex-col">
            <div className="relative z-20 mt-20 flex h-full w-full items-center">
              <hgroup className="space-y-8">
                <div className="mono-tag text-secondary text-sm">
                  [ {t.creditpilot.hero.tag} ]
                </div>
                
                <div className="text-primary max-w-3xl text-balance text-4xl leading-[2.25rem] tracking-tight md:text-[5rem] md:leading-[5rem]">
                  {t.creditpilot.hero.title}
                </div>
                
                <p className="text-secondary max-w-2xl text-lg">
                  {t.creditpilot.hero.subtitle}
                </p>
                
                <div>
                  <div className="flex gap-3 sm:flex-row">
                    <Link 
                      href="https://portal.infinitegz.com/creditpilot" 
                      className="relative isolate inline-flex shrink-0 items-center justify-center border font-mono text-base/6 uppercase tracking-widest gap-x-3 px-4 py-2 sm:text-sm border-[--btn-border] bg-[--btn-bg] text-[--btn-text] hover:border-[--btn-hover] hover:bg-[--btn-hover] rounded-full [--btn-bg:theme(colors.primary)] [--btn-border:theme(colors.primary)] [--btn-hover:theme(colors.primary/80%)] [--btn-text:theme(colors.background)]"
                    >
                      <span className="size-2 animate-pulse rounded-full bg-accent"></span>
                      <span>{t.creditpilot.hero.cta1}</span>
                    </Link>
                  </div>
                </div>
              </hgroup>
            </div>
            
            <div className="relative z-10 flex items-end justify-between gap-6 pb-4 pt-4 lg:min-h-[160px] lg:py-10">
              <div>
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="my-2 size-6">
                  <path fillRule="evenodd" d="M12 2.25a.75.75 0 0 1 .75.75v16.19l6.22-6.22a.75.75 0 1 1 1.06 1.06l-7.5 7.5a.75.75 0 0 1-1.06 0l-7.5-7.5a.75.75 0 1 1 1.06-1.06l6.22 6.22V3a.75.75 0 0 1 .75-.75Z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="flex flex-col items-end gap-6 sm:gap-8 md:flex-row lg:gap-12">
                <div className="flex flex-col items-end gap-3 sm:flex-row">
                  <Link 
                    href="#features" 
                    className="relative isolate inline-flex shrink-0 items-center justify-center border font-mono text-base/6 uppercase tracking-widest gap-x-3 px-4 py-2 sm:text-sm border-[--btn-border] bg-[--btn-bg] text-[--btn-text] hover:bg-[--btn-hover] rounded-full [--btn-bg:transparent] [--btn-border:theme(colors.primary/25%)] [--btn-hover:theme(colors.secondary/20%)] [--btn-text:theme(colors.primary)]"
                  >
                    <span>{t.common.learnMore}</span>
                  </Link>
                </div>
              </div>
            </div>
          
      {/* 底部激光分隔线 */}
      <div className="absolute bottom-0 left-0 right-0">
        <div className="laser-divider"></div>
      </div>
          </div>
        </section>

        {/* Capabilities Section */}
        <section id="features" className="py-16 sm:py-32 relative">
          <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl space-y-16 sm:space-y-32">
            <div className="space-y-12">
              <div className="mono-tag flex items-center gap-2 text-sm text-secondary">
                <span>[</span> <span>{t.creditpilot.capabilities.tag}</span> <span>]</span>
              </div>
              <h2 className="text-balance text-3xl tracking-tight md:text-4xl lg:text-5xl text-primary max-w-2xl">
                {t.creditpilot.capabilities.title}
              </h2>
            </div>

            <div className="grid lg:grid-cols-3 gap-px bg-border">
              {t.creditpilot.capabilities.features.map((feature, index) => (
                <div key={index} className="group relative flex h-full flex-col space-y-4 p-8 bg-background from-secondary/10 via-transparent to-transparent hover:bg-gradient-to-b">
                  <div className="border-primary/10 pointer-events-none absolute inset-0 isolate z-10 border opacity-0 group-hover:opacity-100">
                    <div className="bg-primary absolute -left-1 -top-1 z-10 size-2 -translate-x-px -translate-y-px"></div>
                    <div className="bg-primary absolute -right-1 -top-1 z-10 size-2 -translate-y-px translate-x-px"></div>
                    <div className="bg-primary absolute -bottom-1 -left-1 z-10 size-2 -translate-x-px translate-y-px"></div>
                    <div className="bg-primary absolute -bottom-1 -right-1 z-10 size-2 translate-x-px translate-y-px"></div>
                  </div>
                  
                  <div className="text-primary mb-10 size-10 sm:mb-16 relative z-20">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="1"/>
                      <path d="M12 6v6l4 2" stroke="currentColor" strokeWidth="1" strokeLinecap="round"/>
                    </svg>
                  </div>
                  
                  <div className="group max-w-sm grow relative z-20">
                    <h3 className="text-xl group-hover:text-primary text-primary">{feature.title}</h3>
                    <p className="text-secondary mt-4">
                      {feature.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          
      {/* 底部激光分隔线 */}
      <div className="absolute bottom-0 left-0 right-0">
        <div className="laser-divider"></div>
      </div>
          </div>
        </section>

        {/* How It Works */}
        <section className="py-16 sm:py-32 relative">
          <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl space-y-16">
            <div className="space-y-8 text-center">
              <div className="mono-tag inline-flex items-center gap-2 text-sm text-secondary">
                <span>[</span> <span>{t.creditpilot.howItWorks.tag}</span> <span>]</span>
              </div>
              <h2 className="text-balance text-3xl tracking-tight md:text-5xl text-primary mx-auto max-w-3xl">
                {t.creditpilot.howItWorks.title}
              </h2>
            </div>

            <div className="grid md:grid-cols-3 gap-8">
              {t.creditpilot.howItWorks.steps.map((step, index) => (
                <div key={index} className="p-8 border border-border rounded-lg space-y-4">
                  <div className="mono-tag text-sm text-secondary">{step.number}</div>
                  <h3 className="text-2xl text-primary">{step.title}</h3>
                  <p className="text-secondary">{step.description}</p>
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
                {t.creditpilot.cta.title}
              </h2>
              <p className="text-secondary text-lg max-w-2xl mx-auto">
                {t.creditpilot.cta.description}
              </p>
              <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
                <Link 
                  href="https://portal.infinitegz.com/creditpilot" 
                  className="relative isolate inline-flex shrink-0 items-center justify-center border font-mono text-base/6 uppercase tracking-widest gap-x-3 px-6 py-3 sm:text-sm border-[--btn-border] bg-[--btn-bg] text-[--btn-text] hover:border-[--btn-hover] hover:bg-[--btn-hover] rounded-full [--btn-bg:theme(colors.primary)] [--btn-border:theme(colors.primary)] [--btn-hover:theme(colors.primary/80%)] [--btn-text:theme(colors.background)]"
                >
                  <span>{t.creditpilot.cta.buttonText}</span>
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
