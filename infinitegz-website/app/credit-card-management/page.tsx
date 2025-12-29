'use client'

import Header from '@/components/Header'
import Footer from '@/components/Footer'
import ScrollProgress from '@/components/ScrollProgress'
import Link from 'next/link'
import { useLanguage } from '@/contexts/LanguageContext'
import { 
  CreditCard, 
  Bell, 
  ShoppingCart, 
  TrendingUp, 
  LifeBuoy,
  AlertTriangle,
  Clock,
  Layers
} from 'lucide-react'

export default function CreditCardManagementPage() {
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
                  [ {t.creditCard.hero.tag} ]
                </div>
                
                <div className="text-primary max-w-3xl text-balance text-4xl leading-[2.25rem] tracking-tight md:text-[5rem] md:leading-[5rem]">
                  {t.creditCard.hero.title}
                </div>
                
                <p className="text-secondary max-w-2xl text-lg">
                  {t.creditCard.hero.subtitle}
                </p>
                
                <p className="text-primary/80 max-w-xl text-base mono-tag">
                  [ {t.creditCard.hero.description} ]
                </p>
                
                <div className="flex flex-wrap items-center gap-4 pt-4">
                  <Link 
                    href="https://wa.me/60123456789" 
                    className="relative isolate inline-flex shrink-0 items-center justify-center border font-mono text-base/6 uppercase tracking-widest gap-x-3 px-4 py-2 sm:text-sm border-[--btn-border] bg-[--btn-bg] text-[--btn-text] hover:border-[--btn-hover] hover:bg-[--btn-hover] rounded-full [--btn-bg:theme(colors.primary)] [--btn-border:theme(colors.primary)] [--btn-hover:theme(colors.primary/80%)] [--btn-text:theme(colors.background)]"
                  >
                    <span className="size-2 animate-pulse rounded-full bg-accent"></span>
                    <span>{t.creditCard.hero.cta1}</span>
                  </Link>
                  <Link 
                    href="#calculator" 
                    className="relative isolate inline-flex shrink-0 items-center justify-center border font-mono text-base/6 uppercase tracking-widest gap-x-3 px-4 py-2 sm:text-sm border-[--btn-border] bg-[--btn-bg] text-[--btn-text] hover:bg-[--btn-hover] rounded-full [--btn-bg:transparent] [--btn-border:theme(colors.primary/25%)] [--btn-hover:theme(colors.secondary/20%)] [--btn-text:theme(colors.primary)]"
                  >
                    <span>{t.creditCard.hero.cta2}</span>
                  </Link>
                </div>
              </hgroup>
            </div>
            
            <div className="relative z-10 flex items-end justify-between gap-6 pb-4 pt-4 lg:min-h-[160px] lg:py-10">
              <div>
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="my-2 size-6">
                  <path fillRule="evenodd" d="M12 2.25a.75.75 0 0 1 .75.75v16.19l6.22-6.22a.75.75 0 1 1 1.06 1.06l-7.5 7.5a.75.75 0 0 1-1.06 0l-7.5-7.5a.75.75 0 1 1 1.06-1.06l6.22 6.22V3a.75.75 0 0 1 .75-.75Z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="text-right space-y-2">
                <p className="text-secondary text-sm mono-tag">[ {t.creditCard.hero.stats} ]</p>
                <div className="flex flex-wrap items-center justify-end gap-4 text-sm">
                  <span className="text-primary font-semibold">500+ {t.creditCard.hero.clients}</span>
                  <span className="text-secondary">|</span>
                  <span className="text-primary font-semibold">RM 50M+ {t.creditCard.hero.totalLimit}</span>
                  <span className="text-secondary">|</span>
                  <span className="text-primary font-semibold">RM 10M+ {t.creditCard.hero.saved}</span>
                </div>
              </div>
            </div>
          
            {/* 底部激光分隔线 */}
            <div className="absolute bottom-0 left-0 right-0">
              <div className="laser-divider"></div>
            </div>
          </div>
        </section>

        {/* Value Highlights Section - NEW */}
        <section className="py-16 sm:py-24 relative bg-gradient-to-b from-transparent via-secondary/5 to-transparent">
          <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl">
            <div className="grid md:grid-cols-2 lg:grid-cols-5 gap-6">
              {/* Value 1: Credit Limit */}
              <div className="group p-6 rounded-xl border border-primary/10 hover:border-primary/30 transition-all bg-background/50 backdrop-blur-sm">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-12 h-12 rounded-lg bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center">
                    <CreditCard size={24} className="text-primary" strokeWidth={1.5} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-primary font-semibold text-sm mb-1">信用额度提升</h3>
                    <p className="text-secondary text-xs leading-relaxed">RM 30K → RM 300K</p>
                  </div>
                </div>
              </div>

              {/* Value 2: 0% Interest */}
              <div className="group p-6 rounded-xl border border-primary/10 hover:border-primary/30 transition-all bg-background/50 backdrop-blur-sm">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-12 h-12 rounded-lg bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center">
                    <TrendingUp size={24} className="text-primary" strokeWidth={1.5} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-primary font-semibold text-sm mb-1">0% 利息期</h3>
                    <p className="text-secondary text-xs leading-relaxed">最长 12 个月免息</p>
                  </div>
                </div>
              </div>

              {/* Value 3: Emergency Fund */}
              <div className="group p-6 rounded-xl border border-primary/10 hover:border-primary/30 transition-all bg-background/50 backdrop-blur-sm">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-12 h-12 rounded-lg bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center">
                    <LifeBuoy size={24} className="text-primary" strokeWidth={1.5} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-primary font-semibold text-sm mb-1">应急资金</h3>
                    <p className="text-secondary text-xs leading-relaxed">24小时内可用</p>
                  </div>
                </div>
              </div>

              {/* Value 4: Credit Score */}
              <div className="group p-6 rounded-xl border border-primary/10 hover:border-primary/30 transition-all bg-background/50 backdrop-blur-sm">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-12 h-12 rounded-lg bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center">
                    <TrendingUp size={24} className="text-primary" strokeWidth={1.5} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-primary font-semibold text-sm mb-1">信用评分</h3>
                    <p className="text-secondary text-xs leading-relaxed">影响所有贷款利率</p>
                  </div>
                </div>
              </div>

              {/* Value 5: Extra Income */}
              <div className="group p-6 rounded-xl border border-primary/10 hover:border-primary/30 transition-all bg-background/50 backdrop-blur-sm">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-12 h-12 rounded-lg bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center">
                    <ShoppingCart size={24} className="text-primary" strokeWidth={1.5} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-primary font-semibold text-sm mb-1">额外收益</h3>
                    <p className="text-secondary text-xs leading-relaxed">积分返现 + 税务抵扣</p>
                  </div>
                </div>
              </div>
            </div>
            
            {/* 底部激光分隔线 */}
            <div className="absolute bottom-0 left-0 right-0">
              <div className="laser-divider"></div>
            </div>
          </div>
        </section>

        {/* Pain Points Section */}
        <section className="py-16 sm:py-32 relative">
          <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl space-y-16 sm:space-y-32">
            <div className="space-y-12">
              <div className="mono-tag flex items-center gap-2 text-sm text-secondary">
                <span>[</span> <span>{t.creditCard.painPoints.tag}</span> <span>]</span>
              </div>
              <h2 className="text-balance text-3xl tracking-tight md:text-4xl lg:text-5xl text-primary max-w-2xl">
                {t.creditCard.painPoints.title}
              </h2>
              <p className="text-secondary text-lg max-w-3xl">
                {t.creditCard.painPoints.description}
              </p>
            </div>

            <div className="grid lg:grid-cols-3 gap-px bg-border">
              {t.creditCard.painPoints.items.map((pain, index) => (
                <div key={index} className="group relative flex h-full flex-col space-y-4 p-8 bg-background from-secondary/10 via-transparent to-transparent hover:bg-gradient-to-b">
                  <div className="border-primary/10 pointer-events-none absolute inset-0 isolate z-10 border opacity-0 group-hover:opacity-100">
                    <div className="bg-primary absolute -left-1 -top-1 z-10 size-2 -translate-x-px -translate-y-px"></div>
                    <div className="bg-primary absolute -right-1 -top-1 z-10 size-2 -translate-y-px translate-x-px"></div>
                    <div className="bg-primary absolute -bottom-1 -left-1 z-10 size-2 -translate-x-px translate-y-px"></div>
                    <div className="bg-primary absolute -bottom-1 -right-1 z-10 size-2 translate-x-px translate-y-px"></div>
                  </div>
                  
                  <div className="mb-10 relative z-20">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-primary/20 to-accent/20 backdrop-blur-sm border border-primary/20 group-hover:border-primary/50 transition-all duration-300 group-hover:scale-110">
                      <div className="text-primary">
                        {pain.iconComponent}
                      </div>
                    </div>
                  </div>
                  
                  <div className="group max-w-sm grow relative z-20">
                    <h3 className="text-xl group-hover:text-primary text-primary mb-3">{pain.title}</h3>
                    <p className="text-secondary">
                      {pain.description}
                    </p>
                    <p className="text-primary/60 text-sm mt-3 mono-tag">
                      [ {pain.data} ]
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

        {/* Services Section */}
        <section id="services" className="py-16 sm:py-32 relative">
          <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl space-y-16 sm:space-y-32">
            <div className="space-y-12">
              <div className="mono-tag flex items-center gap-2 text-sm text-secondary">
                <span>[</span> <span>{t.creditCard.services.tag}</span> <span>]</span>
              </div>
              <h2 className="text-balance text-3xl tracking-tight md:text-4xl lg:text-5xl text-primary max-w-2xl">
                {t.creditCard.services.title}
              </h2>
            </div>

            <div className="grid lg:grid-cols-3 gap-px bg-border">
              {t.creditCard.services.items.map((service, index) => (
                <div key={index} className="group relative flex h-full flex-col space-y-4 p-8 bg-background from-secondary/10 via-transparent to-transparent hover:bg-gradient-to-b">
                  <div className="border-primary/10 pointer-events-none absolute inset-0 isolate z-10 border opacity-0 group-hover:opacity-100">
                    <div className="bg-primary absolute -left-1 -top-1 z-10 size-2 -translate-x-px -translate-y-px"></div>
                    <div className="bg-primary absolute -right-1 -top-1 z-10 size-2 -translate-y-px translate-x-px"></div>
                    <div className="bg-primary absolute -bottom-1 -left-1 z-10 size-2 -translate-x-px translate-y-px"></div>
                    <div className="bg-primary absolute -bottom-1 -right-1 z-10 size-2 translate-x-px translate-y-px"></div>
                  </div>
                  
                  <div className="mb-10 sm:mb-16 relative z-20">
                    <div className="inline-flex items-center justify-center w-14 h-14 rounded-xl bg-gradient-to-br from-primary/10 to-secondary/5 backdrop-blur-sm border border-primary/20 group-hover:border-primary/60 transition-all duration-300 group-hover:scale-105 group-hover:rotate-3">
                      <div className="text-primary group-hover:text-accent transition-colors duration-300">
                        {service.iconComponent}
                      </div>
                    </div>
                  </div>
                  
                  <div className="group max-w-sm grow relative z-20">
                    <h3 className="text-xl group-hover:text-primary text-primary mb-3">{service.title}</h3>
                    <p className="text-secondary">
                      {service.description}
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

        {/* Case Studies Section */}
        <section className="py-16 sm:py-32 relative">
          <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl space-y-16">
            <div className="space-y-8 text-center">
              <div className="mono-tag inline-flex items-center gap-2 text-sm text-secondary">
                <span>[</span> <span>{t.creditCard.cases.tag}</span> <span>]</span>
              </div>
              <h2 className="text-balance text-3xl tracking-tight md:text-5xl text-primary mx-auto max-w-3xl">
                {t.creditCard.cases.title}
              </h2>
            </div>

            <div className="grid md:grid-cols-3 gap-8">
              {t.creditCard.cases.items.map((caseItem, index) => (
                <div key={index} className="p-8 border border-border rounded-lg space-y-6 hover:border-primary/50 transition-all">
                  <div className="mono-tag text-sm text-secondary">{caseItem.num}</div>
                  <h3 className="text-2xl text-primary">{caseItem.name}</h3>
                  
                  <div className="space-y-4">
                    <div className="p-4 rounded-lg bg-secondary/5">
                      <p className="text-secondary text-xs mb-2">{t.creditCard.cases.before}</p>
                      <p className="text-secondary text-sm">{caseItem.before}</p>
                    </div>
                    
                    <div className="p-4 rounded-lg bg-secondary/5">
                      <p className="text-secondary text-xs mb-2">{t.creditCard.cases.after}</p>
                      <p className="text-secondary text-sm">{caseItem.after}</p>
                    </div>
                  </div>
                  
                  <div className="pt-4 border-t border-border">
                    <p className="text-secondary text-sm mb-1">{t.creditCard.cases.result}</p>
                    <p className="text-primary text-3xl font-bold">{caseItem.savings}</p>
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

        {/* Pricing Section */}
        <section className="py-16 sm:py-32 relative">
          <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl space-y-16">
            <div className="space-y-8 text-center">
              <div className="mono-tag inline-flex items-center gap-2 text-sm text-secondary">
                <span>[</span> <span>{t.creditCard.pricing.tag}</span> <span>]</span>
              </div>
              <h2 className="text-balance text-3xl tracking-tight md:text-5xl text-primary mx-auto max-w-3xl">
                {t.creditCard.pricing.title}
              </h2>
            </div>

            <div className="grid md:grid-cols-3 gap-8">
              {t.creditCard.pricing.plans.map((plan, index) => (
                <div 
                  key={index} 
                  className={`p-8 border rounded-2xl space-y-6 transition-all ${
                    plan.featured 
                      ? 'border-primary bg-gradient-to-b from-primary/5 to-transparent' 
                      : 'border-border hover:border-primary/50'
                  }`}
                >
                  <div>
                    <h3 className="text-2xl text-primary mb-2">{plan.name}</h3>
                    <p className="text-secondary text-sm">{plan.description}</p>
                  </div>
                  
                  <div className="py-6">
                    <div className="text-primary text-4xl font-bold mb-2">{plan.price}</div>
                    <p className="text-secondary text-sm">{plan.period}</p>
                  </div>
                  
                  <ul className="space-y-3">
                    {plan.features.map((feature, fIndex) => (
                      <li key={fIndex} className="flex items-start gap-3 text-secondary text-sm">
                        <svg className="w-5 h-5 text-primary mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span>{feature}</span>
                      </li>
                    ))}
                  </ul>
                  
                  <Link
                    href={plan.link}
                    className={`block w-full text-center py-3 rounded-full font-mono text-sm uppercase tracking-widest transition-all ${
                      plan.featured
                        ? 'bg-primary text-background hover:bg-primary/90'
                        : 'border border-primary/30 text-primary hover:bg-primary/10'
                    }`}
                  >
                    {plan.cta}
                  </Link>
                </div>
              ))}
            </div>
          
            {/* 底部激光分隔线 */}
            <div className="absolute bottom-0 left-0 right-0">
              <div className="laser-divider"></div>
            </div>
          </div>
        </section>

        {/* Social Proof Section */}
        <section className="py-16 sm:py-32 relative">
          <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl">
            <div className="border border-border rounded-2xl p-8 sm:p-16 bg-gradient-to-b from-secondary/5 to-transparent">
              <div className="grid md:grid-cols-4 gap-8 text-center">
                {t.creditCard.social.stats.map((stat, index) => (
                  <div key={index} className="space-y-2">
                    <div className="text-primary text-4xl md:text-5xl font-bold">{stat.value}</div>
                    <div className="text-secondary text-sm">{stat.label}</div>
                  </div>
                ))}
              </div>
              
              <div className="mt-12 pt-8 border-t border-border flex flex-wrap items-center justify-center gap-6 text-sm text-secondary">
                <div className="flex items-center gap-2">
                  <svg className="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                  <span>{t.creditCard.social.compliance}</span>
                </div>
                <div className="flex items-center gap-2">
                  <svg className="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                  <span>{t.creditCard.social.insurance}</span>
                </div>
              </div>
            </div>
          
            {/* 底部激光分隔线 */}
            <div className="absolute bottom-0 left-0 right-0">
              <div className="laser-divider"></div>
            </div>
          </div>
        </section>

        {/* FAQ + CTA Section */}
        <section className="py-16 sm:py-32">
          <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl space-y-16">
            {/* FAQ */}
            <div className="space-y-8">
              <div className="space-y-4 text-center">
                <div className="mono-tag inline-flex items-center gap-2 text-sm text-secondary">
                  <span>[</span> <span>{t.creditCard.faq.tag}</span> <span>]</span>
                </div>
                <h2 className="text-balance text-3xl tracking-tight md:text-5xl text-primary mx-auto max-w-3xl">
                  {t.creditCard.faq.title}
                </h2>
              </div>
              
              <div className="max-w-3xl mx-auto space-y-4">
                {t.creditCard.faq.items.map((faq, index) => (
                  <details key={index} className="group border border-border rounded-lg">
                    <summary className="flex items-center justify-between p-6 cursor-pointer">
                      <h3 className="text-primary font-semibold">{faq.question}</h3>
                      <svg className="w-5 h-5 text-secondary group-open:rotate-180 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </summary>
                    <div className="px-6 pb-6">
                      <p className="text-secondary">{faq.answer}</p>
                    </div>
                  </details>
                ))}
              </div>
            </div>

            {/* CTA */}
            <div className="border border-border rounded-2xl p-8 sm:p-16 text-center space-y-8 bg-gradient-to-b from-secondary/5 to-transparent">
              <h2 className="text-3xl sm:text-5xl text-primary max-w-3xl mx-auto">
                {t.creditCard.cta.title}
              </h2>
              <p className="text-secondary text-lg max-w-2xl mx-auto">
                {t.creditCard.cta.description}
              </p>
              <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
                <Link 
                  href="https://wa.me/60123456789" 
                  className="relative isolate inline-flex shrink-0 items-center justify-center border font-mono text-base/6 uppercase tracking-widest gap-x-3 px-6 py-3 sm:text-sm border-[--btn-border] bg-[--btn-bg] text-[--btn-text] hover:border-[--btn-hover] hover:bg-[--btn-hover] rounded-full [--btn-bg:theme(colors.primary)] [--btn-border:theme(colors.primary)] [--btn-hover:theme(colors.primary/80%)] [--btn-text:theme(colors.background)]"
                >
                  <span>{t.common.whatsappUs}</span>
                </Link>
                <Link 
                  href="https://portal.infinitegz.com/credit-card" 
                  className="relative isolate inline-flex shrink-0 items-center justify-center border font-mono text-base/6 uppercase tracking-widest gap-x-3 px-6 py-3 sm:text-sm border-[--btn-border] bg-[--btn-bg] text-[--btn-text] hover:bg-[--btn-hover] rounded-full [--btn-bg:transparent] [--btn-border:theme(colors.primary/25%)] [--btn-hover:theme(colors.secondary/20%)] [--btn-text:theme(colors.primary)]"
                >
                  <span>{t.common.bookConsultation}</span>
                </Link>
              </div>
              
              {/* Related Services */}
              <div className="pt-8 mt-8 border-t border-border">
                <p className="text-secondary text-sm mb-4">{t.creditCard.cta.relatedServices}</p>
                <div className="flex flex-wrap items-center justify-center gap-3">
                  <Link href="/creditpilot" className="text-primary hover:underline text-sm">
                    {t.nav.creditpilot}
                  </Link>
                  <span className="text-secondary">•</span>
                  <Link href="/advisory" className="text-primary hover:underline text-sm">
                    {t.nav.advisory}
                  </Link>
                  <span className="text-secondary">•</span>
                  <Link href="/solutions" className="text-primary hover:underline text-sm">
                    {t.nav.solutions}
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </section>

        <Footer />
      </main>
    </>
  )
}
