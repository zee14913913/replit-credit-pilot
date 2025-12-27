/**
 * 马来西亚各大银行贷款批准标准
 * Bank Loan Approval Standards in Malaysia
 */

export interface BankStandard {
  bankName: string;
  bankCode: string;
  
  // DSR Requirements
  dsr: {
    personalLoan: number;      // Personal loan DSR limit (%)
    mortgage: number;           // Home loan DSR limit (%)
    creditCard: number;         // Credit card DSR limit (%)
    businessLoan: number;       // Business loan DSR limit (%)
  };
  
  // Income Requirements
  minIncome: {
    creditCardBasic: number;    // Minimum annual income for basic credit card (RM)
    creditCardGold: number;     // Minimum annual income for gold card (RM)
    creditCardPlatinum: number; // Minimum annual income for platinum card (RM)
    creditCardInfinite: number; // Minimum annual income for infinite/world card (RM)
    personalLoan: number;       // Minimum monthly income for personal loan (RM)
    mortgage: number;           // Minimum monthly income for mortgage (RM)
    businessLoan: number;       // Minimum annual revenue for business loan (RM)
  };
  
  // Loan Limits
  loanLimits: {
    personalLoanMax: number;    // Maximum personal loan amount (RM)
    personalLoanMultiplier: number; // Personal loan as multiple of monthly income
    mortgageMaxPercentage: number;  // Maximum mortgage percentage of property value (%)
    creditCardLimitMultiplier: number; // Credit card limit as multiple of monthly income
  };
  
  // Additional Requirements
  requirements: {
    minAge: number;             // Minimum age
    maxAge: number;             // Maximum age
    minEmploymentMonths: number; // Minimum employment duration (months)
    requiresPayslip: boolean;   // Requires payslip
    requiresEPF: boolean;       // Requires EPF statement
    requiresBankStatement: boolean; // Requires bank statement
  };
}

export const bankStandards: BankStandard[] = [
  {
    bankName: "Maybank",
    bankCode: "MBB",
    dsr: {
      personalLoan: 60,
      mortgage: 70,
      creditCard: 60,
      businessLoan: 60
    },
    minIncome: {
      creditCardBasic: 24000,
      creditCardGold: 36000,
      creditCardPlatinum: 60000,
      creditCardInfinite: 100000,
      personalLoan: 2000,
      mortgage: 3000,
      businessLoan: 500000
    },
    loanLimits: {
      personalLoanMax: 150000,
      personalLoanMultiplier: 10,
      mortgageMaxPercentage: 90,
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
  {
    bankName: "CIMB Bank",
    bankCode: "CIMB",
    dsr: {
      personalLoan: 60,
      mortgage: 70,
      creditCard: 60,
      businessLoan: 60
    },
    minIncome: {
      creditCardBasic: 24000,
      creditCardGold: 36000,
      creditCardPlatinum: 60000,
      creditCardInfinite: 100000,
      personalLoan: 2000,
      mortgage: 3000,
      businessLoan: 500000
    },
    loanLimits: {
      personalLoanMax: 200000,
      personalLoanMultiplier: 12,
      mortgageMaxPercentage: 90,
      creditCardLimitMultiplier: 2.5
    },
    requirements: {
      minAge: 21,
      maxAge: 65,
      minEmploymentMonths: 6,
      requiresPayslip: true,
      requiresEPF: true,
      requiresBankStatement: true
    }
  },
  {
    bankName: "Public Bank",
    bankCode: "PBB",
    dsr: {
      personalLoan: 60,
      mortgage: 70,
      creditCard: 60,
      businessLoan: 60
    },
    minIncome: {
      creditCardBasic: 24000,
      creditCardGold: 36000,
      creditCardPlatinum: 60000,
      creditCardInfinite: 100000,
      personalLoan: 2000,
      mortgage: 3000,
      businessLoan: 500000
    },
    loanLimits: {
      personalLoanMax: 150000,
      personalLoanMultiplier: 10,
      mortgageMaxPercentage: 90,
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
  {
    bankName: "Hong Leong Bank",
    bankCode: "HLB",
    dsr: {
      personalLoan: 60,
      mortgage: 70,
      creditCard: 60,
      businessLoan: 60
    },
    minIncome: {
      creditCardBasic: 24000,
      creditCardGold: 36000,
      creditCardPlatinum: 60000,
      creditCardInfinite: 100000,
      personalLoan: 2000,
      mortgage: 3000,
      businessLoan: 500000
    },
    loanLimits: {
      personalLoanMax: 150000,
      personalLoanMultiplier: 10,
      mortgageMaxPercentage: 90,
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
  {
    bankName: "RHB Bank",
    bankCode: "RHB",
    dsr: {
      personalLoan: 60,
      mortgage: 70,
      creditCard: 60,
      businessLoan: 60
    },
    minIncome: {
      creditCardBasic: 24000,
      creditCardGold: 36000,
      creditCardPlatinum: 60000,
      creditCardInfinite: 100000,
      personalLoan: 2000,
      mortgage: 3000,
      businessLoan: 500000
    },
    loanLimits: {
      personalLoanMax: 150000,
      personalLoanMultiplier: 10,
      mortgageMaxPercentage: 90,
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
  {
    bankName: "AmBank",
    bankCode: "AMB",
    dsr: {
      personalLoan: 60,
      mortgage: 70,
      creditCard: 60,
      businessLoan: 60
    },
    minIncome: {
      creditCardBasic: 24000,
      creditCardGold: 36000,
      creditCardPlatinum: 60000,
      creditCardInfinite: 100000,
      personalLoan: 2000,
      mortgage: 3000,
      businessLoan: 500000
    },
    loanLimits: {
      personalLoanMax: 150000,
      personalLoanMultiplier: 10,
      mortgageMaxPercentage: 90,
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
  {
    bankName: "Affin Bank",
    bankCode: "AFFIN",
    dsr: {
      personalLoan: 60,
      mortgage: 70,
      creditCard: 60,
      businessLoan: 60
    },
    minIncome: {
      creditCardBasic: 24000,
      creditCardGold: 36000,
      creditCardPlatinum: 60000,
      creditCardInfinite: 100000,
      personalLoan: 2000,
      mortgage: 3000,
      businessLoan: 500000
    },
    loanLimits: {
      personalLoanMax: 150000,
      personalLoanMultiplier: 10,
      mortgageMaxPercentage: 90,
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
  {
    bankName: "Bank Islam",
    bankCode: "BANK_ISLAM",
    dsr: {
      personalLoan: 60,
      mortgage: 70,
      creditCard: 60,
      businessLoan: 60
    },
    minIncome: {
      creditCardBasic: 24000,
      creditCardGold: 36000,
      creditCardPlatinum: 60000,
      creditCardInfinite: 100000,
      personalLoan: 2000,
      mortgage: 3000,
      businessLoan: 500000
    },
    loanLimits: {
      personalLoanMax: 150000,
      personalLoanMultiplier: 10,
      mortgageMaxPercentage: 90,
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
  {
    bankName: "Bank Rakyat",
    bankCode: "B_RAKYAT",
    dsr: {
      personalLoan: 60,
      mortgage: 70,
      creditCard: 60,
      businessLoan: 60
    },
    minIncome: {
      creditCardBasic: 24000,
      creditCardGold: 36000,
      creditCardPlatinum: 60000,
      creditCardInfinite: 100000,
      personalLoan: 2000,
      mortgage: 3000,
      businessLoan: 500000
    },
    loanLimits: {
      personalLoanMax: 150000,
      personalLoanMultiplier: 10,
      mortgageMaxPercentage: 90,
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
  {
    bankName: "HSBC Bank",
    bankCode: "HSBC",
    dsr: {
      personalLoan: 60,
      mortgage: 70,
      creditCard: 60,
      businessLoan: 60
    },
    minIncome: {
      creditCardBasic: 30000,
      creditCardGold: 50000,
      creditCardPlatinum: 102000,
      creditCardInfinite: 150000,
      personalLoan: 2500,
      mortgage: 3500,
      businessLoan: 1000000
    },
    loanLimits: {
      personalLoanMax: 200000,
      personalLoanMultiplier: 12,
      mortgageMaxPercentage: 90,
      creditCardLimitMultiplier: 2.5
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
  {
    bankName: "Standard Chartered Bank",
    bankCode: "SCB",
    dsr: {
      personalLoan: 60,
      mortgage: 70,
      creditCard: 60,
      businessLoan: 60
    },
    minIncome: {
      creditCardBasic: 30000,
      creditCardGold: 50000,
      creditCardPlatinum: 90000,
      creditCardInfinite: 150000,
      personalLoan: 2500,
      mortgage: 3500,
      businessLoan: 1000000
    },
    loanLimits: {
      personalLoanMax: 200000,
      personalLoanMultiplier: 12,
      mortgageMaxPercentage: 90,
      creditCardLimitMultiplier: 2.5
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
  {
    bankName: "UOB Bank",
    bankCode: "UOB",
    dsr: {
      personalLoan: 60,
      mortgage: 70,
      creditCard: 60,
      businessLoan: 60
    },
    minIncome: {
      creditCardBasic: 24000,
      creditCardGold: 36000,
      creditCardPlatinum: 60000,
      creditCardInfinite: 100000,
      personalLoan: 2000,
      mortgage: 3000,
      businessLoan: 500000
    },
    loanLimits: {
      personalLoanMax: 150000,
      personalLoanMultiplier: 10,
      mortgageMaxPercentage: 90,
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
  {
    bankName: "OCBC Bank",
    bankCode: "OCBC",
    dsr: {
      personalLoan: 60,
      mortgage: 70,
      creditCard: 60,
      businessLoan: 60
    },
    minIncome: {
      creditCardBasic: 24000,
      creditCardGold: 36000,
      creditCardPlatinum: 60000,
      creditCardInfinite: 100000,
      personalLoan: 2000,
      mortgage: 3000,
      businessLoan: 500000
    },
    loanLimits: {
      personalLoanMax: 150000,
      personalLoanMultiplier: 10,
      mortgageMaxPercentage: 90,
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
  {
    bankName: "Citibank",
    bankCode: "CITI",
    dsr: {
      personalLoan: 60,
      mortgage: 70,
      creditCard: 60,
      businessLoan: 60
    },
    minIncome: {
      creditCardBasic: 30000,
      creditCardGold: 50000,
      creditCardPlatinum: 90000,
      creditCardInfinite: 150000,
      personalLoan: 2500,
      mortgage: 3500,
      businessLoan: 1000000
    },
    loanLimits: {
      personalLoanMax: 200000,
      personalLoanMultiplier: 12,
      mortgageMaxPercentage: 90,
      creditCardLimitMultiplier: 2.5
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
  {
    bankName: "BSN Bank",
    bankCode: "BSN",
    dsr: {
      personalLoan: 60,
      mortgage: 70,
      creditCard: 60,
      businessLoan: 60
    },
    minIncome: {
      creditCardBasic: 18000,
      creditCardGold: 24000,
      creditCardPlatinum: 36000,
      creditCardInfinite: 60000,
      personalLoan: 1500,
      mortgage: 2500,
      businessLoan: 300000
    },
    loanLimits: {
      personalLoanMax: 100000,
      personalLoanMultiplier: 8,
      mortgageMaxPercentage: 90,
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
  {
    bankName: "AEON Credit",
    bankCode: "AEON",
    dsr: {
      personalLoan: 60,
      mortgage: 70,
      creditCard: 60,
      businessLoan: 60
    },
    minIncome: {
      creditCardBasic: 18000,
      creditCardGold: 24000,
      creditCardPlatinum: 36000,
      creditCardInfinite: 60000,
      personalLoan: 1500,
      mortgage: 0,  // AEON doesn't offer mortgage
      businessLoan: 0  // AEON doesn't offer business loan
    },
    loanLimits: {
      personalLoanMax: 50000,
      personalLoanMultiplier: 5,
      mortgageMaxPercentage: 0,
      creditCardLimitMultiplier: 1.5
    },
    requirements: {
      minAge: 21,
      maxAge: 60,
      minEmploymentMonths: 3,
      requiresPayslip: true,
      requiresEPF: false,
      requiresBankStatement: false
    }
  }
];

/**
 * Get bank standard by bank name or code
 */
export function getBankStandard(identifier: string): BankStandard | undefined {
  return bankStandards.find(
    bank => bank.bankName.toLowerCase() === identifier.toLowerCase() ||
            bank.bankCode.toLowerCase() === identifier.toLowerCase()
  );
}

/**
 * Calculate DSR (Debt Service Ratio)
 */
export function calculateDSR(monthlyCommitment: number, monthlyIncome: number): number {
  if (monthlyIncome <= 0) return 0;
  return (monthlyCommitment / monthlyIncome) * 100;
}

/**
 * Check if customer meets DSR requirement for a specific product type
 */
export function checkDSRRequirement(
  monthlyCommitment: number,
  monthlyIncome: number,
  productType: 'personalLoan' | 'mortgage' | 'creditCard' | 'businessLoan',
  bankStandard: BankStandard
): { eligible: boolean; dsr: number; maxDSR: number } {
  const dsr = calculateDSR(monthlyCommitment, monthlyIncome);
  const maxDSR = bankStandard.dsr[productType];
  
  return {
    eligible: dsr <= maxDSR,
    dsr: Number(dsr.toFixed(2)),
    maxDSR
  };
}

/**
 * Calculate maximum loan amount based on DSR
 */
export function calculateMaxLoanAmount(
  monthlyIncome: number,
  monthlyCommitment: number,
  productType: 'personalLoan' | 'mortgage',
  bankStandard: BankStandard,
  interestRate: number,  // Annual interest rate (%)
  tenureMonths: number   // Loan tenure in months
): number {
  const maxDSR = bankStandard.dsr[productType];
  const maxMonthlyPayment = (monthlyIncome * (maxDSR / 100)) - monthlyCommitment;
  
  if (maxMonthlyPayment <= 0) return 0;
  
  // Calculate max loan using PMT formula: P = PMT * ((1 - (1 + r)^-n) / r)
  const monthlyRate = interestRate / 100 / 12;
  const maxLoan = maxMonthlyPayment * ((1 - Math.pow(1 + monthlyRate, -tenureMonths)) / monthlyRate);
  
  return Math.max(0, maxLoan);
}

/**
 * Calculate monthly payment for a loan
 */
export function calculateMonthlyPayment(
  loanAmount: number,
  interestRate: number,  // Annual interest rate (%)
  tenureMonths: number   // Loan tenure in months
): number {
  const monthlyRate = interestRate / 100 / 12;
  const payment = loanAmount * (monthlyRate * Math.pow(1 + monthlyRate, tenureMonths)) / 
                 (Math.pow(1 + monthlyRate, tenureMonths) - 1);
  
  return payment;
}
