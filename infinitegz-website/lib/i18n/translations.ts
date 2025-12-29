export type Language = 'en' | 'zh' | 'ms';

export interface Translations {
  // Navigation
  nav: {
    home: string;
    creditpilot: string;
    advisory: string;
    solutions: string;
    company: string;
    news: string;
    resources: string;
    careers: string;
  };
  
  // Common
  common: {
    learnMore: string;
    getStarted: string;
    readMore: string;
    viewAll: string;
    contactUs: string;
    applyNow: string;
    bookConsultation: string;
    whatsappUs: string;
    explore: string;
    viewDetails: string;
    useCreditPilot: string;
  };
  
  // Home Page
  home: {
    hero: {
      title: string;
      subtitle: string;
      description: string;
      bottomDescription: string;
    };
    products: {
      tag: string;
      title: string;
      items: Array<{
        tag: string;
        title: string;
        description: string;
        features: string[];
        linkText: string;
        linkUrl: string;
      }>;
    };
    content: {
      tag: string;
      title: string;
      description: string;
      features: Array<{
        title: string;
        description: string;
      }>;
      detailsTitle: string;
      details: Array<{
        title: string;
        description: string;
      }>;
    };
    news: {
      tag: string;
      title: string;
      description: string;
      items: Array<{
        date: string;
        title: string;
        description: string;
        category: string;
      }>;
    };
    footer: {
      title: string;
      description: string;
      copyright: string;
      sections: {
        try: string;
        products: string;
        company: string;
        resources: string;
      };
      links: {
        web: string;
        whatsapp: string;
        phone: string;
        creditpilot: string;
        advisory: string;
        creditCard: string;
        digital: string;
        accounting: string;
        about: string;
        careers: string;
        contact: string;
        newsUpdates: string;
        partners: string;
        dsrGuide: string;
        taxOptimization: string;
        faq: string;
        privacy: string;
        legal: string;
        terms: string;
      };
    };
  };
  
  // CreditPilot Page
  creditpilot: {
    meta: {
      title: string;
      description: string;
    };
    hero: {
      tag: string;
      title: string;
      subtitle: string;
      cta1: string;
      cta2: string;
    };
    capabilities: {
      tag: string;
      title: string;
      features: Array<{
        title: string;
        description: string;
      }>;
    };
    howItWorks: {
      tag: string;
      title: string;
      steps: Array<{
        number: string;
        title: string;
        description: string;
      }>;
    };
    cta: {
      title: string;
      description: string;
      buttonText: string;
    };
  };
  
  // Advisory Page
  advisory: {
    meta: {
      title: string;
      description: string;
    };
    hero: {
      tag: string;
      title: string;
      description: string;
    };
    services: {
      tag: string;
      title: string;
      items: Array<{
        num: string;
        title: string;
        description: string;
      }>;
    };
    benefits: {
      tag: string;
      title: string;
      items: Array<{
        icon: string;
        title: string;
        description: string;
      }>;
    };
    cta: {
      title: string;
      description: string;
    };
  };
  
  // Solutions Page
  solutions: {
    meta: {
      title: string;
      description: string;
    };
    hero: {
      tag: string;
      title: string;
      description: string;
    };
    products: Array<{
      tag: string;
      title: string;
      description: string;
      linkText: string;
    }>;
    coreBusiness: {
      tag: string;
      title: string;
      description: string;
      features: Array<{
        icon: string;
        title: string;
        description: string;
      }>;
    };
    complementaryServices: {
      tag: string;
      title: string;
      description: string;
      items: Array<{
        num: string;
        title: string;
        description: string;
      }>;
    };
    pricing: {
      tag: string;
      title: string;
      models: Array<{
        tag: string;
        title: string;
        price: string;
        description: string;
        features: string[];
      }>;
    };
    targetCustomers: {
      tag: string;
      title: string;
      customers: Array<{
        icon: string;
        title: string;
        description: string;
      }>;
    };
    cta: {
      title: string;
      description: string;
    };
  };
  
  // Company Page
  company: {
    meta: {
      title: string;
      description: string;
    };
    hero: {
      tag: string;
      title: string;
      description: string;
    };
    mission: {
      tag: string;
      title: string;
      description: string;
    };
    values: {
      tag: string;
      title: string;
      items: Array<{
        icon: string;
        title: string;
        description: string;
      }>;
    };
    cta: {
      title: string;
      description: string;
    };
  };
  
  // News Page
  news: {
    meta: {
      title: string;
      description: string;
    };
    hero: {
      tag: string;
      title: string;
      description: string;
    };
    items: Array<{
      title: string;
      date: string;
      category: string;
    }>;
  };
  
  // Resources Page
  resources: {
    meta: {
      title: string;
      description: string;
    };
    hero: {
      tag: string;
      title: string;
      description: string;
    };
    stats: Array<{
      number: string;
      title: string;
      description: string;
    }>;
    timeline: {
      tag: string;
      title: string;
      milestones: Array<{
        year: string;
        title: string;
        description: string;
      }>;
    };
  };
  
  // Careers Page
  careers: {
    meta: {
      title: string;
      description: string;
    };
    hero: {
      tag: string;
      title: string;
      description: string;
    };
    benefits: {
      tag: string;
      title: string;
      items: Array<{
        icon: string;
        title: string;
        description: string;
      }>;
    };
    jobs: {
      tag: string;
      title: string;
      positions: Array<{
        title: string;
        department: string;
        location: string;
        type: string;
      }>;
    };
    cta: {
      title: string;
      description: string;
    };
  };
  
  // Credit Card Management Page
  cardManagement: {
    hero: {
      tag: string;
      title: string;
      subtitle: string;
      benefits: Array<{
        icon: string;
        value: string;
        label: string;
      }>;
      cta1: string;
      cta2: string;
      socialProof: string;
    };
    painPoints: {
      tag: string;
      title: string;
      subtitle: string;
      points: Array<{
        icon: string;
        title: string;
        description: string;
        impact: string;
      }>;
      stats: Array<{
        value: string;
        label: string;
      }>;
    };
    solutions: {
      tag: string;
      title: string;
      subtitle: string;
      services: Array<{
        icon: string;
        title: string;
        description: string;
        benefits: string[];
      }>;
    };
    caseStudies: {
      tag: string;
      title: string;
      subtitle: string;
      before: string;
      after: string;
      cases: Array<{
        client: string;
        type: string;
        before: string;
        after: string;
        savings: string;
        period: string;
      }>;
    };
    pricing: {
      tag: string;
      title: string;
      subtitle: string;
      recommended: string;
      plans: {
        individual: {
          label: string;
          options: Array<{
            name: string;
            price: string;
            period: string;
            features: string[];
            recommended?: boolean;
            cta: {
              text: string;
              link: string;
            };
          }>;
        };
        corporate: {
          label: string;
          options: Array<{
            name: string;
            price: string;
            period: string;
            features: string[];
            recommended?: boolean;
            cta: {
              text: string;
              link: string;
            };
          }>;
        };
        loan: {
          label: string;
          options: Array<{
            name: string;
            price: string;
            period: string;
            features: string[];
            recommended?: boolean;
            cta: {
              text: string;
              link: string;
            };
          }>;
        };
      };
    };
    socialProof: {
      stats: Array<{
        value: string;
        label: string;
      }>;
      badges: string[];
    };
    faq: {
      title: string;
      subtitle: string;
      questions: Array<{
        question: string;
        answer: string;
      }>;
    };
    finalCta: {
      title: string;
      subtitle: string;
      cta1: string;
      cta2: string;
      relatedTitle: string;
      relatedServices: Array<{
        name: string;
        link: string;
      }>;
    };
  };
}

export const translations: Record<Language, Translations> = {
  en: {
    nav: {
      home: 'Home',
      creditpilot: 'CreditPilot',
      advisory: 'Advisory',
      solutions: 'Solutions',
      company: 'Company',
      news: 'News',
      resources: 'Resources',
      careers: 'Careers',
    },
    common: {
      learnMore: 'Learn More',
      getStarted: 'Get Started',
      readMore: 'Read More',
      viewAll: 'View All',
      contactUs: 'Contact Us',
      applyNow: 'Apply Now',
      bookConsultation: 'Book Consultation',
      whatsappUs: 'WhatsApp Us',
      explore: 'Explore',
      viewDetails: 'View Details',
      useCreditPilot: 'Use CreditPilot',
    },
    home: {
      hero: {
        title: 'The World\'s Money,\nMade Yours.',
        subtitle: 'Your One-Stop Solution',
        description: 'For Loans, Financial Optimization, And Digital Advisory Services For Your Businesses.',
        bottomDescription: 'INFINITE GZ Provides Comprehensive Financial Analysis, Loan Matching From All Malaysian Banks And Fintech Companies, Plus 8 Complementary Services - All With Zero Upfront Fees.',
      },
      products: {
        tag: 'Our Services',
        title: 'Complete Financial Solutions For Malaysian Businesses',
        items: [
          {
            tag: 'Smart Analysis',
            title: 'CreditPilot',
            description: 'Intelligent Loan Analysis System That Finds The Best Loan Products From All Malaysian Banks, Digital Banks, And Fintech Companies With AI-Powered Matching.',
            features: ['DSR Beautification', 'Best Rate Matching', 'Smart Recommendations', 'Real-Time Analysis'],
            linkText: 'Use Now',
            linkUrl: 'https://portal.infinitegz.com/creditpilot',
          },
          {
            tag: 'Expert Guidance',
            title: 'Loan Advisory',
            description: 'Professional Consultation For All Types Of Loans Including Housing, Automotive, And Business Financing With Zero Upfront Fees And Success-Based Pricing.',
            features: ['Zero Upfront Cost', 'Expert Consultation', 'Success-Based Fee', 'All Loan Types'],
            linkText: 'Consult Now',
            linkUrl: 'https://portal.infinitegz.com/advisory',
          },
          {
            tag: 'Digital Transform',
            title: 'Digitalization & Accounting',
            description: 'Complete Digital Transformation For Traditional Businesses Including E-Commerce Setup, Online Store Management, Accounting Services, And Tax Optimization.',
            features: ['Online Store Setup', '15% Tax Optimization', 'Accounting Services', 'Business Planning'],
            linkText: 'Learn More',
            linkUrl: 'https://portal.infinitegz.com/digital',
          },
        ],
      },
      content: {
        tag: 'Financial Intelligence',
        title: 'Understand Your Finances',
        description: 'INFINITE GZ Provides Comprehensive Financial Analysis And Optimization Services. We Help You Navigate The Complex World Of Banking And Finance In Malaysia, Ensuring You Get The Best Deals And Maintain Optimal Financial Health.',
        features: [
          {
            title: 'DSR Beautification',
            description: 'Optimize Your Debt Service Ratio To Improve Loan Approval Chances And Access Better Rates',
          },
          {
            title: 'Debt Consolidation',
            description: 'Merge Multiple Debts Into One Manageable Payment With Significantly Lower Interest Rates',
          },
          {
            title: 'Tax Optimization',
            description: 'Strategic 15% Tax Deduction Planning For Individuals And Businesses To Maximize Savings',
          },
          {
            title: 'Credit Score',
            description: 'Improve Your Credit Rating Through Strategic Financial Planning And Expert Guidance',
          },
        ],
        detailsTitle: 'Do More With CreditPilot',
        details: [
          {
            title: 'Smart Loan Matching',
            description: 'Our AI-Powered System Analyzes Your Financial Profile And Matches You With The Best Loan Products From All Legitimate Banks, Digital Banks, And Fintech Companies In Malaysia. Get Personalized Recommendations Based On Your Unique Situation.',
          },
          {
            title: 'Comprehensive Services',
            description: 'Beyond Loans, We Offer 8 Complementary Services Including Business Planning, Insurance Consultation, E-Commerce Setup, Accounting, And Credit Card Management - All Completely Free For Our Loan Clients. Your Success Is Our Success.',
          },
          {
            title: 'Zero Upfront Fees',
            description: 'We Only Charge Upon Successful Loan Approval. Our Success-Based Model Ensures We\'re Fully Committed To Getting You The Best Possible Outcome. No Hidden Fees, No Surprises - Just Transparent Service.',
          },
          {
            title: '100% Legal & Compliant',
            description: 'We Only Work With Licensed Financial Institutions Regulated By Bank Negara Malaysia. No Loan Sharks, No Illegal Lending - Your Financial Safety And Security Is Our Top Priority.',
          },
        ],
      },
      news: {
        tag: 'Latest Updates',
        title: 'News & Insights',
        description: 'Stay Informed With The Latest Financial News, Loan Policies, Success Stories, And Expert Insights',
        items: [
          {
            date: 'Dec 20, 2024',
            title: 'New OPR Rate Changes',
            description: 'Bank Negara Malaysia Announces New Overnight Policy Rate. Learn How This Impacts Your Existing And Future Loan Applications.',
            category: 'Policy Update',
          },
          {
            date: 'Dec 15, 2024',
            title: 'RM 2M Business Loan Success',
            description: 'How We Helped A Traditional Manufacturing Business Secure Financing For Digital Transformation And Expansion Plans.',
            category: 'Case Study',
          },
          {
            date: 'Dec 10, 2024',
            title: 'Year-End Tax Planning 2024',
            description: 'Maximize Your Tax Relief Claims And Optimize Your Financial Position Before The Year-End Deadline Approaches.',
            category: 'Financial Tips',
          },
          {
            date: 'Dec 5, 2024',
            title: 'Digital Vs Traditional Banks',
            description: 'Comprehensive Comparison Of Loan Products From Digital Banks And Traditional Banking Institutions In Malaysia.',
            category: 'Guide',
          },
          {
            date: 'Nov 28, 2024',
            title: 'Credit Card Debt Management',
            description: 'Learn Effective Strategies To Manage Multiple Credit Cards, Avoid Late Fees, And Optimize Utilization Ratios.',
            category: 'Financial Tips',
          },
          {
            date: 'Nov 20, 2024',
            title: 'Traditional Business Goes Digital',
            description: 'How A 40-Year-Old Retail Business Tripled Revenue Through Digital Transformation And Online Sales Channels.',
            category: 'Case Study',
          },
        ],
      },
      footer: {
        title: 'Ready To Optimize Your Finances?',
        description: 'Join Thousands Of Malaysian Businesses That Trust INFINITE GZ For Their Financial Success',
        copyright: '© 2024 INFINITE GZ SDN BHD. All Rights Reserved.',
        sections: {
          try: 'Try CreditPilot On',
          products: 'Products',
          company: 'Company',
          resources: 'Resources',
        },
        links: {
          web: 'Web',
          whatsapp: 'WhatsApp',
          phone: 'Phone',
          creditpilot: 'CreditPilot',
          advisory: 'Loan Advisory',
          creditCard: 'Credit Card Services',
          digital: 'Digitalization',
          accounting: 'Accounting Services',
          about: 'About Us',
          careers: 'Careers',
          contact: 'Contact',
          newsUpdates: 'News & Updates',
          partners: 'Partners',
          dsrGuide: 'DSR Guide',
          taxOptimization: 'Tax Optimization',
          faq: 'FAQ',
          privacy: 'Privacy Policy',
          legal: 'Legal',
          terms: 'Terms',
        },
      },
    },
    creditpilot: {
      meta: {
        title: 'CreditPilot | INFINITE GZ',
        description: 'AI-powered loan matching system that finds the best loan products from all Malaysian financial institutions.',
      },
      hero: {
        tag: 'AI-Powered Loan Matching',
        title: 'The Next Frontier Of Smart Financing',
        subtitle: 'Intelligent Analysis Across 50+ Malaysian Financial Institutions',
        cta1: 'Start Free Analysis',
        cta2: 'Learn More',
      },
      capabilities: {
        tag: 'Capabilities',
        title: 'Financial Tools That Work For You',
        features: [
          {
            title: 'Smart Loan Matching',
            description: 'AI-Powered Analysis Across 50+ Malaysian Banks And Fintechs, Ranked By Approval Probability.',
          },
          {
            title: 'DSR Optimization',
            description: 'Improve Your Approval Chances By Up To 40% With Strategic Debt Service Ratio Enhancement.',
          },
          {
            title: 'Real-Time Comparison',
            description: 'Compare Interest Rates, Fees, And Terms From All Major Financial Institutions In Real-Time.',
          },
        ],
      },
      howItWorks: {
        tag: 'How It Works',
        title: 'Get Your Results In 3 Simple Steps',
        steps: [
          {
            number: '01',
            title: 'Enter Your Details',
            description: 'Provide your financial information securely through our platform',
          },
          {
            number: '02',
            title: 'AI Analysis',
            description: 'Our system analyzes 50+ institutions in real-time',
          },
          {
            number: '03',
            title: 'Get Recommendations',
            description: 'Receive ranked loan options with approval probability',
          },
        ],
      },
      cta: {
        title: 'Ready To Find Your Best Loan?',
        description: 'Start your free analysis now and discover the best financing options for your business.',
        buttonText: 'Start Free Analysis',
      },
    },

    advisory: {
      meta: {
        title: 'Advisory Services | INFINITE GZ',
        description: 'Comprehensive business advisory services. 8 complementary services completely free for loan clients.',
      },
      hero: {
        tag: 'Complete Financial Solutions',
        title: '8 Complementary Business Services',
        description: 'All Services Completely Free For Loan Clients. From Financial Optimization To E-Commerce Solutions.',
      },
      services: {
        tag: '8 Core Services',
        title: 'Comprehensive Business Support',
        items: [
          {
            num: '01',
            title: 'Financial Optimization',
            description: 'DSR Enhancement, Debt Consolidation, Fixed Deposit Planning, Credit Score Optimization, Cash Flow Management',
          },
          {
            num: '02',
            title: 'Marketing & Advertising',
            description: 'Channel Design, Marketing Strategy, Market Planning, Supplier Advertising Solutions',
          },
          {
            num: '03',
            title: 'Business Planning',
            description: 'Business Plans, Financing Design, Business Model Development, Market Analysis',
          },
          {
            num: '04',
            title: 'Insurance Services',
            description: 'Product Recommendations, Insurance Planning, Coverage Analysis',
          },
          {
            num: '05',
            title: 'E-Commerce Solutions',
            description: 'Quick Store Setup, Promotion, Operations, Channel Building, E-Commerce Support ⭐',
          },
          {
            num: '06',
            title: 'Membership System',
            description: 'System Design, Points & Rewards, Benefits Planning',
          },
          {
            num: '07',
            title: 'Accounting & Audit',
            description: 'Bookkeeping, Tax Filing, Financial Statements, Audit Support, 15% Tax Optimization',
          },
          {
            num: '08',
            title: 'Credit Card Management',
            description: 'Payment Reminders, Payment On Behalf, Purchase On Behalf Services (50/50 Revenue Share)',
          },
        ],
      },
      benefits: {
        tag: 'Why Choose Us',
        title: 'Expert Financial Guidance',
        items: [
          {
            icon: '🎯',
            title: 'Personalized Solutions',
            description: 'Tailored financial strategies designed specifically for your business needs and goals.',
          },
          {
            icon: '💼',
            title: 'Industry Expertise',
            description: 'Deep understanding of Malaysian financial landscape and regulatory requirements.',
          },
          {
            icon: '🤝',
            title: 'Ongoing Support',
            description: 'Continuous guidance and support throughout your financial journey with us.',
          },
        ],
      },
      cta: {
        title: 'Ready to Optimize Your Business Finance?',
        description: 'Book a free consultation with our experts today and discover how we can help your business thrive.',
      },
    },
    solutions: {
      meta: {
        title: 'Solutions | INFINITE GZ',
        description: 'Financial solutions for all Malaysian businesses. From loan consulting to digital transformation.',
      },
      hero: {
        tag: 'Financial Solutions for all Malaysian businesses',
        title: 'Complete Financial Solutions',
        description: 'INFINITE GZ is your one-stop platform for loans, financial optimization, and business services. From CreditPilot\'s AI matching system to comprehensive advisory services, we help Malaysian SMEs access better financing and grow their businesses.',
      },
      products: [
        {
          tag: 'AI SYSTEM',
          title: 'CreditPilot',
          description: 'AI-powered loan matching system that analyzes your financial profile and finds the best loan products from 50+ Malaysian banks and fintech companies. 98% match accuracy, 2-minute analysis.',
          linkText: 'Learn more',
        },
        {
          tag: '8 SERVICES',
          title: 'Advisory',
          description: 'Comprehensive business services including financial optimization, e-commerce solutions, accounting, marketing strategy, and more. All services completely free for loan clients.',
          linkText: 'View all services',
        },
        {
          tag: 'INFRASTRUCTURE',
          title: 'Resources',
          description: 'Powered by comprehensive loan database, real-time rate monitoring, and advanced DSR optimization algorithms. 50+ institutions, RM 500M+ facilitated, serving 5,000+ businesses.',
          linkText: 'Explore infrastructure',
        },
      ],
      coreBusiness: {
        tag: 'Core Business',
        title: 'Loan Consulting & Financial Optimization',
        description: 'We collect loan product information from all licensed institutions in Malaysia (banks, digital banks, fintech companies), create better financial conditions for clients, and help them secure the best low-interest loans. We do not provide any illegal loans.',
        features: [
          {
            icon: '📊',
            title: 'Comprehensive Database',
            description: '50+ licensed financial institutions including banks, digital banks, and fintech companies',
          },
          {
            icon: '💰',
            title: 'Best Rates',
            description: 'Compare and secure the lowest interest rates available in the market',
          },
          {
            icon: '✅',
            title: '100% Legal',
            description: 'Only work with licensed and regulated financial institutions',
          },
          {
            icon: '🎯',
            title: 'DSR Optimization',
            description: 'Enhance debt service ratio to improve loan approval probability',
          },
          {
            icon: '🔄',
            title: 'Debt Consolidation',
            description: 'Consolidate multiple debts to reduce monthly payment pressure',
          },
          {
            icon: '⭐',
            title: 'Credit Enhancement',
            description: 'Optimize credit scores and improve CTOS/CCRIS reports',
          },
        ],
      },
      complementaryServices: {
        tag: '8 Complementary Services',
        title: 'Complementary Business Services',
        description: 'All complementary services are completely free for loan clients. All Services Completely Free For Loan Clients.',
        items: [
          {
            num: '01',
            title: 'Financial Optimization',
            description: 'DSR Enhancement, Debt Consolidation, Fixed Deposit Planning',
          },
          {
            num: '02',
            title: 'Marketing Strategy',
            description: 'Channel Design, Marketing Strategy, Market Planning',
          },
          {
            num: '03',
            title: 'Business Planning',
            description: 'Business Plans, Financing Design, Business Model Development',
          },
          {
            num: '04',
            title: 'Insurance Services',
            description: 'Product Recommendations, Insurance Planning',
          },
          {
            num: '05',
            title: 'E-Commerce Solutions',
            description: 'Store Setup, Promotion, Operations, Channel Building ⭐',
          },
          {
            num: '06',
            title: 'Membership System',
            description: 'System Design, Points Rewards, Benefits Design',
          },
          {
            num: '07',
            title: 'Accounting & Audit',
            description: 'Bookkeeping, Tax Filing, 15% Tax Optimization',
          },
          {
            num: '08',
            title: 'Credit Card Mgmt',
            description: 'Payment Reminders, Payment/Purchase On Behalf (50/50 Share)',
          },
        ],
      },
      pricing: {
        tag: 'Pricing Model',
        title: 'Zero Upfront Fees',
        models: [
          {
            tag: 'CORE SERVICE',
            title: 'Success Fee',
            price: '💼',
            description: 'Charge after loan approval. Only charge upon successful loan approval and disbursement.',
            features: ['No Upfront Cost', 'No Hidden Charges', 'Success-Based Pricing'],
          },
          {
            tag: '8 SERVICES',
            title: 'Completely FREE',
            price: '🎁',
            description: 'Completely free for loan clients. All 8 complementary services free for loan clients.',
            features: ['Financial Optimization', 'E-Commerce Solutions', 'Accounting & More'],
          },
          {
            tag: 'SPECIAL PARTNERS',
            title: '50/50 Split',
            price: '🤝',
            description: 'Profit sharing model. Profit sharing for credit card management services.',
            features: ['Revenue Sharing', 'Win-Win Partnership', 'Transparent Pricing'],
          },
        ],
      },
      targetCustomers: {
        tag: 'Target Customers',
        title: 'Who We Serve',
        customers: [
          {
            icon: '👔',
            title: 'Traditional Business Owners',
            description: '40-50 year old traditional business owners who need loans for business expansion or digital transformation',
          },
          {
            icon: '🏢',
            title: 'SME Companies',
            description: 'Small and medium enterprises needing loans, including manufacturing, retail, F&B, etc.',
          },
          {
            icon: '💳',
            title: 'High Credit Card Debt',
            description: 'Clients with high credit card debt who need debt consolidation and financial optimization',
          },
          {
            icon: '🤝',
            title: 'Business Partners',
            description: 'Suppliers, member customers who need comprehensive business support',
          },
        ],
      },
      cta: {
        title: 'Ready to Transform Your Business?',
        description: 'Join 5,000+ businesses that have secured better financing through INFINITE GZ',
      },
    },
    company: {
      meta: {
        title: 'Company | INFINITE GZ',
        description: 'Learn about INFINITE GZ SDN BHD - Malaysia\'s leading financial technology and advisory services company.',
      },
      hero: {
        tag: 'About Us',
        title: 'Building The Future Of Finance',
        description: 'We Are A Malaysian Financial Technology And Advisory Services Company Dedicated To Helping Businesses Access Better Financing.',
      },
      mission: {
        tag: 'Our Mission',
        title: 'Democratizing Access To Finance',
        description: 'Our mission is to make financial services accessible to all Malaysian businesses, regardless of size or industry.',
      },
      values: {
        tag: 'Our Values',
        title: 'What Drives Us',
        items: [
          {
            icon: '🎯',
            title: 'Customer First',
            description: 'We prioritize our clients\' success above all else.'
          },
          {
            icon: '💡',
            title: 'Innovation',
            description: 'Using AI and technology to transform financial services.'
          },
          {
            icon: '🤝',
            title: 'Integrity',
            description: 'Transparent, honest, and ethical in all our dealings.'
          },
          {
            icon: '🚀',
            title: 'Excellence',
            description: 'Committed to delivering exceptional results every time.'
          }
        ]
      },
      cta: {
        title: 'Join Us On This Journey',
        description: 'Whether you\'re looking for financing or want to join our team, we\'d love to hear from you.'
      }
    },
    news: {
      meta: {
        title: 'News | INFINITE GZ',
        description: 'Latest news, updates, and success stories from INFINITE GZ.',
      },
      hero: {
        tag: 'Latest Updates',
        title: 'News & Success Stories',
        description: 'Stay Updated With Our Latest News, Case Studies, And Success Stories.',
      },
    
      items: [
        { title: 'INFINITE GZ Secures RM 500M+ in Financing', date: '2024-12', category: 'Milestone' },
        { title: 'New AI Features in CreditPilot', date: '2024-12', category: 'Product' },
        { title: 'Success Story: Manufacturing SME Growth', date: '2024-11', category: 'Case Study' },
        { title: 'Partnership with Major Banks Announced', date: '2024-11', category: 'Partnership' },
        { title: 'INFINITE GZ Wins Fintech Award', date: '2024-10', category: 'Recognition' },
        { title: 'Expanding to 50+ Financial Institutions', date: '2024-10', category: 'Growth' },
      ],
    },

    resources: {
      meta: {
        title: 'Resources | INFINITE GZ',
        description: 'Comprehensive loan database, real-time rate monitoring, and advanced optimization tools.',
      },
      hero: {
        tag: 'Infrastructure',
        title: 'We Go Further, Faster',
        description: 'Powered By Comprehensive Database And Advanced Algorithms To Serve Malaysian Businesses.',
      },
    
      stats: [
        { number: '50+', title: 'Financial Institutions', description: 'Banks, digital banks, and fintech companies' },
        { number: 'RM 500M+', title: 'Loans Facilitated', description: 'Total financing secured for our clients' },
        { number: '2 Min', title: 'Analysis Time', description: 'Fast, accurate loan matching results' },
        { number: '98%', title: 'Match Accuracy', description: 'AI-powered precision in loan recommendations' },
      ],
      timeline: {
        tag: 'Our Journey',
        title: 'Building The Future',
        milestones: [
          { year: '2020', title: 'Company Founded', description: 'Started with a vision to democratize access to finance' },
          { year: '2021', title: 'First 1,000 Clients', description: 'Reached our first major milestone in client success' },
          { year: '2022', title: 'CreditPilot Launch', description: 'Introduced AI-powered loan matching system' },
          { year: '2023', title: 'RM 100M+ Facilitated', description: 'Crossed significant financing milestone' },
          { year: '2024', title: '50+ Institution Network', description: 'Expanded to comprehensive financial institution coverage' },
        ],
      },
    },

    careers: {
      meta: {
        title: 'Careers | INFINITE GZ',
        description: 'Join our team and help build the future of financial services in Malaysia.',
      },
      hero: {
        tag: 'Join Our Team',
        title: 'Build The Future Of Finance',
        description: 'Join Our Team Of Passionate Professionals Dedicated To Transforming Financial Services.',
      },
      benefits: {
        tag: 'Benefits',
        title: 'Why Work With Us',
        items: [
          {
            icon: '💰',
            title: 'Competitive Salary',
            description: 'Above market rate compensation with performance bonuses',
          },
          {
            icon: '🏥',
            title: 'Health Benefits',
            description: 'Comprehensive medical and dental insurance',
          },
          {
            icon: '📚',
            title: 'Learning & Development',
            description: 'Continuous training and career development opportunities',
          },
          {
            icon: '🏠',
            title: 'Flexible Work',
            description: 'Hybrid work arrangement with flexible hours',
          },
          {
            icon: '🎉',
            title: 'Team Events',
            description: 'Regular team building activities and company events',
          },
          {
            icon: '🚀',
            title: 'Career Growth',
            description: 'Clear career progression path in a growing company',
          },
        ],
      },
    
      jobs: {
        tag: 'Open Positions',
        title: 'Join Our Growing Team',
        positions: [
          { title: 'Senior Financial Advisor', department: 'Advisory', location: 'Kuala Lumpur', type: 'Full-time' },
          { title: 'AI/ML Engineer', department: 'Technology', location: 'Kuala Lumpur / Remote', type: 'Full-time' },
          { title: 'Business Development Manager', department: 'Sales', location: 'Kuala Lumpur', type: 'Full-time' },
          { title: 'Digital Marketing Specialist', department: 'Marketing', location: 'Remote', type: 'Full-time' },
          { title: 'Accountant', department: 'Finance', location: 'Kuala Lumpur', type: 'Full-time' },
          { title: 'Customer Success Manager', department: 'Operations', location: 'Kuala Lumpur', type: 'Full-time' },
        ],
      },
      cta: {
        title: "Don't See Your Role?",
        description: "We're always looking for talented individuals. Send us your CV and tell us how you can contribute.",
      },
    },
    cardManagement: {
      hero: {
        tag: 'Professional Credit Card Management',
        title: 'Save RM 1,200-5,000 Annually',
        subtitle: 'Through Professional Credit Card Management Services',
        benefits: [
          { icon: '💰', value: 'RM 500-2,000/year', label: 'Avoid Late Payment Penalties' },
          { icon: '🎁', value: 'RM 800-3,000/year', label: 'Additional Rewards & Cashback' },
          { icon: '📈', value: '50-100 Points', label: 'Credit Score Improvement' },
        ],
        cta1: 'Free WhatsApp Consultation',
        cta2: 'View Pricing',
        socialProof: 'Over 500 clients | Managing 1,000+ cards | Total savings RM 600,000+',
      },
      painPoints: {
        tag: 'Common Problems',
        title: 'Are You Facing These Credit Card Challenges?',
        subtitle: 'Malaysian credit card debt: RM 50.7B | Overdue debt: RM 551.8M (1.1%)',
        points: [
          {
            icon: '😰',
            title: 'Forgot to Pay',
            description: 'Multiple cards, different due dates, easily miss payments',
            impact: 'Late fee RM 150-300/time + Credit score damage',
          },
          {
            icon: '💸',
            title: 'Don\'t Know How to Optimize',
            description: 'Don\'t understand card rewards, wasted points, high annual fees',
            impact: 'Lost RM 800-3,000/year in benefits',
          },
          {
            icon: '🔢',
            title: 'Multiple Card Chaos',
            description: 'Manage 2-3 cards, confused statements, stress',
            impact: 'Minimum payment trap, 18% annual interest',
          },
        ],
        stats: [
          { value: 'RM 50.7B', label: 'Total Card Debt' },
          { value: '18% p.a.', label: 'Maximum Interest' },
          { value: 'RM 551.8M', label: 'Overdue Amount' },
          { value: '50,000+', label: 'Youths in Debt' },
        ],
      },
      solutions: {
        tag: 'Our Solutions',
        title: 'Professional 5-in-1 Service',
        subtitle: 'Comprehensive credit card management to maximize your benefits',
        services: [
          {
            icon: '⏰',
            title: 'Payment Reminder Service',
            description: '3-tier reminder system ensures you never miss a payment',
            benefits: [
              'WhatsApp + SMS + Email triple notification',
              'Reminder 7/3/1 days before due date',
              'Monthly statement review',
              'Overdue alert system',
            ],
          },
          {
            icon: '💳',
            title: 'Payment-On-Behalf Service',
            description: 'We pay on your behalf to ensure timely payments',
            benefits: [
              '100% on-time payment guarantee',
              'Processed within 2 business days',
              'Automatic deduction from designated account',
              'Monthly reconciliation report',
            ],
          },
          {
            icon: '🛍️',
            title: 'Purchase-On-Behalf Service',
            description: 'Use the optimal card to maximize rewards',
            benefits: [
              'Intelligent card selection system',
              'Maximize cashback and points',
              '50/50 revenue share model',
              'Transparent transaction records',
            ],
          },
          {
            icon: '📊',
            title: 'Card Optimization',
            description: 'Spending pattern analysis and strategy recommendations',
            benefits: [
              'Monthly spending analysis',
              'Optimal card usage recommendations',
              'Annual fee waiver negotiation',
              'Rewards redemption reminders',
            ],
          },
          {
            icon: '💼',
            title: 'Debt Management Consultation',
            description: 'DSR analysis and debt consolidation recommendations',
            benefits: [
              'Free DSR calculation',
              'Debt consolidation plan',
              'Credit score improvement strategy',
              'Lower interest rate solutions',
            ],
          },
        ],
      },
      caseStudies: {
        tag: 'Success Stories',
        title: 'Real Client Results',
        subtitle: 'See how our clients save thousands annually',
        before: 'Before',
        after: 'After',
        cases: [
          {
            client: 'Mr. Wang',
            type: 'Individual | 4 Cards',
            before: 'Monthly payment RM 2,500 | Confused management | Frequent late fees',
            after: 'Consolidated loan + Smart management | Automated payments | Optimized rewards',
            savings: 'Saved RM 3,200',
            period: 'Within 12 months',
          },
          {
            client: 'Ms. Li',
            type: 'Professional | High Spending',
            before: 'Monthly RM 8,000 spending | Using wrong cards | Points wasted',
            after: 'Optimized card strategy | Maximized rewards | Annual fee waived',
            savings: 'Extra RM 5,000/year',
            period: 'Ongoing',
          },
          {
            client: 'ABC Company',
            type: 'SME | 10 Corporate Cards',
            before: 'Employee reimbursement chaos | High admin costs | Overspending',
            after: 'Centralized management | Automated reconciliation | Spending control',
            savings: 'Saved RM 12,000/year',
            period: 'First year',
          },
        ],
      },
      pricing: {
        tag: 'Transparent Pricing',
        title: 'Flexible Plans for Every Need',
        subtitle: 'Choose the plan that works best for you',
        recommended: 'Most Popular',
        plans: {
          individual: {
            label: 'Individual',
            options: [
              {
                name: 'Success-Based',
                price: '50/50 Split',
                period: 'Pay only when you save',
                features: [
                  'No upfront fees',
                  '50% of all savings/benefits',
                  'Annual fee waivers',
                  'Cashback & rewards optimization',
                  'Interest savings',
                  'Late fee avoidance',
                  'Quarterly billing',
                ],
                recommended: true,
                cta: { text: 'Get Started', link: 'https://wa.me/60123456789' },
              },
              {
                name: 'Monthly Subscription',
                price: 'RM 99/month',
                period: 'Up to 3 cards',
                features: [
                  'Additional RM 30/card',
                  'Payment reminder service',
                  'Card optimization',
                  'Monthly spending analysis',
                  'Annual fee negotiation',
                  'Payment-on-behalf: +RM 50/month',
                ],
                cta: { text: 'Subscribe Now', link: 'https://portal.infinitegz.com/card-management' },
              },
              {
                name: 'FREE for Loan Clients',
                price: 'RM 0',
                period: 'First 12 months',
                features: [
                  'All standard services included',
                  'Must have active loan with us',
                  '50% discount after 12 months',
                  'Full payment reminder service',
                  'Basic card optimization',
                ],
                cta: { text: 'Check Eligibility', link: '/creditpilot' },
              },
            ],
          },
          corporate: {
            label: 'Corporate',
            options: [
              {
                name: 'Tier 1',
                price: 'RM 299/month',
                period: 'RM 0-20K monthly spending',
                features: [
                  'Up to 10 corporate cards',
                  'Centralized management',
                  'Monthly reconciliation',
                  'Basic spending analytics',
                  'Employee card tracking',
                ],
                cta: { text: 'Contact Sales', link: 'https://wa.me/60123456789' },
              },
              {
                name: 'Tier 2',
                price: 'RM 599/month',
                period: 'RM 20-50K monthly spending',
                features: [
                  'Up to 25 corporate cards',
                  'Advanced analytics',
                  'Dedicated account manager',
                  'Custom spending limits',
                  'Automated approvals',
                  'Quarterly business review',
                ],
                recommended: true,
                cta: { text: 'Contact Sales', link: 'https://wa.me/60123456789' },
              },
              {
                name: 'Tier 3',
                price: 'RM 999/month',
                period: 'RM 50-100K monthly spending',
                features: [
                  'Unlimited corporate cards',
                  'Premium support',
                  'Custom integrations',
                  'Advanced fraud detection',
                  'Multi-entity management',
                  'White-label reporting',
                ],
                cta: { text: 'Contact Sales', link: 'https://wa.me/60123456789' },
              },
            ],
          },
          loan: {
            label: 'Loan Clients',
            options: [
              {
                name: 'Complimentary',
                price: 'FREE',
                period: 'First 12 months',
                features: [
                  'All individual services included',
                  'Priority support',
                  'Free debt consultation',
                  '50% discount after 12 months',
                  'Exclusive loan client benefits',
                ],
                recommended: true,
                cta: { text: 'Learn More', link: '/advisory' },
              },
            ],
          },
        },
      },
      socialProof: {
        stats: [
          { value: '500+', label: 'Happy Clients' },
          { value: '1,000+', label: 'Cards Managed' },
          { value: 'RM 600K+', label: 'Total Savings' },
          { value: '98%', label: 'Satisfaction Rate' },
        ],
        badges: [
          'PDPA 2010 Compliant',
          'Licensed Financial Advisor',
          'Bank Negara Approved',
          'ISO 27001 Certified',
        ],
      },
      faq: {
        title: 'Frequently Asked Questions',
        subtitle: 'Everything you need to know',
        questions: [
          {
            question: 'How do you charge?',
            answer: 'We offer 3 pricing models: (1) Success-based: 50% of savings generated, no upfront fees. (2) Monthly subscription: RM 99/month for up to 3 cards. (3) FREE for loan clients for first 12 months. Choose what works best for you.',
          },
          {
            question: 'Is payment-on-behalf service safe?',
            answer: 'Absolutely. We only debit from your designated account with your authorization. All transactions are recorded and you receive monthly reconciliation reports. We maintain RM 1M professional indemnity insurance.',
          },
          {
            question: 'How do I cancel the service?',
            answer: 'You can cancel anytime with 30 days written notice. For subscription plans, you get a prorated refund. For success-based plans within commitment period, early termination fee applies (50% of remaining fees or RM 500, whichever is lower).',
          },
          {
            question: 'Do you support all banks in Malaysia?',
            answer: 'Yes, we support all major banks including Maybank, CIMB, Public Bank, Hong Leong, RHB, Am Bank, and digital banks. We can manage cards from any licensed financial institution in Malaysia.',
          },
          {
            question: 'Will you see my credit card number?',
            answer: 'No. We only need your card statements (which show last 4 digits). For payment-on-behalf service, payments are made directly from your bank account to the credit card issuer. We never store full card numbers.',
          },
          {
            question: 'What if I miss a payment even with your service?',
            answer: 'We provide 3-tier reminders and best-effort service. However, if you don\'t maintain sufficient funds in your account, we cannot be held liable. Our liability is capped at RM 10,000 or 12 months\' fees, whichever is lower.',
          },
          {
            question: 'Can I use this for my company cards?',
            answer: 'Yes! We have dedicated corporate plans starting from RM 299/month. Perfect for SMEs managing multiple employee cards. Includes centralized management, reconciliation, and spending analytics.',
          },
        ],
      },
      finalCta: {
        title: 'Ready to Start Saving?',
        subtitle: 'Join 500+ satisfied clients and start maximizing your credit card benefits today',
        cta1: 'WhatsApp Free Consultation',
        cta2: 'Book Appointment',
        relatedTitle: 'Related Services',
        relatedServices: [
          { name: 'CreditPilot (Smart Loan Matching)', link: '/creditpilot' },
          { name: 'Loan Advisory', link: '/advisory' },
          { name: 'Financial Optimization', link: '/solutions' },
        ],
      },
    },
  },
  zh: {
    nav: {
      home: '首页',
      creditpilot: '智能贷款',
      advisory: '咨询服务',
      solutions: '解决方案',
      company: '公司介绍',
      news: '新闻动态',
      resources: '资源中心',
      careers: '招聘信息',
    },
    common: {
      learnMore: '了解更多',
      getStarted: '立即开始',
      readMore: '阅读更多',
      viewAll: '查看全部',
      contactUs: '联系我们',
      applyNow: '立即申请',
      bookConsultation: '预约咨询',
      whatsappUs: 'WhatsApp联系',
      explore: '探索',
      viewDetails: '查看详情',
      useCreditPilot: '使用 CreditPilot',
    },
        home: {
      hero: {
        title: '世界的财富，\n为您所有。',
        subtitle: '您的一站式解决方案',
        description: '为您的企业提供贷款、财务优化和数字咨询服务。',
        bottomDescription: 'INFINITE GZ 提供全面的财务分析，从马来西亚所有银行和金融科技公司匹配贷款，以及8项互补服务 - 全部零前期费用。',
      },
      products: {
        tag: '我们的服务',
        title: '马来西亚企业的完整金融解决方案',
        items: [
          {
            tag: '智能分析',
            title: 'CreditPilot智能贷款',
            description: '智能贷款分析系统，通过AI驱动的匹配，从所有马来西亚银行、数字银行和金融科技公司中找到最佳贷款产品。',
            features: ['DSR 美化', '最佳利率匹配', '智能推荐', '实时分析'],
            linkText: '立即使用',
            linkUrl: 'https://portal.infinitegz.com/creditpilot',
          },
          {
            tag: '专家指导',
            title: '贷款咨询',
            description: '专业咨询服务涵盖所有贷款类型，包括房屋、汽车和商业融资，零前期费用，基于成功的定价。',
            features: ['零前期成本', '专家咨询', '成功收费', '所有贷款类型'],
            linkText: '立即咨询',
            linkUrl: 'https://portal.infinitegz.com/advisory',
          },
          {
            tag: '数字化转型',
            title: '数字化与会计服务',
            description: '传统企业的完整数字化转型，包括电子商务设置、在线商店管理、会计服务和税务优化。',
            features: ['在线商店设置', '15%税务优化', '会计服务', '业务规划'],
            linkText: '了解更多',
            linkUrl: 'https://portal.infinitegz.com/digital',
          },
        ],
      },
      content: {
        tag: '金融智能',
        title: '了解您的财务状况',
        description: 'INFINITE GZ 提供全面的财务分析和优化服务。我们帮助您应对马来西亚银行和金融的复杂世界，确保您获得最优惠的交易并保持最佳财务健康。',
        features: [
          {
            title: 'DSR 美化',
            description: '优化您的债务偿还比率，提高贷款批准机会并获得更优惠的利率',
          },
          {
            title: '债务合并',
            description: '将多笔债务合并为一笔可管理的付款，利率显著降低',
          },
          {
            title: '税务优化',
            description: '为个人和企业提供战略性的15%税收减免规划，以最大化节省',
          },
          {
            title: '信用评分',
            description: '通过战略性财务规划和专家指导提高您的信用评级',
          },
        ],
        detailsTitle: '使用 CreditPilot 做更多事情',
        details: [
          {
            title: '智能贷款匹配',
            description: '我们的AI驱动系统分析您的财务状况，并从所有合法银行、数字银行和马来西亚金融科技公司为您匹配最佳贷款产品。根据您的独特情况获得个性化推荐。',
          },
          {
            title: '全面服务',
            description: '除了贷款，我们还提供8项互补服务，包括业务规划、保险咨询、电子商务设置、会计和信用卡管理 - 所有服务对我们的贷款客户完全免费。您的成功就是我们的成功。',
          },
          {
            title: '零前期费用',
            description: '我们仅在贷款成功批准后收费。我们的基于成功的模式确保我们完全致力于为您获得最佳结果。没有隐藏费用，没有意外 - 只有透明的服务。',
          },
          {
            title: '100%合法合规',
            description: '我们只与马来西亚国家银行监管的持牌金融机构合作。没有高利贷，没有非法借贷 - 您的财务安全是我们的首要任务。',
          },
        ],
      },
      news: {
        tag: '最新动态',
        title: '新闻与见解',
        description: '了解最新的金融新闻、贷款政策、成功案例和专家见解',
        items: [
          {
            date: '2024年12月20日',
            title: '新OPR利率变化',
            description: '马来西亚国家银行宣布新的隔夜政策利率。了解这如何影响您现有和未来的贷款申请。',
            category: '政策更新',
          },
          {
            date: '2024年12月15日',
            title: 'RM 200万商业贷款成功案例',
            description: '我们如何帮助一家传统制造企业为数字化转型和扩张计划获得融资。',
            category: '案例研究',
          },
          {
            date: '2024年12月10日',
            title: '2024年年终税务规划',
            description: '在年底截止日期临近之前，最大化您的税收减免申请并优化您的财务状况。',
            category: '财务提示',
          },
          {
            date: '2024年12月5日',
            title: '数字银行vs传统银行',
            description: '全面比较马来西亚数字银行和传统银行机构的贷款产品。',
            category: '指南',
          },
          {
            date: '2024年11月28日',
            title: '信用卡债务管理',
            description: '学习有效的策略来管理多张信用卡，避免滞纳金并优化使用率。',
            category: '财务提示',
          },
          {
            date: '2024年11月20日',
            title: '传统企业走向数字化',
            description: '一家有40年历史的零售企业如何通过数字化转型和在线销售渠道将收入提高三倍。',
            category: '案例研究',
          },
        ],
      },
      footer: {
        title: '准备优化您的财务了吗？',
        description: '加入数千家信赖INFINITE GZ实现财务成功的马来西亚企业',
        copyright: '© 2024 INFINITE GZ SDN BHD. 版权所有。',
        sections: {
          try: '在这里使用CreditPilot',
          products: '产品',
          company: '公司',
          resources: '资源',
        },
        links: {
          web: '网页',
          whatsapp: 'WhatsApp',
          phone: '电话',
          creditpilot: 'CreditPilot',
          advisory: '贷款咨询',
          creditCard: '信用卡服务',
          digital: '数字化',
          accounting: '会计服务',
          about: '关于我们',
          careers: '招聘',
          contact: '联系',
          newsUpdates: '新闻动态',
          partners: '合作伙伴',
          dsrGuide: 'DSR指南',
          taxOptimization: '税务优化',
          faq: '常见问题',
          privacy: '隐私政策',
          legal: '法律',
          terms: '条款',
        },
      },
    },
    creditpilot: {
      meta: {
        title: '智能贷款 | INFINITE GZ',
        description: 'AI智能贷款匹配系统，从所有马来西亚金融机构中找到最佳贷款产品。',
      },
      hero: {
        tag: 'AI智能贷款匹配',
        title: '智能融资的新前沿',
        subtitle: '跨越50+马来西亚金融机构的智能分析',
        cta1: '开始免费分析',
        cta2: '了解更多',
      },
      capabilities: {
        tag: '核心功能',
        title: '为您服务的金融工具',
        features: [
          {
            title: '智能贷款匹配',
            description: 'AI驱动的分析，覆盖50+马来西亚银行和金融科技公司，按批准概率排名。',
          },
          {
            title: 'DSR优化',
            description: '通过战略性债务服务比率优化，将批准机会提高40%。',
          },
          {
            title: '实时比较',
            description: '实时比较所有主要金融机构的利率、费用和条款。',
          },
        ],
      },
      howItWorks: {
        tag: '工作流程',
        title: '3步轻松获取结果',
        steps: [
          {
            number: '01',
            title: '输入您的详细信息',
            description: '通过我们的平台安全地提供您的财务信息',
          },
          {
            number: '02',
            title: 'AI分析',
            description: '我们的系统实时分析50+家机构',
          },
          {
            number: '03',
            title: '获取推荐',
            description: '收到按批准概率排名的贷款选项',
          },
        ],
      },
      cta: {
        title: '准备好找到最佳贷款了吗？',
        description: '立即开始免费分析，发现最适合您业务的融资选项。',
        buttonText: '开始免费分析',
      },
    },

    advisory: {
      meta: {
        title: '咨询服务 | INFINITE GZ',
        description: '全面的商业咨询服务。8项互补服务对贷款客户完全免费。',
      },
      hero: {
        tag: '完整金融解决方案',
        title: '8大互补业务服务',
        description: '对贷款客户完全免费的所有服务。从财务优化到电商解决方案。',
      },
      services: {
        tag: '8大核心服务',
        title: '全面业务支持',
        items: [
          {
            num: '01',
            title: '企业财务优化',
            description: 'DSR美化、债务整合、定存规划、信用评分优化、现金流管理',
          },
          {
            num: '02',
            title: '广告策划',
            description: '推广渠道设计、营销策略、市场方案、供应商广告解决方案',
          },
          {
            num: '03',
            title: '商业计划',
            description: '商业计划书、融资方案设计、商业模式开发、市场分析',
          },
          {
            num: '04',
            title: '保险服务',
            description: '产品推荐、保险规划、覆盖面分析',
          },
          {
            num: '05',
            title: '线上商店建设',
            description: '快速建站、推广、运营、渠道建设、电商支持 ⭐',
          },
          {
            num: '06',
            title: '会员制度建设',
            description: '系统设计、积分与奖励、福利规划',
          },
          {
            num: '07',
            title: '会计与审计',
            description: '记账服务、税务申报、财务报表、审计支持、15%扣税优化',
          },
          {
            num: '08',
            title: '信用卡管理',
            description: '付款提醒、代付、代买服务（50/50分成）',
          },
        ],
      },
      benefits: {
        tag: '为什么选择我们',
        title: '专业财务指导',
        items: [
          {
            icon: '🎯',
            title: '个性化解决方案',
            description: '专为您的业务需求和目标量身定制的财务策略。',
          },
          {
            icon: '💼',
            title: '行业专业知识',
            description: '深入了解马来西亚金融格局和监管要求。',
          },
          {
            icon: '🤝',
            title: '持续支持',
            description: '在您与我们的财务旅程中提供持续的指导和支持。',
          },
        ],
      },
      cta: {
        title: '准备优化您的业务财务了吗？',
        description: '立即预约与我们专家的免费咨询，了解我们如何帮助您的业务蓬勃发展。',
      },
    },
    solutions: {
      meta: {
        title: '解决方案 | INFINITE GZ',
        description: '为所有马来西亚企业提供金融解决方案。从贷款咨询到数字化转型。',
      },
      hero: {
        tag: '为所有马来西亚企业提供金融解决方案',
        title: '完整金融解决方案',
        description: 'INFINITE GZ是您的一站式平台，提供贷款、财务优化和商业服务。从CreditPilot的AI匹配系统到全面的咨询服务，我们帮助马来西亚中小企业获得更好的融资并发展业务。',
      },
      products: [
        {
          tag: 'AI系统',
          title: 'CreditPilot',
          description: 'AI智能贷款匹配系统，分析您的财务状况，从50+马来西亚银行和金融科技公司中找到最佳贷款产品。98%匹配准确率，2分钟分析。',
          linkText: '了解更多',
        },
        {
          tag: '8项服务',
          title: '咨询服务',
          description: '全面的商业服务，包括财务优化、电商解决方案、会计、营销策略等。对贷款客户完全免费。',
          linkText: '查看所有服务',
        },
        {
          tag: '基础设施',
          title: '资源中心',
          description: '由全面的贷款数据库、实时利率监控和先进的DSR优化算法提供支持。50+机构，RM 500M+便利，服务5,000+企业。',
          linkText: '探索基础设施',
        },
      ],
      coreBusiness: {
        tag: '核心业务',
        title: '贷款咨询与财务优化',
        description: '我们收集马来西亚所有合法机构（银行、数字银行、金融科技公司）的贷款产品信息，为客户创造更好的财务状况，帮助他们获得最佳低息贷款。我们不提供任何非法贷款。',
        features: [
          {
            icon: '📊',
            title: '全面数据库',
            description: '50+持牌金融机构，包括银行、数字银行和金融科技公司',
          },
          {
            icon: '💰',
            title: '最优利率',
            description: '比较并获得市场上最低的利率',
          },
          {
            icon: '✅',
            title: '100%合法',
            description: '只与持牌和受监管的金融机构合作',
          },
          {
            icon: '🎯',
            title: 'DSR优化',
            description: '美化债务服务比率，提高贷款批准概率',
          },
          {
            icon: '🔄',
            title: '债务整合',
            description: '整合多个债务，减少月供压力',
          },
          {
            icon: '⭐',
            title: '信用提升',
            description: '优化信用评分，改善CTOS/CCRIS报告',
          },
        ],
      },
      complementaryServices: {
        tag: '8大衍生业务',
        title: '互补业务服务',
        description: '所有互补服务对贷款客户完全免费。对贷款客户完全免费的所有服务。',
        items: [
          {
            num: '01',
            title: '财务优化',
            description: 'DSR美化、债务整合、定存规划',
          },
          {
            num: '02',
            title: '营销策略',
            description: '渠道设计、营销策略、市场规划',
          },
          {
            num: '03',
            title: '商业计划',
            description: '商业计划书、融资设计、商业模式开发',
          },
          {
            num: '04',
            title: '保险服务',
            description: '产品推荐、保险规划',
          },
          {
            num: '05',
            title: '电商解决方案',
            description: '商店建设、推广、运营、渠道建设 ⭐',
          },
          {
            num: '06',
            title: '会员系统',
            description: '系统设计、积分奖励、福利设计',
          },
          {
            num: '07',
            title: '会计与审计',
            description: '记账服务、税务申报、15%扣税优化',
          },
          {
            num: '08',
            title: '信用卡管理',
            description: '付款提醒、代付代买（50/50分成）',
          },
        ],
      },
      pricing: {
        tag: '收费模式',
        title: '零前期费用',
        models: [
          {
            tag: '核心服务',
            title: '成功费',
            price: '💼',
            description: '贷款批准后收费。只在贷款成功批准和发放后收费。',
            features: ['无前期成本', '无隐藏费用', '基于成功的定价'],
          },
          {
            tag: '8项服务',
            title: '完全免费',
            price: '🎁',
            description: '对贷款客户完全免费。对贷款客户的所有8项互补服务免费。',
            features: ['财务优化', '电商解决方案', '会计及更多'],
          },
          {
            tag: '特殊合作伙伴',
            title: '50/50分成',
            price: '🤝',
            description: '利润分享模式。信用卡管理服务的利润分享。',
            features: ['收入分享', '双赢合作', '透明定价'],
          },
        ],
      },
      targetCustomers: {
        tag: '目标客户',
        title: '我们服务的对象',
        customers: [
          {
            icon: '👔',
            title: '传统企业主',
            description: '40-50岁的传统企业主，需要贷款进行业务扩展或数字化转型',
          },
          {
            icon: '🏢',
            title: '中小企业',
            description: '需要贷款的中小企业，包括制造业、零售、餐饮等',
          },
          {
            icon: '💳',
            title: '高信用卡债务',
            description: '高信用卡债务客户，需要债务整合和财务优化',
          },
          {
            icon: '🤝',
            title: '业务合作伙伴',
            description: '供应商、会员客户，需要全面的业务支持',
          },
        ],
      },
      cta: {
        title: '准备好转型您的业务了吗？',
        description: '加入5,000+通过INFINITE GZ获得更好融资的企业',
      },
    },
    company: {
      meta: {
        title: '公司介绍 | INFINITE GZ',
        description: '了解INFINITE GZ SDN BHD - 马来西亚领先的金融科技和咨询服务公司。',
      },
      hero: {
        tag: '关于我们',
        title: '构建金融的未来',
        description: '我们是一家马来西亚金融科技和咨询服务公司，致力于帮助企业获得更好的融资。',
      },
      mission: {
        tag: '我们的使命',
        title: '普及金融服务',
        description: '我们的使命是让所有马来西亚企业都能获得金融服务，无论规模或行业如何。',
      },
      values: {
        tag: '我们的价值观',
        title: '驱动我们前进的力量',
        items: [
          {
            icon: '🎯',
            title: '客户至上',
            description: '我们始终将客户的成功放在首位。'
          },
          {
            icon: '💡',
            title: '创新',
            description: '利用AI和技术改变金融服务。'
          },
          {
            icon: '🤝',
            title: '诚信',
            description: '在所有交易中保持透明、诚实和道德。'
          },
          {
            icon: '🚀',
            title: '卓越',
            description: '致力于每次都提供卓越的结果。'
          }
        ]
      },
      cta: {
        title: '与我们一起前进',
        description: '无论您是在寻找融资还是想加入我们的团队，我们都很乐意听到您的声音。'
      }
    },
    news: {
      meta: {
        title: '新闻动态 | INFINITE GZ',
        description: '来自INFINITE GZ的最新新闻、更新和成功案例。',
      },
      hero: {
        tag: '最新更新',
        title: '新闻与成功案例',
        description: '及时了解我们的最新新闻、案例研究和成功案例。',
      },
    
      items: [
        { title: 'INFINITE GZ 获得超过 RM 5亿融资', date: '2024-12', category: '里程碑' },
        { title: 'CreditPilot 新增 AI 功能', date: '2024-12', category: '产品' },
        { title: '成功案例：制造业中小企业增长', date: '2024-11', category: '案例研究' },
        { title: '宣布与主要银行建立合作伙伴关系', date: '2024-11', category: '合作' },
        { title: 'INFINITE GZ 荣获金融科技奖', date: '2024-10', category: '荣誉' },
        { title: '扩展至 50+ 金融机构', date: '2024-10', category: '增长' },
      ],
    },

    resources: {
      meta: {
        title: '资源中心 | INFINITE GZ',
        description: '全面的贷款数据库、实时利率监控和先进的优化工具。',
      },
      hero: {
        tag: '基础设施',
        title: '我们走得更远、更快',
        description: '由全面的数据库和先进算法提供支持，服务马来西亚企业。',
      },
    
      stats: [
        { number: '50+', title: '金融机构', description: '银行、数字银行和金融科技公司' },
        { number: 'RM 5亿+', title: '促成贷款', description: '为客户获得的总融资额' },
        { number: '2分钟', title: '分析时间', description: '快速、准确的贷款匹配结果' },
        { number: '98%', title: '匹配准确度', description: 'AI驱动的贷款推荐精准度' },
      ],
      timeline: {
        tag: '我们的旅程',
        title: '建设未来',
        milestones: [
          { year: '2020', title: '公司成立', description: '带着普及金融服务的愿景起步' },
          { year: '2021', title: '首批1000名客户', description: '达成客户成功的第一个重要里程碑' },
          { year: '2022', title: 'CreditPilot 推出', description: '推出AI驱动的贷款匹配系统' },
          { year: '2023', title: '促成RM 1亿+', description: '跨越重要的融资里程碑' },
          { year: '2024', title: '50+机构网络', description: '扩展至全面的金融机构覆盖' },
        ],
      },
    },


    careers: {
      meta: {
        title: '招聘信息 | INFINITE GZ',
        description: '加入我们的团队，帮助构建马来西亚金融服务的未来。',
      },
      hero: {
        tag: '加入我们的团队',
        title: '构建金融的未来',
        description: '加入我们充满激情的专业团队，致力于转型金融服务。',
      },
      benefits: {
        tag: '福利',
        title: '为什么与我们合作',
        items: [
          {
            icon: '💰',
            title: '有竞争力的薪资',
            description: '高于市场水平的薪酬和绩效奖金',
          },
          {
            icon: '🏥',
            title: '健康福利',
            description: '全面的医疗和牙科保险',
          },
          {
            icon: '📚',
            title: '学习与发展',
            description: '持续培训和职业发展机会',
          },
          {
            icon: '🏠',
            title: '灵活工作',
            description: '混合工作安排，工作时间灵活',
          },
          {
            icon: '🎉',
            title: '团队活动',
            description: '定期的团队建设活动和公司活动',
          },
          {
            icon: '🚀',
            title: '职业成长',
            description: '在成长型公司中明确的职业发展路径',
          },
        ],
      },
    
      jobs: {
        tag: '开放职位',
        title: '加入我们成长的团队',
        positions: [
          { title: '高级财务顾问', department: '咨询', location: '吉隆坡', type: '全职' },
          { title: 'AI/ML 工程师', department: '技术', location: '吉隆坡/远程', type: '全职' },
          { title: '业务拓展经理', department: '销售', location: '吉隆坡', type: '全职' },
          { title: '数字营销专员', department: '营销', location: '远程', type: '全职' },
          { title: '会计师', department: '财务', location: '吉隆坡', type: '全职' },
          { title: '客户成功经理', department: '运营', location: '吉隆坡', type: '全职' },
        ],
      },
      cta: {
        title: '找不到适合的职位？',
        description: '我们一直在寻找有才华的人才。发送您的简历，告诉我们您能如何贡献。',
      },
    },
    cardManagement: {
      hero: {
        tag: '专业信用卡管理',
        title: '每年节省 RM 1,200-5,000',
        subtitle: '通过专业信用卡管理服务',
        benefits: [
          { icon: '💰', value: 'RM 500-2,000/年', label: '避免逾期罚款' },
          { icon: '🎁', value: 'RM 800-3,000/年', label: '额外奖励与现金返还' },
          { icon: '📈', value: '50-100分', label: '信用评分提升' },
        ],
        cta1: '免费WhatsApp咨询',
        cta2: '查看定价',
        socialProof: '超过500位客户 | 管理1,000+张卡 | 累计节省RM 600,000+',
      },
      painPoints: {
        tag: '常见问题',
        title: '您是否也遇到这些信用卡困扰？',
        subtitle: '马来西亚信用卡债务：RM 50.7B | 逾期债务：RM 551.8M (1.1%)',
        points: [
          {
            icon: '😰',
            title: '忘记还款',
            description: '多张卡片，不同到期日，容易错过还款',
            impact: '逾期费RM 150-300/次 + 信用评分损害',
          },
          {
            icon: '💸',
            title: '不懂优化',
            description: '不了解卡片奖励，积分浪费，年费高昂',
            impact: '每年损失RM 800-3,000收益',
          },
          {
            icon: '🔢',
            title: '多卡混乱',
            description: '管理2-3张卡，账单混乱，压力大',
            impact: '最低还款陷阱，18%年利率',
          },
        ],
        stats: [
          { value: 'RM 50.7B', label: '信用卡总债务' },
          { value: '18% p.a.', label: '最高利率' },
          { value: 'RM 551.8M', label: '逾期金额' },
          { value: '50,000+', label: '负债年轻人' },
        ],
      },
      solutions: {
        tag: '我们的解决方案',
        title: '专业5合1服务',
        subtitle: '全方位信用卡管理，最大化您的收益',
        services: [
          {
            icon: '⏰',
            title: '支付提醒服务',
            description: '三重提醒系统，确保您永不错过还款',
            benefits: [
              'WhatsApp + 短信 + 邮件三重通知',
              '到期前7/3/1天提醒',
              '月度账单审查',
              '逾期警报系统',
            ],
          },
          {
            icon: '💳',
            title: '代付服务',
            description: '我们代您支付，确保按时还款',
            benefits: [
              '100%按时还款保证',
              '2个工作日内处理',
              '从指定账户自动扣款',
              '月度对账报告',
            ],
          },
          {
            icon: '🛍️',
            title: '代购服务',
            description: '使用最优信用卡，最大化奖励',
            benefits: [
              '智能选卡系统',
              '最大化现金返还和积分',
              '50/50收益分成模式',
              '透明交易记录',
            ],
          },
          {
            icon: '📊',
            title: '信用卡优化',
            description: '消费模式分析与策略建议',
            benefits: [
              '月度消费分析',
              '最优信用卡使用建议',
              '年费豁免谈判',
              '奖励兑换提醒',
            ],
          },
          {
            icon: '💼',
            title: '债务管理咨询',
            description: 'DSR分析与债务整合建议',
            benefits: [
              '免费DSR计算',
              '债务整合方案',
              '信用评分改善策略',
              '降低利率解决方案',
            ],
          },
        ],
      },
      caseStudies: {
        tag: '成功案例',
        title: '真实客户成果',
        subtitle: '看看我们的客户如何每年节省数千令吉',
        before: '使用前',
        after: '使用后',
        cases: [
          {
            client: '王先生',
            type: '个人 | 4张卡',
            before: '月还RM 2,500 | 管理混乱 | 经常逾期',
            after: '整合贷款 + 智能管理 | 自动还款 | 优化奖励',
            savings: '节省RM 3,200',
            period: '12个月内',
          },
          {
            client: '李女士',
            type: '专业人士 | 高消费',
            before: '月消费RM 8,000 | 用错卡 | 积分浪费',
            after: '优化用卡策略 | 最大化奖励 | 年费豁免',
            savings: '额外RM 5,000/年',
            period: '持续收益',
          },
          {
            client: 'ABC公司',
            type: '中小企业 | 10张企业卡',
            before: '员工报销混乱 | 管理成本高 | 超支',
            after: '集中管理 | 自动对账 | 支出控制',
            savings: '节省RM 12,000/年',
            period: '第一年',
          },
        ],
      },
      pricing: {
        tag: '透明定价',
        title: '灵活方案满足各种需求',
        subtitle: '选择最适合您的方案',
        recommended: '最受欢迎',
        plans: {
          individual: {
            label: '个人客户',
            options: [
              {
                name: '成功费用',
                price: '50/50分成',
                period: '只在您节省时付费',
                features: [
                  '无预付费用',
                  '所有节省/收益的50%',
                  '年费豁免',
                  '现金返还与奖励优化',
                  '利息节省',
                  '避免逾期费',
                  '每季度结算',
                ],
                recommended: true,
                cta: { text: '立即开始', link: 'https://wa.me/60123456789' },
              },
              {
                name: '月度订阅',
                price: 'RM 99/月',
                period: '最多3张卡',
                features: [
                  '额外RM 30/卡',
                  '支付提醒服务',
                  '信用卡优化',
                  '月度消费分析',
                  '年费谈判',
                  '代付服务：+RM 50/月',
                ],
                cta: { text: '立即订阅', link: 'https://portal.infinitegz.com/card-management' },
              },
              {
                name: '贷款客户免费',
                price: 'RM 0',
                period: '前12个月',
                features: [
                  '包含所有标准服务',
                  '须有我们的有效贷款',
                  '12个月后50%折扣',
                  '完整支付提醒服务',
                  '基础信用卡优化',
                ],
                cta: { text: '检查资格', link: '/creditpilot' },
              },
            ],
          },
          corporate: {
            label: '企业客户',
            options: [
              {
                name: '级别1',
                price: 'RM 299/月',
                period: 'RM 0-20K月消费',
                features: [
                  '最多10张企业卡',
                  '集中管理',
                  '月度对账',
                  '基础消费分析',
                  '员工卡追踪',
                ],
                cta: { text: '联系销售', link: 'https://wa.me/60123456789' },
              },
              {
                name: '级别2',
                price: 'RM 599/月',
                period: 'RM 20-50K月消费',
                features: [
                  '最多25张企业卡',
                  '高级分析',
                  '专属客户经理',
                  '自定义支出限额',
                  '自动审批',
                  '季度业务审查',
                ],
                recommended: true,
                cta: { text: '联系销售', link: 'https://wa.me/60123456789' },
              },
              {
                name: '级别3',
                price: 'RM 999/月',
                period: 'RM 50-100K月消费',
                features: [
                  '无限企业卡',
                  '高级支持',
                  '自定义集成',
                  '高级欺诈检测',
                  '多实体管理',
                  '白标报告',
                ],
                cta: { text: '联系销售', link: 'https://wa.me/60123456789' },
              },
            ],
          },
          loan: {
            label: '贷款客户',
            options: [
              {
                name: '免费服务',
                price: '免费',
                period: '前12个月',
                features: [
                  '包含所有个人服务',
                  '优先支持',
                  '免费债务咨询',
                  '12个月后50%折扣',
                  '专属贷款客户福利',
                ],
                recommended: true,
                cta: { text: '了解更多', link: '/advisory' },
              },
            ],
          },
        },
      },
      socialProof: {
        stats: [
          { value: '500+', label: '满意客户' },
          { value: '1,000+', label: '管理卡片' },
          { value: 'RM 600K+', label: '累计节省' },
          { value: '98%', label: '满意度' },
        ],
        badges: [
          'PDPA 2010合规',
          '持牌财务顾问',
          'Bank Negara认可',
          'ISO 27001认证',
        ],
      },
      faq: {
        title: '常见问题',
        subtitle: '您需要了解的一切',
        questions: [
          {
            question: '如何收费？',
            answer: '我们提供3种定价模式：(1) 成功费用：节省金额的50%，无预付费。(2) 月度订阅：最多3张卡每月RM 99。(3) 贷款客户前12个月免费。选择最适合您的方式。',
          },
          {
            question: '代付服务安全吗？',
            answer: '绝对安全。我们仅在您授权下从指定账户扣款。所有交易都有记录，您会收到月度对账报告。我们维持RM 100万专业责任保险。',
          },
          {
            question: '如何取消服务？',
            answer: '您可以提前30天书面通知随时取消。订阅计划可获得按比例退款。成功费用计划在承诺期内取消，需支付提前终止费（剩余费用的50%或RM 500，取较低者）。',
          },
          {
            question: '支持马来西亚所有银行吗？',
            answer: '是的，我们支持所有主要银行，包括Maybank、CIMB、Public Bank、Hong Leong、RHB、AmBank和数字银行。我们可以管理马来西亚任何持牌金融机构的信用卡。',
          },
          {
            question: '您会看到我的信用卡号吗？',
            answer: '不会。我们只需要您的信用卡账单（显示最后4位数字）。对于代付服务，款项直接从您的银行账户支付给信用卡发卡机构。我们从不存储完整的卡号。',
          },
          {
            question: '如果使用您的服务还是错过付款怎么办？',
            answer: '我们提供三重提醒和尽最大努力的服务。但是，如果您账户资金不足，我们不承担责任。我们的责任上限为RM 10,000或12个月费用，取较低者。',
          },
          {
            question: '可以用于公司卡吗？',
            answer: '可以！我们有专门的企业计划，起价RM 299/月。非常适合管理多张员工卡的中小企业。包括集中管理、对账和支出分析。',
          },
        ],
      },
      finalCta: {
        title: '准备开始节省了吗？',
        subtitle: '加入500+满意客户，今天开始最大化您的信用卡收益',
        cta1: 'WhatsApp免费咨询',
        cta2: '预约咨询',
        relatedTitle: '相关服务',
        relatedServices: [
          { name: 'CreditPilot（智能贷款匹配）', link: '/creditpilot' },
          { name: '贷款咨询', link: '/advisory' },
          { name: '财务优化', link: '/solutions' },
        ],
      },
    },
  },
  ms: {
    nav: {
      home: 'Laman Utama',
      creditpilot: 'CreditPilot',
      advisory: 'Perkhidmatan',
      solutions: 'Penyelesaian',
      company: 'Syarikat',
      news: 'Berita',
      resources: 'Sumber',
      careers: 'Kerjaya',
    },
    common: {
      learnMore: 'Ketahui Lebih Lanjut',
      getStarted: 'Mulakan',
      readMore: 'Baca Lagi',
      viewAll: 'Lihat Semua',
      contactUs: 'Hubungi Kami',
      applyNow: 'Mohon Sekarang',
      bookConsultation: 'Tempah Konsultasi',
      whatsappUs: 'WhatsApp Kami',
      explore: 'Terokai',
      viewDetails: 'Lihat Butiran',
      useCreditPilot: 'Guna CreditPilot',
    },
        home: {
      hero: {
        title: 'Wang Dunia,\nMilik Anda.',
        subtitle: 'Penyelesaian Sehenti Anda',
        description: 'Untuk Pinjaman, Pengoptimuman Kewangan, Dan Perkhidmatan Nasihat Digital Untuk Perniagaan Anda.',
        bottomDescription: 'INFINITE GZ Menyediakan Analisis Kewangan Menyeluruh, Padanan Pinjaman Dari Semua Bank Dan Syarikat Fintech Malaysia, Serta 8 Perkhidmatan Pelengkap - Semua Tanpa Yuran Pendahuluan.',
      },
      products: {
        tag: 'Perkhidmatan Kami',
        title: 'Penyelesaian Kewangan Lengkap Untuk Perniagaan Malaysia',
        items: [
          {
            tag: 'Analisis Pintar',
            title: 'CreditPilot',
            description: 'Sistem Analisis Pinjaman Pintar Yang Mencari Produk Pinjaman Terbaik Dari Semua Bank Malaysia, Bank Digital, Dan Syarikat Fintech Dengan Padanan Berkuasa AI.',
            features: ['Penambahbaikan DSR', 'Padanan Kadar Terbaik', 'Cadangan Pintar', 'Analisis Masa Nyata'],
            linkText: 'Guna Sekarang',
            linkUrl: 'https://portal.infinitegz.com/creditpilot',
          },
          {
            tag: 'Bimbingan Pakar',
            title: 'Nasihat Pinjaman',
            description: 'Perundingan Profesional Untuk Semua Jenis Pinjaman Termasuk Perumahan, Automotif, Dan Pembiayaan Perniagaan Dengan Yuran Pendahuluan Sifar Dan Harga Berasaskan Kejayaan.',
            features: ['Kos Pendahuluan Sifar', 'Perundingan Pakar', 'Yuran Berasaskan Kejayaan', 'Semua Jenis Pinjaman'],
            linkText: 'Berunding Sekarang',
            linkUrl: 'https://portal.infinitegz.com/advisory',
          },
          {
            tag: 'Transformasi Digital',
            title: 'Pendigitalan & Perakaunan',
            description: 'Transformasi Digital Lengkap Untuk Perniagaan Tradisional Termasuk Persediaan E-Dagang, Pengurusan Kedai Dalam Talian, Perkhidmatan Perakaunan, Dan Pengoptimuman Cukai.',
            features: ['Persediaan Kedai Dalam Talian', 'Pengoptimuman Cukai 15%', 'Perkhidmatan Perakaunan', 'Perancangan Perniagaan'],
            linkText: 'Ketahui Lebih Lanjut',
            linkUrl: 'https://portal.infinitegz.com/digital',
          },
        ],
      },
      content: {
        tag: 'Kecerdasan Kewangan',
        title: 'Fahami Kewangan Anda',
        description: 'INFINITE GZ Menyediakan Analisis Dan Perkhidmatan Pengoptimuman Kewangan Menyeluruh. Kami Membantu Anda Mengemudi Dunia Perbankan Dan Kewangan Yang Kompleks Di Malaysia, Memastikan Anda Mendapat Tawaran Terbaik Dan Mengekalkan Kesihatan Kewangan Optimum.',
        features: [
          {
            title: 'Penambahbaikan DSR',
            description: 'Optimumkan Nisbah Perkhidmatan Hutang Anda Untuk Meningkatkan Peluang Kelulusan Pinjaman Dan Akses Kadar Yang Lebih Baik',
          },
          {
            title: 'Penyatuan Hutang',
            description: 'Gabungkan Pelbagai Hutang Menjadi Satu Bayaran Terurus Dengan Kadar Faedah Yang Jauh Lebih Rendah',
          },
          {
            title: 'Pengoptimuman Cukai',
            description: 'Perancangan Potongan Cukai 15% Strategik Untuk Individu Dan Perniagaan Untuk Memaksimumkan Penjimatan',
          },
          {
            title: 'Skor Kredit',
            description: 'Tingkatkan Penarafan Kredit Anda Melalui Perancangan Kewangan Strategik Dan Bimbingan Pakar',
          },
        ],
        detailsTitle: 'Lakukan Lebih Dengan CreditPilot',
        details: [
          {
            title: 'Padanan Pinjaman Pintar',
            description: 'Sistem Berkuasa AI Kami Menganalisis Profil Kewangan Anda Dan Memadankan Anda Dengan Produk Pinjaman Terbaik Dari Semua Bank Sah, Bank Digital, Dan Syarikat Fintech Di Malaysia. Dapatkan Cadangan Diperibadikan Berdasarkan Situasi Unik Anda.',
          },
          {
            title: 'Perkhidmatan Menyeluruh',
            description: 'Selain Pinjaman, Kami Menawarkan 8 Perkhidmatan Pelengkap Termasuk Perancangan Perniagaan, Perundingan Insurans, Persediaan E-Dagang, Perakaunan, Dan Pengurusan Kad Kredit - Semua Percuma Sepenuhnya Untuk Pelanggan Pinjaman Kami. Kejayaan Anda Adalah Kejayaan Kami.',
          },
          {
            title: 'Yuran Pendahuluan Sifar',
            description: 'Kami Hanya Mengenakan Bayaran Selepas Kelulusan Pinjaman Berjaya. Model Berasaskan Kejayaan Kami Memastikan Kami Komited Sepenuhnya Untuk Mendapatkan Hasil Terbaik Untuk Anda. Tiada Yuran Tersembunyi, Tiada Kejutan - Hanya Perkhidmatan Telus.',
          },
          {
            title: '100% Sah & Patuh',
            description: 'Kami Hanya Bekerja Dengan Institusi Kewangan Berlesen Yang Dikawal Oleh Bank Negara Malaysia. Tiada Along, Tiada Pinjaman Haram - Keselamatan Dan Keamanan Kewangan Anda Adalah Keutamaan Utama Kami.',
          },
        ],
      },
      news: {
        tag: 'Kemas Kini Terkini',
        title: 'Berita & Pandangan',
        description: 'Kekal Bermaklumat Dengan Berita Kewangan Terkini, Dasar Pinjaman, Kisah Kejayaan, Dan Pandangan Pakar',
        items: [
          {
            date: '20 Dis 2024',
            title: 'Perubahan Kadar OPR Baru',
            description: 'Bank Negara Malaysia Mengumumkan Kadar Dasar Semalaman Baru. Ketahui Bagaimana Ini Memberi Kesan Kepada Permohonan Pinjaman Sedia Ada Dan Masa Hadapan Anda.',
            category: 'Kemas Kini Dasar',
          },
          {
            date: '15 Dis 2024',
            title: 'Kejayaan Pinjaman Perniagaan RM 2 Juta',
            description: 'Bagaimana Kami Membantu Perniagaan Pembuatan Tradisional Mendapatkan Pembiayaan Untuk Transformasi Digital Dan Rancangan Pengembangan.',
            category: 'Kajian Kes',
          },
          {
            date: '10 Dis 2024',
            title: 'Perancangan Cukai Akhir Tahun 2024',
            description: 'Maksimumkan Tuntutan Pelepasan Cukai Anda Dan Optimumkan Kedudukan Kewangan Anda Sebelum Tarikh Akhir Akhir Tahun Menghampiri.',
            category: 'Petua Kewangan',
          },
          {
            date: '5 Dis 2024',
            title: 'Bank Digital Vs Bank Tradisional',
            description: 'Perbandingan Menyeluruh Produk Pinjaman Dari Bank Digital Dan Institusi Perbankan Tradisional Di Malaysia.',
            category: 'Panduan',
          },
          {
            date: '28 Nov 2024',
            title: 'Pengurusan Hutang Kad Kredit',
            description: 'Pelajari Strategi Berkesan Untuk Menguruskan Pelbagai Kad Kredit, Elakkan Yuran Lewat, Dan Optimumkan Nisbah Penggunaan.',
            category: 'Petua Kewangan',
          },
          {
            date: '20 Nov 2024',
            title: 'Perniagaan Tradisional Menjadi Digital',
            description: 'Bagaimana Perniagaan Runcit Berusia 40 Tahun Meningkatkan Hasil Tiga Kali Ganda Melalui Transformasi Digital Dan Saluran Jualan Dalam Talian.',
            category: 'Kajian Kes',
          },
        ],
      },
      footer: {
        title: 'Bersedia Untuk Mengoptimumkan Kewangan Anda?',
        description: 'Sertai Ribuan Perniagaan Malaysia Yang Mempercayai INFINITE GZ Untuk Kejayaan Kewangan Mereka',
        copyright: '© 2024 INFINITE GZ SDN BHD. Hak Cipta Terpelihara.',
        sections: {
          try: 'Cuba CreditPilot Di',
          products: 'Produk',
          company: 'Syarikat',
          resources: 'Sumber',
        },
        links: {
          web: 'Web',
          whatsapp: 'WhatsApp',
          phone: 'Telefon',
          creditpilot: 'CreditPilot',
          advisory: 'Nasihat Pinjaman',
          creditCard: 'Perkhidmatan Kad Kredit',
          digital: 'Pendigitalan',
          accounting: 'Perkhidmatan Perakaunan',
          about: 'Tentang Kami',
          careers: 'Kerjaya',
          contact: 'Hubungi',
          newsUpdates: 'Berita & Kemas Kini',
          partners: 'Rakan Kongsi',
          dsrGuide: 'Panduan DSR',
          taxOptimization: 'Pengoptimuman Cukai',
          faq: 'Soalan Lazim',
          privacy: 'Dasar Privasi',
          legal: 'Undang-undang',
          terms: 'Terma',
        },
      },
    },
    creditpilot: {
      meta: {
        title: 'CreditPilot | INFINITE GZ',
        description: 'Sistem padanan pinjaman berkuasa AI yang mencari produk pinjaman terbaik dari semua institusi kewangan Malaysia.',
      },
      hero: {
        tag: 'Padanan Pinjaman Berkuasa AI',
        title: 'Sempadan Baharu Pembiayaan Pintar',
        subtitle: 'Analisis Pintar Merentasi 50+ Institusi Kewangan Malaysia',
        cta1: 'Mulakan Analisis Percuma',
        cta2: 'Ketahui Lebih Lanjut',
      },
      capabilities: {
        tag: 'Keupayaan',
        title: 'Alat Kewangan Yang Berfungsi Untuk Anda',
        features: [
          {
            title: 'Padanan Pinjaman Pintar',
            description: 'Analisis Berkuasa AI Merentasi 50+ Bank Dan Syarikat Fintech Malaysia, Disusun Mengikut Kebarangkalian Kelulusan.',
          },
          {
            title: 'Pengoptimuman DSR',
            description: 'Tingkatkan Peluang Kelulusan Anda Sehingga 40% Dengan Peningkatan Nisbah Perkhidmatan Hutang Strategik.',
          },
          {
            title: 'Perbandingan Masa Nyata',
            description: 'Bandingkan Kadar Faedah, Yuran, Dan Terma Dari Semua Institusi Kewangan Utama Secara Masa Nyata.',
          },
        ],
      },
      howItWorks: {
        tag: 'Cara Ia Berfungsi',
        title: 'Dapatkan Keputusan Anda Dalam 3 Langkah Mudah',
        steps: [
          {
            number: '01',
            title: 'Masukkan Butiran Anda',
            description: 'Berikan maklumat kewangan anda dengan selamat melalui platform kami',
          },
          {
            number: '02',
            title: 'Analisis AI',
            description: 'Sistem kami menganalisis 50+ institusi secara masa nyata',
          },
          {
            number: '03',
            title: 'Dapatkan Cadangan',
            description: 'Terima pilihan pinjaman yang disusun dengan kebarangkalian kelulusan',
          },
        ],
      },
      cta: {
        title: 'Bersedia Untuk Mencari Pinjaman Terbaik Anda?',
        description: 'Mulakan analisis percuma anda sekarang dan temui pilihan pembiayaan terbaik untuk perniagaan anda.',
        buttonText: 'Mulakan Analisis Percuma',
      },
    },

    advisory: {
      meta: {
        title: 'Perkhidmatan Nasihat | INFINITE GZ',
        description: 'Perkhidmatan nasihat perniagaan yang komprehensif. 8 perkhidmatan pelengkap percuma sepenuhnya untuk pelanggan pinjaman.',
      },
      hero: {
        tag: 'Penyelesaian Kewangan Lengkap',
        title: '8 Perkhidmatan Perniagaan Pelengkap',
        description: 'Semua Perkhidmatan Percuma Sepenuhnya Untuk Pelanggan Pinjaman. Dari Pengoptimuman Kewangan Hingga Penyelesaian E-Dagang.',
      },
      services: {
        tag: '8 Perkhidmatan Teras',
        title: 'Sokongan Perniagaan Menyeluruh',
        items: [
          {
            num: '01',
            title: 'Pengoptimuman Kewangan',
            description: 'Peningkatan DSR, Penyatuan Hutang, Perancangan Deposit Tetap, Pengoptimuman Skor Kredit, Pengurusan Aliran Tunai',
          },
          {
            num: '02',
            title: 'Pemasaran & Pengiklanan',
            description: 'Reka Bentuk Saluran, Strategi Pemasaran, Perancangan Pasaran, Penyelesaian Pengiklanan Pembekal',
          },
          {
            num: '03',
            title: 'Perancangan Perniagaan',
            description: 'Pelan Perniagaan, Reka Bentuk Pembiayaan, Pembangunan Model Perniagaan, Analisis Pasaran',
          },
          {
            num: '04',
            title: 'Perkhidmatan Insurans',
            description: 'Cadangan Produk, Perancangan Insurans, Analisis Liputan',
          },
          {
            num: '05',
            title: 'Penyelesaian E-Dagang',
            description: 'Persediaan Kedai Pantas, Promosi, Operasi, Pembinaan Saluran, Sokongan E-Dagang ⭐',
          },
          {
            num: '06',
            title: 'Sistem Keahlian',
            description: 'Reka Bentuk Sistem, Mata & Ganjaran, Perancangan Faedah',
          },
          {
            num: '07',
            title: 'Perakaunan & Audit',
            description: 'Simpan Kira, Pemfailan Cukai, Penyata Kewangan, Sokongan Audit, Pengoptimuman Cukai 15%',
          },
          {
            num: '08',
            title: 'Pengurusan Kad Kredit',
            description: 'Peringatan Pembayaran, Pembayaran Bagi Pihak, Perkhidmatan Pembelian Bagi Pihak (Perkongsian Hasil 50/50)',
          },
        ],
      },
      benefits: {
        tag: 'Mengapa Memilih Kami',
        title: 'Bimbingan Kewangan Pakar',
        items: [
          {
            icon: '🎯',
            title: 'Penyelesaian Diperibadikan',
            description: 'Strategi kewangan disesuaikan khusus untuk keperluan dan matlamat perniagaan anda.',
          },
          {
            icon: '💼',
            title: 'Kepakaran Industri',
            description: 'Pemahaman mendalam tentang landskap kewangan Malaysia dan keperluan peraturan.',
          },
          {
            icon: '🤝',
            title: 'Sokongan Berterusan',
            description: 'Bimbingan dan sokongan berterusan sepanjang perjalanan kewangan anda bersama kami.',
          },
        ],
      },
      cta: {
        title: 'Bersedia Untuk Mengoptimumkan Kewangan Perniagaan Anda?',
        description: 'Tempah konsultasi percuma dengan pakar kami hari ini dan ketahui bagaimana kami boleh membantu perniagaan anda berkembang maju.',
      },
    },
    solutions: {
      meta: {
        title: 'Penyelesaian | INFINITE GZ',
        description: 'Penyelesaian kewangan untuk semua perniagaan Malaysia. Dari perundingan pinjaman hingga transformasi digital.',
      },
      hero: {
        tag: 'Penyelesaian kewangan untuk semua perniagaan Malaysia',
        title: 'Penyelesaian Kewangan Lengkap',
        description: 'INFINITE GZ adalah platform sehenti anda untuk pinjaman, pengoptimuman kewangan, dan perkhidmatan perniagaan. Dari sistem padanan AI CreditPilot hingga perkhidmatan nasihat yang komprehensif, kami membantu PKS Malaysia mengakses pembiayaan yang lebih baik dan mengembangkan perniagaan mereka.',
      },
      products: [
        {
          tag: 'SISTEM AI',
          title: 'CreditPilot',
          description: 'Sistem padanan pinjaman berkuasa AI yang menganalisis profil kewangan anda dan mencari produk pinjaman terbaik dari 50+ bank dan syarikat fintech Malaysia. Ketepatan padanan 98%, analisis 2 minit.',
          linkText: 'Ketahui lebih lanjut',
        },
        {
          tag: '8 PERKHIDMATAN',
          title: 'Nasihat',
          description: 'Perkhidmatan perniagaan yang komprehensif termasuk pengoptimuman kewangan, penyelesaian e-dagang, perakaunan, strategi pemasaran, dan banyak lagi. Semua perkhidmatan percuma sepenuhnya untuk pelanggan pinjaman.',
          linkText: 'Lihat semua perkhidmatan',
        },
        {
          tag: 'INFRASTRUKTUR',
          title: 'Sumber',
          description: 'Dikuasakan oleh pangkalan data pinjaman yang komprehensif, pemantauan kadar masa nyata, dan algoritma pengoptimuman DSR yang canggih. 50+ institusi, RM 500J+ difasilitasi, melayani 5,000+ perniagaan.',
          linkText: 'Terokai infrastruktur',
        },
      ],
      coreBusiness: {
        tag: 'Perniagaan Teras',
        title: 'Perundingan Pinjaman & Pengoptimuman Kewangan',
        description: 'Kami mengumpul maklumat produk pinjaman dari semua institusi berlesen di Malaysia (bank, bank digital, syarikat fintech), mewujudkan keadaan kewangan yang lebih baik untuk pelanggan, dan membantu mereka mendapatkan pinjaman faedah rendah terbaik. Kami tidak menyediakan sebarang pinjaman haram.',
        features: [
          {
            icon: '📊',
            title: 'Pangkalan Data Menyeluruh',
            description: '50+ institusi kewangan berlesen termasuk bank, bank digital, dan syarikat fintech',
          },
          {
            icon: '💰',
            title: 'Kadar Terbaik',
            description: 'Bandingkan dan dapatkan kadar faedah terendah yang tersedia di pasaran',
          },
          {
            icon: '✅',
            title: '100% Sah',
            description: 'Hanya bekerja dengan institusi kewangan berlesen dan dikawal selia',
          },
          {
            icon: '🎯',
            title: 'Pengoptimuman DSR',
            description: 'Tingkatkan nisbah perkhidmatan hutang untuk meningkatkan kebarangkalian kelulusan pinjaman',
          },
          {
            icon: '🔄',
            title: 'Penyatuan Hutang',
            description: 'Satukan pelbagai hutang untuk mengurangkan tekanan bayaran bulanan',
          },
          {
            icon: '⭐',
            title: 'Peningkatan Kredit',
            description: 'Optimumkan skor kredit dan tingkatkan laporan CTOS/CCRIS',
          },
        ],
      },
      complementaryServices: {
        tag: '8 Perkhidmatan Pelengkap',
        title: 'Perkhidmatan Perniagaan Pelengkap',
        description: 'Semua perkhidmatan pelengkap percuma sepenuhnya untuk pelanggan pinjaman. Semua Perkhidmatan Percuma Sepenuhnya Untuk Pelanggan Pinjaman.',
        items: [
          {
            num: '01',
            title: 'Pengoptimuman Kewangan',
            description: 'Peningkatan DSR, Penyatuan Hutang, Perancangan Deposit Tetap',
          },
          {
            num: '02',
            title: 'Strategi Pemasaran',
            description: 'Reka Bentuk Saluran, Strategi Pemasaran, Perancangan Pasaran',
          },
          {
            num: '03',
            title: 'Perancangan Perniagaan',
            description: 'Pelan Perniagaan, Reka Bentuk Pembiayaan, Pembangunan Model Perniagaan',
          },
          {
            num: '04',
            title: 'Perkhidmatan Insurans',
            description: 'Cadangan Produk, Perancangan Insurans',
          },
          {
            num: '05',
            title: 'Penyelesaian E-Dagang',
            description: 'Persediaan Kedai, Promosi, Operasi, Pembinaan Saluran ⭐',
          },
          {
            num: '06',
            title: 'Sistem Keahlian',
            description: 'Reka Bentuk Sistem, Ganjaran Mata, Reka Bentuk Faedah',
          },
          {
            num: '07',
            title: 'Perakaunan & Audit',
            description: 'Simpan Kira, Pemfailan Cukai, Pengoptimuman Cukai 15%',
          },
          {
            num: '08',
            title: 'Pengurusan Kad Kredit',
            description: 'Peringatan Pembayaran, Pembayaran/Pembelian Bagi Pihak (Perkongsian 50/50)',
          },
        ],
      },
      pricing: {
        tag: 'Model Harga',
        title: 'Tiada Yuran Pendahuluan',
        models: [
          {
            tag: 'PERKHIDMATAN TERAS',
            title: 'Yuran Kejayaan',
            price: '💼',
            description: 'Caj selepas kelulusan pinjaman. Hanya caj selepas kelulusan pinjaman yang berjaya dan pengeluaran.',
            features: ['Tiada Kos Pendahuluan', 'Tiada Caj Tersembunyi', 'Harga Berasaskan Kejayaan'],
          },
          {
            tag: '8 PERKHIDMATAN',
            title: 'Percuma Sepenuhnya',
            price: '🎁',
            description: 'Percuma sepenuhnya untuk pelanggan pinjaman. Semua 8 perkhidmatan pelengkap percuma untuk pelanggan pinjaman.',
            features: ['Pengoptimuman Kewangan', 'Penyelesaian E-Dagang', 'Perakaunan & Lain-lain'],
          },
          {
            tag: 'RAKAN KONGSI KHAS',
            title: 'Perkongsian 50/50',
            price: '🤝',
            description: 'Model perkongsian keuntungan. Perkongsian keuntungan untuk perkhidmatan pengurusan kad kredit.',
            features: ['Perkongsian Hasil', 'Perkongsian Menang-Menang', 'Harga Telus'],
          },
        ],
      },
      targetCustomers: {
        tag: 'Pelanggan Sasaran',
        title: 'Siapa Yang Kami Layani',
        customers: [
          {
            icon: '👔',
            title: 'Pemilik Perniagaan Tradisional',
            description: 'Pemilik perniagaan tradisional berusia 40-50 tahun yang memerlukan pinjaman untuk pengembangan perniagaan atau transformasi digital',
          },
          {
            icon: '🏢',
            title: 'Syarikat PKS',
            description: 'Perusahaan kecil dan sederhana yang memerlukan pinjaman, termasuk pembuatan, runcit, F&B, dll.',
          },
          {
            icon: '💳',
            title: 'Hutang Kad Kredit Tinggi',
            description: 'Pelanggan dengan hutang kad kredit tinggi yang memerlukan penyatuan hutang dan pengoptimuman kewangan',
          },
          {
            icon: '🤝',
            title: 'Rakan Kongsi Perniagaan',
            description: 'Pembekal, pelanggan ahli yang memerlukan sokongan perniagaan yang menyeluruh',
          },
        ],
      },
      cta: {
        title: 'Bersedia Untuk Mengubah Perniagaan Anda?',
        description: 'Sertai 5,000+ perniagaan yang telah mendapat pembiayaan yang lebih baik melalui INFINITE GZ',
      },
    },
    company: {
      meta: {
        title: 'Syarikat | INFINITE GZ',
        description: 'Ketahui tentang INFINITE GZ SDN BHD - syarikat teknologi kewangan dan perkhidmatan nasihat terkemuka Malaysia.',
      },
      hero: {
        tag: 'Tentang Kami',
        title: 'Membina Masa Depan Kewangan',
        description: 'Kami Adalah Syarikat Teknologi Kewangan Dan Perkhidmatan Nasihat Malaysia Yang Berdedikasi Untuk Membantu Perniagaan Mengakses Pembiayaan Yang Lebih Baik.',
      },
      mission: {
        tag: 'Misi Kami',
        title: 'Mendemokrasikan Akses Kepada Kewangan',
        description: 'Misi kami adalah untuk menjadikan perkhidmatan kewangan boleh diakses oleh semua perniagaan Malaysia, tanpa mengira saiz atau industri.',
      },
      values: {
        tag: 'Nilai Kami',
        title: 'Apa Yang Mendorong Kami',
        items: [
          {
            icon: '🎯',
            title: 'Pelanggan Dahulu',
            description: 'Kami mengutamakan kejayaan pelanggan di atas segalanya.'
          },
          {
            icon: '💡',
            title: 'Inovasi',
            description: 'Menggunakan AI dan teknologi untuk mengubah perkhidmatan kewangan.'
          },
          {
            icon: '🤝',
            title: 'Integriti',
            description: 'Telus, jujur, dan beretika dalam semua urusan kami.'
          },
          {
            icon: '🚀',
            title: 'Kecemerlangan',
            description: 'Komited untuk menyampaikan hasil yang luar biasa setiap kali.'
          }
        ]
      },
      cta: {
        title: 'Sertai Kami Dalam Perjalanan Ini',
        description: 'Sama ada anda mencari pembiayaan atau ingin menyertai pasukan kami, kami ingin mendengar daripada anda.'
      }
    },
    news: {
      meta: {
        title: 'Berita | INFINITE GZ',
        description: 'Berita terkini, kemas kini, dan kisah kejayaan dari INFINITE GZ.',
      },
      hero: {
        tag: 'Kemas Kini Terkini',
        title: 'Berita & Kisah Kejayaan',
        description: 'Kekal Dikemas Kini Dengan Berita Terkini, Kajian Kes, Dan Kisah Kejayaan Kami.',
      },
    
      items: [
        { title: 'INFINITE GZ Memperoleh RM 500 Juta+ Pembiayaan', date: '2024-12', category: 'Pencapaian' },
        { title: 'Ciri AI Baharu dalam CreditPilot', date: '2024-12', category: 'Produk' },
        { title: 'Kisah Kejayaan: Pertumbuhan PKS Pembuatan', date: '2024-11', category: 'Kajian Kes' },
        { title: 'Perkongsian dengan Bank Utama Diumumkan', date: '2024-11', category: 'Perkongsian' },
        { title: 'INFINITE GZ Memenangi Anugerah Fintech', date: '2024-10', category: 'Pengiktirafan' },
        { title: 'Mengembang ke 50+ Institusi Kewangan', date: '2024-10', category: 'Pertumbuhan' },
      ],
    },
    resources: {
      meta: {
        title: 'Sumber | INFINITE GZ',
        description: 'Pangkalan data pinjaman yang komprehensif, pemantauan kadar masa nyata, dan alat pengoptimuman canggih.',
      },
      hero: {
        tag: 'Infrastruktur',
        title: 'Kami Pergi Lebih Jauh, Lebih Cepat',
        description: 'Dikuasakan Oleh Pangkalan Data Menyeluruh Dan Algoritma Canggih Untuk Melayani Perniagaan Malaysia.',
      },
    
      stats: [
        { number: '50+', title: 'Institusi Kewangan', description: 'Bank, bank digital, dan syarikat fintech' },
        { number: 'RM 500 Juta+', title: 'Pinjaman Difasilitasi', description: 'Jumlah pembiayaan yang dijamin untuk pelanggan kami' },
        { number: '2 Minit', title: 'Masa Analisis', description: 'Hasil padanan pinjaman yang pantas dan tepat' },
        { number: '98%', title: 'Ketepatan Padanan', description: 'Ketepatan berkuasa AI dalam cadangan pinjaman' },
      ],
      timeline: {
        tag: 'Perjalanan Kami',
        title: 'Membina Masa Depan',
        milestones: [
          { year: '2020', title: 'Syarikat Ditubuhkan', description: 'Bermula dengan visi untuk mendemokrasikan akses kepada kewangan' },
          { year: '2021', title: '1,000 Pelanggan Pertama', description: 'Mencapai pencapaian utama pertama dalam kejayaan pelanggan' },
          { year: '2022', title: 'Pelancaran CreditPilot', description: 'Memperkenalkan sistem padanan pinjaman berkuasa AI' },
          { year: '2023', title: 'RM 100 Juta+ Difasilitasi', description: 'Melepasi pencapaian pembiayaan yang signifikan' },
          { year: '2024', title: 'Rangkaian 50+ Institusi', description: 'Mengembang ke liputan institusi kewangan yang komprehensif' },
        ],
      },
    },
    careers: {
      meta: {
        title: 'Kerjaya | INFINITE GZ',
        description: 'Sertai pasukan kami dan bantu membina masa depan perkhidmatan kewangan di Malaysia.',
      },
      hero: {
        tag: 'Sertai Pasukan Kami',
        title: 'Membina Masa Depan Kewangan',
        description: 'Sertai Pasukan Profesional Kami Yang Bersemangat Berdedikasi Untuk Mengubah Perkhidmatan Kewangan.',
      },
      benefits: {
        tag: 'Faedah',
        title: 'Mengapa Bekerja Dengan Kami',
        items: [
          {
            icon: '💰',
            title: 'Gaji Kompetitif',
            description: 'Pampasan di atas kadar pasaran dengan bonus prestasi',
          },
          {
            icon: '🏥',
            title: 'Faedah Kesihatan',
            description: 'Insurans perubatan dan pergigian yang menyeluruh',
          },
          {
            icon: '📚',
            title: 'Pembelajaran & Pembangunan',
            description: 'Latihan berterusan dan peluang pembangunan kerjaya',
          },
          {
            icon: '🏠',
            title: 'Kerja Fleksibel',
            description: 'Susunan kerja hibrid dengan waktu fleksibel',
          },
          {
            icon: '🎉',
            title: 'Acara Pasukan',
            description: 'Aktiviti pembinaan pasukan dan acara syarikat secara berkala',
          },
          {
            icon: '🚀',
            title: 'Pertumbuhan Kerjaya',
            description: 'Laluan kemajuan kerjaya yang jelas dalam syarikat yang berkembang',
          },
        ],
      },
    
      jobs: {
        tag: 'Jawatan Kosong',
        title: 'Sertai Pasukan Kami Yang Berkembang',
        positions: [
          { title: 'Penasihat Kewangan Kanan', department: 'Nasihat', location: 'Kuala Lumpur', type: 'Sepenuh Masa' },
          { title: 'Jurutera AI/ML', department: 'Teknologi', location: 'Kuala Lumpur / Jauh', type: 'Sepenuh Masa' },
          { title: 'Pengurus Pembangunan Perniagaan', department: 'Jualan', location: 'Kuala Lumpur', type: 'Sepenuh Masa' },
          { title: 'Pakar Pemasaran Digital', department: 'Pemasaran', location: 'Jauh', type: 'Sepenuh Masa' },
          { title: 'Akauntan', department: 'Kewangan', location: 'Kuala Lumpur', type: 'Sepenuh Masa' },
          { title: 'Pengurus Kejayaan Pelanggan', department: 'Operasi', location: 'Kuala Lumpur', type: 'Sepenuh Masa' },
        ],
      },
      cta: {
        title: 'Tidak Jumpa Peranan Anda?',
        description: 'Kami sentiasa mencari individu berbakat. Hantar CV anda dan beritahu kami bagaimana anda boleh menyumbang.',
      },
    },
    cardManagement: {
      hero: {
        tag: 'Pengurusan Kad Kredit Profesional',
        title: 'Jimat RM 1,200-5,000 Setahun',
        subtitle: 'Melalui Perkhidmatan Pengurusan Kad Kredit Profesional',
        benefits: [
          { icon: '💰', value: 'RM 500-2,000/tahun', label: 'Elak Penalti Lewat Bayar' },
          { icon: '🎁', value: 'RM 800-3,000/tahun', label: 'Ganjaran & Pulangan Tunai Tambahan' },
          { icon: '📈', value: '50-100 Mata', label: 'Peningkatan Skor Kredit' },
        ],
        cta1: 'Perundingan WhatsApp Percuma',
        cta2: 'Lihat Harga',
        socialProof: 'Lebih 500 pelanggan | Menguruskan 1,000+ kad | Jumlah penjimatan RM 600,000+',
      },
      painPoints: {
        tag: 'Masalah Biasa',
        title: 'Adakah Anda Menghadapi Cabaran Kad Kredit Ini?',
        subtitle: 'Hutang kad kredit Malaysia: RM 50.7B | Hutang tertunggak: RM 551.8M (1.1%)',
        points: [
          {
            icon: '😰',
            title: 'Terlupa Bayar',
            description: 'Pelbagai kad, tarikh tamat berbeza, mudah terlepas bayaran',
            impact: 'Yuran lewat RM 150-300/kali + Kerosakan skor kredit',
          },
          {
            icon: '💸',
            title: 'Tidak Tahu Cara Optimalkan',
            description: 'Tidak faham ganjaran kad, mata terbuang, yuran tahunan tinggi',
            impact: 'Kehilangan RM 800-3,000/tahun faedah',
          },
          {
            icon: '🔢',
            title: 'Kekacauan Pelbagai Kad',
            description: 'Urus 2-3 kad, penyata keliru, tekanan',
            impact: 'Perangkap bayaran minimum, faedah 18% setahun',
          },
        ],
        stats: [
          { value: 'RM 50.7B', label: 'Jumlah Hutang Kad' },
          { value: '18% p.a.', label: 'Kadar Faedah Maksimum' },
          { value: 'RM 551.8M', label: 'Jumlah Tertunggak' },
          { value: '50,000+', label: 'Belia Berhutang' },
        ],
      },
      solutions: {
        tag: 'Penyelesaian Kami',
        title: 'Perkhidmatan Profesional 5-dalam-1',
        subtitle: 'Pengurusan kad kredit menyeluruh untuk memaksimumkan faedah anda',
        services: [
          {
            icon: '⏰',
            title: 'Perkhidmatan Peringatan Bayaran',
            description: 'Sistem peringatan 3 peringkat memastikan anda tidak terlepas bayaran',
            benefits: [
              'WhatsApp + SMS + E-mel tiga kali notifikasi',
              'Peringatan 7/3/1 hari sebelum tarikh tamat',
              'Semakan penyata bulanan',
              'Sistem amaran tertunggak',
            ],
          },
          {
            icon: '💳',
            title: 'Perkhidmatan Bayaran Wakil',
            description: 'Kami bayar bagi pihak anda untuk memastikan bayaran tepat masa',
            benefits: [
              'Jaminan bayaran tepat masa 100%',
              'Diproses dalam 2 hari bekerja',
              'Potongan automatik dari akaun yang ditetapkan',
              'Laporan penyesuaian bulanan',
            ],
          },
          {
            icon: '🛍️',
            title: 'Perkhidmatan Pembelian Wakil',
            description: 'Gunakan kad yang paling optimum untuk memaksimumkan ganjaran',
            benefits: [
              'Sistem pemilihan kad pintar',
              'Maksimumkan pulangan tunai dan mata',
              'Model perkongsian hasil 50/50',
              'Rekod transaksi telus',
            ],
          },
          {
            icon: '📊',
            title: 'Pengoptimuman Kad',
            description: 'Analisis corak perbelanjaan dan cadangan strategi',
            benefits: [
              'Analisis perbelanjaan bulanan',
              'Cadangan penggunaan kad optimum',
              'Rundingan pengecualian yuran tahunan',
              'Peringatan penebusan ganjaran',
            ],
          },
          {
            icon: '💼',
            title: 'Perundingan Pengurusan Hutang',
            description: 'Analisis DSR dan cadangan penyatuan hutang',
            benefits: [
              'Pengiraan DSR percuma',
              'Pelan penyatuan hutang',
              'Strategi peningkatan skor kredit',
              'Penyelesaian kadar faedah lebih rendah',
            ],
          },
        ],
      },
      caseStudies: {
        tag: 'Kisah Kejayaan',
        title: 'Hasil Pelanggan Sebenar',
        subtitle: 'Lihat bagaimana pelanggan kami menjimatkan ribuan setiap tahun',
        before: 'Sebelum',
        after: 'Selepas',
        cases: [
          {
            client: 'Encik Wang',
            type: 'Individu | 4 Kad',
            before: 'Bayaran bulanan RM 2,500 | Pengurusan keliru | Sering lewat bayar',
            after: 'Pinjaman disatukan + Pengurusan pintar | Bayaran automatik | Ganjaran optimum',
            savings: 'Jimat RM 3,200',
            period: 'Dalam 12 bulan',
          },
          {
            client: 'Puan Li',
            type: 'Profesional | Perbelanjaan Tinggi',
            before: 'Perbelanjaan bulanan RM 8,000 | Guna kad yang salah | Mata terbuang',
            after: 'Strategi kad optimum | Ganjaran maksimum | Yuran tahunan dikecualikan',
            savings: 'Tambahan RM 5,000/tahun',
            period: 'Berterusan',
          },
          {
            client: 'Syarikat ABC',
            type: 'PKS | 10 Kad Korporat',
            before: 'Kekacauan tuntutan pekerja | Kos pentadbiran tinggi | Berbelanja lebih',
            after: 'Pengurusan berpusat | Penyesuaian automatik | Kawalan perbelanjaan',
            savings: 'Jimat RM 12,000/tahun',
            period: 'Tahun pertama',
          },
        ],
      },
      pricing: {
        tag: 'Harga Telus',
        title: 'Pelan Fleksibel untuk Setiap Keperluan',
        subtitle: 'Pilih pelan yang paling sesuai untuk anda',
        recommended: 'Paling Popular',
        plans: {
          individual: {
            label: 'Individu',
            options: [
              {
                name: 'Yuran Berjaya',
                price: 'Perkongsian 50/50',
                period: 'Bayar hanya apabila anda jimat',
                features: [
                  'Tiada yuran pendahuluan',
                  '50% daripada semua penjimatan/faedah',
                  'Pengecualian yuran tahunan',
                  'Pengoptimuman pulangan tunai & ganjaran',
                  'Penjimatan faedah',
                  'Elakkan yuran lewat',
                  'Bil suku tahunan',
                ],
                recommended: true,
                cta: { text: 'Mulakan Sekarang', link: 'https://wa.me/60123456789' },
              },
              {
                name: 'Langganan Bulanan',
                price: 'RM 99/bulan',
                period: 'Sehingga 3 kad',
                features: [
                  'Tambahan RM 30/kad',
                  'Perkhidmatan peringatan bayaran',
                  'Pengoptimuman kad',
                  'Analisis perbelanjaan bulanan',
                  'Rundingan yuran tahunan',
                  'Bayaran wakil: +RM 50/bulan',
                ],
                cta: { text: 'Langgan Sekarang', link: 'https://portal.infinitegz.com/card-management' },
              },
              {
                name: 'PERCUMA untuk Pelanggan Pinjaman',
                price: 'RM 0',
                period: '12 bulan pertama',
                features: [
                  'Semua perkhidmatan standard termasuk',
                  'Mesti ada pinjaman aktif dengan kami',
                  'Diskaun 50% selepas 12 bulan',
                  'Perkhidmatan peringatan bayaran penuh',
                  'Pengoptimuman kad asas',
                ],
                cta: { text: 'Semak Kelayakan', link: '/creditpilot' },
              },
            ],
          },
          corporate: {
            label: 'Korporat',
            options: [
              {
                name: 'Tahap 1',
                price: 'RM 299/bulan',
                period: 'RM 0-20K perbelanjaan bulanan',
                features: [
                  'Sehingga 10 kad korporat',
                  'Pengurusan berpusat',
                  'Penyesuaian bulanan',
                  'Analitik perbelanjaan asas',
                  'Penjejakan kad pekerja',
                ],
                cta: { text: 'Hubungi Jualan', link: 'https://wa.me/60123456789' },
              },
              {
                name: 'Tahap 2',
                price: 'RM 599/bulan',
                period: 'RM 20-50K perbelanjaan bulanan',
                features: [
                  'Sehingga 25 kad korporat',
                  'Analitik lanjutan',
                  'Pengurus akaun khusus',
                  'Had perbelanjaan tersuai',
                  'Kelulusan automatik',
                  'Semakan perniagaan suku tahunan',
                ],
                recommended: true,
                cta: { text: 'Hubungi Jualan', link: 'https://wa.me/60123456789' },
              },
              {
                name: 'Tahap 3',
                price: 'RM 999/bulan',
                period: 'RM 50-100K perbelanjaan bulanan',
                features: [
                  'Kad korporat tanpa had',
                  'Sokongan premium',
                  'Integrasi tersuai',
                  'Pengesanan penipuan lanjutan',
                  'Pengurusan pelbagai entiti',
                  'Pelaporan label putih',
                ],
                cta: { text: 'Hubungi Jualan', link: 'https://wa.me/60123456789' },
              },
            ],
          },
          loan: {
            label: 'Pelanggan Pinjaman',
            options: [
              {
                name: 'Percuma',
                price: 'PERCUMA',
                period: '12 bulan pertama',
                features: [
                  'Semua perkhidmatan individu termasuk',
                  'Sokongan keutamaan',
                  'Perundingan hutang percuma',
                  'Diskaun 50% selepas 12 bulan',
                  'Faedah eksklusif pelanggan pinjaman',
                ],
                recommended: true,
                cta: { text: 'Ketahui Lebih Lanjut', link: '/advisory' },
              },
            ],
          },
        },
      },
      socialProof: {
        stats: [
          { value: '500+', label: 'Pelanggan Gembira' },
          { value: '1,000+', label: 'Kad Diuruskan' },
          { value: 'RM 600K+', label: 'Jumlah Penjimatan' },
          { value: '98%', label: 'Kadar Kepuasan' },
        ],
        badges: [
          'Patuh PDPA 2010',
          'Penasihat Kewangan Berlesen',
          'Diluluskan Bank Negara',
          'Diperakui ISO 27001',
        ],
      },
      faq: {
        title: 'Soalan Lazim',
        subtitle: 'Segala yang anda perlu tahu',
        questions: [
          {
            question: 'Bagaimana anda mengenakan bayaran?',
            answer: 'Kami menawarkan 3 model harga: (1) Yuran berjaya: 50% daripada penjimatan yang dijana, tiada yuran pendahuluan. (2) Langganan bulanan: RM 99/bulan untuk sehingga 3 kad. (3) PERCUMA untuk pelanggan pinjaman untuk 12 bulan pertama. Pilih yang paling sesuai untuk anda.',
          },
          {
            question: 'Adakah perkhidmatan bayaran wakil selamat?',
            answer: 'Sudah tentu. Kami hanya mendebit dari akaun yang anda tetapkan dengan kebenaran anda. Semua transaksi direkodkan dan anda menerima laporan penyesuaian bulanan. Kami mengekalkan insurans indemniti profesional RM 1M.',
          },
          {
            question: 'Bagaimana cara membatalkan perkhidmatan?',
            answer: 'Anda boleh membatalkan pada bila-bila masa dengan notis bertulis 30 hari. Untuk pelan langganan, anda mendapat bayaran balik pro-rata. Untuk pelan yuran berjaya dalam tempoh komitmen, yuran penamatan awal dikenakan (50% yuran baki atau RM 500, mana yang lebih rendah).',
          },
          {
            question: 'Adakah anda menyokong semua bank di Malaysia?',
            answer: 'Ya, kami menyokong semua bank utama termasuk Maybank, CIMB, Public Bank, Hong Leong, RHB, AmBank, dan bank digital. Kami boleh menguruskan kad daripada mana-mana institusi kewangan berlesen di Malaysia.',
          },
          {
            question: 'Adakah anda akan melihat nombor kad kredit saya?',
            answer: 'Tidak. Kami hanya memerlukan penyata kad kredit anda (yang menunjukkan 4 digit terakhir). Untuk perkhidmatan bayaran wakil, bayaran dibuat terus dari akaun bank anda kepada pengeluar kad kredit. Kami tidak pernah menyimpan nombor kad penuh.',
          },
          {
            question: 'Bagaimana jika saya terlepas bayaran walaupun dengan perkhidmatan anda?',
            answer: 'Kami menyediakan peringatan 3 peringkat dan perkhidmatan terbaik. Walau bagaimanapun, jika anda tidak mengekalkan dana yang mencukupi dalam akaun anda, kami tidak boleh bertanggungjawab. Liabiliti kami dihadkan kepada RM 10,000 atau yuran 12 bulan, mana yang lebih rendah.',
          },
          {
            question: 'Bolehkah saya gunakan ini untuk kad syarikat?',
            answer: 'Boleh! Kami mempunyai pelan korporat khusus bermula dari RM 299/bulan. Sempurna untuk PKS yang menguruskan pelbagai kad pekerja. Termasuk pengurusan berpusat, penyesuaian, dan analitik perbelanjaan.',
          },
        ],
      },
      finalCta: {
        title: 'Bersedia untuk Mula Menjimat?',
        subtitle: 'Sertai 500+ pelanggan yang berpuas hati dan mula memaksimumkan faedah kad kredit anda hari ini',
        cta1: 'Perundingan Percuma WhatsApp',
        cta2: 'Tempah Temu Janji',
        relatedTitle: 'Perkhidmatan Berkaitan',
        relatedServices: [
          { name: 'CreditPilot (Padanan Pinjaman Pintar)', link: '/creditpilot' },
          { name: 'Nasihat Pinjaman', link: '/advisory' },
          { name: 'Pengoptimuman Kewangan', link: '/solutions' },
        ],
      },
    },
  },
};
