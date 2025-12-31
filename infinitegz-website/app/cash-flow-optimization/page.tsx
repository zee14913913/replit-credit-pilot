'use client';

import Link from 'next/link';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import ScrollProgress from '@/components/ScrollProgress';
import { useLanguage } from '@/contexts/LanguageContext';
import { 
  Activity,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Calendar,
  Package,
  Clock,
  AlertCircle,
  CheckCircle,
  ArrowRight,
  Zap,
  Target,
  BarChart3,
  PieChart,
  LineChart
,
  Stethoscope,
  Lightbulb,
  Calculator,
  CreditCard,
  ShoppingCart,
  Store,
  Users,
  FileText,
  Building2,
  ChefHat,
  Shirt
} from 'lucide-react';
import { useState } from 'react';

export default function CashFlowOptimizationPage() {
  const { t } = useLanguage();
  
  // Health Score Calculator State
  const [healthInputs, setHealthInputs] = useState({
    dso: '',
    dpo: '',
    dio: '',
    monthlyRevenue: '',
    monthlyExpense: ''
  });
  
  const [healthScore, setHealthScore] = useState<number | null>(null);
  const [showResults, setShowResults] = useState(false);

  // Calculate Health Score
  const calculateHealthScore = () => {
    const dso = parseFloat(healthInputs.dso) || 0;
    const dpo = parseFloat(healthInputs.dpo) || 0;
    const dio = parseFloat(healthInputs.dio) || 0;
    const revenue = parseFloat(healthInputs.monthlyRevenue) || 0;
    const expense = parseFloat(healthInputs.monthlyExpense) || 0;

    // Cash Conversion Cycle
    const ccc = dso + dio - dpo;
    
    // Current Ratio (simplified)
    const currentRatio = revenue / (expense || 1);
    
    // Score calculation (0-100)
    let score = 100;
    
    // DSO penalty (ideal: <45 days)
    if (dso > 45) score -= Math.min((dso - 45) * 0.5, 20);
    
    // DIO penalty (ideal: <60 days)
    if (dio > 60) score -= Math.min((dio - 60) * 0.4, 20);
    
    // DPO bonus (longer is better)
    if (dpo < 30) score -= (30 - dpo) * 0.3;
    
    // CCC penalty (ideal: <50 days)
    if (ccc > 50) score -= Math.min((ccc - 50) * 0.3, 20);
    
    // Current Ratio check
    if (currentRatio < 1.2) score -= 15;
    else if (currentRatio > 2) score += 10;
    
    setHealthScore(Math.max(0, Math.min(100, Math.round(score))));
    setShowResults(true);
  };

  const getHealthColor = (score: number) => {
    if (score >= 71) return 'text-white border-zinc-800';
    if (score >= 41) return 'text-zinc-300 border-zinc-700';
    return 'text-zinc-300 border-zinc-700';
  };

  const getHealthLabel = (score: number) => {
    if (score >= 71) return 'Healthy';
    if (score >= 41) return 'Warning';
    return 'Critical';
  };

  return (
    <div className="min-h-screen bg-black text-zinc-300">
      <ScrollProgress />
      <Header />
      
      {/* Hero Section */}
      <section className="relative min-h-[90vh] flex items-center justify-center overflow-hidden pt-20">
        {/* Gradient Background */}
        <div className="absolute inset-0 bg-black" />
        
        {/* Animated Pulse */}
        <div className="absolute inset-0 opacity-20">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-500 rounded-full blur-3xl animate-pulse" />
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-400 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
        </div>

        <div className="relative z-10 container mx-auto px-6 py-20 text-center">
          {/* Tag */}
          <div className="inline-block mb-6">
            <span className="px-4 py-2 bg-zinc-950/50 border border-zinc-800 rounded-full text-white text-sm font-semibold inline-flex items-center gap-2"><Activity className="w-4 h-4" />
              Health Diagnostic Service
            </span>
          </div>

          {/* Title */}
          <h1 className="text-5xl md:text-7xl font-bold mb-6 text-white">
            Is Your Business<br />Financially Healthy?
          </h1>

          {/* Subtitle */}
          <p className="text-xl md:text-2xl text-zinc-500 mb-8 max-w-3xl mx-auto">
            82% of SMEs fail due to poor cash flow management
          </p>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto mb-12">
            {[
              { value: '82%', label: 'Failure Rate' },
              { value: '56%', label: 'Face Cash Issues' },
              { value: '94.6%', label: 'No Planning' },
              { value: 'RM 180K', label: 'Avg. Cash Freed' }
            ].map((stat, index) => (
              <div key={index} className="p-4 bg-zinc-950/50/50 backdrop-blur border border-zinc-800 rounded-lg">
                <div className="text-2xl md:text-3xl font-bold text-primary mb-1">{stat.value}</div>
                <div className="text-sm text-zinc-500">{stat.label}</div>
              </div>
            ))}
          </div>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a 
              href="#health-check"
              className="group px-8 py-4 bg-primary text-background font-bold rounded-full hover:shadow-lg hover:shadow-primary/50 transition-all inline-flex items-center justify-center gap-2"
            >
              Free Health Check
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </a>
            <a
              href="https://wa.me/60123456789"
              target="_blank"
              rel="noopener noreferrer"
              className="px-8 py-4 bg-muted text-zinc-300 font-bold rounded-full hover:bg-muted/80 transition-all inline-flex items-center justify-center gap-2"
            >
              WhatsApp Consultation
            </a>
          </div>
        </div>

        {/* Scroll Indicator */}
        <div className="absolute bottom-10 left-1/2 -translate-x-1/2 animate-bounce">
          <div className="w-6 h-10 border-2 border-zinc-800/50 rounded-full flex justify-center">
            <div className="w-1 h-3 bg-purple-400 rounded-full mt-2 animate-pulse" />
          </div>
        </div>
      </section>

      {/* Laser Divider */}
      <div className="h-px bg-black opacity-30" />

      {/* Health Score System Section */}
      <section className="py-20 relative overflow-hidden">
        <div className="container mx-auto px-6">
          {/* Section Header */}
          <div className="text-center mb-16">
            <span className="px-4 py-2 bg-zinc-950/50 border border-zinc-800 rounded-full text-white text-sm font-semibold inline-block mb-4">
              Health Diagnostic
            </span>
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              Cash Flow Health Score
            </h2>
            <p className="text-xl text-zinc-500 max-w-3xl mx-auto">
              Like a body checkup, but for your business finances
            </p>
          </div>

          {/* Health Score Visual */}
          <div className="max-w-4xl mx-auto mb-16">
            <div className="grid md:grid-cols-3 gap-6">
              {/* Critical */}
              <div className="p-6 bg-zinc-950/50 border-2 border-zinc-800 rounded-xl">
                <div className="text-4xl font-bold text-zinc-300 mb-2">0-40</div>
                <div className="text-lg font-semibold text-zinc-300 mb-3">Critical</div>
                <ul className="text-sm text-zinc-500 space-y-2">
                  <li>• High bankruptcy risk</li>
                  <li>• Urgent action needed</li>
                  <li>• Cash running out fast</li>
                </ul>
              </div>

              {/* Warning */}
              <div className="p-6 bg-zinc-950/50 border-2 border-zinc-800 rounded-xl">
                <div className="text-4xl font-bold text-zinc-300 mb-2">41-70</div>
                <div className="text-lg font-semibold text-zinc-300 mb-3">Warning</div>
                <ul className="text-sm text-zinc-500 space-y-2">
                  <li>• Room for improvement</li>
                  <li>• Optimize now to avoid crisis</li>
                  <li>• Cash flow unstable</li>
                </ul>
              </div>

              {/* Healthy */}
              <div className="p-6 bg-zinc-950/50 border-2 border-zinc-800 rounded-xl">
                <div className="text-4xl font-bold text-white mb-2">71-100</div>
                <div className="text-lg font-semibold text-white mb-3">Healthy</div>
                <ul className="text-sm text-zinc-500 space-y-2">
                  <li>• Strong financial health</li>
                  <li>• Ready for growth</li>
                  <li>• Cash flow stable</li>
                </ul>
              </div>
            </div>
          </div>

          {/* 5 Metrics */}
          <div className="max-w-4xl mx-auto">
            <h3 className="text-2xl font-bold mb-6 text-center">Your Score is Based on 5 Metrics:</h3>
            <div className="grid md:grid-cols-5 gap-4">
              {[
                { icon: Calendar, label: 'DSO', desc: 'Days Sales Outstanding' },
                { icon: Clock, label: 'DPO', desc: 'Days Payable Outstanding' },
                { icon: Package, label: 'DIO', desc: 'Days Inventory Outstanding' },
                { icon: TrendingUp, label: 'CCC', desc: 'Cash Conversion Cycle' },
                { icon: BarChart3, label: 'Ratio', desc: 'Current Ratio' }
              ].map((metric, index) => (
                <div key={index} className="p-4 bg-zinc-950/50/50 border border-zinc-800 rounded-lg text-center">
                  <metric.icon className="w-8 h-8 text-white mx-auto mb-2" />
                  <div className="font-bold text-zinc-300 mb-1">{metric.label}</div>
                  <div className="text-xs text-zinc-500">{metric.desc}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Laser Divider */}
      <div className="h-px bg-black opacity-30" />

      {/* Interactive Health Check Tool */}
      <section id="health-check" className="py-20 relative overflow-hidden bg-gradient-to-b from-background to-card/30">
        <div className="container mx-auto px-6">
          <div className="max-w-3xl mx-auto">
            {/* Section Header */}
            <div className="text-center mb-12">
              <h2 className="text-4xl md:text-5xl font-bold mb-4">
                Free Health Check
              </h2>
              <p className="text-xl text-zinc-500">
                Enter 5 numbers, get instant diagnosis
              </p>
            </div>

            {/* Input Form */}
            <div className="bg-zinc-950/50/80 backdrop-blur border border-zinc-800 rounded-2xl p-8 mb-8">
              <div className="space-y-6">
                {/* DSO */}
                <div>
                  <label className="block text-sm font-semibold mb-2">
                    1. Average Days to Collect Payment (DSO)
                  </label>
                  <input
                    type="number"
                    placeholder="e.g., 45 days"
                    value={healthInputs.dso}
                    onChange={(e) => setHealthInputs({...healthInputs, dso: e.target.value})}
                    className="w-full px-4 py-3 bg-black border border-zinc-800 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                  <p className="text-xs text-zinc-500 mt-1">Industry average: 30-60 days</p>
                </div>

                {/* DPO */}
                <div>
                  <label className="block text-sm font-semibold mb-2">
                    2. Average Days to Pay Suppliers (DPO)
                  </label>
                  <input
                    type="number"
                    placeholder="e.g., 30 days"
                    value={healthInputs.dpo}
                    onChange={(e) => setHealthInputs({...healthInputs, dpo: e.target.value})}
                    className="w-full px-4 py-3 bg-black border border-zinc-800 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                  <p className="text-xs text-zinc-500 mt-1">Longer is better for cash flow</p>
                </div>

                {/* DIO */}
                <div>
                  <label className="block text-sm font-semibold mb-2">
                    3. Average Days Inventory Sits (DIO)
                  </label>
                  <input
                    type="number"
                    placeholder="e.g., 60 days"
                    value={healthInputs.dio}
                    onChange={(e) => setHealthInputs({...healthInputs, dio: e.target.value})}
                    className="w-full px-4 py-3 bg-black border border-zinc-800 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                  <p className="text-xs text-zinc-500 mt-1">Ideal: 30-60 days</p>
                </div>

                {/* Revenue */}
                <div>
                  <label className="block text-sm font-semibold mb-2">
                    4. Average Monthly Revenue (RM)
                  </label>
                  <input
                    type="number"
                    placeholder="e.g., 50000"
                    value={healthInputs.monthlyRevenue}
                    onChange={(e) => setHealthInputs({...healthInputs, monthlyRevenue: e.target.value})}
                    className="w-full px-4 py-3 bg-black border border-zinc-800 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>

                {/* Expense */}
                <div>
                  <label className="block text-sm font-semibold mb-2">
                    5. Average Monthly Expense (RM)
                  </label>
                  <input
                    type="number"
                    placeholder="e.g., 40000"
                    value={healthInputs.monthlyExpense}
                    onChange={(e) => setHealthInputs({...healthInputs, monthlyExpense: e.target.value})}
                    className="w-full px-4 py-3 bg-black border border-zinc-800 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>

                {/* Calculate Button */}
                <button
                  onClick={calculateHealthScore}
                  className="w-full py-4 bg-primary text-background font-bold rounded-lg hover:shadow-lg hover:shadow-primary/50 transition-all"
                >
                  Diagnose Now
                </button>
              </div>
            </div>

            {/* Results */}
            {showResults && healthScore !== null && (
              <div className={`bg-zinc-950/50/80 backdrop-blur border-2 rounded-2xl p-8 ${getHealthColor(healthScore)}`}>
                <div className="text-center mb-6">
                  <div className="text-6xl font-bold mb-2">{healthScore}/100</div>
                  <div className="text-2xl font-semibold">{getHealthLabel(healthScore)}</div>
                </div>

                {/* CCC Display */}
                <div className="bg-black/50 rounded-lg p-4 mb-6">
                  <div className="text-sm text-zinc-500 mb-2">Your Cash Conversion Cycle:</div>
                  <div className="text-3xl font-bold">
                    {(parseFloat(healthInputs.dso) + parseFloat(healthInputs.dio) - parseFloat(healthInputs.dpo)).toFixed(0)} days
                  </div>
                  <div className="text-sm text-zinc-500 mt-1">
                    (Ideal: &lt;50 days)
                  </div>
                </div>

                {/* Recommendations */}
                <div className="space-y-3">
                  <div className="font-semibold mb-2">📋 Recommendations:</div>
                  {healthScore < 70 && parseFloat(healthInputs.dso) > 45 && (
                    <div className="flex gap-3 p-3 bg-zinc-950/50 rounded-lg">
                      <AlertCircle className="w-5 h-5 text-zinc-300 flex-shrink-0 mt-0.5" />
                      <div className="text-sm">
                        <span className="font-semibold">Slow collections:</span> Your DSO is {healthInputs.dso} days. 
                        Reduce to 40 days to free up ~RM {Math.round((parseFloat(healthInputs.monthlyRevenue) * (parseFloat(healthInputs.dso) - 40) / 30) / 1000)}K cash.
                      </div>
                    </div>
                  )}
                  {healthScore < 70 && parseFloat(healthInputs.dio) > 60 && (
                    <div className="flex gap-3 p-3 bg-zinc-950/50 rounded-lg">
                      <AlertCircle className="w-5 h-5 text-zinc-300 flex-shrink-0 mt-0.5" />
                      <div className="text-sm">
                        <span className="font-semibold">Slow inventory:</span> Your DIO is {healthInputs.dio} days. 
                        Reduce to 55 days to free up cash.
                      </div>
                    </div>
                  )}
                  {parseFloat(healthInputs.dpo) < 30 && (
                    <div className="flex gap-3 p-3 bg-zinc-950/50 rounded-lg">
                      <Zap className="w-5 h-5 text-white flex-shrink-0 mt-0.5" />
                      <div className="text-sm">
                        <span className="font-semibold">Quick tip:</span> Negotiate longer payment terms with suppliers. 
                        Extend DPO to 45 days to improve cash flow.
                      </div>
                    </div>
                  )}
                </div>

                {/* CTA */}
                <div className="mt-6 pt-6 border-t border-zinc-800">
                  <div className="text-center">
                    <p className="text-sm text-zinc-500 mb-4">
                      Want a complete optimization plan?
                    </p>
                    <div className="flex flex-col sm:flex-row gap-3 justify-center">
                      <button className="px-6 py-3 bg-primary text-background font-semibold rounded-lg hover:shadow-lg transition-all">
                        Download Full Report
                      </button>
                      <a
                        href="https://wa.me/60123456789"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-6 py-3 bg-muted text-zinc-300 font-semibold rounded-lg hover:bg-muted/80 transition-all"
                      >
                        WhatsApp Consultation
                      </a>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Laser Divider */}
      <div className="h-px bg-black opacity-30" />

      {/* Real Case Studies - WOW FACTOR */}
      <section className="py-20 relative overflow-hidden">
        <div className="container mx-auto px-6">
          {/* Section Header */}
          <div className="text-center mb-16">
            <span className="px-4 py-2 bg-zinc-950/50 border border-zinc-800 rounded-full text-white text-sm font-semibold inline-block mb-4">
              Real Transformations
            </span>
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              Before & After: The Numbers Don't Lie
            </h2>
            <p className="text-xl text-zinc-500 max-w-3xl mx-auto">
              Real businesses, real results, real impact
            </p>
          </div>

          {/* Case 1: Restaurant */}
          <div className="max-w-5xl mx-auto mb-16">
            <div className="bg-gradient-to-br from-zinc-900/10 to-pink-500/10 border border-zinc-800 rounded-2xl p-8">
              <div className="flex items-start gap-4 mb-6">
                <div className="p-4 bg-zinc-950/50 border border-zinc-800 rounded-lg"><Store className="w-8 h-8 text-white" /></div>
                <div>
                  <h3 className="text-2xl font-bold mb-2">Case 1: Restaurant Owner</h3>
                  <p className="text-lg text-zinc-300 font-semibold mb-1">"Business is good, but I'm running out of cash!"</p>
                  <p className="text-zinc-500">Daily revenue RM 3,000, yet can't pay salaries on time</p>
                </div>
              </div>

              {/* Before/After Grid */}
              <div className="grid md:grid-cols-2 gap-6 mb-6">
                {/* Before */}
                <div className="bg-black/50 rounded-xl p-6">
                  <div className="text-zinc-300 font-bold mb-4 flex items-center gap-2">
                    <TrendingDown className="w-5 h-5" />
                    BEFORE (Crisis Mode)
                  </div>
                  <div className="space-y-3 text-sm">
                    <div className="flex justify-between">
                      <span className="text-zinc-500">Cash Reserve:</span>
                      <span className="font-semibold">RM 2,500 (3 days)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-zinc-500">Cash Gaps/Month:</span>
                      <span className="font-semibold text-zinc-300">4-5 times</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-zinc-500">Emergency Loans:</span>
                      <span className="font-semibold text-zinc-300">RM 15,000 @ 18%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-zinc-500">Owner Stress:</span>
                      <span className="font-semibold text-zinc-300">High</span>
                    </div>
                  </div>
                </div>

                {/* After */}
                <div className="bg-black/50 rounded-xl p-6">
                  <div className="text-white font-bold mb-4 flex items-center gap-2">
                    <TrendingUp className="w-5 h-5" />
                    AFTER (3 Months)
                  </div>
                  <div className="space-y-3 text-sm">
                    <div className="flex justify-between">
                      <span className="text-zinc-500">Cash Reserve:</span>
                      <span className="font-semibold text-white">RM 18,000 (20 days)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-zinc-500">Cash Gaps/Month:</span>
                      <span className="font-semibold text-white">0 times</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-zinc-500">Interest Saved:</span>
                      <span className="font-semibold text-white">RM 2,700/year</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-zinc-500">Owner Stress:</span>
                      <span className="font-semibold text-white">Low</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Solution Highlight */}
              <div className="bg-zinc-950/50 border border-zinc-800 rounded-xl p-6">
                <div className="font-bold mb-3 flex items-center gap-2">
                  <Zap className="w-5 h-5 text-white" />
                  The Solution (No Loan Needed!)
                </div>
                <div className="grid md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <div className="text-white font-semibold mb-1">Step 1:</div>
                    <div className="text-zinc-500">Negotiated 7-day payment terms with supplier</div>
                  </div>
                  <div>
                    <div className="text-white font-semibold mb-1">Step 2:</div>
                    <div className="text-zinc-500">Introduced e-wallet payments (instant cash)</div>
                  </div>
                  <div>
                    <div className="text-white font-semibold mb-1">Step 3:</div>
                    <div className="text-zinc-500">Staggered payment schedule (avoid same-day crunch)</div>
                  </div>
                </div>
                <div className="mt-4 pt-4 border-t border-zinc-800">
                  <div className="text-center">
                    <span className="text-2xl font-bold text-white">Result: RM 15,500 cash freed</span>
                    <p className="text-sm text-zinc-500 mt-1">Revenue grew 28% (used freed cash to expand menu)</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Case 2: Retail Store */}
          <div className="max-w-5xl mx-auto">
            <div className="bg-zinc-950/50 border border-zinc-800 rounded-2xl p-8">
              <div className="flex items-start gap-4 mb-6">
                <div className="p-4 bg-zinc-950/50 border border-zinc-800 rounded-lg"><Store className="w-8 h-8 text-white" /></div>
                <div>
                  <h3 className="text-2xl font-bold mb-2">Case 2: Retail Store Owner</h3>
                  <p className="text-lg text-white font-semibold mb-1">"I made RM 30K profit, but only RM 500 in the bank?"</p>
                  <p className="text-zinc-500">RM 100K revenue, RM 70K cost, RM 30K profit... where's the money?</p>
                </div>
              </div>

              {/* Problem Discovery */}
              <div className="bg-black/50 rounded-xl p-6 mb-6">
                <div className="font-bold mb-4 text-zinc-300 flex items-center gap-2">
                  <AlertCircle className="w-5 h-5" />
                  Cash Trapped in 3 Places:
                </div>
                <div className="grid md:grid-cols-3 gap-4">
                  <div className="text-center p-4 bg-zinc-950/50 rounded-lg">
                    <Package className="w-8 h-8 text-zinc-300 mx-auto mb-2" />
                    <div className="text-2xl font-bold mb-1">RM 35K</div>
                    <div className="text-sm text-zinc-500">Slow-moving inventory (180 days)</div>
                  </div>
                  <div className="text-center p-4 bg-zinc-950/50 rounded-lg">
                    <Clock className="w-8 h-8 text-zinc-300 mx-auto mb-2" />
                    <div className="text-2xl font-bold mb-1">RM 18K</div>
                    <div className="text-sm text-zinc-500">Unpaid invoices (75 days overdue)</div>
                  </div>
                  <div className="text-center p-4 bg-zinc-950/50 rounded-lg">
                    <DollarSign className="w-8 h-8 text-zinc-300 mx-auto mb-2" />
                    <div className="text-2xl font-bold mb-1">RM 12K</div>
                    <div className="text-sm text-zinc-500">Prepaid to suppliers</div>
                  </div>
                </div>
              </div>

              {/* Metrics Improvement */}
              <div className="bg-gradient-to-r from-zinc-900/10 to-pink-500/10 rounded-xl p-6 mb-6">
                <div className="grid md:grid-cols-2 gap-8">
                  {/* Before Metrics */}
                  <div>
                    <div className="text-zinc-300 font-bold mb-4">Before (Crisis)</div>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between p-2 bg-black/30 rounded">
                        <span>Cash Conversion Cycle:</span>
                        <span className="font-bold text-zinc-300">155 days</span>
                      </div>
                      <div className="flex justify-between p-2 bg-black/30 rounded">
                        <span>DIO (Inventory):</span>
                        <span className="font-bold">180 days</span>
                      </div>
                      <div className="flex justify-between p-2 bg-black/30 rounded">
                        <span>DSO (Receivables):</span>
                        <span className="font-bold">75 days</span>
                      </div>
                      <div className="flex justify-between p-2 bg-black/30 rounded">
                        <span>DPO (Payables):</span>
                        <span className="font-bold">100 days</span>
                      </div>
                      <div className="flex justify-between p-2 bg-zinc-950/50 rounded font-bold">
                        <span>Cash Tied Up:</span>
                        <span className="text-zinc-300">RM 65,000</span>
                      </div>
                    </div>
                  </div>

                  {/* After Metrics */}
                  <div>
                    <div className="text-white font-bold mb-4">After (3 Months)</div>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between p-2 bg-black/30 rounded">
                        <span>Cash Conversion Cycle:</span>
                        <span className="font-bold text-white">48 days ↓69%</span>
                      </div>
                      <div className="flex justify-between p-2 bg-black/30 rounded">
                        <span>DIO (Inventory):</span>
                        <span className="font-bold text-white">60 days ↓67%</span>
                      </div>
                      <div className="flex justify-between p-2 bg-black/30 rounded">
                        <span>DSO (Receivables):</span>
                        <span className="font-bold text-white">33 days ↓56%</span>
                      </div>
                      <div className="flex justify-between p-2 bg-black/30 rounded">
                        <span>DPO (Payables):</span>
                        <span className="font-bold text-white">45 days ↑45%</span>
                      </div>
                      <div className="flex justify-between p-2 bg-zinc-950/50 rounded font-bold">
                        <span>Cash Freed:</span>
                        <span className="text-white">RM 53,000</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Result */}
              <div className="bg-zinc-950/50 border border-zinc-800 rounded-xl p-6 text-center">
                <div className="text-3xl font-bold text-white mb-2">
                  RM 53,000 Cash Released
                </div>
                <p className="text-zinc-500 mb-4">
                  Equivalent to 2 months of revenue, without taking a loan
                </p>
                <div className="inline-flex items-center gap-2 text-sm text-white">
                  <CheckCircle className="w-4 h-4" />
                  No more emergency loans (save RM 4,500/year interest)
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Laser Divider */}
      <div className="h-px bg-black opacity-30" />

      {/* Subscription Plans */}
      <section className="py-20 relative overflow-hidden bg-gradient-to-b from-background to-card/30">
        <div className="container mx-auto px-6">
          {/* Section Header */}
          <div className="text-center mb-16">
            <span className="px-4 py-2 bg-zinc-950/50 border border-zinc-800 rounded-full text-white text-sm font-semibold inline-block mb-4">
              Subscription Plans
            </span>
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              Continuous Health Monitoring
            </h2>
            <p className="text-xl text-zinc-500 max-w-3xl mx-auto">
              Like a fitness tracker, but for your business cash flow
            </p>
          </div>

          {/* Pricing Grid */}
          <div className="max-w-6xl mx-auto grid md:grid-cols-3 gap-8">
            {/* Basic */}
            <div className="bg-zinc-950/50/80 backdrop-blur border border-zinc-800 rounded-2xl p-8 hover:border-zinc-800/50 transition-all">
              <div className="text-center mb-6">
                <div className="text-2xl font-bold mb-2">Basic</div>
                <div className="text-4xl font-bold text-primary mb-2">RM 500<span className="text-lg text-zinc-500">/mo</span></div>
                <div className="text-sm text-zinc-500">For startups & small businesses</div>
              </div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-5 h-5 text-white flex-shrink-0 mt-0.5" />
                  <span className="text-sm">Monthly health report</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-5 h-5 text-white flex-shrink-0 mt-0.5" />
                  <span className="text-sm">5-metric health score</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-5 h-5 text-white flex-shrink-0 mt-0.5" />
                  <span className="text-sm">Basic recommendations</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-5 h-5 text-white flex-shrink-0 mt-0.5" />
                  <span className="text-sm">Email support</span>
                </li>
              </ul>
              <button className="w-full py-3 bg-muted text-zinc-300 font-semibold rounded-lg hover:bg-muted/80 transition-all">
                Get Started
              </button>
            </div>

            {/* Pro (Popular) */}
            <div className="bg-zinc-950/50 border-2 border-zinc-800 rounded-2xl p-8 relative scale-105 shadow-lg shadow-white/20">
              <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                <span className="px-4 py-1 bg-primary text-background text-sm font-bold rounded-full">
                  MOST POPULAR
                </span>
              </div>
              <div className="text-center mb-6">
                <div className="text-2xl font-bold mb-2">Pro</div>
                <div className="text-4xl font-bold text-primary mb-2">RM 1,200<span className="text-lg text-zinc-500">/mo</span></div>
                <div className="text-sm text-zinc-500">For growing businesses</div>
              </div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-5 h-5 text-white flex-shrink-0 mt-0.5" />
                  <span className="text-sm font-semibold">Bi-weekly reports</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-5 h-5 text-white flex-shrink-0 mt-0.5" />
                  <span className="text-sm font-semibold">Alert system (issues detected)</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-5 h-5 text-white flex-shrink-0 mt-0.5" />
                  <span className="text-sm font-semibold">Detailed optimization plan</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-5 h-5 text-white flex-shrink-0 mt-0.5" />
                  <span className="text-sm font-semibold">WhatsApp support</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-5 h-5 text-white flex-shrink-0 mt-0.5" />
                  <span className="text-sm font-semibold">Quarterly strategy call</span>
                </li>
              </ul>
              <button className="w-full py-3 bg-primary text-background font-bold rounded-lg hover:shadow-lg hover:shadow-primary/50 transition-all">
                Start Pro Trial
              </button>
            </div>

            {/* Enterprise */}
            <div className="bg-zinc-950/50/80 backdrop-blur border border-zinc-800 rounded-2xl p-8 hover:border-zinc-800/50 transition-all">
              <div className="text-center mb-6">
                <div className="text-2xl font-bold mb-2">Enterprise</div>
                <div className="text-4xl font-bold text-primary mb-2">RM 2,500<span className="text-lg text-zinc-500">/mo</span></div>
                <div className="text-sm text-zinc-500">For established companies</div>
              </div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-5 h-5 text-white flex-shrink-0 mt-0.5" />
                  <span className="text-sm font-semibold">Weekly reports</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-5 h-5 text-white flex-shrink-0 mt-0.5" />
                  <span className="text-sm font-semibold">Real-time monitoring</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-5 h-5 text-white flex-shrink-0 mt-0.5" />
                  <span className="text-sm font-semibold">CFO-level consultation</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-5 h-5 text-white flex-shrink-0 mt-0.5" />
                  <span className="text-sm font-semibold">Dedicated account manager</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-5 h-5 text-white flex-shrink-0 mt-0.5" />
                  <span className="text-sm font-semibold">Custom dashboard</span>
                </li>
              </ul>
              <button className="w-full py-3 bg-muted text-zinc-300 font-semibold rounded-lg hover:bg-muted/80 transition-all">
                Contact Sales
              </button>
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
            Ready to Optimize Your Cash Flow?
          </h2>
          <p className="text-xl text-zinc-500 mb-8 max-w-2xl mx-auto">
            Join 500+ businesses that improved their financial health
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a 
              href="#health-check"
              className="px-8 py-4 bg-primary text-background font-bold rounded-full hover:shadow-lg hover:shadow-primary/50 transition-all inline-flex items-center justify-center gap-2"
            >
              Start Free Assessment
              <ArrowRight className="w-5 h-5" />
            </a>
            <a
              href="https://wa.me/60123456789"
              target="_blank"
              rel="noopener noreferrer"
              className="px-8 py-4 bg-muted text-zinc-300 font-bold rounded-full hover:bg-muted/80 transition-all"
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
