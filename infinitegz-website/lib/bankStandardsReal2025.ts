/**
 * 马来西亚银行贷款批准标准 - 2025年真实数据
 * 基于官方指南和实际银行政策
 * 最后更新: 2025-12-28
 */

// ============= 类型定义 =============

/**
 * 申请人身份类型
 */
export type ApplicantIdentity = 
  | 'malaysian_citizen'      // 马来西亚公民
  | 'permanent_resident'     // 永久居民
  | 'foreigner'              // 外国人
  | 'government_employee'    // 公务员
  | 'glc_employee'           // GLC员工
  | 'private_employee'       // 私企员工
  | 'self_employed'          // 自雇
  | 'contract_worker'        // 合约工
  | 'professional';          // 专业人士（医生/律师等）

/**
 * 就业类型
 */
export type EmploymentType = 
  | 'salaried'               // 受薪
  | 'self_employed'          // 自雇
  | 'government'             // 政府
  | 'contract';              // 合约

/**
 * 贷款类型
 */
export type LoanType = 
  | 'personal'               // 个人贷款
  | 'housing'                // 房贷
  | 'car'                    // 车贷
  | 'credit_card';           // 信用卡

/**
 * 收入认定规则
 */
export interface IncomeRecognitionRule {
  employmentType: EmploymentType;
  recognitionRate: number;           // 认定比例 (0-1)
  minBusinessYears?: number;         // 最低营业年限（自雇）
  requiredDocuments: string[];       // 所需文件
  notes: string;                     // 备注
}

/**
 * DSR限制（按收入区间）
 */
export interface DSRLimit {
  minNetIncome: number;              // 最低净收入
  maxNetIncome?: number;             // 最高净收入
  dsrLimit: number;                  // DSR限制 (百分比)
  notes?: string;
}

/**
 * 身份特殊条件
 */
export interface IdentityCondition {
  identity: ApplicantIdentity;
  accepted: boolean;                 // 是否接受
  lvtAdjustment?: number;            // LTV调整（百分比）
  interestRatePremium?: number;      // 利率溢价（百分比）
  dsrAdjustment?: number;            // DSR调整（百分比）
  additionalDocuments?: string[];    // 额外文件
  specialNotes?: string;             // 特殊说明
}

/**
 * 完整银行标准
 */
export interface BankStandardReal {
  bankName: string;
  bankCode: string;
  
  // DSR限制（按贷款类型）
  dsr: {
    [key in LoanType]: DSRLimit[];
  };
  
  // 收入认定规则（按银行）
  incomeRecognition: {
    [key in EmploymentType]: IncomeRecognitionRule;
  };
  
  // 身份条件
  identityConditions: IdentityCondition[];
  
  // 贷款限制
  loanLimits: {
    personalLoanMax: number;
    personalLoanMultiplier: number;    // 月收入倍数
    housingLTV: {
      firstProperty: number;
      secondProperty: number;
      thirdProperty: number;
    };
    carLTV: {
      newCar: number;
      usedCar: number;
    };
    creditCardLimitMultiplier: number;
  };
  
  // 其他要求
  requirements: {
    minAge: number;
    maxAge: number;
    minEmploymentMonths: number;
    requiresPayslip: boolean;
    requiresEPF: boolean;
    requiresBankStatement: boolean;
  };
  
  // 特殊优势（如有）
  specialFeatures?: string[];
}

// ============= 银行标准数据 =============

export const bankStandardsReal2025: BankStandardReal[] = [
  // ===== Maybank =====
  {
    bankName: 'Maybank',
    bankCode: 'MBB',
    
    dsr: {
      personal: [
        { minNetIncome: 0, maxNetIncome: 3500, dsrLimit: 40, notes: '低收入最严格' },
        { minNetIncome: 3500, dsrLimit: 70, notes: '高收入' }
      ],
      housing: [
        { minNetIncome: 0, maxNetIncome: 3500, dsrLimit: 40 },
        { minNetIncome: 3500, dsrLimit: 70 }
      ],
      car: [
        { minNetIncome: 0, maxNetIncome: 3500, dsrLimit: 40 },
        { minNetIncome: 3500, dsrLimit: 70 }
      ],
      credit_card: [
        { minNetIncome: 0, maxNetIncome: 3500, dsrLimit: 40 },
        { minNetIncome: 3500, dsrLimit: 70 }
      ]
    },
    
    incomeRecognition: {
      salaried: {
        employmentType: 'salaried',
        recognitionRate: 1.0,
        requiredDocuments: ['最近3个月工资单', '最近EPF单据', '最近3个月银行账单'],
        notes: '基本薪资+固定津贴100%认可，奖金50-70%'
      },
      government: {
        employmentType: 'government',
        recognitionRate: 1.0,
        requiredDocuments: ['最近3个月工资单', 'EPF单据'],
        notes: '享有额外优势，但LPPSA更优'
      },
      self_employed: {
        employmentType: 'self_employed',
        recognitionRate: 0.7,
        minBusinessYears: 3,
        requiredDocuments: ['过去3年报税单', '审计财报', '12个月银行流水', 'SSM证书'],
        notes: '取3年平均×70%，较保守'
      },
      contract: {
        employmentType: 'contract',
        recognitionRate: 0.8,
        requiredDocuments: ['合约书', '最近6个月工资单', '雇主信'],
        notes: '需合约至少12个月有效期'
      }
    },
    
    identityConditions: [
      {
        identity: 'malaysian_citizen',
        accepted: true,
        notes: '优先，最容易'
      },
      {
        identity: 'permanent_resident',
        accepted: true,
        lvtAdjustment: -5,
        additionalDocuments: ['PR证书', '额外工作证明'],
        specialNotes: '需额外文件，LTV可能降至85%'
      },
      {
        identity: 'foreigner',
        accepted: false,
        specialNotes: '大多数情况拒绝，仅极少数接受'
      },
      {
        identity: 'government_employee',
        accepted: true,
        dsrAdjustment: 5,
        specialNotes: '优先，但LPPSA更优'
      },
      {
        identity: 'self_employed',
        accepted: true,
        specialNotes: '条件严格，70%打折'
      }
    ],
    
    loanLimits: {
      personalLoanMax: 100000,
      personalLoanMultiplier: 10,
      housingLTV: {
        firstProperty: 90,
        secondProperty: 90,
        thirdProperty: 70
      },
      carLTV: {
        newCar: 90,
        usedCar: 70
      },
      creditCardLimitMultiplier: 2
    },
    
    requirements: {
      minAge: 21,
      maxAge: 60,
      minEmploymentMonths: 6,
      requiresPayslip: true,
      requiresEPF: true,
      requiresBankStatement: true
    },
    
    specialFeatures: [
      '低收入客户最严格（40% DSR）',
      '自雇人士打折较重（70%）'
    ]
  },

  // ===== CIMB =====
  {
    bankName: 'CIMB Bank',
    bankCode: 'CIMB',
    
    dsr: {
      personal: [
        { minNetIncome: 0, maxNetIncome: 3000, dsrLimit: 65, notes: '低收入最友好' },
        { minNetIncome: 3000, dsrLimit: 75, notes: '高收入' }
      ],
      housing: [
        { minNetIncome: 0, maxNetIncome: 3000, dsrLimit: 65 },
        { minNetIncome: 3000, dsrLimit: 75 }
      ],
      car: [
        { minNetIncome: 0, maxNetIncome: 3000, dsrLimit: 65 },
        { minNetIncome: 3000, dsrLimit: 75 }
      ],
      credit_card: [
        { minNetIncome: 0, maxNetIncome: 3000, dsrLimit: 65 },
        { minNetIncome: 3000, dsrLimit: 75 }
      ]
    },
    
    incomeRecognition: {
      salaried: {
        employmentType: 'salaried',
        recognitionRate: 1.0,
        requiredDocuments: ['最近3个月工资单', 'EPF单据', '银行账单'],
        notes: '标准认可100%'
      },
      government: {
        employmentType: 'government',
        recognitionRate: 1.0,
        requiredDocuments: ['工资单', 'EPF单据'],
        notes: '标准认可'
      },
      self_employed: {
        employmentType: 'self_employed',
        recognitionRate: 0.8,
        minBusinessYears: 3,
        requiredDocuments: ['最近1年报税单', '12个月流水', 'SSM证书'],
        notes: '取最近1年×80%，较宽松'
      },
      contract: {
        employmentType: 'contract',
        recognitionRate: 0.8,
        requiredDocuments: ['合约书', '工资单', '雇主信'],
        notes: '对合约接受度高'
      }
    },
    
    identityConditions: [
      {
        identity: 'malaysian_citizen',
        accepted: true
      },
      {
        identity: 'permanent_resident',
        accepted: true,
        additionalDocuments: ['PR证书'],
        specialNotes: '接受，需额外文件'
      },
      {
        identity: 'foreigner',
        accepted: true,
        interestRatePremium: 1.0,
        dsrAdjustment: -15,
        specialNotes: '某些情况接受（工作3+年，大公司）'
      },
      {
        identity: 'self_employed',
        accepted: true,
        specialNotes: '对自雇最友好（80%认可）'
      }
    ],
    
    loanLimits: {
      personalLoanMax: 250000,
      personalLoanMultiplier: 8,
      housingLTV: {
        firstProperty: 90,
        secondProperty: 90,
        thirdProperty: 70
      },
      carLTV: {
        newCar: 90,
        usedCar: 80
      },
      creditCardLimitMultiplier: 2.5
    },
    
    requirements: {
      minAge: 21,
      maxAge: 60,
      minEmploymentMonths: 6,
      requiresPayslip: true,
      requiresEPF: true,
      requiresBankStatement: true
    },
    
    specialFeatures: [
      '对自雇最友好（认可80%+）',
      'DSR相对宽松（65-75%）',
      '愿意接受PR和某些外国人',
      '低收入友好',
      '最"包容"的银行'
    ]
  },

  // ===== RHB =====
  {
    bankName: 'RHB Bank',
    bankCode: 'RHB',
    
    dsr: {
      personal: [
        { minNetIncome: 0, maxNetIncome: 3000, dsrLimit: 55, notes: '整体较严' },
        { minNetIncome: 3000, dsrLimit: 60 }
      ],
      housing: [
        { minNetIncome: 0, maxNetIncome: 3000, dsrLimit: 55 },
        { minNetIncome: 3000, dsrLimit: 60 }
      ],
      car: [
        { minNetIncome: 0, maxNetIncome: 3000, dsrLimit: 55 },
        { minNetIncome: 3000, dsrLimit: 60 }
      ],
      credit_card: [
        { minNetIncome: 0, maxNetIncome: 3000, dsrLimit: 55 },
        { minNetIncome: 3000, dsrLimit: 60 }
      ]
    },
    
    incomeRecognition: {
      salaried: {
        employmentType: 'salaried',
        recognitionRate: 1.0,
        requiredDocuments: ['工资单', 'EPF', '银行账单'],
        notes: '标准认可'
      },
      government: {
        employmentType: 'government',
        recognitionRate: 1.0,
        requiredDocuments: ['工资单', 'EPF'],
        notes: '标准认可'
      },
      self_employed: {
        employmentType: 'self_employed',
        recognitionRate: 0.6,
        minBusinessYears: 3,
        requiredDocuments: ['3年报税单', '审计财报', '银行流水', 'SSM'],
        notes: '取3年平均×60%，最严格'
      },
      contract: {
        employmentType: 'contract',
        recognitionRate: 0.7,
        requiredDocuments: ['合约书', '工资单'],
        notes: '较保守'
      }
    },
    
    identityConditions: [
      {
        identity: 'malaysian_citizen',
        accepted: true
      },
      {
        identity: 'permanent_resident',
        accepted: true,
        specialNotes: '可能，需谨慎'
      },
      {
        identity: 'foreigner',
        accepted: false,
        specialNotes: '大多数拒绝'
      },
      {
        identity: 'self_employed',
        accepted: true,
        specialNotes: '困难（仅60%认可）'
      }
    ],
    
    loanLimits: {
      personalLoanMax: 150000,
      personalLoanMultiplier: 5,
      housingLTV: {
        firstProperty: 90,
        secondProperty: 85,
        thirdProperty: 70
      },
      carLTV: {
        newCar: 90,
        usedCar: 70
      },
      creditCardLimitMultiplier: 2
    },
    
    requirements: {
      minAge: 21,
      maxAge: 60,
      minEmploymentMonths: 6,
      requiresPayslip: true,
      requiresEPF: true,
      requiresBankStatement: true
    },
    
    specialFeatures: [
      '对自雇最严格（60%打折）',
      'DSR整体最严（55-60%）',
      '不太接受PR和外国人',
      '较传统的审批'
    ]
  },

  // ===== Hong Leong Bank =====
  {
    bankName: 'Hong Leong Bank',
    bankCode: 'HLB',
    
    dsr: {
      personal: [
        { minNetIncome: 0, maxNetIncome: 3000, dsrLimit: 60 },
        { minNetIncome: 3000, dsrLimit: 80, notes: '高收入最宽松' }
      ],
      housing: [
        { minNetIncome: 0, maxNetIncome: 3000, dsrLimit: 60 },
        { minNetIncome: 3000, dsrLimit: 80 }
      ],
      car: [
        { minNetIncome: 0, maxNetIncome: 3000, dsrLimit: 60 },
        { minNetIncome: 3000, dsrLimit: 80 }
      ],
      credit_card: [
        { minNetIncome: 0, maxNetIncome: 3000, dsrLimit: 60 },
        { minNetIncome: 3000, dsrLimit: 80 }
      ]
    },
    
    incomeRecognition: {
      salaried: {
        employmentType: 'salaried',
        recognitionRate: 1.0,
        requiredDocuments: ['工资单', 'EPF', '银行账单'],
        notes: '标准认可'
      },
      government: {
        employmentType: 'government',
        recognitionRate: 1.0,
        requiredDocuments: ['工资单', 'EPF'],
        notes: '标准认可'
      },
      self_employed: {
        employmentType: 'self_employed',
        recognitionRate: 0.9,
        minBusinessYears: 3,
        requiredDocuments: ['最近1年报税单', '银行流水', 'SSM证书'],
        notes: '取最近1年×90%，最宽松'
      },
      contract: {
        employmentType: 'contract',
        recognitionRate: 0.85,
        requiredDocuments: ['合约书', '工资单'],
        notes: '较友好'
      }
    },
    
    identityConditions: [
      {
        identity: 'malaysian_citizen',
        accepted: true,
        specialNotes: '优先，DSR最宽松'
      },
      {
        identity: 'permanent_resident',
        accepted: true
      },
      {
        identity: 'foreigner',
        accepted: true,
        specialNotes: '某些情况接受（较其他银行更愿意）'
      },
      {
        identity: 'self_employed',
        accepted: true,
        specialNotes: '接受（90%认可，最宽松）'
      }
    ],
    
    loanLimits: {
      personalLoanMax: 250000,
      personalLoanMultiplier: 7,
      housingLTV: {
        firstProperty: 90,
        secondProperty: 90,
        thirdProperty: 70
      },
      carLTV: {
        newCar: 90,
        usedCar: 80
      },
      creditCardLimitMultiplier: 2.5
    },
    
    requirements: {
      minAge: 21,
      maxAge: 60,
      minEmploymentMonths: 6,
      requiresPayslip: true,
      requiresEPF: true,
      requiresBankStatement: true
    },
    
    specialFeatures: [
      '对自雇最宽松（90%认可）',
      'DSR最宽松（80%高收入）',
      '联名房贷50%拆分优势',
      '愿意接受各类身份',
      '最有可能通过的银行'
    ]
  },

  // ===== Public Bank =====
  {
    bankName: 'Public Bank',
    bankCode: 'PBB',
    
    dsr: {
      personal: [
        { minNetIncome: 0, maxNetIncome: 3000, dsrLimit: 60 },
        { minNetIncome: 3000, dsrLimit: 70 }
      ],
      housing: [
        { minNetIncome: 0, maxNetIncome: 3000, dsrLimit: 60 },
        { minNetIncome: 3000, dsrLimit: 70 }
      ],
      car: [
        { minNetIncome: 0, maxNetIncome: 3000, dsrLimit: 60 },
        { minNetIncome: 3000, dsrLimit: 70 }
      ],
      credit_card: [
        { minNetIncome: 0, maxNetIncome: 3000, dsrLimit: 60 },
        { minNetIncome: 3000, dsrLimit: 70 }
      ]
    },
    
    incomeRecognition: {
      salaried: {
        employmentType: 'salaried',
        recognitionRate: 1.0,
        requiredDocuments: ['工资单', 'EPF', '银行账单'],
        notes: '标准认可'
      },
      government: {
        employmentType: 'government',
        recognitionRate: 1.0,
        requiredDocuments: ['工资单', 'EPF'],
        notes: '标准认可'
      },
      self_employed: {
        employmentType: 'self_employed',
        recognitionRate: 0.75,
        minBusinessYears: 3,
        requiredDocuments: ['3年报税单', '审计财报', '银行流水', 'SSM'],
        notes: '中等认可'
      },
      contract: {
        employmentType: 'contract',
        recognitionRate: 0.75,
        requiredDocuments: ['合约书', '工资单'],
        notes: '中等'
      }
    },
    
    identityConditions: [
      {
        identity: 'malaysian_citizen',
        accepted: true
      },
      {
        identity: 'permanent_resident',
        accepted: true,
        specialNotes: '接受，标准流程'
      },
      {
        identity: 'foreigner',
        accepted: false,
        specialNotes: '较少接受'
      },
      {
        identity: 'self_employed',
        accepted: true,
        specialNotes: '中等条件'
      }
    ],
    
    loanLimits: {
      personalLoanMax: 150000,
      personalLoanMultiplier: 8,
      housingLTV: {
        firstProperty: 90,
        secondProperty: 90,
        thirdProperty: 70
      },
      carLTV: {
        newCar: 90,
        usedCar: 75
      },
      creditCardLimitMultiplier: 2
    },
    
    requirements: {
      minAge: 21,
      maxAge: 60,
      minEmploymentMonths: 6,
      requiresPayslip: true,
      requiresEPF: true,
      requiresBankStatement: true
    }
  },

  // ===== HSBC =====
  {
    bankName: 'HSBC Malaysia',
    bankCode: 'HSBC',
    
    dsr: {
      personal: [
        { minNetIncome: 0, maxNetIncome: 3000, dsrLimit: 60 },
        { minNetIncome: 3000, dsrLimit: 70 }
      ],
      housing: [
        { minNetIncome: 0, maxNetIncome: 3000, dsrLimit: 60 },
        { minNetIncome: 3000, dsrLimit: 70 }
      ],
      car: [
        { minNetIncome: 0, maxNetIncome: 3000, dsrLimit: 60 },
        { minNetIncome: 3000, dsrLimit: 70 }
      ],
      credit_card: [
        { minNetIncome: 0, maxNetIncome: 3000, dsrLimit: 60 },
        { minNetIncome: 3000, dsrLimit: 70 }
      ]
    },
    
    incomeRecognition: {
      salaried: {
        employmentType: 'salaried',
        recognitionRate: 1.0,
        requiredDocuments: ['工资单', '银行账单'],
        notes: '国际标准'
      },
      government: {
        employmentType: 'government',
        recognitionRate: 1.0,
        requiredDocuments: ['工资单'],
        notes: '标准认可'
      },
      self_employed: {
        employmentType: 'self_employed',
        recognitionRate: 0.75,
        minBusinessYears: 3,
        requiredDocuments: ['报税单', '审计财报', 'SSM'],
        notes: '国际审核标准'
      },
      contract: {
        employmentType: 'contract',
        recognitionRate: 0.75,
        requiredDocuments: ['合约书', '工资单'],
        notes: '需验证'
      }
    },
    
    identityConditions: [
      {
        identity: 'malaysian_citizen',
        accepted: true
      },
      {
        identity: 'permanent_resident',
        accepted: true,
        specialNotes: '国际银行，对PR友好'
      },
      {
        identity: 'foreigner',
        accepted: true,
        interestRatePremium: 0.5,
        specialNotes: '外国人首选（经验丰富）'
      },
      {
        identity: 'professional',
        accepted: true,
        dsrAdjustment: 5,
        specialNotes: '专业人士优惠'
      }
    ],
    
    loanLimits: {
      personalLoanMax: 200000,
      personalLoanMultiplier: 6,
      housingLTV: {
        firstProperty: 90,
        secondProperty: 85,
        thirdProperty: 70
      },
      carLTV: {
        newCar: 85,
        usedCar: 70
      },
      creditCardLimitMultiplier: 2
    },
    
    requirements: {
      minAge: 21,
      maxAge: 60,
      minEmploymentMonths: 6,
      requiresPayslip: true,
      requiresEPF: false,
      requiresBankStatement: true
    },
    
    specialFeatures: [
      '国际银行标准',
      '对PR和外国人友好',
      '专业人士优惠',
      '外国人首选'
    ]
  },

  // ===== BSN =====
  {
    bankName: 'Bank Simpanan Nasional',
    bankCode: 'BSN',
    
    dsr: {
      personal: [
        { minNetIncome: 0, maxNetIncome: 3000, dsrLimit: 60 },
        { minNetIncome: 3000, dsrLimit: 75 }
      ],
      housing: [
        { minNetIncome: 0, maxNetIncome: 3000, dsrLimit: 60 },
        { minNetIncome: 3000, dsrLimit: 75 }
      ],
      car: [
        { minNetIncome: 0, maxNetIncome: 3000, dsrLimit: 60 },
        { minNetIncome: 3000, dsrLimit: 75 }
      ],
      credit_card: [
        { minNetIncome: 0, maxNetIncome: 3000, dsrLimit: 60 },
        { minNetIncome: 3000, dsrLimit: 75 }
      ]
    },
    
    incomeRecognition: {
      salaried: {
        employmentType: 'salaried',
        recognitionRate: 1.0,
        requiredDocuments: ['工资单', 'EPF', '银行账单'],
        notes: '政府银行标准'
      },
      government: {
        employmentType: 'government',
        recognitionRate: 1.0,
        requiredDocuments: ['工资单', 'EPF'],
        notes: '政府员工优先'
      },
      self_employed: {
        employmentType: 'self_employed',
        recognitionRate: 0.7,
        minBusinessYears: 3,
        requiredDocuments: ['报税单', '银行流水', 'SSM'],
        notes: '较保守'
      },
      contract: {
        employmentType: 'contract',
        recognitionRate: 0.75,
        requiredDocuments: ['合约书', '工资单'],
        notes: '标准'
      }
    },
    
    identityConditions: [
      {
        identity: 'malaysian_citizen',
        accepted: true,
        specialNotes: '政府银行，优先本地人'
      },
      {
        identity: 'government_employee',
        accepted: true,
        dsrAdjustment: 5,
        specialNotes: '政府员工优惠'
      },
      {
        identity: 'permanent_resident',
        accepted: true,
        specialNotes: '接受但需额外审核'
      },
      {
        identity: 'foreigner',
        accepted: false,
        specialNotes: '一般不接受'
      }
    ],
    
    loanLimits: {
      personalLoanMax: 150000,
      personalLoanMultiplier: 6,
      housingLTV: {
        firstProperty: 90,
        secondProperty: 90,
        thirdProperty: 70
      },
      carLTV: {
        newCar: 90,
        usedCar: 75
      },
      creditCardLimitMultiplier: 2
    },
    
    requirements: {
      minAge: 21,
      maxAge: 60,
      minEmploymentMonths: 6,
      requiresPayslip: true,
      requiresEPF: true,
      requiresBankStatement: true
    },
    
    specialFeatures: [
      '政府银行',
      '政府员工优惠',
      '优先本地人'
    ]
  },

  // ===== Bank Islam =====
  {
    bankName: 'Bank Islam Malaysia',
    bankCode: 'BIMB',
    
    dsr: {
      personal: [
        { minNetIncome: 0, maxNetIncome: 3000, dsrLimit: 50 },
        { minNetIncome: 3000, dsrLimit: 70 }
      ],
      housing: [
        { minNetIncome: 0, maxNetIncome: 3000, dsrLimit: 50 },
        { minNetIncome: 3000, dsrLimit: 70 }
      ],
      car: [
        { minNetIncome: 0, maxNetIncome: 3000, dsrLimit: 50 },
        { minNetIncome: 3000, dsrLimit: 70 }
      ],
      credit_card: [
        { minNetIncome: 0, maxNetIncome: 3000, dsrLimit: 50 },
        { minNetIncome: 3000, dsrLimit: 70 }
      ]
    },
    
    incomeRecognition: {
      salaried: {
        employmentType: 'salaried',
        recognitionRate: 1.0,
        requiredDocuments: ['工资单', 'EPF', '银行账单'],
        notes: '伊斯兰标准'
      },
      government: {
        employmentType: 'government',
        recognitionRate: 1.0,
        requiredDocuments: ['工资单', 'EPF'],
        notes: '优先'
      },
      self_employed: {
        employmentType: 'self_employed',
        recognitionRate: 0.7,
        minBusinessYears: 3,
        requiredDocuments: ['报税单', 'SSM', '银行流水'],
        notes: '困难（70%打折）'
      },
      contract: {
        employmentType: 'contract',
        recognitionRate: 0.7,
        requiredDocuments: ['合约书', '工资单'],
        notes: '较严'
      }
    },
    
    identityConditions: [
      {
        identity: 'malaysian_citizen',
        accepted: true,
        specialNotes: '优先'
      },
      {
        identity: 'permanent_resident',
        accepted: true,
        specialNotes: '可能，需确认回教身份'
      },
      {
        identity: 'foreigner',
        accepted: false,
        specialNotes: '通常拒绝'
      },
      {
        identity: 'government_employee',
        accepted: true,
        specialNotes: '优先'
      },
      {
        identity: 'self_employed',
        accepted: true,
        specialNotes: '困难（70%打折）'
      }
    },
    
    loanLimits: {
      personalLoanMax: 150000,
      personalLoanMultiplier: 6,
      housingLTV: {
        firstProperty: 90,
        secondProperty: 90,
        thirdProperty: 70
      },
      carLTV: {
        newCar: 90,
        usedCar: 75
      },
      creditCardLimitMultiplier: 2
    },
    
    requirements: {
      minAge: 21,
      maxAge: 60,
      minEmploymentMonths: 6,
      requiresPayslip: true,
      requiresEPF: true,
      requiresBankStatement: true
    },
    
    specialFeatures: [
      '伊斯兰银行',
      '偏好马来西亚人和穆斯林',
      'DSR相对严格（50-70%）',
      'Shariah产品'
    ]
  }
];

// ============= 辅助函数 =============

/**
 * 获取银行标准
 */
export function getBankStandardReal(identifier: string): BankStandardReal | undefined {
  return bankStandardsReal2025.find(
    bank => bank.bankCode === identifier || bank.bankName === identifier
  );
}

/**
 * 获取DSR限制
 */
export function getDSRLimit(
  bankCode: string,
  loanType: LoanType,
  netIncome: number
): number {
  const bank = getBankStandardReal(bankCode);
  if (!bank) return 0;

  const limits = bank.dsr[loanType];
  for (const limit of limits) {
    if (netIncome >= limit.minNetIncome && 
        (limit.maxNetIncome === undefined || netIncome < limit.maxNetIncome)) {
      return limit.dsrLimit;
    }
  }
  
  // 返回最后一个限制（通常是最高收入的限制）
  return limits[limits.length - 1].dsrLimit;
}

/**
 * 计算认定收入
 */
export function calculateRecognizedIncome(
  bankCode: string,
  grossIncome: number,
  employmentType: EmploymentType,
  businessYears?: number
): {
  recognizedIncome: number;
  recognitionRate: number;
  notes: string;
} {
  const bank = getBankStandardReal(bankCode);
  if (!bank) {
    return { recognizedIncome: 0, recognitionRate: 0, notes: '银行未找到' };
  }

  const rule = bank.incomeRecognition[employmentType];
  
  // 检查自雇年限
  if (employmentType === 'self_employed') {
    if (!businessYears || businessYears < (rule.minBusinessYears || 2)) {
      return {
        recognizedIncome: 0,
        recognitionRate: 0,
        notes: `需要至少${rule.minBusinessYears || 2}年营业记录`
      };
    }
  }

  const recognizedIncome = grossIncome * rule.recognitionRate;
  
  return {
    recognizedIncome,
    recognitionRate: rule.recognitionRate,
    notes: rule.notes
  };
}

/**
 * 检查身份资格
 */
export function checkIdentityEligibility(
  bankCode: string,
  identity: ApplicantIdentity
): {
  accepted: boolean;
  conditions?: IdentityCondition;
  message: string;
} {
  const bank = getBankStandardReal(bankCode);
  if (!bank) {
    return { accepted: false, message: '银行未找到' };
  }

  const condition = bank.identityConditions.find(ic => ic.identity === identity);
  
  if (!condition) {
    return { accepted: true, message: '无特殊限制' };
  }

  if (!condition.accepted) {
    return {
      accepted: false,
      conditions: condition,
      message: condition.specialNotes || '此身份不被接受'
    };
  }

  return {
    accepted: true,
    conditions: condition,
    message: condition.specialNotes || '接受'
  };
}

/**
 * 计算DSR
 */
export function calculateDSR(
  monthlyCommitment: number,
  monthlyNetIncome: number
): number {
  if (monthlyNetIncome <= 0) return 100;
  return (monthlyCommitment / monthlyNetIncome) * 100;
}

/**
 * 检查DSR是否符合要求
 */
export function checkDSRRequirement(
  bankCode: string,
  loanType: LoanType,
  netIncome: number,
  totalCommitment: number
): {
  passes: boolean;
  dsr: number;
  dsrLimit: number;
  message: string;
} {
  const dsr = calculateDSR(totalCommitment, netIncome);
  const dsrLimit = getDSRLimit(bankCode, loanType, netIncome);

  const passes = dsr <= dsrLimit;

  return {
    passes,
    dsr,
    dsrLimit,
    message: passes
      ? `DSR ${dsr.toFixed(2)}% 符合 ${dsrLimit}% 限制`
      : `DSR ${dsr.toFixed(2)}% 超过 ${dsrLimit}% 限制`
  };
}

/**
 * 获取推荐银行（根据身份和收入）
 */
export function getRecommendedBanks(
  identity: ApplicantIdentity,
  employmentType: EmploymentType,
  netIncome: number,
  loanType: LoanType = 'personal'
): Array<{
  bank: BankStandardReal;
  score: number;
  reasons: string[];
}> {
  const recommendations: Array<{
    bank: BankStandardReal;
    score: number;
    reasons: string[];
  }> = [];

  for (const bank of bankStandardsReal2025) {
    let score = 50;
    const reasons: string[] = [];

    // 检查身份资格
    const eligibility = checkIdentityEligibility(bank.bankCode, identity);
    if (!eligibility.accepted) {
      continue; // 跳过不接受此身份的银行
    }

    // DSR宽松度
    const dsrLimit = getDSRLimit(bank.bankCode, loanType, netIncome);
    score += dsrLimit * 0.5; // DSR越高分数越高
    reasons.push(`DSR限制: ${dsrLimit}%`);

    // 收入认定率
    const incomeRecognition = bank.incomeRecognition[employmentType];
    score += incomeRecognition.recognitionRate * 30;
    reasons.push(`收入认定: ${(incomeRecognition.recognitionRate * 100).toFixed(0)}%`);

    // 身份优势
    if (eligibility.conditions?.dsrAdjustment) {
      score += eligibility.conditions.dsrAdjustment;
      reasons.push(`DSR调整: +${eligibility.conditions.dsrAdjustment}%`);
    }

    // 特殊功能加分
    if (bank.specialFeatures && bank.specialFeatures.length > 0) {
      score += bank.specialFeatures.length * 2;
    }

    recommendations.push({ bank, score, reasons });
  }

  // 按分数排序
  return recommendations.sort((a, b) => b.score - a.score);
}

export default bankStandardsReal2025;
