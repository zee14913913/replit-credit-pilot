'use client'

import Header from '@/components/Header'
import Footer from '@/components/Footer'
import ScrollProgress from '@/components/ScrollProgress'
import Link from 'next/link'
import { useLanguage } from '@/contexts/LanguageContext'

export default function CareersPage() {
  const { t } = useLanguage()
  
  return (
    <>
      <ScrollProgress />
      <main className="min-h-screen bg-[rgb(10,10,10)]">
        <Header />
        
        {/* Hero Section */}
        <section className="relative pb-px">
          <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl flex min-h-screen flex-col justify-center">
            <div className="relative z-20 py-20 text-center">
              <div className="space-y-8">
                <div className="mono-tag text-secondary text-sm">
                  [ {t.careers.hero.tag} ]
                </div>
                
                <h1 className="text-primary mx-auto max-w-4xl text-balance text-5xl leading-tight tracking-tight md:text-7xl md:leading-tight lg:text-8xl lg:leading-tight">
                  {t.careers.hero.title}
                </h1>
                
                <p className="text-secondary mx-auto max-w-3xl text-lg md:text-xl leading-relaxed">
                  {t.careers.hero.description}
                </p>
              </div>
            </div>
          
      {/* 底部激光分隔线 */}
      <div className="absolute bottom-0 left-0 right-0">
        <div className="laser-divider"></div>
      </div>
          </div>
        </section>

        {/* Benefits Section */}
        <section className="py-16 sm:py-32 relative">
          <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl space-y-16">
            <div className="space-y-8">
              <div className="mono-tag flex items-center gap-2 text-sm text-secondary">
                <span>[</span> <span>{t.careers.benefits.tag}</span> <span>]</span>
              </div>
              <h2 className="text-balance text-3xl tracking-tight md:text-5xl lg:text-6xl text-primary max-w-3xl">
                {t.careers.benefits.title}
              </h2>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
              {t.careers.benefits.items.map((benefit, index) => (
                <div key={index} className="p-6 border border-border rounded-lg space-y-4 hover:border-primary/30 transition-colors">
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

        {/* Open Positions */}
        <section className="py-16 sm:py-32 relative">
          <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl space-y-16">
            <div className="space-y-8 text-center">
              <div className="mono-tag inline-flex items-center gap-2 text-sm text-secondary">
                <span>[</span> <span>{t.careers.jobs.tag}</span> <span>]</span>
              </div>
              <h2 className="text-balance text-3xl tracking-tight md:text-5xl text-primary mx-auto max-w-3xl">
                {t.careers.jobs.title}
              </h2>
            </div>

            <div className="space-y-4">
              {t.careers.jobs.positions.map((job, index) => (
                <Link
                  key={index}
                  href="#"
                  className="block p-6 border border-border rounded-lg hover:border-primary/30 hover:bg-secondary/5 transition-all group"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                    <div className="space-y-2">
                      <h3 className="text-xl text-primary group-hover:text-primary/80 transition-colors">{job.title}</h3>
                      <div className="flex flex-wrap gap-3 text-sm text-secondary">
                        <span className="mono-tag">{job.department}</span>
                        <span>•</span>
                        <span>{job.location}</span>
                        <span>•</span>
                        <span>{job.type}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-primary">
                      <span>{t.common.applyNow}</span>
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

        {/* CTA Section */}
        <section className="py-16 sm:py-32">
          <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl">
            <div className="border border-border rounded-2xl p-8 sm:p-16 text-center space-y-8 bg-gradient-to-b from-secondary/5 to-transparent">
              <h2 className="text-3xl sm:text-5xl text-primary max-w-3xl mx-auto">
                {t.careers.cta.title}
              </h2>
              <p className="text-secondary text-lg max-w-2xl mx-auto">
                {t.careers.cta.description}
              </p>
              <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
                <Link 
                  href="mailto:careers@infinitegz.com" 
                  className="relative isolate inline-flex shrink-0 items-center justify-center border font-mono text-base/6 uppercase tracking-widest gap-x-3 px-6 py-3 sm:text-sm border-[--btn-border] bg-[--btn-bg] text-[--btn-text] hover:border-[--btn-hover] hover:bg-[--btn-hover] rounded-full [--btn-bg:theme(colors.primary)] [--btn-border:theme(colors.primary)] [--btn-hover:theme(colors.primary/80%)] [--btn-text:theme(colors.background)]"
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
