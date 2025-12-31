'use client';

import Link from 'next/link';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import ScrollProgress from '@/components/ScrollProgress';
import { useLanguage } from '@/contexts/LanguageContext';
import { 
  FileText,
  CheckCircle,
  Star,
  Download,
  Clock,
  Target,
  TrendingUp,
  Users,
  DollarSign,
  Award,
  ArrowRight,
  Zap,
  Package,
  FileCheck,
  BarChart3,
  PieChart,
  Calendar,
  Building2,
  Shield
} from 'lucide-react';

export default function BusinessPlanningPage() {
  const { t } = useLanguage();

  // Service packages data
  const packages = [
    {
      name: 'Basic',
      price: 'RM 3,000',
      delivery: '7 Days',
      popular: false,
      features: [
        { text: 'Executive Summary (5 pages)', included: true },
        { text: 'Company Profile', included: true },
        { text: 'Financial Projections (3 years)', included: true },
        { text: 'Chinese Version', included: true },
        { text: 'Market Analysis', included: false },
        { text: 'Competitive Analysis', included: false },
        { text: 'English Version', included: false },
        { text: 'Editable Financial Model', included: false }
      ]
    },
    {
      name: 'Professional',
      price: 'RM 5,500',
      delivery: '10 Days',
      popular: true,
      features: [
        { text: 'All Basic Features', included: true },
        { text: 'Market Analysis Report (15 pages)', included: true },
        { text: 'Competitive Analysis (5 competitors)', included: true },
        { text: 'Marketing Strategy', included: true },
        { text: 'English Version', included: true },
        { text: 'Editable Financial Model (Excel)', included: true },
        { text: 'Pitch Deck (PPT)', included: false },
        { text: '1 Revision Round', included: false }
      ]
    },
    {
      name: 'Premium',
      price: 'RM 8,500',
      delivery: '14 Days',
      popular: false,
      features: [
        { text: 'All Professional Features', included: true },
        { text: '3-Year Financial Model (Advanced)', included: true },
        { text: 'Pitch Deck Presentation (PPT)', included: true },
        { text: 'Bilingual (Chinese + English)', included: true },
        { text: '1 Revision Round', included: true },
        { text: '1-Hour Bank Meeting Prep', included: true },
        { text: 'Industry Report Bundle', included: true },
        { text: 'Priority Support', included: true }
      ]
    }
  ];

  // Success metrics
  const successMetrics = [
    { label: 'Approval Rate', value: '84.2%', change: '+6.5%' },
    { label: 'Avg Approval Time', value: '21 Days', change: '-53%' },
    { label: 'Avg Loan Amount', value: 'RM 500K', change: 'Up to RM 2M' },
    { label: 'Client Satisfaction', value: '4.9/5.0', change: '500+ reviews' }
  ];

  return (
    <div className="min-h-screen bg-black text-foreground">
      <ScrollProgress />
      <Header />
      
      {/* Hero Section */}
      <section className="relative min-h-[90vh] flex items-center justify-center overflow-hidden pt-20">
        {/* Gradient Background */}
        <div className="absolute inset-0 bg-black" />
        
        {/* Document Pattern */}
        <div className="absolute inset-0 opacity-5">
          <div className="absolute inset-0" style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
            backgroundSize: '60px 60px'
          }} />
        </div>

        <div className="relative z-10 container mx-auto px-6 py-20 text-center">
          {/* Tag */}
          <div className="inline-block mb-6">
            <span className="px-4 py-2 bg-zinc-950/50 border border-zinc-800 rounded-full text-white text-sm font-semibold inline-flex items-center gap-2"><FileText className="w-4 h-4" />
              Professional Document Delivery
            </span>
          </div>

          {/* Title */}
          <h1 className="text-5xl md:text-7xl font-bold mb-6 bg-black bg-clip-text text-transparent">
            Your Business Plan,<br />Done by Professionals
          </h1>

          {/* Subtitle */}
          <p className="text-xl md:text-2xl text-muted-foreground mb-8 max-w-3xl mx-auto">
            85% Loan Approval Rate | Bilingual | 7-14 Days Delivery
          </p>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto mb-12">
            {successMetrics.map((stat, index) => (
              <div key={index} className="p-4 bg-zinc-950/50/50 backdrop-blur border border-zinc-800 rounded-lg">
                <div className="text-2xl md:text-3xl font-bold text-white mb-1">{stat.value}</div>
                <div className="text-xs text-muted-foreground mb-1">{stat.label}</div>
                <div className="text-xs text-white">{stat.change}</div>
              </div>
            ))}
          </div>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a 
              href="#packages"
              className="group px-8 py-4 bg-primary text-background font-bold rounded-full hover:shadow-lg hover:shadow-primary/50 transition-all inline-flex items-center justify-center gap-2"
            >
              View Packages
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </a>
            <a
              href="#samples"
              className="px-8 py-4 bg-muted text-foreground font-bold rounded-full hover:bg-muted/80 transition-all inline-flex items-center justify-center gap-2"
            >
              View Sample BP
            </a>
          </div>
        </div>

        {/* Scroll Indicator */}
        <div className="absolute bottom-10 left-1/2 -translate-x-1/2 animate-bounce">
          <div className="w-6 h-10 border-2 border-zinc-700/50 rounded-full flex justify-center">
            <div className="w-1 h-3 bg-green-400 rounded-full mt-2 animate-pulse" />
          </div>
        </div>
      </section>

      {/* Laser Divider */}
      <div className="h-px bg-black opacity-30" />

      {/* Business Plan Samples Gallery */}
      <section id="samples" className="py-20 relative overflow-hidden">
        <div className="container mx-auto px-6">
          {/* Section Header */}
          <div className="text-center mb-16">
            <span className="px-4 py-2 bg-zinc-950/50 border border-zinc-800 rounded-full text-white text-sm font-semibold inline-block mb-4">
              Document Gallery
            </span>
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              See What You'll Receive
            </h2>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
              Real business plan samples from different industries
            </p>
          </div>

          {/* Sample Cards */}
          <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {/* Manufacturing BP */}
            <div className="group bg-zinc-950/50/50 border border-zinc-800 rounded-2xl overflow-hidden hover:border-zinc-800/50 transition-all hover:shadow-lg hover:shadow-primary/10">
              <div className="aspect-[3/4] bg-zinc-950/50 flex items-center justify-center relative overflow-hidden">
                <FileText className="w-24 h-24 text-white group-hover:scale-110 transition-transform" />
                <div className="absolute inset-0 bg-gradient-to-t from-background/90 to-transparent" />
                <div className="absolute bottom-4 left-4 right-4">
                  <div className="text-xs text-white mb-1">Case Study</div>
                  <div className="text-sm font-bold">Manufacturing Industry</div>
                </div>
              </div>
              <div className="p-6">
                <h3 className="text-lg font-bold mb-2">Auto Parts Manufacturer</h3>
                <div className="flex items-center gap-4 text-sm text-muted-foreground mb-3">
                  <span className="flex items-center gap-1">
                    <FileText className="w-4 h-4" />
                    45 pages
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    7 days
                  </span>
                </div>
                <div className="flex items-center gap-2 mb-3">
                  <CheckCircle className="w-4 h-4 text-white" />
                  <span className="text-sm">Chinese Version</span>
                </div>
                <div className="pt-3 border-t border-zinc-800">
                  <div className="text-xs text-muted-foreground mb-1">Loan Approved</div>
                  <div className="text-lg font-bold text-white">RM 500K @ 5.5%</div>
                  <div className="text-xs text-muted-foreground">Maybank | 21 days approval</div>
                </div>
              </div>
            </div>

            {/* F&B BP */}
            <div className="group bg-zinc-950/50/50 border border-zinc-800 rounded-2xl overflow-hidden hover:border-zinc-800/50 transition-all hover:shadow-lg hover:shadow-primary/10">
              <div className="aspect-[3/4] bg-zinc-950/50 flex items-center justify-center relative overflow-hidden">
                <FileText className="w-24 h-24 text-zinc-300 group-hover:scale-110 transition-transform" />
                <div className="absolute inset-0 bg-gradient-to-t from-background/90 to-transparent" />
                <div className="absolute bottom-4 left-4 right-4">
                  <div className="text-xs text-zinc-300 mb-1">Case Study</div>
                  <div className="text-sm font-bold">F&B Industry</div>
                </div>
              </div>
              <div className="p-6">
                <h3 className="text-lg font-bold mb-2">Restaurant Chain</h3>
                <div className="flex items-center gap-4 text-sm text-muted-foreground mb-3">
                  <span className="flex items-center gap-1">
                    <FileText className="w-4 h-4" />
                    38 pages
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    5 days
                  </span>
                </div>
                <div className="flex items-center gap-2 mb-3">
                  <CheckCircle className="w-4 h-4 text-white" />
                  <span className="text-sm">English Version</span>
                </div>
                <div className="pt-3 border-t border-zinc-800">
                  <div className="text-xs text-muted-foreground mb-1">Loan Approved</div>
                  <div className="text-lg font-bold text-white">RM 300K @ 6.2%</div>
                  <div className="text-xs text-muted-foreground">CIMB | 18 days approval</div>
                </div>
              </div>
            </div>

            {/* Retail BP */}
            <div className="group bg-zinc-950/50/50 border border-zinc-800 rounded-2xl overflow-hidden hover:border-zinc-800/50 transition-all hover:shadow-lg hover:shadow-primary/10">
              <div className="aspect-[3/4] bg-zinc-950/50 flex items-center justify-center relative overflow-hidden">
                <FileText className="w-24 h-24 text-white group-hover:scale-110 transition-transform" />
                <div className="absolute inset-0 bg-gradient-to-t from-background/90 to-transparent" />
                <div className="absolute bottom-4 left-4 right-4">
                  <div className="text-xs text-white mb-1">Case Study</div>
                  <div className="text-sm font-bold">Retail Industry</div>
                </div>
              </div>
              <div className="p-6">
                <h3 className="text-lg font-bold mb-2">Fashion Retail Store</h3>
                <div className="flex items-center gap-4 text-sm text-muted-foreground mb-3">
                  <span className="flex items-center gap-1">
                    <FileText className="w-4 h-4" />
                    52 pages
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    10 days
                  </span>
                </div>
                <div className="flex items-center gap-2 mb-3">
                  <CheckCircle className="w-4 h-4 text-white" />
                  <span className="text-sm">Bilingual (CN + EN)</span>
                </div>
                <div className="pt-3 border-t border-zinc-800">
                  <div className="text-xs text-muted-foreground mb-1">Loan Approved</div>
                  <div className="text-lg font-bold text-white">RM 800K @ 5.8%</div>
                  <div className="text-xs text-muted-foreground">Hong Leong | 25 days approval</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Laser Divider */}
      <div className="h-px bg-black opacity-30" />

      {/* What's Included Checklist */}
      <section className="py-20 relative overflow-hidden bg-gradient-to-b from-background to-card/30">
        <div className="container mx-auto px-6">
          {/* Section Header */}
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              📦 What You'll Receive
            </h2>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
              Not just a document, but a complete financing toolkit
            </p>
          </div>

          {/* Deliverables Grid */}
          <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-6">
            {[
              {
                icon: FileText,
                title: 'Complete Business Plan (PDF + Word)',
                desc: 'Professionally formatted, ready to submit',
                color: 'text-white'
              },
              {
                icon: BarChart3,
                title: 'Financial Forecast Model (Excel)',
                desc: 'Editable 3-year projections with formulas',
                color: 'text-white'
              },
              {
                icon: Target,
                title: 'Industry Analysis Report (10-15 pages)',
                desc: 'Market size, trends, and growth projections',
                color: 'text-white'
              },
              {
                icon: Users,
                title: 'Competitive Analysis (5 Competitors)',
                desc: 'Detailed comparison table with positioning',
                color: 'text-zinc-300'
              },
              {
                icon: TrendingUp,
                title: 'Financing Strategy Recommendation',
                desc: 'Best banks, loan types, and terms',
                color: 'text-white'
              },
              {
                icon: Award,
                title: '1-Hour Bank Meeting Coaching (Premium)',
                desc: 'Prepare for Q&A and presentation tips',
                color: 'text-zinc-300'
              }
            ].map((item, index) => (
              <div key={index} className="group p-6 bg-zinc-950/50/80 backdrop-blur border border-zinc-800 rounded-xl hover:border-zinc-800/50 transition-all hover:shadow-lg">
                <div className="flex items-start gap-4">
                  <div className={`p-3 bg-black rounded-lg ${item.color}`}>
                    <item.icon className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold mb-2">{item.title}</h3>
                    <p className="text-sm text-muted-foreground">{item.desc}</p>
                  </div>
                  <CheckCircle className="w-5 h-5 text-white flex-shrink-0 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Laser Divider */}
      <div className="h-px bg-black opacity-30" />

      {/* Service Packages */}
      <section id="packages" className="py-20 relative overflow-hidden">
        <div className="container mx-auto px-6">
          {/* Section Header */}
          <div className="text-center mb-16">
            <span className="px-4 py-2 bg-zinc-950/50 border border-zinc-800 rounded-full text-white text-sm font-semibold inline-block mb-4">
              Transparent Pricing
            </span>
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              Choose Your Package
            </h2>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
              Fixed price, no hidden fees, money-back guarantee
            </p>
          </div>

          {/* Pricing Grid */}
          <div className="max-w-7xl mx-auto grid md:grid-cols-3 gap-8">
            {packages.map((pkg, index) => (
              <div
                key={index}
                className={`relative bg-zinc-950/50/80 backdrop-blur border rounded-2xl p-8 transition-all hover:shadow-lg ${
                  pkg.popular
                    ? 'border-zinc-800 scale-105 shadow-xl shadow-white/20'
                    : 'border-zinc-800 hover:border-zinc-800/50'
                }`}
              >
                {/* Popular Badge */}
                {pkg.popular && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                    <span className="px-4 py-1 bg-primary text-background text-sm font-bold rounded-full flex items-center gap-1">
                      <Star className="w-4 h-4 fill-current" />
                      MOST POPULAR
                    </span>
                  </div>
                )}

                {/* Package Header */}
                <div className="text-center mb-8">
                  <h3 className="text-2xl font-bold mb-2">{pkg.name}</h3>
                  <div className="text-4xl font-bold text-white mb-2">{pkg.price}</div>
                  <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
                    <Clock className="w-4 h-4" />
                    <span>{pkg.delivery} Delivery</span>
                  </div>
                </div>

                {/* Features List */}
                <ul className="space-y-3 mb-8">
                  {pkg.features.map((feature, fIndex) => (
                    <li key={fIndex} className="flex items-start gap-3">
                      {feature.included ? (
                        <CheckCircle className="w-5 h-5 text-white flex-shrink-0 mt-0.5" />
                      ) : (
                        <div className="w-5 h-5 rounded-full border-2 border-muted-foreground/30 flex-shrink-0 mt-0.5" />
                      )}
                      <span className={`text-sm ${feature.included ? 'text-foreground' : 'text-muted-foreground'}`}>
                        {feature.text}
                      </span>
                    </li>
                  ))}
                </ul>

                {/* CTA Button */}
                <button
                  className={`w-full py-3 font-bold rounded-lg transition-all ${
                    pkg.popular
                      ? 'bg-primary text-background hover:shadow-lg hover:shadow-primary/50'
                      : 'bg-muted text-foreground hover:bg-muted/80'
                  }`}
                >
                  {pkg.popular ? 'Get Started Now' : 'Select Package'}
                </button>
              </div>
            ))}
          </div>

          {/* Money Back Guarantee */}
          <div className="max-w-3xl mx-auto mt-12 p-6 bg-zinc-950/50 border border-zinc-800 rounded-xl text-center">
            <Shield className="w-12 h-12 text-white mx-auto mb-3" />
            <h3 className="text-lg font-bold mb-2">100% Satisfaction Guarantee</h3>
            <p className="text-sm text-muted-foreground">
              If your loan is rejected due to BP quality issues, we'll refund 50% of your payment
            </p>
          </div>
        </div>
      </section>

      {/* Laser Divider */}
      <div className="h-px bg-black opacity-30" />

      {/* Success Case Study - WOW FACTOR */}
      <section className="py-20 relative overflow-hidden">
        <div className="container mx-auto px-6">
          {/* Section Header */}
          <div className="text-center mb-16">
            <span className="px-4 py-2 bg-zinc-950/50 border border-zinc-800 rounded-full text-white text-sm font-semibold inline-flex items-center gap-2 mb-4">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-lightbulb"><path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/><path d="M9 18h6"/><path d="M10 22h4"/></svg>
              Real Transformation
            </span>
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              From Rejection to Approval
            </h2>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
              How we turned a rejected application into RM 500K approval
            </p>
          </div>

          {/* Case Study */}
          <div className="max-w-5xl mx-auto">
            <div className="bg-zinc-950/50 border border-zinc-800 rounded-2xl p-8">
              {/* Header */}
              <div className="flex items-start gap-4 mb-8">
                <div className="p-4 bg-zinc-950/50 border border-zinc-800 rounded-lg"><Building2 className="w-12 h-12 text-white" /></div>
                <div>
                  <h3 className="text-2xl font-bold mb-2">Case: Factory Owner</h3>
                  <p className="text-lg text-zinc-300 font-semibold mb-1">
                    "Bank said my business plan is garbage"
                  </p>
                  <p className="text-muted-foreground">
                    Spent 2 weeks writing 30-page BP, rejected by bank in 5 minutes
                  </p>
                </div>
              </div>

              {/* Before/After Comparison */}
              <div className="grid md:grid-cols-2 gap-8 mb-8">
                {/* His BP (Rejected) */}
                <div className="bg-black/50 rounded-xl p-6">
                  <div className="text-zinc-300 font-bold mb-4 flex items-center gap-2">
                    His BP (Rejected)
                  </div>
                  <div className="space-y-3 text-sm">
                    <div className="flex justify-between items-center p-3 bg-zinc-900 rounded-lg">
                      <span>Pages:</span>
                      <span className="font-semibold text-zinc-300">30 (too long)</span>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-zinc-900 rounded-lg">
                      <span>Time Spent:</span>
                      <span className="font-semibold text-zinc-300">2 weeks</span>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-zinc-900 rounded-lg">
                      <span>Result:</span>
                      <span className="font-semibold text-zinc-300">REJECTED</span>
                    </div>
                    <div className="p-3 bg-zinc-900 rounded-lg">
                      <div className="text-xs text-zinc-300 font-semibold mb-2">Bank Feedback:</div>
                      <ul className="text-xs text-muted-foreground space-y-1">
                        <li>• Executive Summary too long (5 pages)</li>
                        <li>• Market analysis copied from Wikipedia</li>
                        <li>• No competitive analysis</li>
                        <li>• Unrealistic financial projections (50% growth/year)</li>
                        <li>• Vague financing purpose ("expansion")</li>
                      </ul>
                    </div>
                  </div>
                </div>

                {/* Our BP (Approved) */}
                <div className="bg-black/50 rounded-xl p-6">
                  <div className="text-white font-bold mb-4 flex items-center gap-2">
                    Our BP (Approved)
                  </div>
                  <div className="space-y-3 text-sm">
                    <div className="flex justify-between items-center p-3 bg-zinc-950/50 rounded-lg">
                      <span>Pages:</span>
                      <span className="font-semibold text-white">45 (well-structured)</span>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-zinc-950/50 rounded-lg">
                      <span>Delivery:</span>
                      <span className="font-semibold text-white">7 days</span>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-zinc-950/50 rounded-lg">
                      <span>Result:</span>
                      <span className="font-semibold text-white">APPROVED RM 500K</span>
                    </div>
                    <div className="p-3 bg-zinc-950/50 rounded-lg">
                      <div className="text-xs text-white font-semibold mb-2">Bank Response:</div>
                      <ul className="text-xs text-muted-foreground space-y-1">
                        <li>• "Most professional BP we've seen this year"</li>
                        <li>• Interest rate: 5.8% (below market avg 6.5%)</li>
                        <li>• Approval time: 21 days (vs avg 45 days)</li>
                        <li>• Loan term: 7 years</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>

              {/* The Secret Sauce */}
              <div className="bg-zinc-950/50 border border-zinc-800 rounded-xl p-6">
                <div className="font-bold mb-4 flex items-center gap-2 text-lg">
                  <Zap className="w-5 h-5 text-white" />
                  Our "Bank Perspective" Approach
                </div>
                <div className="grid md:grid-cols-3 gap-6">
                  <div>
                    <div className="text-white font-semibold mb-2 text-sm">1. Executive Summary</div>
                    <div className="text-xs text-muted-foreground">
                      Compressed to 1 page using "3-30-3 Rule": 3 seconds to hook, 30 seconds for key data, 3 minutes for full summary
                    </div>
                  </div>
                  <div>
                    <div className="text-white font-semibold mb-2 text-sm">2. Market Analysis</div>
                    <div className="text-xs text-muted-foreground">
                      Used MIDA reports and industry data. Showed RM 28B market with 6.5% growth rate
                    </div>
                  </div>
                  <div>
                    <div className="text-white font-semibold mb-2 text-sm">3. Financial Projections</div>
                    <div className="text-xs text-muted-foreground">
                      3 scenarios: Conservative (70% probability), Reasonable (60%), Optimistic (30%)
                    </div>
                  </div>
                </div>
                <div className="mt-6 pt-6 border-t border-zinc-800 text-center">
                  <div className="text-2xl font-bold text-white mb-2">
                    RM 500K Loan Approved @ 5.8%
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Plus: Editable Excel model + Bank meeting coaching
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Laser Divider */}
      <div className="h-px bg-black opacity-30" />

      {/* FAQ Section */}
      <section className="py-20 relative overflow-hidden bg-gradient-to-b from-background to-card/30">
        <div className="container mx-auto px-6">
          <div className="max-w-4xl mx-auto">
            {/* Section Header */}
            <div className="text-center mb-16">
              <h2 className="text-4xl md:text-5xl font-bold mb-4">
                Frequently Asked Questions
              </h2>
            </div>

            {/* FAQ Items */}
            <div className="space-y-6">
              {[
                {
                  q: "I don't know how to write financial projections, what do I do?",
                  a: "We do it for you! Just provide your historical data (if any) and business goals. Our team will create professional 3-year financial projections with detailed assumptions."
                },
                {
                  q: "What if the bank rejects my BP after I paid?",
                  a: "We offer 1 FREE revision for Professional & Premium packages. If rejection is due to BP quality issues (not your business fundamentals), we refund 50% of your payment."
                },
                {
                  q: "Can I buy only the financial model without the full BP?",
                  a: "Yes! We offer standalone financial modeling service at RM 1,500. However, we recommend the full BP package for better bank approval chances."
                },
                {
                  q: "Do you provide Chinese AND English versions?",
                  a: "Basic package includes Chinese version only. Professional includes English version. Premium includes both in a single integrated document."
                },
                {
                  q: "How long does the approval process take?",
                  a: "Based on our 500+ clients: Average 21-25 days for approval (vs market average 45 days). Some clients get approved in as fast as 18 days."
                }
              ].map((faq, index) => (
                <div key={index} className="bg-zinc-950/50/80 backdrop-blur border border-zinc-800 rounded-xl p-6 hover:border-zinc-800/50 transition-all">
                  <h3 className="text-lg font-bold mb-3 flex items-start gap-3">
                    <span className="text-white">Q:</span>
                    <span>{faq.q}</span>
                  </h3>
                  <div className="flex items-start gap-3 text-muted-foreground">
                    <span className="text-white font-bold">A:</span>
                    <p className="text-sm">{faq.a}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Laser Divider */}
      <div className="h-px bg-black opacity-30" />

      {/* Final CTA */}
      <section className="py-20 relative overflow-hidden">
        <div className="absolute inset-0 bg-zinc-950/50" />
        <div className="relative z-10 container mx-auto px-6 text-center">
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            Ready to Get Your Loan Approved?
          </h2>
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            Join 500+ businesses that secured financing with our professional business plans
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a 
              href="#packages"
              className="px-8 py-4 bg-primary text-background font-bold rounded-full hover:shadow-lg hover:shadow-primary/50 transition-all inline-flex items-center justify-center gap-2"
            >
              Choose Your Package
              <ArrowRight className="w-5 h-5" />
            </a>
            <a
              href="https://wa.me/60123456789"
              target="_blank"
              rel="noopener noreferrer"
              className="px-8 py-4 bg-muted text-foreground font-bold rounded-full hover:bg-muted/80 transition-all"
            >
              WhatsApp Consultation
            </a>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
