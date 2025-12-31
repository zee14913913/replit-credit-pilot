// Additional translations for new service pages
// This file extends the main translations.ts

export interface CashFlowOptimizationTranslations {
  meta: {
    title: string;
    description: string;
  };
  hero: {
    tag: string;
    title: string;
    subtitle: string;
    stats: Array<{
      value: string;
      label: string;
    }>;
    cta1: string;
    cta2: string;
  };
  healthScore: {
    tag: string;
    title: string;
    description: string;
    levels: {
      critical: { range: string; label: string; desc: string[] };
      warning: { range: string; label: string; desc: string[] };
      healthy: { range: string; label: string; desc: string[] };
    };
    metrics: Array<{
      label: string;
      desc: string;
    }>;
  };
  healthCheck: {
    title: string;
    description: string;
    inputs: Array<{
      label: string;
      placeholder: string;
      hint: string;
    }>;
    button: string;
    results: {
      healthLabel: {
        critical: string;
        warning: string;
        healthy: string;
      };
      cccLabel: string;
      cccIdeal: string;
      recommendations: {
        title: string;
        slowCollections: string;
        slowInventory: string;
        quickTip: string;
      };
      ctaText: string;
      downloadReport: string;
      whatsappConsultation: string;
    };
  };
  cases: {
    tag: string;
    title: string;
    description: string;
    case1: {
      title: string;
      problem: string;
      context: string;
      before: {
        title: string;
        cashReserve: string;
        cashGaps: string;
        emergencyLoans: string;
        ownerStress: string;
      };
      after: {
        title: string;
        cashReserve: string;
        cashGaps: string;
        interestSaved: string;
        ownerStress: string;
      };
      solution: {
        title: string;
        steps: string[];
        result: string;
        resultDesc: string;
      };
    };
    case2: {
      title: string;
      problem: string;
      context: string;
      trapped: {
        title: string;
        inventory: { amount: string; desc: string };
        receivables: { amount: string; desc: string };
        prepaid: { amount: string; desc: string };
      };
      metricsTitle: string;
      before: {
        ccc: string;
        dio: string;
        dso: string;
        dpo: string;
        cashTied: string;
      };
      after: {
        ccc: string;
        dio: string;
        dso: string;
        dpo: string;
        cashFreed: string;
      };
      result: {
        title: string;
        desc: string;
        benefit: string;
      };
    };
  };
  pricing: {
    tag: string;
    title: string;
    description: string;
    plans: Array<{
      name: string;
      price: string;
      period: string;
      desc: string;
      features: string[];
      cta: string;
    }>;
  };
  finalCta: {
    title: string;
    description: string;
    cta1: string;
    cta2: string;
  };
}

export interface BusinessPlanningTranslations {
  meta: {
    title: string;
    description: string;
  };
  hero: {
    tag: string;
    title: string;
    subtitle: string;
    stats: Array<{
      value: string;
      label: string;
      change: string;
    }>;
    cta1: string;
    cta2: string;
  };
  samples: {
    tag: string;
    title: string;
    description: string;
    cases: Array<{
      industry: string;
      title: string;
      pages: string;
      delivery: string;
      language: string;
      loanApproved: string;
      amount: string;
      bank: string;
    }>;
  };
  deliverables: {
    title: string;
    description: string;
    items: Array<{
      title: string;
      desc: string;
    }>;
  };
  packages: {
    tag: string;
    title: string;
    description: string;
    plans: Array<{
      name: string;
      price: string;
      delivery: string;
      popular: boolean;
      features: Array<{
        text: string;
        included: boolean;
      }>;
      cta: string;
    }>;
    guarantee: {
      title: string;
      description: string;
    };
  };
  caseStudy: {
    tag: string;
    title: string;
    description: string;
    header: {
      title: string;
      problem: string;
      context: string;
    };
    hisBP: {
      title: string;
      pages: string;
      timeSpent: string;
      result: string;
      feedback: {
        title: string;
        points: string[];
      };
    };
    ourBP: {
      title: string;
      pages: string;
      delivery: string;
      result: string;
      response: {
        title: string;
        points: string[];
      };
    };
    solution: {
      title: string;
      steps: Array<{
        title: string;
        desc: string;
      }>;
      result: {
        title: string;
        desc: string;
      };
    };
  };
  faq: {
    title: string;
    items: Array<{
      q: string;
      a: string;
    }>;
  };
  finalCta: {
    title: string;
    description: string;
    cta1: string;
    cta2: string;
  };
}

// English Translations
export const cashFlowOptimizationEN: CashFlowOptimizationTranslations = {
  meta: {
    title: 'Cash Flow Optimization | INFINITE GZ',
    description: '82% of SMEs fail due to poor cash flow. Get your free health check and optimize your business finances.'
  },
  hero: {
    tag: '🩺 Health Diagnostic Service',
    title: 'Is Your Business\nFinancially Healthy?',
    subtitle: '82% of SMEs fail due to poor cash flow management',
    stats: [
      { value: '82%', label: 'Failure Rate' },
      { value: '56%', label: 'Face Cash Issues' },
      { value: '94.6%', label: 'No Planning' },
      { value: 'RM 180K', label: 'Avg. Cash Freed' }
    ],
    cta1: 'Free Health Check',
    cta2: 'WhatsApp Consultation'
  },
  healthScore: {
    tag: '🩺 Health Diagnostic',
    title: 'Cash Flow Health Score',
    description: 'Like a body checkup, but for your business finances',
    levels: {
      critical: {
        range: '0-40',
        label: '🔴 Critical',
        desc: ['High bankruptcy risk', 'Urgent action needed', 'Cash running out fast']
      },
      warning: {
        range: '41-70',
        label: '🟡 Warning',
        desc: ['Room for improvement', 'Optimize now to avoid crisis', 'Cash flow unstable']
      },
      healthy: {
        range: '71-100',
        label: '🟢 Healthy',
        desc: ['Strong financial health', 'Ready for growth', 'Cash flow stable']
      }
    },
    metrics: [
      { label: 'DSO', desc: 'Days Sales Outstanding' },
      { label: 'DPO', desc: 'Days Payable Outstanding' },
      { label: 'DIO', desc: 'Days Inventory Outstanding' },
      { label: 'CCC', desc: 'Cash Conversion Cycle' },
      { label: 'Ratio', desc: 'Current Ratio' }
    ]
  },
  healthCheck: {
    title: '🧮 Free Health Check',
    description: 'Enter 5 numbers, get instant diagnosis',
    inputs: [
      { label: '1. Average Days to Collect Payment (DSO)', placeholder: 'e.g., 45 days', hint: 'Industry average: 30-60 days' },
      { label: '2. Average Days to Pay Suppliers (DPO)', placeholder: 'e.g., 30 days', hint: 'Longer is better for cash flow' },
      { label: '3. Average Days Inventory Sits (DIO)', placeholder: 'e.g., 60 days', hint: 'Ideal: 30-60 days' },
      { label: '4. Average Monthly Revenue (RM)', placeholder: 'e.g., 50000', hint: '' },
      { label: '5. Average Monthly Expense (RM)', placeholder: 'e.g., 40000', hint: '' }
    ],
    button: '🩺 Diagnose Now',
    results: {
      healthLabel: {
        critical: '🔴 Critical',
        warning: '🟡 Warning',
        healthy: '🟢 Healthy'
      },
      cccLabel: 'Your Cash Conversion Cycle:',
      cccIdeal: '(Ideal: <50 days)',
      recommendations: {
        title: '📋 Recommendations:',
        slowCollections: 'Slow collections: Your DSO is {days} days. Reduce to 40 days to free up ~RM {amount}K cash.',
        slowInventory: 'Slow inventory: Your DIO is {days} days. Reduce to 55 days to free up cash.',
        quickTip: 'Quick tip: Negotiate longer payment terms with suppliers. Extend DPO to 45 days to improve cash flow.'
      },
      ctaText: 'Want a complete optimization plan?',
      downloadReport: 'Download Full Report',
      whatsappConsultation: 'WhatsApp Consultation'
    }
  },
  cases: {
    tag: '💡 Real Transformations',
    title: 'Before & After: The Numbers Don\'t Lie',
    description: 'Real businesses, real results, real impact',
    case1: {
      title: 'Case 1: Restaurant Owner',
      problem: '"Business is good, but I\'m running out of cash!"',
      context: 'Daily revenue RM 3,000, yet can\'t pay salaries on time',
      before: {
        title: 'BEFORE (Crisis Mode)',
        cashReserve: 'Cash Reserve: RM 2,500 (3 days)',
        cashGaps: 'Cash Gaps/Month: 4-5 times',
        emergencyLoans: 'Emergency Loans: RM 15,000 @ 18%',
        ownerStress: 'Owner Stress: ⭐⭐⭐⭐⭐'
      },
      after: {
        title: 'AFTER (3 Months)',
        cashReserve: 'Cash Reserve: RM 18,000 (20 days)',
        cashGaps: 'Cash Gaps/Month: 0 times ✓',
        interestSaved: 'Interest Saved: RM 2,700/year',
        ownerStress: 'Owner Stress: ⭐ (Relaxed)'
      },
      solution: {
        title: 'The Solution (No Loan Needed!)',
        steps: [
          'Step 1: Negotiated 7-day payment terms with supplier',
          'Step 2: Introduced e-wallet payments (instant cash)',
          'Step 3: Staggered payment schedule (avoid same-day crunch)'
        ],
        result: '💰 Result: RM 15,500 cash freed',
        resultDesc: 'Revenue grew 28% (used freed cash to expand menu)'
      }
    },
    case2: {
      title: 'Case 2: Retail Store Owner',
      problem: '"I made RM 30K profit, but only RM 500 in the bank?"',
      context: 'RM 100K revenue, RM 70K cost, RM 30K profit... where\'s the money?',
      trapped: {
        title: 'Cash Trapped in 3 Places:',
        inventory: { amount: 'RM 35K', desc: 'Slow-moving inventory (180 days)' },
        receivables: { amount: 'RM 18K', desc: 'Unpaid invoices (75 days overdue)' },
        prepaid: { amount: 'RM 12K', desc: 'Prepaid to suppliers' }
      },
      metricsTitle: '📊 Metrics Improvement',
      before: {
        ccc: 'Cash Conversion Cycle: 155 days',
        dio: 'DIO (Inventory): 180 days',
        dso: 'DSO (Receivables): 75 days',
        dpo: 'DPO (Payables): 100 days',
        cashTied: 'Cash Tied Up: RM 65,000'
      },
      after: {
        ccc: 'Cash Conversion Cycle: 48 days ↓69%',
        dio: 'DIO (Inventory): 60 days ↓67%',
        dso: 'DSO (Receivables): 33 days ↓56%',
        dpo: 'DPO (Payables): 45 days ↑45%',
        cashFreed: 'Cash Freed: RM 53,000 ✓'
      },
      result: {
        title: '💎 RM 53,000 Cash Released',
        desc: 'Equivalent to 2 months of revenue, without taking a loan',
        benefit: 'No more emergency loans (save RM 4,500/year interest)'
      }
    }
  },
  pricing: {
    tag: '💳 Subscription Plans',
    title: 'Continuous Health Monitoring',
    description: 'Like a fitness tracker, but for your business cash flow',
    plans: [
      {
        name: 'Basic',
        price: 'RM 500',
        period: '/mo',
        desc: 'For startups & small businesses',
        features: [
          'Monthly health report',
          '5-metric health score',
          'Basic recommendations',
          'Email support'
        ],
        cta: 'Get Started'
      },
      {
        name: 'Pro',
        price: 'RM 1,200',
        period: '/mo',
        desc: 'For growing businesses',
        features: [
          'Bi-weekly reports',
          'Alert system (issues detected)',
          'Detailed optimization plan',
          'WhatsApp support',
          'Quarterly strategy call'
        ],
        cta: 'Start Pro Trial'
      },
      {
        name: 'Enterprise',
        price: 'RM 2,500',
        period: '/mo',
        desc: 'For established companies',
        features: [
          'Weekly reports',
          'Real-time monitoring',
          'CFO-level consultation',
          'Dedicated account manager',
          'Custom dashboard'
        ],
        cta: 'Contact Sales'
      }
    ]
  },
  finalCta: {
    title: 'Ready to Optimize Your Cash Flow?',
    description: 'Join 500+ businesses that improved their financial health',
    cta1: 'Start Free Assessment',
    cta2: 'WhatsApp Consultation'
  }
};

export const businessPlanningEN: BusinessPlanningTranslations = {
  meta: {
    title: 'Business Planning | Professional BP Writing | INFINITE GZ',
    description: '85% loan approval rate. Professional business plan writing service. Bilingual (EN/CN). 7-14 days delivery.'
  },
  hero: {
    tag: '📄 Professional Document Delivery',
    title: 'Your Business Plan,\nDone by Professionals',
    subtitle: '85% Loan Approval Rate | Bilingual | 7-14 Days Delivery',
    stats: [
      { value: '84.2%', label: 'Approval Rate', change: '+6.5%' },
      { value: '21 Days', label: 'Avg Approval Time', change: '-53%' },
      { value: 'RM 500K', label: 'Avg Loan Amount', change: 'Up to RM 2M' },
      { value: '4.9/5.0', label: 'Client Satisfaction', change: '500+ reviews' }
    ],
    cta1: 'View Packages',
    cta2: 'View Sample BP'
  },
  samples: {
    tag: '📄 Document Gallery',
    title: 'See What You\'ll Receive',
    description: 'Real business plan samples from different industries',
    cases: [
      {
        industry: 'Manufacturing Industry',
        title: 'Auto Parts Manufacturer',
        pages: '45 pages',
        delivery: '7 days',
        language: 'Chinese Version',
        loanApproved: 'Loan Approved',
        amount: 'RM 500K @ 5.5%',
        bank: 'Maybank | 21 days approval'
      },
      {
        industry: 'F&B Industry',
        title: 'Restaurant Chain',
        pages: '38 pages',
        delivery: '5 days',
        language: 'English Version',
        loanApproved: 'Loan Approved',
        amount: 'RM 300K @ 6.2%',
        bank: 'CIMB | 18 days approval'
      },
      {
        industry: 'Retail Industry',
        title: 'Fashion Retail Store',
        pages: '52 pages',
        delivery: '10 days',
        language: 'Bilingual (CN + EN)',
        loanApproved: 'Loan Approved',
        amount: 'RM 800K @ 5.8%',
        bank: 'Hong Leong | 25 days approval'
      }
    ]
  },
  deliverables: {
    title: '📦 What You\'ll Receive',
    description: 'Not just a document, but a complete financing toolkit',
    items: [
      { title: 'Complete Business Plan (PDF + Word)', desc: 'Professionally formatted, ready to submit' },
      { title: 'Financial Forecast Model (Excel)', desc: 'Editable 3-year projections with formulas' },
      { title: 'Industry Analysis Report (10-15 pages)', desc: 'Market size, trends, and growth projections' },
      { title: 'Competitive Analysis (5 Competitors)', desc: 'Detailed comparison table with positioning' },
      { title: 'Financing Strategy Recommendation', desc: 'Best banks, loan types, and terms' },
      { title: '1-Hour Bank Meeting Coaching (Premium)', desc: 'Prepare for Q&A and presentation tips' }
    ]
  },
  packages: {
    tag: '💰 Transparent Pricing',
    title: 'Choose Your Package',
    description: 'Fixed price, no hidden fees, money-back guarantee',
    plans: [
      {
        name: 'Basic',
        price: 'RM 3,000',
        delivery: '7 Days Delivery',
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
        ],
        cta: 'Select Package'
      },
      {
        name: 'Professional',
        price: 'RM 5,500',
        delivery: '10 Days Delivery',
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
        ],
        cta: 'Get Started Now'
      },
      {
        name: 'Premium',
        price: 'RM 8,500',
        delivery: '14 Days Delivery',
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
        ],
        cta: 'Select Package'
      }
    ],
    guarantee: {
      title: '100% Satisfaction Guarantee',
      description: 'If your loan is rejected due to BP quality issues, we\'ll refund 50% of your payment'
    }
  },
  caseStudy: {
    tag: '💡 Real Transformation',
    title: 'From Rejection to Approval',
    description: 'How we turned a rejected application into RM 500K approval',
    header: {
      title: 'Case: Factory Owner',
      problem: '"Bank said my business plan is garbage"',
      context: 'Spent 2 weeks writing 30-page BP, rejected by bank in 5 minutes'
    },
    hisBP: {
      title: '❌ His BP (Rejected)',
      pages: 'Pages: 30 (too long)',
      timeSpent: 'Time Spent: 2 weeks',
      result: 'Result: REJECTED',
      feedback: {
        title: 'Bank Feedback:',
        points: [
          'Executive Summary too long (5 pages)',
          'Market analysis copied from Wikipedia',
          'No competitive analysis',
          'Unrealistic financial projections (50% growth/year)',
          'Vague financing purpose ("expansion")'
        ]
      }
    },
    ourBP: {
      title: '✓ Our BP (Approved)',
      pages: 'Pages: 45 (well-structured)',
      delivery: 'Delivery: 7 days',
      result: 'Result: APPROVED RM 500K',
      response: {
        title: 'Bank Response:',
        points: [
          '"Most professional BP we\'ve seen this year"',
          'Interest rate: 5.8% (below market avg 6.5%)',
          'Approval time: 21 days (vs avg 45 days)',
          'Loan term: 7 years'
        ]
      }
    },
    solution: {
      title: 'Our "Bank Perspective" Approach',
      steps: [
        { title: '1. Executive Summary', desc: 'Compressed to 1 page using "3-30-3 Rule": 3 seconds to hook, 30 seconds for key data, 3 minutes for full summary' },
        { title: '2. Market Analysis', desc: 'Used MIDA reports and industry data. Showed RM 28B market with 6.5% growth rate' },
        { title: '3. Financial Projections', desc: '3 scenarios: Conservative (70% probability), Reasonable (60%), Optimistic (30%)' }
      ],
      result: {
        title: 'RM 500K Loan Approved @ 5.8%',
        desc: 'Plus: Editable Excel model + Bank meeting coaching'
      }
    }
  },
  faq: {
    title: 'Frequently Asked Questions',
    items: [
      {
        q: 'I don\'t know how to write financial projections, what do I do?',
        a: 'We do it for you! Just provide your historical data (if any) and business goals. Our team will create professional 3-year financial projections with detailed assumptions.'
      },
      {
        q: 'What if the bank rejects my BP after I paid?',
        a: 'We offer 1 FREE revision for Professional & Premium packages. If rejection is due to BP quality issues (not your business fundamentals), we refund 50% of your payment.'
      },
      {
        q: 'Can I buy only the financial model without the full BP?',
        a: 'Yes! We offer standalone financial modeling service at RM 1,500. However, we recommend the full BP package for better bank approval chances.'
      },
      {
        q: 'Do you provide Chinese AND English versions?',
        a: 'Basic package includes Chinese version only. Professional includes English version. Premium includes both in a single integrated document.'
      },
      {
        q: 'How long does the approval process take?',
        a: 'Based on our 500+ clients: Average 21-25 days for approval (vs market average 45 days). Some clients get approved in as fast as 18 days.'
      }
    ]
  },
  finalCta: {
    title: 'Ready to Get Your Loan Approved?',
    description: 'Join 500+ businesses that secured financing with our professional business plans',
    cta1: 'Choose Your Package',
    cta2: 'WhatsApp Consultation'
  }
};
