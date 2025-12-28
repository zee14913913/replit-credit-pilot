/**
 * 马来西亚各大银行贷款批准标准 - 2025年真实数据
 * Bank Loan Approval Standards in Malaysia - 2025 Real Data
 * 
 * 数据来源:
 * - Direct Lending (2024)
 * - iProperty.com.my (2023)
 * - iMoney.my (2021-2024)
 * - 各银行官方网站
 * 
 * 更新日期: 2025-12-28
 */

export interface BankStandard {
  bankName: string;
  bankCode: string;
  
  // 计算基础 (Net Salary 或 Gross Salary)
  incomeCalculationBase: 'net' | 'gross';
  
  // DSR要求 (根据收入水平分层)
  dsr: {
    lowIncome: {
      threshold: number;  // 收入门槛 (RM)
      maxDSR: number;     // 最高DSR百分比
    };
    highIncome: {
      threshold: number;
      maxDSR: number;
    };
  };
  
  // 最低收入要求
  minIncome: {
    personalLoan: number;       // 个人贷款最低月收入 (RM)
    mortgage: number;            // 房屋贷款最低月收入 (RM)
    creditCardBasic: number;     // 基础信用卡最低年收入 (RM)
    creditCardPlatinum: number;  // 白金信用卡最低年收入 (RM)
  };
  
  // 贷款限额
  loanLimits: {
    personalLoanMax: number;           // 个人贷款最高额 (RM)
    personalLoanIncomeMultiplier: number; // 个人贷款收入倍数
    mortgageMaxLTV: number;            // 房贷最高LTV百分比
    creditCardIncomeMultiplier: number; // 信用卡额度收入倍数
  };
  
  // 利率范围
  interestRates: {
    personalLoanMin: number;   // 个人贷款最低利率 (% p.a.)
    personalLoanMax: number;   // 个人贷款最高利率 (% p.a.)
    mortgageMin: number;       // 房贷最低利率 (% p.a.)
    mortgageMax: number;       // 房贷最高利率 (% p.a.)
  };
  
  // 其他要求
  requirements: {
    minAge: number;
    maxAge: number;
    minEmploymentMonths: number;
    selfEmployedMinMonths: number; // 自雇人士最低经营月数
  };
  
  // 特殊政策
  specialPolicies?: {
    recognizesRentalIncome?: number;    // 租金收入识别百分比 (%)
    recognizesForeignIncome?: number;   // 外国收入识别百分比 (%)
    fastApproval?: boolean;             // 是否提供快速批准
    approvalDays?: number;              // 批准天数
  };
}

export const bankStandards2025: BankStandard[] = [
  {
    bankName: "Maybank",
    bankCode: "MBB",
    incomeCalculationBase: 'net',
    dsr: {
      lowIncome: {
        threshold: 3499,
        maxDSR: 40  // 低收入者DSR限制严格
      },
      highIncome: {
        threshold: 3500,
        maxDSR: 70  // 高收入者DSR宽松
      }
    },
    minIncome: {
      personalLoan: 2000,
      mortgage: 3000,
      creditCardBasic: 24000,
      creditCardPlatinum: 60000
    },
    loanLimits: {
      personalLoanMax: 100000,
      personalLoanIncomeMultiplier: 5,  // 保守估计
      mortgageMaxLTV: 90,
      creditCardIncomeMultiplier: 2
    },
    interestRates: {
      personalLoanMin: 6.5,
      personalLoanMax: 8.0,
      mortgageMin: 2.0,
      mortgageMax: 4.0
    },
    requirements: {
      minAge: 21,
      maxAge: 60,
      minEmploymentMonths: 6,
      selfEmployedMinMonths: 24
    }
  },
  
  {
    bankName: "CIMB Bank",
    bankCode: "CIMB",
    incomeCalculationBase: 'net',
    dsr: {
      lowIncome: {
        threshold: 2999,
        maxDSR: 65
      },
      highIncome: {
        threshold: 3000,
        maxDSR: 75  // 最高DSR限额之一
      }
    },
    minIncome: {
      personalLoan: 2000,
      mortgage: 3000,
      creditCardBasic: 24000,
      creditCardPlatinum: 60000
    },
    loanLimits: {
      personalLoanMax: 100000,
      personalLoanIncomeMultiplier: 8,  // 8倍月薪
      mortgageMaxLTV: 90,
      creditCardIncomeMultiplier: 2.5
    },
    interestRates: {
      personalLoanMin: 6.88,
      personalLoanMax: 14.88,
      mortgageMin: 2.0,
      mortgageMax: 4.0
    },
    requirements: {
      minAge: 21,
      maxAge: 58,
      minEmploymentMonths: 6,
      selfEmployedMinMonths: 24
    },
    specialPolicies: {
      recognizesRentalIncome: 100,  // 认可100%租金收入
      fastApproval: true,
      approvalDays: 1  // 1个工作日批准
    }
  },
  
  {
    bankName: "Public Bank",
    bankCode: "PBB",
    incomeCalculationBase: 'net',
    dsr: {
      lowIncome: {
        threshold: 2999,
        maxDSR: 60
      },
      highIncome: {
        threshold: 3000,
        maxDSR: 70
      }
    },
    minIncome: {
      personalLoan: 2000,
      mortgage: 3000,
      creditCardBasic: 24000,
      creditCardPlatinum: 60000
    },
    loanLimits: {
      personalLoanMax: 150000,
      personalLoanIncomeMultiplier: 6,
      mortgageMaxLTV: 90,
      creditCardIncomeMultiplier: 2
    },
    interestRates: {
      personalLoanMin: 5.5,
      personalLoanMax: 10.0,
      mortgageMin: 2.0,
      mortgageMax: 4.0
    },
    requirements: {
      minAge: 21,
      maxAge: 60,
      minEmploymentMonths: 6,
      selfEmployedMinMonths: 24
    },
    specialPolicies: {
      recognizesRentalIncome: 80  // 只认可80%租金收入
    }
  },
  
  {
    bankName: "Hong Leong Bank",
    bankCode: "HLB",
    incomeCalculationBase: 'net',
    dsr: {
      lowIncome: {
        threshold: 2999,
        maxDSR: 60
      },
      highIncome: {
        threshold: 3000,
        maxDSR: 80  // 最高DSR限额
      }
    },
    minIncome: {
      personalLoan: 2000,
      mortgage: 3000,
      creditCardBasic: 24000,
      creditCardPlatinum: 60000
    },
    loanLimits: {
      personalLoanMax: 250000,  // 最高限额之一
      personalLoanIncomeMultiplier: 7,
      mortgageMaxLTV: 90,
      creditCardIncomeMultiplier: 2
    },
    interestRates: {
      personalLoanMin: 5.5,
      personalLoanMax: 12.0,
      mortgageMin: 2.0,
      mortgageMax: 4.0
    },
    requirements: {
      minAge: 21,
      maxAge: 60,
      minEmploymentMonths: 6,
      selfEmployedMinMonths: 24
    },
    specialPolicies: {
      recognizesForeignIncome: 100  // 认可100%外国收入
    }
  },
  
  {
    bankName: "RHB Bank",
    bankCode: "RHB",
    incomeCalculationBase: 'net',
    dsr: {
      lowIncome: {
        threshold: 2204,
        maxDSR: 55  // 较保守
      },
      highIncome: {
        threshold: 2205,
        maxDSR: 60
      }
    },
    minIncome: {
      personalLoan: 2000,
      mortgage: 3000,
      creditCardBasic: 24000,
      creditCardPlatinum: 60000
    },
    loanLimits: {
      personalLoanMax: 150000,
      personalLoanIncomeMultiplier: 5,
      mortgageMaxLTV: 90,
      creditCardIncomeMultiplier: 2
    },
    interestRates: {
      personalLoanMin: 6.0,
      personalLoanMax: 12.0,
      mortgageMin: 2.0,
      mortgageMax: 4.0
    },
    requirements: {
      minAge: 21,
      maxAge: 60,
      minEmploymentMonths: 6,
      selfEmployedMinMonths: 24
    },
    specialPolicies: {
      recognizesForeignIncome: 45  // 只认可45%外国收入
    }
  },
  
  {
    bankName: "AmBank",
    bankCode: "AMB",
    incomeCalculationBase: 'net',
    dsr: {
      lowIncome: {
        threshold: 2999,
        maxDSR: 60
      },
      highIncome: {
        threshold: 3000,
        maxDSR: 70
      }
    },
    minIncome: {
      personalLoan: 2000,
      mortgage: 3000,
      creditCardBasic: 24000,
      creditCardPlatinum: 60000
    },
    loanLimits: {
      personalLoanMax: 150000,
      personalLoanIncomeMultiplier: 6,
      mortgageMaxLTV: 90,
      creditCardIncomeMultiplier: 2
    },
    interestRates: {
      personalLoanMin: 6.0,
      personalLoanMax: 12.0,
      mortgageMin: 2.0,
      mortgageMax: 4.0
    },
    requirements: {
      minAge: 21,
      maxAge: 60,
      minEmploymentMonths: 6,
      selfEmployedMinMonths: 24
    }
  },
  
  {
    bankName: "Affin Bank",
    bankCode: "AFFIN",
    incomeCalculationBase: 'gross',  // 使用总收入
    dsr: {
      lowIncome: {
        threshold: 4999,
        maxDSR: 60
      },
      highIncome: {
        threshold: 5000,
        maxDSR: 80
      }
    },
    minIncome: {
      personalLoan: 2000,
      mortgage: 3000,
      creditCardBasic: 24000,
      creditCardPlatinum: 60000
    },
    loanLimits: {
      personalLoanMax: 150000,
      personalLoanIncomeMultiplier: 6,
      mortgageMaxLTV: 90,
      creditCardIncomeMultiplier: 2
    },
    interestRates: {
      personalLoanMin: 6.0,
      personalLoanMax: 12.0,
      mortgageMin: 2.0,
      mortgageMax: 4.0
    },
    requirements: {
      minAge: 21,
      maxAge: 60,
      minEmploymentMonths: 6,
      selfEmployedMinMonths: 24
    }
  },
  
  {
    bankName: "Bank Islam",
    bankCode: "BANK_ISLAM",
    incomeCalculationBase: 'gross',  // 使用总收入
    dsr: {
      lowIncome: {
        threshold: 2999,
        maxDSR: 50  // 伊斯兰银行较保守
      },
      highIncome: {
        threshold: 3000,
        maxDSR: 70
      }
    },
    minIncome: {
      personalLoan: 2000,
      mortgage: 3000,
      creditCardBasic: 24000,
      creditCardPlatinum: 60000
    },
    loanLimits: {
      personalLoanMax: 150000,
      personalLoanIncomeMultiplier: 5,
      mortgageMaxLTV: 90,
      creditCardIncomeMultiplier: 2
    },
    interestRates: {
      personalLoanMin: 5.0,
      personalLoanMax: 10.0,
      mortgageMin: 2.0,
      mortgageMax: 4.0
    },
    requirements: {
      minAge: 21,
      maxAge: 60,
      minEmploymentMonths: 6,
      selfEmployedMinMonths: 24
    }
  },
  
  {
    bankName: "Bank Rakyat",
    bankCode: "B_RAKYAT",
    incomeCalculationBase: 'net',
    dsr: {
      lowIncome: {
        threshold: 2999,
        maxDSR: 60
      },
      highIncome: {
        threshold: 3000,
        maxDSR: 70
      }
    },
    minIncome: {
      personalLoan: 2000,
      mortgage: 3000,
      creditCardBasic: 24000,
      creditCardPlatinum: 60000
    },
    loanLimits: {
      personalLoanMax: 400000,  // 最高限额（薪水转账）
      personalLoanIncomeMultiplier: 10,  // 10倍月薪！
      mortgageMaxLTV: 90,
      creditCardIncomeMultiplier: 2
    },
    interestRates: {
      personalLoanMin: 4.0,
      personalLoanMax: 10.0,
      mortgageMin: 2.0,
      mortgageMax: 4.0
    },
    requirements: {
      minAge: 21,
      maxAge: 60,
      minEmploymentMonths: 6,
      selfEmployedMinMonths: 24
    }
  },
  
  {
    bankName: "HSBC Bank",
    bankCode: "HSBC",
    incomeCalculationBase: 'net',
    dsr: {
      lowIncome: {
        threshold: 2999,
        maxDSR: 60
      },
      highIncome: {
        threshold: 3000,
        maxDSR: 70
      }
    },
    minIncome: {
      personalLoan: 2500,  // 较高要求
      mortgage: 3500,
      creditCardBasic: 30000,
      creditCardPlatinum: 102000
    },
    loanLimits: {
      personalLoanMax: 200000,
      personalLoanIncomeMultiplier: 7,
      mortgageMaxLTV: 90,
      creditCardIncomeMultiplier: 2.5
    },
    interestRates: {
      personalLoanMin: 6.0,
      personalLoanMax: 14.0,
      mortgageMin: 2.0,
      mortgageMax: 4.0
    },
    requirements: {
      minAge: 21,
      maxAge: 60,
      minEmploymentMonths: 6,
      selfEmployedMinMonths: 24
    },
    specialPolicies: {
      recognizesRentalIncome: 100
    }
  },
  
  {
    bankName: "BSN Bank",
    bankCode: "BSN",
    incomeCalculationBase: 'net',
    dsr: {
      lowIncome: {
        threshold: 2999,
        maxDSR: 60
      },
      highIncome: {
        threshold: 3000,
        maxDSR: 75
      }
    },
    minIncome: {
      personalLoan: 1500,  // 较低门槛
      mortgage: 2500,
      creditCardBasic: 18000,
      creditCardPlatinum: 36000
    },
    loanLimits: {
      personalLoanMax: 100000,
      personalLoanIncomeMultiplier: 10,  // 10倍月薪
      mortgageMaxLTV: 90,
      creditCardIncomeMultiplier: 2
    },
    interestRates: {
      personalLoanMin: 5.0,
      personalLoanMax: 12.0,
      mortgageMin: 2.0,
      mortgageMax: 4.0
    },
    requirements: {
      minAge: 21,
      maxAge: 60,
      minEmploymentMonths: 6,
      selfEmployedMinMonths: 24
    }
  }
];

/**
 * 根据净收入计算最大DSR
 */
export function getMaxDSR(bank: BankStandard, netIncome: number): number {
  if (netIncome < bank.dsr.lowIncome.threshold) {
    return bank.dsr.lowIncome.maxDSR;
  }
  return bank.dsr.highIncome.maxDSR;
}

/**
 * 计算DSR (Debt Service Ratio)
 */
export function calculateDSR(monthlyCommitment: number, monthlyIncome: number): number {
  if (monthlyIncome <= 0) return 0;
  return (monthlyCommitment / monthlyIncome) * 100;
}

/**
 * 计算净收入 (估算：总收入的85%)
 */
export function calculateNetIncome(grossIncome: number): number {
  return grossIncome * 0.85;  // 扣除EPF (11%), SOCSO (0.5%), 税务 (约3.5%)
}

/**
 * 根据DSR计算最大贷款额
 */
export function calculateMaxLoanByDSR(
  monthlyIncome: number,
  monthlyCommitment: number,
  bank: BankStandard,
  loanTenureMonths: number = 60
): number {
  // 1. 计算净收入（如果银行使用净收入）
  const income = bank.incomeCalculationBase === 'net' 
    ? calculateNetIncome(monthlyIncome) 
    : monthlyIncome;
  
  // 2. 获取最大DSR限额
  const maxDSR = getMaxDSR(bank, income);
  
  // 3. 计算可用于还款的最大月供
  const maxMonthlyPayment = (income * maxDSR / 100) - monthlyCommitment;
  
  if (maxMonthlyPayment <= 0) return 0;
  
  // 4. 使用平均利率计算贷款额
  const avgRate = (bank.interestRates.personalLoanMin + bank.interestRates.personalLoanMax) / 2;
  const monthlyRate = avgRate / 100 / 12;
  
  // PMT公式反算：P = PMT * ((1 - (1 + r)^-n) / r)
  const maxLoan = maxMonthlyPayment * ((1 - Math.pow(1 + monthlyRate, -loanTenureMonths)) / monthlyRate);
  
  return maxLoan;
}

/**
 * 根据收入倍数计算最大贷款额
 */
export function calculateMaxLoanByMultiplier(
  monthlyIncome: number,
  bank: BankStandard
): number {
  return monthlyIncome * bank.loanLimits.personalLoanIncomeMultiplier;
}

/**
 * 计算最终最大贷款额（取DSR和收入倍数的较小值）
 */
export function calculateFinalMaxLoan(
  monthlyIncome: number,
  monthlyCommitment: number,
  bank: BankStandard,
  loanTenureMonths: number = 60
): number {
  const loanByDSR = calculateMaxLoanByDSR(monthlyIncome, monthlyCommitment, bank, loanTenureMonths);
  const loanByMultiplier = calculateMaxLoanByMultiplier(monthlyIncome, bank);
  const finalLoan = Math.min(loanByDSR, loanByMultiplier, bank.loanLimits.personalLoanMax);
  
  return Math.max(0, finalLoan);
}

/**
 * 计算月供
 */
export function calculateMonthlyPayment(
  loanAmount: number,
  annualInterestRate: number,
  tenureMonths: number
): number {
  const monthlyRate = annualInterestRate / 100 / 12;
  const payment = loanAmount * (monthlyRate * Math.pow(1 + monthlyRate, tenureMonths)) / 
                 (Math.pow(1 + monthlyRate, tenureMonths) - 1);
  
  return payment;
}

/**
 * 获取银行标准（通过银行名或代码）
 */
export function getBankStandard2025(identifier: string): BankStandard | undefined {
  return bankStandards2025.find(
    bank => bank.bankName.toLowerCase() === identifier.toLowerCase() ||
            bank.bankCode.toLowerCase() === identifier.toLowerCase()
  );
}
