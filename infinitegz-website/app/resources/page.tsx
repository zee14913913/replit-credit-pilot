'use client'

import Header from '@/components/Header'
import Footer from '@/components/Footer'
import ScrollProgress from '@/components/ScrollProgress'
import Link from 'next/link'
import { useLanguage } from '@/contexts/LanguageContext'

export default function ResourcesPage() {
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
                  [ {t.resources.hero.tag} ]
                </div>
                
                <h1 className="text-primary mx-auto max-w-4xl text-balance text-5xl leading-tight tracking-tight md:text-7xl md:leading-tight lg:text-8xl lg:leading-tight">
                  {t.resources.hero.title}
                </h1>
                
                <p className="text-secondary mx-auto max-w-3xl text-lg md:text-xl leading-relaxed">
                  {t.resources.hero.description}
                </p>
              </div>
            </div>
          
      {/* 底部激光分隔线 */}
      <div className="absolute bottom-0 left-0 right-0">
        <div className="laser-divider"></div>
      </div>
          </div>
        </section>

        {/* Stats Section */}
        <section className="py-16 sm:py-32 relative">
          <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl">
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
              {t.resources.stats.map((stat, index) => (
                <div key={index} className="p-8 border border-border rounded-lg text-center space-y-4">
                  <div className="text-5xl font-light text-primary">{stat.number}</div>
                  <h3 className="text-xl text-primary">{stat.title}</h3>
                  <p className="text-secondary text-sm">{stat.description}</p>
                </div>
              ))}
            </div>
          
      {/* 底部激光分隔线 */}
      <div className="absolute bottom-0 left-0 right-0">
        <div className="laser-divider"></div>
      </div>
          </div>
        </section>

        {/* Timeline Section */}
        <section className="py-16 sm:py-32 relative">
          <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl space-y-16">
            <div className="space-y-8 text-center">
              <div className="mono-tag inline-flex items-center gap-2 text-sm text-secondary">
                <span>[</span> <span>{t.resources.timeline.tag}</span> <span>]</span>
              </div>
              <h2 className="text-balance text-3xl tracking-tight md:text-5xl text-primary mx-auto max-w-3xl">
                {t.resources.timeline.title}
              </h2>
            </div>

            <div className="space-y-8">
              {t.resources.timeline.milestones.map((milestone, index) => (
                <div key={index} className="flex gap-8 items-start">
                  <div className="mono-tag text-primary w-20 flex-shrink-0">{milestone.year}</div>
                  <div className="flex-grow">
                    <h3 className="text-2xl text-primary mb-2">{milestone.title}</h3>
                    <p className="text-secondary">{milestone.description}</p>
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

        <Footer />
      </main>
    </>
  )
}
