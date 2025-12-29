'use client';

import Link from 'next/link';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import ScrollProgress from '@/components/ScrollProgress';
import DSRCalculator from '@/components/DSRCalculator';
import { useLanguage } from '@/contexts/LanguageContext';
import { 
  Database, 
  Sparkles, 
  TrendingUp, 
  RefreshCw, 
  Target,
  AlertTriangle,
  Clock,
  Layers,
  CheckCircle,
  ArrowRight
} from 'lucide-react';

export default function FinancialOptimizationPage() {
  const { t } = useLanguage();

  return (
    <div className="min-h-screen bg-background text-foreground">
      <ScrollProgress />
      <Header />
      
      {/* Hero Section */}
      <section className="relative min-h-[90vh] flex items-center justify-center overflow-hidden pt-20">
        {/* Gradient Background */}
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-accent/5 to-background" />
        
        {/* Animated Grid */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute inset-0" style={{
            backgroundImage: 'linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px)',
            backgroundSize: '50px 50px'
          }} />
        </div>

        <div className="relative z-10 max-w-7xl mx-auto px-6 text-center">
          {/* Tag */}
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 mb-6">
            <Database className="w-4 h-4 text-primary" />
            <span className="text-sm font-medium text-primary uppercase tracking-wider">
              {t.financialOptimization.hero.tag}
            </span>
          </div>

          {/* Main Title */}
          <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
            <span className="bg-gradient-to-r from-primary via-accent to-primary bg-clip-text text-transparent animate-gradient">
              {t.financialOptimization.hero.title}
            </span>
          </h1>

          {/* Subtitle */}
          <p className="text-xl md:text-2xl text-muted-foreground mb-8 max-w-4xl mx-auto">
            {t.financialOptimization.hero.subtitle}
          </p>

          {/* Description */}
          <p className="text-lg text-muted-foreground mb-12 max-w-3xl mx-auto">
            {t.financialOptimization.hero.description}
          </p>

          {/* CTAs */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12">
            <a
              href="#calculator"
              className="px-8 py-4 rounded-full bg-primary text-black font-bold hover:bg-primary/90 transition-all duration-300 hover:scale-105 shadow-lg shadow-primary/20"
            >
              {t.financialOptimization.hero.cta1}
            </a>
            <a
              href="https://wa.me/60123456789"
              target="_blank"
              rel="noopener noreferrer"
              className="px-8 py-4 rounded-full bg-muted text-foreground font-bold hover:bg-muted/80 transition-all duration-300 hover:scale-105 flex items-center gap-2"
            >
              {t.financialOptimization.hero.cta2}
              <ArrowRight className="w-5 h-5" />
            </a>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 max-w-5xl mx-auto">
            {t.financialOptimization.hero.stats.map((stat) => (
              <div
                key={stat.label}
                className="p-6 rounded-lg bg-gradient-to-br from-muted/50 to-background border border-border hover:border-primary transition-colors"
              >
                <div className="text-3xl md:text-4xl font-bold text-primary mb-2">
                  {stat.value}
                </div>
                <div className="text-sm text-muted-foreground">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom Laser Divider */}
        <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-primary to-transparent" />
      </section>

      {/* 5 Core Values */}
      <section className="py-32 relative">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 mb-4">
              <Sparkles className="w-4 h-4 text-primary" />
              <span className="text-sm font-medium text-primary uppercase tracking-wider">
                Core Advantages
              </span>
            </div>
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              5 Professional Services
            </h2>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
              Comprehensive DSR optimization, maximizing your loan capacity
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              {
                icon: Database,
                title: '8 Banks DSR Standard Comparison',
                description: 'Maybank: 40-70% | CIMB: 65-75% | Hong Leong: 60-80%. Find the most lenient bank, avoid rejection.',
                data: 'Success rate +80%',
                color: 'primary'
              },
              {
                icon: Sparkles,
                title: 'Intelligent Bank Recommendation System',
                description: 'AI analyzes your identity, income, employment type. Recommends the 3 most suitable banks.',
                data: 'AI-Powered',
                color: 'accent'
              },
              {
                icon: TrendingUp,
                title: 'Self-Employed Income Maximization',
                description: 'RHB only recognizes 60%, Hong Leong recognizes 90%. Monthly income RM10K, recognition diff RM3K!',
                data: 'Recognition diff up to RM5K/month',
                color: 'primary'
              },
              {
                icon: RefreshCw,
                title: 'Debt Restructuring Plan',
                description: 'Consolidate high-interest debts, reduce monthly payment pressure.',
                data: 'Monthly payment -RM 500-2,000',
                color: 'accent'
              },
              {
                icon: Target,
                title: '3-Year Financial Growth Roadmap',
                description: 'Not just solving current loans, planning future financing strategies.',
                data: 'Save RM 50K-200K interest',
                color: 'primary'
              },
            ].map((value, index) => (
              <div
                key={index}
                className="group relative p-8 rounded-2xl bg-gradient-to-br from-muted/30 to-background border border-border hover:border-primary transition-all duration-300 hover:-translate-y-2"
              >
                {/* Icon */}
                <div className={`w-14 h-14 rounded-xl bg-gradient-to-br from-${value.color} to-${value.color}/50 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300`}>
                  <value.icon className="w-7 h-7 text-black" strokeWidth={1.5} />
                </div>

                {/* Title */}
                <h3 className="text-xl font-bold mb-3 group-hover:text-primary transition-colors">
                  {value.title}
                </h3>

                {/* Description */}
                <p className="text-muted-foreground mb-4 leading-relaxed">
                  {value.description}
                </p>

                {/* Data */}
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20">
                  <span className="text-sm font-bold text-primary">{value.data}</span>
                </div>

                {/* Hover Effect */}
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-primary/0 to-accent/0 group-hover:from-primary/5 group-hover:to-accent/5 transition-all duration-300 pointer-events-none" />
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 3 Pain Points */}
      <section className="py-32 relative bg-muted/30">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-red-500/10 border border-red-500/20 mb-4">
              <AlertTriangle className="w-4 h-4 text-red-500" />
              <span className="text-sm font-medium text-red-500 uppercase tracking-wider">
                Common Challenges
              </span>
            </div>
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              3 Major Financing Obstacles
            </h2>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
              These problems prevent thousands of businesses from obtaining financing
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: AlertTriangle,
                title: 'DSR Exceeds, Loan Rejected',
                description: '60% of loan applications rejected due to DSR exceeding limit. Different banks have vastly different standards (40%-80%).',
                data: 'RM 10B+ unmet loan demand',
                color: 'red'
              },
              {
                icon: Clock,
                title: "Don't Know Which Bank Easiest to Approve",
                description: '8 banks have huge standard differences. Choosing wrong bank = wasting time + affecting credit record.',
                data: 'Wrong bank = 3 months wasted',
                color: 'yellow'
              },
              {
                icon: Layers,
                title: 'Self-Employed Income Too Discounted',
                description: 'Bank recognition rate 60%-90%. Monthly income RM10K, might only recognize RM6K-9K.',
                data: 'Recognition diff up to RM5K/month',
                color: 'orange'
              },
            ].map((pain, index) => (
              <div
                key={index}
                className="group relative p-8 rounded-2xl bg-gradient-to-br from-background to-muted border-2 border-border hover:border-red-500/50 transition-all duration-300"
              >
                {/* Icon */}
                <div className={`w-16 h-16 rounded-xl bg-${pain.color}-500/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300`}>
                  <pain.icon className={`w-8 h-8 text-${pain.color}-500`} strokeWidth={1.5} />
                </div>

                {/* Title */}
                <h3 className="text-2xl font-bold mb-4">{pain.title}</h3>

                {/* Description */}
                <p className="text-muted-foreground mb-6 leading-relaxed">
                  {pain.description}
                </p>

                {/* Data */}
                <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full bg-${pain.color}-500/10 border border-${pain.color}-500/20`}>
                  <span className={`text-sm font-bold text-${pain.color}-500`}>{pain.data}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Professional DSR Calculator */}
      <section id="calculator" className="py-32 relative">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 mb-4">
              <Database className="w-4 h-4 text-primary" />
              <span className="text-sm font-medium text-primary uppercase tracking-wider">
                Professional Tool
              </span>
            </div>
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              Free DSR Assessment
            </h2>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
              Based on real 2025 standards from 8 Malaysian banks, get professional DSR analysis instantly
            </p>
          </div>

          {/* Calculator Component */}
          <div className="max-w-5xl mx-auto">
            <div className="p-8 rounded-2xl bg-gradient-to-br from-muted/50 to-background border-2 border-border">
              <DSRCalculator language="en" />
            </div>
          </div>
        </div>
      </section>

      {/* Client Cases */}
      <section className="py-32 relative bg-muted/30">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 mb-4">
              <CheckCircle className="w-4 h-4 text-primary" />
              <span className="text-sm font-medium text-primary uppercase tracking-wider">
                Success Stories
              </span>
            </div>
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              Real Clients, Real Results
            </h2>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
              Helping 500+ clients optimize DSR and successfully obtain financing
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                name: 'Mr. Zhang - Manufacturing',
                age: '45 years old',
                income: 'RM 2,744/month',
                before: 'DSR 72%, rejected by 3 banks',
                after: 'Clear credit card, DSR → 58%',
                result: 'CIMB approved RM 30K',
                savings: 'Save RM 10K/year interest',
                avatar: '👨‍💼'
              },
              {
                name: 'Ms. Lee - E-commerce Owner',
                age: '35 years old',
                income: 'RM 13,000/month',
                before: 'RHB only recognizes RM 6,600 (60%)',
                after: 'Switch to Hong Leong, recognizes RM 11,700 (90%)',
                result: 'Loan capacity diff RM 496K',
                savings: '10 years save RM 200K+ interest',
                avatar: '👩‍💼'
              },
              {
                name: 'Mr. Wang - Joint Housing Loan',
                age: '40 years old',
                income: 'Couple combined RM 5,700',
                before: 'Single application DSR 110%, rejected',
                after: 'Hong Leong 50% split rule',
                result: 'DSR → 78%, approved RM 400K',
                savings: 'Avoid guarantor cost RM 20K-50K',
                avatar: '👨‍👩‍👧'
              },
            ].map((caseStudy, index) => (
              <div
                key={index}
                className="group p-8 rounded-2xl bg-gradient-to-br from-background to-muted border-2 border-border hover:border-primary transition-all duration-300 hover:-translate-y-2"
              >
                {/* Avatar */}
                <div className="text-6xl mb-4 text-center">{caseStudy.avatar}</div>

                {/* Name & Info */}
                <h3 className="text-2xl font-bold mb-2 text-center">{caseStudy.name}</h3>
                <p className="text-muted-foreground text-center mb-6">{caseStudy.age} | {caseStudy.income}</p>

                {/* Before */}
                <div className="mb-4 p-4 rounded-lg bg-red-500/10 border border-red-500/20">
                  <div className="text-sm font-bold text-red-500 mb-2">BEFORE:</div>
                  <p className="text-sm">{caseStudy.before}</p>
                </div>

                {/* After */}
                <div className="mb-4 p-4 rounded-lg bg-green-500/10 border border-green-500/20">
                  <div className="text-sm font-bold text-green-500 mb-2">AFTER:</div>
                  <p className="text-sm">{caseStudy.after}</p>
                </div>

                {/* Result */}
                <div className="mb-4 p-4 rounded-lg bg-primary/10 border border-primary/20">
                  <div className="text-sm font-bold text-primary mb-2">RESULT:</div>
                  <p className="text-sm font-bold">{caseStudy.result}</p>
                </div>

                {/* Savings */}
                <div className="text-center p-4 rounded-lg bg-gradient-to-r from-primary/20 to-accent/20 border border-primary">
                  <div className="text-2xl font-bold text-primary">{caseStudy.savings}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ + CTA */}
      <section className="py-32 relative">
        <div className="max-w-4xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              Frequently Asked Questions
            </h2>
          </div>

          <div className="space-y-6 mb-16">
            {[
              {
                q: 'What is DSR?',
                a: 'Debt Service Ratio = Monthly Debt ÷ Monthly Net Income × 100%. It is the key indicator banks use to assess your repayment ability.'
              },
              {
                q: 'Why do different banks have different DSR limits?',
                a: 'Each bank has different risk policies. Maybank limits low-income customers to 40%, while Hong Leong allows high-income customers up to 80%.'
              },
              {
                q: 'Why is self-employed income discounted?',
                a: 'Banks consider self-employed income unstable, so they discount it. RHB only recognizes 60%, Hong Leong recognizes 90%.'
              },
              {
                q: 'Do you charge for your services?',
                a: '✅ Completely FREE for loan clients. Our income comes from bank partnership commissions.'
              },
              {
                q: 'How long to get assessment results?',
                a: 'Free DSR assessment is instant. Complete bank recommendations and optimization plan delivered within 24 hours.'
              },
            ].map((faq, index) => (
              <div
                key={index}
                className="p-6 rounded-lg bg-muted border border-border hover:border-primary transition-colors"
              >
                <h3 className="font-bold text-lg mb-2 flex items-start gap-2">
                  <span className="text-primary">Q:</span>
                  {faq.q}
                </h3>
                <p className="text-muted-foreground pl-6">
                  <span className="text-primary font-bold">A:</span> {faq.a}
                </p>
              </div>
            ))}
          </div>

          {/* Final CTA */}
          <div className="text-center p-12 rounded-2xl bg-gradient-to-br from-primary/20 to-accent/20 border-2 border-primary">
            <h3 className="text-3xl font-bold mb-4">
              Ready to Optimize Your Financing?
            </h3>
            <p className="text-xl text-muted-foreground mb-8">
              Join 500+ businesses that have obtained better financing through INFINITE GZ
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <a
                href="#calculator"
                className="px-8 py-4 rounded-full bg-primary text-black font-bold hover:bg-primary/90 transition-all duration-300 hover:scale-105"
              >
                Start Free Assessment
              </a>
              <a
                href="https://wa.me/60123456789"
                target="_blank"
                rel="noopener noreferrer"
                className="px-8 py-4 rounded-full bg-muted text-foreground font-bold hover:bg-muted/80 transition-all duration-300 hover:scale-105"
              >
                WhatsApp Consultation
              </a>
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
