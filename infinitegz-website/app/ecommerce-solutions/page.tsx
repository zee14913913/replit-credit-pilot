'use client';

import Link from 'next/link';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import ScrollProgress from '@/components/ScrollProgress';
import { useLanguage } from '@/contexts/LanguageContext';
import { 
  ShoppingCart,
  TrendingUp,
  Zap,
  Package,
  Users,
  BarChart3,
  Smartphone,
  ArrowRight,
  CheckCircle,
  Star,
  Globe,
  Code,
  Database,
  Cloud,
  CreditCard,
  Truck,
  MessageCircle,
  LineChart,
  PieChart,
  Target,
  Award,
  Rocket
} from 'lucide-react';
import { useState } from 'react';

export default function EcommerceSolutionsPage() {
  const { t } = useLanguage();

  // Platform data
  const platforms = [
    { name: 'Shopee', color: 'from-zinc-700 to-zinc-800', traffic: '43%' },
    { name: 'Lazada', color: 'from-white to-white', traffic: '9%' },
    { name: 'TikTok Shop', color: 'from-black to-gray-700', traffic: '32%' },
    { name: 'Instagram Shop', color: 'from-white to-white', traffic: '8%' },
    { name: 'Facebook Shop', color: 'from-zinc-700 to-zinc-800', traffic: '5%' },
    { name: 'WooCommerce', color: 'from-zinc-700 to-zinc-800', traffic: '3%' }
  ];

  // Tech stack
  const techStack = [
    { category: 'Frontend', items: ['React', 'Next.js', 'Tailwind CSS'] },
    { category: 'Backend', items: ['Node.js', 'Python API'] },
    { category: 'Database', items: ['PostgreSQL', 'Redis'] },
    { category: 'Payment', items: ['iPay88', 'Senangpay', 'Stripe'] },
    { category: 'Logistics', items: ['J&T API', 'Poslaju', 'DHL'] },
    { category: 'Cloud', items: ['AWS', 'Google Cloud'] }
  ];

  return (
    <div className="min-h-screen bg-black text-foreground">
      <ScrollProgress />
      <Header />
      
      {/* Hero Section */}
      <section className="relative min-h-[90vh] flex items-center justify-center overflow-hidden pt-20">
        {/* Gradient Background */}
        <div className="absolute inset-0 bg-black" />
        
        {/* Animated Network */}
        <div className="absolute inset-0 opacity-20">
          <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-yellow-400 rounded-full blur-3xl animate-pulse" />
          <div className="absolute bottom-1/4 right-1/4 w-64 h-64 bg-yellow-500 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
          <div className="absolute top-1/2 left-1/2 w-64 h-64 bg-yellow-500 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '2s' }} />
        </div>

        <div className="relative z-10 container mx-auto px-6 py-20 text-center">
          {/* Tag */}
          <div className="inline-block mb-6">
            <span className="px-4 py-2 bg-zinc-950/50 border border-zinc-800/30 rounded-full text-white text-sm font-semibold">
              Platform Integration Service
            </span>
          </div>

          {/* Title */}
          <h1 className="text-5xl md:text-7xl font-bold mb-6 bg-black bg-clip-text text-transparent">
            From Zero to<br />500% GMV Growth
          </h1>

          {/* Subtitle */}
          <p className="text-xl md:text-2xl text-muted-foreground mb-8 max-w-3xl mx-auto">
            Shopee | Lazada | TikTok Shop | Multi-Channel Integration
          </p>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto mb-12">
            {[
              { value: '71x', label: 'GMV Growth' },
              { value: '500%', label: 'Avg ROI' },
              { value: '6 Platforms', label: 'Integrated' },
              { value: '142', label: 'Clients Served' }
            ].map((stat, index) => (
              <div key={index} className="p-4 bg-zinc-950/50/50 backdrop-blur border border-zinc-800 rounded-lg">
                <div className="text-2xl md:text-3xl font-bold text-white mb-1">{stat.value}</div>
                <div className="text-sm text-muted-foreground">{stat.label}</div>
              </div>
            ))}
          </div>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a 
              href="#packages"
              className="group px-8 py-4 bg-primary text-background font-bold rounded-full hover:shadow-lg hover:shadow-yellow-400/50 transition-all inline-flex items-center justify-center gap-2"
            >
              View Packages
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </a>
            <a
              href="#case-study"
              className="px-8 py-4 bg-muted text-foreground font-bold rounded-full hover:bg-muted/80 transition-all inline-flex items-center justify-center gap-2"
            >
              See Success Story
            </a>
          </div>
        </div>

        {/* Scroll Indicator */}
        <div className="absolute bottom-10 left-1/2 -translate-x-1/2 animate-bounce">
          <div className="w-6 h-10 border-2 border-orange-400/50 rounded-full flex justify-center">
            <div className="w-1 h-3 bg-orange-400 rounded-full mt-2 animate-pulse" />
          </div>
        </div>
      </section>

      {/* Laser Divider */}
      <div className="h-px bg-black opacity-30" />

      {/* Platform Ecosystem */}
      <section className="py-20 relative overflow-hidden">
        <div className="container mx-auto px-6">
          {/* Section Header */}
          <div className="text-center mb-16">
            <span className="px-4 py-2 bg-zinc-950/50 border border-zinc-800/30 rounded-full text-white text-sm font-semibold inline-block mb-4">
              Platform Ecosystem
            </span>
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              We Integrate All Major Platforms
            </h2>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
              Multi-channel sync, unified management, explosive growth
            </p>
          </div>

          {/* Ecosystem Diagram */}
          <div className="max-w-5xl mx-auto mb-16">
            {/* Your Business (Center) */}
            <div className="text-center mb-8">
              <div className="inline-block p-6 bg-zinc-950/50 border-2 border-zinc-800 rounded-2xl backdrop-blur">
                <ShoppingCart className="w-12 h-12 text-white mx-auto mb-3" />
                <div className="text-xl font-bold">Your Business</div>
              </div>
            </div>

            {/* Arrow Down */}
            <div className="flex justify-center mb-8">
              <div className="w-0.5 h-12 bg-zinc-700" />
            </div>

            {/* Integration Hub */}
            <div className="text-center mb-8">
              <div className="inline-block p-6 bg-zinc-950/50/80 backdrop-blur border border-zinc-800 rounded-2xl">
                <Globe className="w-10 h-10 text-white mx-auto mb-3" />
                <div className="text-lg font-bold mb-1">INFINITE GZ</div>
                <div className="text-sm text-muted-foreground">Integration Hub</div>
              </div>
            </div>

            {/* Connecting Lines */}
            <div className="flex justify-center mb-8">
              <div className="grid grid-cols-6 gap-4 w-full max-w-4xl">
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="flex justify-center">
                    <div className="w-0.5 h-12 bg-zinc-700/50" />
                  </div>
                ))}
              </div>
            </div>

            {/* Platforms */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              {platforms.map((platform, index) => (
                <div key={index} className="group p-4 bg-zinc-950/50/50 border border-zinc-800 rounded-xl hover:border-zinc-800/50 transition-all text-center">
                  <div className={`w-12 h-12 mx-auto mb-3 rounded-full bg-gradient-to-br ${platform.color} flex items-center justify-center`}>
                    <ShoppingCart className="w-6 h-6 text-white" />
                  </div>
                  <div className="font-semibold text-sm mb-1">{platform.name}</div>
                  <div className="text-xs text-muted-foreground">{platform.traffic} traffic</div>
                </div>
              ))}
            </div>

            {/* Arrow Down */}
            <div className="flex justify-center my-8">
              <div className="w-0.5 h-12 bg-gradient-to-b from-transparent to-yellow-400" />
            </div>

            {/* Unified Dashboard */}
            <div className="text-center">
              <div className="inline-block p-6 bg-zinc-950/50 border-2 border-zinc-800 rounded-2xl backdrop-blur">
                <BarChart3 className="w-12 h-12 text-white mx-auto mb-3" />
                <div className="text-xl font-bold mb-2">Unified Dashboard</div>
                <div className="text-sm text-muted-foreground space-y-1">
                  <div>• Real-time inventory sync</div>
                  <div>• Centralized order management</div>
                  <div>• Cross-platform analytics</div>
                </div>
              </div>
            </div>
          </div>

          {/* Platform Stats */}
          <div className="max-w-4xl mx-auto grid md:grid-cols-3 gap-6">
            <div className="p-6 bg-zinc-950/50 border border-zinc-800/30 rounded-xl text-center">
              <div className="text-3xl font-bold text-white mb-2">128.4B</div>
              <div className="text-sm text-muted-foreground">Southeast Asia E-commerce GMV (2024)</div>
            </div>
            <div className="p-6 bg-zinc-950/50 border border-zinc-800 rounded-xl text-center">
              <div className="text-3xl font-bold text-white mb-2">+12%</div>
              <div className="text-sm text-muted-foreground">Year-over-Year Growth</div>
            </div>
            <div className="p-6 bg-zinc-950/50 border border-zinc-800 rounded-xl text-center">
              <div className="text-3xl font-bold text-white mb-2">84%</div>
              <div className="text-sm text-muted-foreground">Market Share (Top 3 Platforms)</div>
            </div>
          </div>
        </div>
      </section>

      {/* Laser Divider */}
      <div className="h-px bg-black opacity-30" />

      {/* Technical Capabilities */}
      <section className="py-20 relative overflow-hidden bg-gradient-to-b from-background to-card/30">
        <div className="container mx-auto px-6">
          {/* Section Header */}
          <div className="text-center mb-16">
            <span className="px-4 py-2 bg-zinc-950/50 border border-zinc-800 rounded-full text-white text-sm font-semibold inline-block mb-4">
              💻 Technical Stack
            </span>
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              Enterprise-Grade Technology
            </h2>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
              Built for scale, reliability, and performance
            </p>
          </div>

          {/* Tech Stack Grid */}
          <div className="max-w-6xl mx-auto grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">
            {techStack.map((stack, index) => (
              <div key={index} className="p-6 bg-zinc-950/50/80 backdrop-blur border border-zinc-800 rounded-xl hover:border-zinc-800/50 transition-all">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 bg-zinc-950/50 rounded-lg">
                    <Code className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-lg font-bold">{stack.category}</h3>
                </div>
                <div className="space-y-2">
                  {stack.items.map((item, i) => (
                    <div key={i} className="flex items-center gap-2 text-sm">
                      <CheckCircle className="w-4 h-4 text-zinc-300 flex-shrink-0" />
                      <span>{item}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Feature Comparison Matrix */}
          <div className="max-w-6xl mx-auto">
            <h3 className="text-2xl font-bold mb-6 text-center">Feature Matrix</h3>
            <div className="overflow-x-auto">
              <table className="w-full bg-zinc-950/50/80 backdrop-blur border border-zinc-800 rounded-xl">
                <thead>
                  <tr className="border-b border-zinc-800">
                    <th className="p-4 text-left">Feature</th>
                    <th className="p-4 text-center">Basic</th>
                    <th className="p-4 text-center">Pro</th>
                    <th className="p-4 text-center">Enterprise</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { feature: 'Store Setup', basic: true, pro: true, enterprise: true },
                    { feature: 'Product Upload (SKUs)', basic: '50', pro: '200', enterprise: 'Unlimited' },
                    { feature: 'Inventory Sync', basic: false, pro: true, enterprise: true },
                    { feature: 'Order Automation', basic: false, pro: false, enterprise: true },
                    { feature: 'Multi-Platform Integration', basic: '1', pro: '3', enterprise: 'All' },
                    { feature: 'Analytics Dashboard', basic: 'Basic', pro: 'Advanced', enterprise: 'Custom' },
                    { feature: 'Customer Service System', basic: false, pro: true, enterprise: true },
                    { feature: 'ERP Integration', basic: false, pro: false, enterprise: true }
                  ].map((row, index) => (
                    <tr key={index} className="border-b border-zinc-800 last:border-0 hover:bg-muted/30 transition-colors">
                      <td className="p-4 font-medium">{row.feature}</td>
                      <td className="p-4 text-center">
                        {typeof row.basic === 'boolean' ? (
                          row.basic ? <CheckCircle className="w-5 h-5 text-zinc-300 mx-auto" /> : <span className="text-muted-foreground">—</span>
                        ) : (
                          <span className="text-sm">{row.basic}</span>
                        )}
                      </td>
                      <td className="p-4 text-center">
                        {typeof row.pro === 'boolean' ? (
                          row.pro ? <CheckCircle className="w-5 h-5 text-zinc-300 mx-auto" /> : <span className="text-muted-foreground">—</span>
                        ) : (
                          <span className="text-sm">{row.pro}</span>
                        )}
                      </td>
                      <td className="p-4 text-center">
                        {typeof row.enterprise === 'boolean' ? (
                          row.enterprise ? <CheckCircle className="w-5 h-5 text-zinc-300 mx-auto" /> : <span className="text-muted-foreground">—</span>
                        ) : (
                          <span className="text-sm">{row.enterprise}</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </section>

      {/* Laser Divider */}
      <div className="h-px bg-black opacity-30" />

      {/* Success Case Study - WOW FACTOR */}
      <section id="case-study" className="py-20 relative overflow-hidden">
        <div className="container mx-auto px-6">
          {/* Section Header */}
          <div className="text-center mb-16">
            <span className="px-4 py-2 bg-zinc-950/50 border border-zinc-800 rounded-full text-white text-sm font-semibold inline-flex items-center gap-2 mb-4">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-lightbulb"><path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/><path d="M9 18h6"/><path d="M10 22h4"/></svg>
              Real Transformation
            </span>
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              From RM 500 to RM 35,600
            </h2>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
              71x GMV growth in just 2 months
            </p>
          </div>

          {/* Case Study */}
          <div className="max-w-6xl mx-auto">
            <div className="bg-zinc-950/50 border border-zinc-800/30 rounded-2xl p-8">
              {/* Header */}
              <div className="flex items-start gap-4 mb-8">
                <div className="p-4 bg-zinc-950/50 border border-zinc-800 rounded-lg">
                  <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-shirt text-zinc-300"><path d="M20.38 3.46 16 2a4 4 0 0 1-8 0L3.62 3.46a2 2 0 0 0-1.34 2.23l.58 3.47a1 1 0 0 0 .99.84H6v10c0 1.1.9 2 2 2h8a2 2 0 0 0 2-2V10h2.15a1 1 0 0 0 .99-.84l.58-3.47a2 2 0 0 0-1.34-2.23z"/></svg>
                </div>
                <div>
                  <h3 className="text-2xl font-bold mb-2">Case: Traditional Clothing Store</h3>
                  <p className="text-lg text-white font-semibold mb-1">
                    "Opened Shopee store, 3 months only sold RM 500"
                  </p>
                  <p className="text-muted-foreground">
                    50 products uploaded, refreshed daily, only 10 items sold in 3 months
                  </p>
                </div>
              </div>

              {/* 5 Fatal Mistakes */}
              <div className="bg-black/50 rounded-xl p-6 mb-8">
                <div className="font-bold mb-4 text-zinc-300 flex items-center gap-2 text-lg">
                  ❌ 5 Fatal Mistakes Discovered
                </div>
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {[
                    { icon: '📸', title: 'Poor Photos', desc: 'Phone camera, messy background, bad lighting. Click rate: 0.3% (avg: 2.5%)' },
                    { icon: '📝', title: 'Generic Titles', desc: '"Women Dress" (too vague) vs "Korean A-Line Dress | Slim Fit | S-3XL"' },
                    { icon: 'Pricing', title: 'Wrong Pricing', desc: 'RM 89 (RM 10 more than store). Competitors: RM 59-79 with free shipping' },
                    { icon: '💬', title: 'Slow Response', desc: '8-hour reply time (avg: 2 min). 50% inquiries lost' },
                    { icon: '⭐', title: 'No Reviews', desc: '0 reviews vs competitors with 500+ reviews. Conversion: 0.1%' }
                  ].map((mistake, index) => (
                    <div key={index} className="p-4 bg-zinc-900 border border-zinc-800 rounded-lg">
                      <div className="text-2xl mb-2">{mistake.icon}</div>
                      <div className="font-semibold mb-1 text-sm">{mistake.title}</div>
                      <div className="text-xs text-muted-foreground">{mistake.desc}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* 4-Week Transformation Plan */}
              <div className="bg-zinc-950/50 border border-zinc-800 rounded-xl p-6 mb-8">
                <div className="font-bold mb-6 flex items-center gap-2 text-lg">
                  <Zap className="w-6 h-6 text-white" />
                  4-Week Transformation Plan
                </div>
                <div className="grid md:grid-cols-4 gap-4">
                  {[
                    {
                      week: 'Week 1',
                      title: 'Product Reboot',
                      items: ['Professional lightbox photos (6 angles)', 'Model fitting (3 lifestyle shots)', 'SEO-optimized titles', 'Smart pricing (RM 49/79/139)']
                    },
                    {
                      week: 'Week 2',
                      title: 'System Setup',
                      items: ['24/7 chatbot (auto-reply)', 'Multi-platform inventory sync', 'Real-time analytics dashboard']
                    },
                    {
                      week: 'Week 3',
                      title: 'Traffic Explosion',
                      items: ['Shopee ads (RM 30/day, ROI 1:14)', 'Live streaming (Wed 8PM)', 'Instagram/TikTok seeding']
                    },
                    {
                      week: 'Week 4',
                      title: 'Trust Building',
                      items: ['First 50 orders @ RM 39 (loss leader)', 'Photo review incentive (RM 10 voucher)', '80 reviews in 30 days']
                    }
                  ].map((phase, index) => (
                    <div key={index} className="p-4 bg-black/50 rounded-lg">
                      <div className="text-white font-bold mb-2 text-sm">{phase.week}</div>
                      <div className="font-semibold mb-3">{phase.title}</div>
                      <ul className="space-y-1">
                        {phase.items.map((item, i) => (
                          <li key={i} className="text-xs text-muted-foreground flex items-start gap-1">
                            <CheckCircle className="w-3 h-3 text-zinc-300 flex-shrink-0 mt-0.5" />
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </div>

              {/* GMV Growth Chart */}
              <div className="bg-black/50 rounded-xl p-6 mb-8">
                <div className="font-bold mb-4 text-center flex items-center justify-center gap-2">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-trending-up text-zinc-300"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>
                  GMV Growth Trajectory
                </div>
                <div className="grid md:grid-cols-3 gap-6">
                  {[
                    {
                      month: 'Month 1',
                      gmv: 'RM 8,500',
                      growth: '+1,600%',
                      orders: '142 orders',
                      conversion: '3.2%',
                      roi: 'ROI 1:14',
                      reviews: '85 reviews'
                    },
                    {
                      month: 'Month 2',
                      gmv: 'RM 18,200',
                      growth: '+213%',
                      orders: '298 orders',
                      conversion: '5.1%',
                      roi: 'ROI 1:22',
                      reviews: '203 reviews'
                    },
                    {
                      month: 'Month 3',
                      gmv: 'RM 35,600',
                      growth: '+95%',
                      orders: '521 orders',
                      conversion: '7.2%',
                      roi: 'Natural 62%',
                      reviews: '412 reviews'
                    }
                  ].map((period, index) => (
                    <div key={index} className="p-6 bg-zinc-950/50 border border-zinc-800 rounded-xl">
                      <div className="text-sm text-zinc-300 mb-2">{period.month}</div>
                      <div className="text-3xl font-bold text-zinc-300 mb-1">{period.gmv}</div>
                      <div className="text-sm text-zinc-300 mb-4">{period.growth} from previous</div>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Orders:</span>
                          <span className="font-semibold">{period.orders}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Conversion:</span>
                          <span className="font-semibold">{period.conversion}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Traffic:</span>
                          <span className="font-semibold">{period.roi}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Reviews:</span>
                          <span className="font-semibold">{period.reviews}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Final Results */}
              <div className="bg-zinc-950/50 border border-zinc-800/30 rounded-xl p-6 text-center">
                <div className="text-4xl font-bold text-white mb-2">
                  71x GMV Growth
                </div>
                <p className="text-lg text-muted-foreground mb-4">
                  From RM 500 (3 months) → RM 62,300 (next 3 months)
                </p>
                <div className="grid md:grid-cols-3 gap-4 text-sm">
                  <div className="flex items-center justify-center gap-2">
                    <CheckCircle className="w-4 h-4 text-zinc-300" />
                    <span>Net profit: RM 18,500 (30%)</span>
                  </div>
                  <div className="flex items-center justify-center gap-2">
                    <CheckCircle className="w-4 h-4 text-zinc-300" />
                    <span>Repeat purchase: 18%</span>
                  </div>
                  <div className="flex items-center justify-center gap-2">
                    <CheckCircle className="w-4 h-4 text-zinc-300" />
                    <span>Planning 2nd store opening</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Laser Divider */}
      <div className="h-px bg-black opacity-30" />

      {/* Pricing Packages */}
      <section id="packages" className="py-20 relative overflow-hidden bg-gradient-to-b from-background to-card/30">
        <div className="container mx-auto px-6">
          {/* Section Header */}
          <div className="text-center mb-16">
            <span className="px-4 py-2 bg-zinc-950/50 border border-zinc-800/30 rounded-full text-white text-sm font-semibold inline-block mb-4">
              Service Packages
            </span>
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              Choose Your Growth Plan
            </h2>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
              From startup to enterprise, we scale with you
            </p>
          </div>

          {/* Pricing Grid */}
          <div className="max-w-7xl mx-auto grid md:grid-cols-3 gap-8">
            {[
              {
                name: 'Basic',
                price: 'RM 2,500',
                period: 'one-time',
                popular: false,
                desc: 'Perfect for testing the waters',
                features: [
                  'Store setup (1 platform)',
                  'Up to 50 SKUs',
                  'Basic product photos (lightbox)',
                  'SEO-optimized titles',
                  'Initial inventory upload',
                  '1 month support'
                ],
                cta: 'Get Started'
              },
              {
                name: 'Pro',
                price: 'RM 5,800',
                period: 'one-time',
                popular: true,
                desc: 'For serious sellers',
                features: [
                  'Multi-store setup (3 platforms)',
                  'Up to 200 SKUs',
                  'Professional photos + model shots',
                  'Inventory sync system',
                  '24/7 chatbot setup',
                  'Analytics dashboard',
                  'Ad campaign setup (RM 500 credit)',
                  '3 months support'
                ],
                cta: 'Start Selling'
              },
              {
                name: 'Enterprise',
                price: 'Custom',
                period: 'contact us',
                popular: false,
                desc: 'Full omnichannel solution',
                features: [
                  'All platforms integrated',
                  'Unlimited SKUs',
                  'Custom photography package',
                  'Full automation (inventory + orders)',
                  'ERP/CRM integration',
                  'Dedicated account manager',
                  'White-label solution available',
                  '12 months support'
                ],
                cta: 'Contact Sales'
              }
            ].map((pkg, index) => (
              <div
                key={index}
                className={`relative bg-zinc-950/50/80 backdrop-blur border rounded-2xl p-8 transition-all hover:shadow-lg ${
                  pkg.popular
                    ? 'border-zinc-800 scale-105 shadow-xl shadow-yellow-400/20'
                    : 'border-zinc-800 hover:border-zinc-800/50'
                }`}
              >
                {pkg.popular && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                    <span className="px-4 py-1 bg-primary text-background text-sm font-bold rounded-full flex items-center gap-1">
                      <Star className="w-4 h-4 fill-current" />
                      MOST POPULAR
                    </span>
                  </div>
                )}

                <div className="text-center mb-8">
                  <h3 className="text-2xl font-bold mb-2">{pkg.name}</h3>
                  <div className="text-4xl font-bold text-white mb-1">{pkg.price}</div>
                  <div className="text-sm text-muted-foreground mb-3">{pkg.period}</div>
                  <p className="text-sm text-muted-foreground">{pkg.desc}</p>
                </div>

                <ul className="space-y-3 mb-8">
                  {pkg.features.map((feature, fIndex) => (
                    <li key={fIndex} className="flex items-start gap-3">
                      <CheckCircle className="w-5 h-5 text-zinc-300 flex-shrink-0 mt-0.5" />
                      <span className="text-sm">{feature}</span>
                    </li>
                  ))}
                </ul>

                <button
                  className={`w-full py-3 font-bold rounded-lg transition-all ${
                    pkg.popular
                      ? 'bg-primary text-background hover:shadow-lg hover:shadow-yellow-400/50'
                      : 'bg-muted text-foreground hover:bg-muted/80'
                  }`}
                >
                  {pkg.cta}
                </button>
              </div>
            ))}
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
            Ready to Scale Your E-Commerce?
          </h2>
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            Join 142+ businesses making 6-7 figures monthly
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a 
              href="#packages"
              className="px-8 py-4 bg-primary text-background font-bold rounded-full hover:shadow-lg hover:shadow-yellow-400/50 transition-all inline-flex items-center justify-center gap-2"
            >
              View Packages
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
