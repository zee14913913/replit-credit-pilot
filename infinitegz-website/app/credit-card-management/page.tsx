'use client';

import { useState } from 'react';
import Link from 'next/link';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import ScrollProgress from '@/components/ScrollProgress';
import { useLanguage } from '@/contexts/LanguageContext';

export default function CreditCardManagementPage() {
  const { t } = useLanguage();
  const [selectedPlan, setSelectedPlan] = useState<'individual' | 'corporate' | 'loan'>('individual');

  return (
    <div className="min-h-screen bg-[rgb(10,10,10)]">
      <ScrollProgress />
      <Header />

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden pt-20">
        {/* Background gradient */}
        <div className="absolute inset-0 bg-gradient-to-b from-black via-[rgb(10,10,10)] to-[rgb(10,10,10)]" />
        
        {/* Animated background elements */}
        <div className="absolute inset-0 overflow-hidden opacity-20">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/30 rounded-full blur-3xl animate-pulse" />
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/30 rounded-full blur-3xl animate-pulse delay-1000" />
        </div>

        <div className="relative z-10 max-w-7xl mx-auto px-6 text-center">
          {/* Tag */}
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-500/10 border border-blue-500/20 mb-8">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
            </span>
            <span className="text-sm text-blue-400 font-medium">
              {t.cardManagement.hero.tag}
            </span>
          </div>

          {/* Main Title */}
          <h1 className="text-5xl md:text-7xl lg:text-8xl font-bold mb-8 leading-tight">
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-white via-blue-100 to-purple-100">
              {t.cardManagement.hero.title}
            </span>
          </h1>

          {/* Subtitle */}
          <p className="text-xl md:text-2xl text-gray-400 mb-12 max-w-3xl mx-auto leading-relaxed">
            {t.cardManagement.hero.subtitle}
          </p>

          {/* Key Benefits */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12 max-w-5xl mx-auto">
            {t.cardManagement.hero.benefits.map((benefit: any, index: number) => (
              <div 
                key={index}
                className="p-6 rounded-2xl bg-gradient-to-br from-white/5 to-white/[0.02] border border-white/10 backdrop-blur-sm hover:border-blue-500/30 transition-all duration-300"
              >
                <div className="text-3xl mb-3">{benefit.icon}</div>
                <div className="text-2xl md:text-3xl font-bold text-white mb-2">
                  {benefit.value}
                </div>
                <div className="text-sm text-gray-400">
                  {benefit.label}
                </div>
              </div>
            ))}
          </div>

          {/* CTAs */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-8">
            <Link 
              href="https://wa.me/60123456789"
              className="group px-8 py-4 rounded-full bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold hover:shadow-2xl hover:shadow-blue-500/50 transition-all duration-300 flex items-center gap-2"
            >
              <span>{t.cardManagement.hero.cta1}</span>
              <svg className="w-5 h-5 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
              </svg>
            </Link>
            <Link 
              href="#pricing"
              className="px-8 py-4 rounded-full border border-white/20 text-white font-semibold hover:bg-white/5 transition-all duration-300"
            >
              {t.cardManagement.hero.cta2}
            </Link>
          </div>

          {/* Social Proof */}
          <div className="text-sm text-gray-500">
            {t.cardManagement.hero.socialProof}
          </div>
        </div>

        {/* Laser divider */}
        <div className="absolute bottom-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-blue-500 to-transparent animate-pulse"></div>
      </section>

      {/* Pain Points Section */}
      <section className="relative py-24 overflow-hidden">
        <div className="max-w-7xl mx-auto px-6">
          {/* Section Header */}
          <div className="text-center mb-16">
            <div className="inline-block px-4 py-2 rounded-full bg-red-500/10 border border-red-500/20 mb-4">
              <span className="text-sm text-red-400 font-medium">
                {t.cardManagement.painPoints.tag}
              </span>
            </div>
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
              {t.cardManagement.painPoints.title}
            </h2>
            <p className="text-xl text-gray-400 max-w-3xl mx-auto">
              {t.cardManagement.painPoints.subtitle}
            </p>
          </div>

          {/* Pain Points Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
            {t.cardManagement.painPoints.points.map((point: any, index: number) => (
              <div 
                key={index}
                className="p-8 rounded-2xl bg-gradient-to-br from-red-500/5 to-red-500/[0.02] border border-red-500/20 hover:border-red-500/40 transition-all duration-300"
              >
                <div className="text-5xl mb-4">{point.icon}</div>
                <h3 className="text-2xl font-bold text-white mb-3">
                  {point.title}
                </h3>
                <p className="text-gray-400 mb-4">
                  {point.description}
                </p>
                <div className="text-red-400 font-semibold">
                  {point.impact}
                </div>
              </div>
            ))}
          </div>

          {/* Statistics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 p-8 rounded-2xl bg-gradient-to-br from-white/5 to-white/[0.02] border border-white/10">
            {t.cardManagement.painPoints.stats.map((stat: any, index: number) => (
              <div key={index} className="text-center">
                <div className="text-3xl md:text-4xl font-bold text-white mb-2">
                  {stat.value}
                </div>
                <div className="text-sm text-gray-400">
                  {stat.label}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Laser divider */}
        <div className="absolute bottom-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-blue-500 to-transparent animate-pulse"></div>
      </section>

      {/* Solutions Section */}
      <section className="relative py-24 overflow-hidden">
        <div className="max-w-7xl mx-auto px-6">
          {/* Section Header */}
          <div className="text-center mb-16">
            <div className="inline-block px-4 py-2 rounded-full bg-green-500/10 border border-green-500/20 mb-4">
              <span className="text-sm text-green-400 font-medium">
                {t.cardManagement.solutions.tag}
              </span>
            </div>
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
              {t.cardManagement.solutions.title}
            </h2>
            <p className="text-xl text-gray-400 max-w-3xl mx-auto">
              {t.cardManagement.solutions.subtitle}
            </p>
          </div>

          {/* Services Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {t.cardManagement.solutions.services.map((service: any, index: number) => (
              <div 
                key={index}
                className="group p-8 rounded-2xl bg-gradient-to-br from-white/5 to-white/[0.02] border border-white/10 hover:border-blue-500/50 transition-all duration-300 hover:transform hover:scale-105"
              >
                {/* Icon */}
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <span className="text-3xl">{service.icon}</span>
                </div>

                {/* Content */}
                <h3 className="text-2xl font-bold text-white mb-3">
                  {service.title}
                </h3>
                <p className="text-gray-400 mb-6">
                  {service.description}
                </p>

                {/* Benefits List */}
                <ul className="space-y-2">
                  {service.benefits.map((benefit: string, idx: number) => (
                    <li key={idx} className="flex items-start gap-2 text-sm text-gray-300">
                      <svg className="w-5 h-5 text-green-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span>{benefit}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>

        {/* Laser divider */}
        <div className="absolute bottom-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-blue-500 to-transparent animate-pulse"></div>
      </section>

      {/* Case Studies Section */}
      <section className="relative py-24 overflow-hidden">
        <div className="max-w-7xl mx-auto px-6">
          {/* Section Header */}
          <div className="text-center mb-16">
            <div className="inline-block px-4 py-2 rounded-full bg-purple-500/10 border border-purple-500/20 mb-4">
              <span className="text-sm text-purple-400 font-medium">
                {t.cardManagement.caseStudies.tag}
              </span>
            </div>
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
              {t.cardManagement.caseStudies.title}
            </h2>
            <p className="text-xl text-gray-400 max-w-3xl mx-auto">
              {t.cardManagement.caseStudies.subtitle}
            </p>
          </div>

          {/* Case Studies Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {t.cardManagement.caseStudies.cases.map((caseStudy: any, index: number) => (
              <div 
                key={index}
                className="p-8 rounded-2xl bg-gradient-to-br from-white/5 to-white/[0.02] border border-white/10 hover:border-purple-500/50 transition-all duration-300"
              >
                {/* Client Info */}
                <div className="flex items-center gap-4 mb-6">
                  <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center text-white font-bold text-xl">
                    {caseStudy.client.charAt(0)}
                  </div>
                  <div>
                    <div className="font-semibold text-white">{caseStudy.client}</div>
                    <div className="text-sm text-gray-400">{caseStudy.type}</div>
                  </div>
                </div>

                {/* Before/After */}
                <div className="space-y-4 mb-6">
                  <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20">
                    <div className="text-xs text-red-400 mb-2 font-semibold">
                      {t.cardManagement.caseStudies.before}
                    </div>
                    <div className="text-sm text-gray-300">
                      {caseStudy.before}
                    </div>
                  </div>
                  <div className="p-4 rounded-xl bg-green-500/10 border border-green-500/20">
                    <div className="text-xs text-green-400 mb-2 font-semibold">
                      {t.cardManagement.caseStudies.after}
                    </div>
                    <div className="text-sm text-gray-300">
                      {caseStudy.after}
                    </div>
                  </div>
                </div>

                {/* Results */}
                <div className="pt-6 border-t border-white/10">
                  <div className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-blue-400 mb-2">
                    {caseStudy.savings}
                  </div>
                  <div className="text-sm text-gray-400">
                    {caseStudy.period}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Laser divider */}
        <div className="absolute bottom-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-blue-500 to-transparent animate-pulse"></div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="relative py-24 overflow-hidden">
        <div className="max-w-7xl mx-auto px-6">
          {/* Section Header */}
          <div className="text-center mb-16">
            <div className="inline-block px-4 py-2 rounded-full bg-blue-500/10 border border-blue-500/20 mb-4">
              <span className="text-sm text-blue-400 font-medium">
                {t.cardManagement.pricing.tag}
              </span>
            </div>
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
              {t.cardManagement.pricing.title}
            </h2>
            <p className="text-xl text-gray-400 max-w-3xl mx-auto">
              {t.cardManagement.pricing.subtitle}
            </p>
          </div>

          {/* Plan Selector */}
          <div className="flex justify-center gap-4 mb-12">
            {(['individual', 'corporate', 'loan'] as const).map((plan) => (
              <button
                key={plan}
                onClick={() => setSelectedPlan(plan)}
                className={`px-6 py-3 rounded-full font-semibold transition-all duration-300 ${
                  selectedPlan === plan
                    ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg shadow-blue-500/50'
                    : 'bg-white/5 text-gray-400 hover:bg-white/10'
                }`}
              >
                {t.cardManagement.pricing.plans[plan].label}
              </button>
            ))}
          </div>

          {/* Pricing Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {t.cardManagement.pricing.plans[selectedPlan].options.map((option: any, index: number) => (
              <div 
                key={index}
                className={`relative p-8 rounded-2xl border transition-all duration-300 ${
                  option.recommended
                    ? 'bg-gradient-to-br from-blue-500/10 to-purple-500/10 border-blue-500/50 scale-105'
                    : 'bg-gradient-to-br from-white/5 to-white/[0.02] border-white/10 hover:border-blue-500/30'
                }`}
              >
                {option.recommended && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full bg-gradient-to-r from-blue-600 to-purple-600 text-white text-sm font-semibold">
                    {t.cardManagement.pricing.recommended}
                  </div>
                )}

                <div className="text-center mb-6">
                  <h3 className="text-2xl font-bold text-white mb-2">
                    {option.name}
                  </h3>
                  <div className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400 mb-2">
                    {option.price}
                  </div>
                  <div className="text-sm text-gray-400">
                    {option.period}
                  </div>
                </div>

                <ul className="space-y-3 mb-8">
                  {option.features.map((feature: string, idx: number) => (
                    <li key={idx} className="flex items-start gap-2 text-sm text-gray-300">
                      <svg className="w-5 h-5 text-green-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>

                <Link
                  href={option.cta.link}
                  className={`block w-full py-3 rounded-full text-center font-semibold transition-all duration-300 ${
                    option.recommended
                      ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:shadow-lg hover:shadow-blue-500/50'
                      : 'bg-white/5 text-white hover:bg-white/10'
                  }`}
                >
                  {option.cta.text}
                </Link>
              </div>
            ))}
          </div>
        </div>

        {/* Laser divider */}
        <div className="absolute bottom-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-blue-500 to-transparent animate-pulse"></div>
      </section>

      {/* Social Proof Section */}
      <section className="relative py-24 overflow-hidden">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {t.cardManagement.socialProof.stats.map((stat: any, index: number) => (
              <div key={index} className="text-center">
                <div className="text-5xl md:text-6xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400 mb-3">
                  {stat.value}
                </div>
                <div className="text-gray-400">
                  {stat.label}
                </div>
              </div>
            ))}
          </div>

          {/* Trust Badges */}
          <div className="mt-16 flex flex-wrap justify-center items-center gap-8">
            {t.cardManagement.socialProof.badges.map((badge: string, index: number) => (
              <div 
                key={index}
                className="px-6 py-3 rounded-full bg-white/5 border border-white/10 text-sm text-gray-300"
              >
                {badge}
              </div>
            ))}
          </div>
        </div>

        {/* Laser divider */}
        <div className="absolute bottom-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-blue-500 to-transparent animate-pulse"></div>
      </section>

      {/* FAQ Section */}
      <section className="relative py-24 overflow-hidden">
        <div className="max-w-4xl mx-auto px-6">
          {/* Section Header */}
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
              {t.cardManagement.faq.title}
            </h2>
            <p className="text-xl text-gray-400">
              {t.cardManagement.faq.subtitle}
            </p>
          </div>

          {/* FAQ Items */}
          <div className="space-y-6">
            {t.cardManagement.faq.questions.map((item: any, index: number) => (
              <details 
                key={index}
                className="group p-6 rounded-2xl bg-gradient-to-br from-white/5 to-white/[0.02] border border-white/10 hover:border-blue-500/30 transition-all duration-300"
              >
                <summary className="flex items-center justify-between cursor-pointer text-lg font-semibold text-white">
                  <span>{item.question}</span>
                  <svg className="w-5 h-5 text-gray-400 group-open:rotate-180 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </summary>
                <div className="mt-4 text-gray-400 leading-relaxed">
                  {item.answer}
                </div>
              </details>
            ))}
          </div>
        </div>

        {/* Laser divider */}
        <div className="absolute bottom-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-blue-500 to-transparent animate-pulse"></div>
      </section>

      {/* Final CTA Section */}
      <section className="relative py-24 overflow-hidden">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
            {t.cardManagement.finalCta.title}
          </h2>
          <p className="text-xl text-gray-400 mb-12">
            {t.cardManagement.finalCta.subtitle}
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-8">
            <Link 
              href="https://wa.me/60123456789"
              className="group px-8 py-4 rounded-full bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold hover:shadow-2xl hover:shadow-blue-500/50 transition-all duration-300 flex items-center gap-2"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
              </svg>
              <span>{t.cardManagement.finalCta.cta1}</span>
            </Link>
            <Link 
              href="https://portal.infinitegz.com/card-management"
              className="px-8 py-4 rounded-full border border-white/20 text-white font-semibold hover:bg-white/5 transition-all duration-300"
            >
              {t.cardManagement.finalCta.cta2}
            </Link>
          </div>

          {/* Related Services */}
          <div className="mt-16">
            <div className="text-sm text-gray-500 mb-4">
              {t.cardManagement.finalCta.relatedTitle}
            </div>
            <div className="flex flex-wrap justify-center gap-4">
              {t.cardManagement.finalCta.relatedServices.map((service: any, index: number) => (
                <Link
                  key={index}
                  href={service.link}
                  className="px-4 py-2 rounded-full bg-white/5 border border-white/10 text-sm text-gray-300 hover:border-blue-500/30 hover:text-white transition-all duration-300"
                >
                  {service.name}
                </Link>
              ))}
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
