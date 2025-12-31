'use client'

import Header from '@/components/Header'
import Footer from '@/components/Footer'
import ScrollProgress from '@/components/ScrollProgress'
import Link from 'next/link'
import { useLanguage } from '@/contexts/LanguageContext'
import { getNews } from '@/lib/newsLoader'
import { useMemo } from 'react'

export default function NewsPage() {
  const { t, language } = useLanguage()
  
  // Dynamically load news based on current language
  const newsItems = useMemo(() => getNews(language), [language])
  
  return (
    <>
      <ScrollProgress />
      <main className="min-h-screen bg-[rgb(10,10,10)]">
        <Header />
        
        {/* Hero Section */}
        <section className="relative pb-px">
          <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl flex min-h-screen flex-col justify-center">
            <div className="relative z-20 py-24 text-center">
              <div className="space-y-12">
                <div className="mono-tag text-white text-sm" style={{ textShadow: '1px 1px 3px rgba(0,0,0,0.7), 0 0 10px rgba(255,255,255,0.2)' }}>
                  [ {t.news.hero.tag} ]
                </div>
                
                <h1 className="text-white mx-auto max-w-4xl text-balance text-5xl leading-tight tracking-tight md:text-7xl md:leading-tight lg:text-8xl lg:leading-tight font-bold" style={{ textShadow: '2px 2px 8px rgba(0,0,0,0.9), 0 0 20px rgba(255,255,255,0.3)' }}>
                  {t.news.hero.title}
                </h1>
                
                <p className="text-white mx-auto max-w-3xl text-lg md:text-xl leading-relaxed" style={{ textShadow: '1px 1px 4px rgba(0,0,0,0.8), 0 0 15px rgba(255,255,255,0.2)' }}>
                  {t.news.hero.description}
                </p>
              </div>
            </div>
          
      {/* 底部激光分隔线 */}
      <div className="absolute bottom-0 left-0 right-0">
        <div className="laser-divider"></div>
      </div>
          </div>
        </section>

        {/* News Grid */}
        <section className="pt-24 pb-16 sm:pt-40 sm:pb-32">
          <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl space-y-20">
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-10 lg:gap-12">
              {newsItems.map((news) => (
                <Link
                  key={news.id}
                  href="#"
                  className="group p-8 border border-border rounded-lg hover:border-primary/30 hover:bg-secondary/5 transition-all space-y-6"
                >
                  <div className="mono-tag text-xs text-zinc-200" style={{ textShadow: '1px 1px 2px rgba(0,0,0,0.6)' }}>{news.category}</div>
                  <h3 className="text-xl text-white group-hover:text-zinc-100 transition-colors font-semibold" style={{ textShadow: '2px 2px 6px rgba(0,0,0,0.8), 0 0 15px rgba(255,255,255,0.2)' }}>
                    {news.title}
                  </h3>
                  <div className="flex items-center justify-between text-sm text-zinc-300" style={{ textShadow: '1px 1px 2px rgba(0,0,0,0.6)' }}>
                    <span>{news.date}</span>
                    <div className="flex items-center gap-2 text-primary">
                      <span>{t.common.readMore}</span>
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

        <Footer />
      </main>
    </>
  )
}
