/**
 * DSR (Debt Service Ratio) 计算器 - 2025年真实公式
 * 基于马来西亚银行实际批准标准
 * 最后更新: 2025-12-28
 */

// ============= 类型定义 =============

/**
 * 收入信息
 */
export interface IncomeInfo {
  grossSalary: number;           // 总薪资
  epfDeduction: number;          // EPF扣除 (8%)
  incomeTax: number;             // 所得税
  socso: number;                 // SOCSO
  otherDeductions?: number;      // 其他扣除
  bonusMonthly?: number;         // 月均奖金
  allowances?: number;           // 固定津贴
}

/**
 * 债务承诺
 */
export interface DebtCommitment {
  type: 'housing' | 'car' | 'personal' | 'ptptn' | 'credit_card' | 'other';
  monthlyPayment: number;
  creditCardUsed?: number;       // 信用卡已用额度（仅信用卡需要）
  creditCardLimit?: number;      // 信用卡总额度
}

/**
 * DSR计算结果
 */
export interface DSRCalculationResult {
  // 收入部分
  grossIncome: number;
  totalDeductions: number;
  netIncome: number;
  
  // 债务部分
  existingCommitments: number;
  newLoanCommitment: number;
  totalCommitments: number;
  
  // DSR
  currentDSR: number;            // 现有DSR
  projectedDSR: number;          // 加入新贷款后的DSR
  
  // 评估
  assessment: {
    status: 'excellent' | 'good' | 'fair' | 'risky' | 'rejected';
    message: string;
    recommendations: string[];
  };
  
  // 可用额度
  availableCommitment: number;   // 可承受的额外月供
  maxLoanAmount?: number;        // 最大可贷额（估算）
}

// ============= 计算函数 =============

/**
 * 计算净收入
 */
export function calculateNetIncome(income: IncomeInfo): {
  grossIncome: number;
  netIncome: number;
  breakdown: {
    basicSalary: number;
    allowances: number;
    bonus: number;
    totalGross: number;
    epf: number;
    tax: number;
    socso: number;
    otherDeductions: number;
    totalDeductions: number;
  };
} {
  const basicSalary = income.grossSalary;
  const allowances = income.allowances || 0;
  const bonus = income.bonusMonthly || 0;
  
  const totalGross = basicSalary + allowances + bonus;
  
  const epf = income.epfDeduction;
  const tax = income.incomeTax;
  const socso = income.socso;
  const otherDeductions = income.otherDeductions || 0;
  
  const totalDeductions = epf + tax + socso + otherDeductions;
  const netIncome = totalGross - totalDeductions;
  
  return {
    grossIncome: totalGross,
    netIncome,
    breakdown: {
      basicSalary,
      allowances,
      bonus,
      totalGross,
      epf,
      tax,
      socso,
      otherDeductions,
      totalDeductions
    }
  };
}

/**
 * 计算月度债务承诺
 * 
 * 关键规则：
 * - 信用卡承诺 = 已用额度 × 5%（银行统一保守假设）
 * - 不是用"最低还款额"
 */
export function calculateMonthlyCommitments(debts: DebtCommitment[]): {
  total: number;
  breakdown: Array<{
    type: string;
    amount: number;
    notes?: string;
  }>;
} {
  const breakdown: Array<{ type: string; amount: number; notes?: string }> = [];
  let total = 0;
  
  for (const debt of debts) {
    let amount = debt.monthlyPayment;
    let notes: string | undefined;
    
    // 信用卡特殊处理
    if (debt.type === 'credit_card' && debt.creditCardUsed !== undefined) {
      // 使用5%规则
      amount = debt.creditCardUsed * 0.05;
      notes = `已用 RM ${debt.creditCardUsed.toFixed(2)} × 5% = RM ${amount.toFixed(2)}`;
    }
    
    breakdown.push({
      type: debt.type,
      amount,
      notes
    });
    
    total += amount;
  }
  
  return { total, breakdown };
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
 * 完整DSR计算
 */
export function performDSRCalculation(
  income: IncomeInfo,
  existingDebts: DebtCommitment[],
  newLoanMonthlyPayment: number = 0,
  dsrLimit: number = 70
): DSRCalculationResult {
  // 1. 计算净收入
  const incomeCalc = calculateNetIncome(income);
  const netIncome = incomeCalc.netIncome;
  
  // 2. 计算现有承诺
  const commitmentsCalc = calculateMonthlyCommitments(existingDebts);
  const existingCommitments = commitmentsCalc.total;
  
  // 3. 计算DSR
  const currentDSR = calculateDSR(existingCommitments, netIncome);
  const totalCommitments = existingCommitments + newLoanMonthlyPayment;
  const projectedDSR = calculateDSR(totalCommitments, netIncome);
  
  // 4. 评估状态
  let status: 'excellent' | 'good' | 'fair' | 'risky' | 'rejected';
  let message: string;
  const recommendations: string[] = [];
  
  if (projectedDSR <= 30) {
    status = 'excellent';
    message = 'DSR极低，财务状况极佳';
    recommendations.push('可考虑投资或储蓄');
  } else if (projectedDSR <= 50) {
    status = 'good';
    message = 'DSR健康，财务状况良好';
    recommendations.push('保持当前财务纪律');
  } else if (projectedDSR <= dsrLimit) {
    status = 'fair';
    message = `DSR在${dsrLimit}%限制内，但偏高`;
    recommendations.push('考虑清付部分债务以降低DSR');
    recommendations.push('避免新增债务');
  } else if (projectedDSR <= dsrLimit + 10) {
    status = 'risky';
    message = `DSR ${projectedDSR.toFixed(2)}% 超过限制 ${dsrLimit}%`;
    recommendations.push('需要清付现有债务');
    recommendations.push('或减少新贷款额');
    recommendations.push('或选择DSR限制更宽松的银行');
  } else {
    status = 'rejected';
    message = `DSR ${projectedDSR.toFixed(2)}% 严重超标`;
    recommendations.push('必须大幅清付现有债务');
    recommendations.push('或显著减少新贷款额');
    recommendations.push('建议等待3-6个月后重新申请');
  }
  
  // 5. 计算可用额度
  const maxAllowedCommitment = netIncome * (dsrLimit / 100);
  const availableCommitment = Math.max(0, maxAllowedCommitment - existingCommitments);
  
  // 6. 估算最大可贷额（简化估算，基于5年期限，8%利率）
  let maxLoanAmount: number | undefined;
  if (availableCommitment > 0) {
    // 使用平息法粗略估算
    // 月供 = [(本金 × 年期 × 利率) + 本金] ÷ 期限月数
    // 反推：本金 ≈ 月供 × 期限月数 / (1 + 年期 × 利率)
    const years = 5;
    const rate = 0.08;
    const months = years * 12;
    maxLoanAmount = (availableCommitment * months) / (1 + years * rate);
  }
  
  return {
    grossIncome: incomeCalc.grossIncome,
    totalDeductions: incomeCalc.breakdown.totalDeductions,
    netIncome,
    existingCommitments,
    newLoanCommitment: newLoanMonthlyPayment,
    totalCommitments,
    currentDSR,
    projectedDSR,
    assessment: {
      status,
      message,
      recommendations
    },
    availableCommitment,
    maxLoanAmount
  };
}

/**
 * 计算平息法月供
 * 
 * 公式：月供 = [(本金 × 年期 × 年利率) + 本金] ÷ 期限月数
 */
export function calculateFlatRateMonthlyPayment(
  principal: number,
  years: number,
  annualRate: number
): {
  monthlyPayment: number;
  totalInterest: number;
  totalPayment: number;
  effectiveRate: number;
} {
  const months = years * 12;
  
  // 计算总利息
  const totalInterest = principal * years * annualRate;
  
  // 计算总还款额
  const totalPayment = principal + totalInterest;
  
  // 计算月供
  const monthlyPayment = totalPayment / months;
  
  // 计算有效利率（简化估算）
  const effectiveRate = ((1 + annualRate / 12) ** 12 - 1);
  
  return {
    monthlyPayment,
    totalInterest,
    totalPayment,
    effectiveRate
  };
}

/**
 * 计算减余法月供（估算）
 * 
 * 公式：月供 = 本金 × [r(1+r)^n] / [(1+r)^n - 1]
 * 其中：r = 月利率，n = 总期限月数
 */
export function calculateDiminishingRateMonthlyPayment(
  principal: number,
  years: number,
  annualRate: number
): {
  monthlyPayment: number;
  totalInterest: number;
  totalPayment: number;
} {
  const months = years * 12;
  const monthlyRate = annualRate / 12;
  
  // 月供公式
  const numerator = monthlyRate * Math.pow(1 + monthlyRate, months);
  const denominator = Math.pow(1 + monthlyRate, months) - 1;
  const monthlyPayment = principal * (numerator / denominator);
  
  // 总还款
  const totalPayment = monthlyPayment * months;
  
  // 总利息
  const totalInterest = totalPayment - principal;
  
  return {
    monthlyPayment,
    totalInterest,
    totalPayment
  };
}

/**
 * DSR优化建议生成器
 */
export function generateDSROptimizationPlan(
  currentDSR: number,
  targetDSR: number,
  existingDebts: DebtCommitment[],
  netIncome: number
): Array<{
  action: string;
  description: string;
  dsrImpact: number;
  timeline: string;
  priority: 'high' | 'medium' | 'low';
}> {
  const plan: Array<{
    action: string;
    description: string;
    dsrImpact: number;
    timeline: string;
    priority: 'high' | 'medium' | 'low';
  }> = [];
  
  const dsrGap = currentDSR - targetDSR;
  
  if (dsrGap <= 0) {
    return []; // 已经达标
  }
  
  // 按优先级排序债务（信用卡 > 个人贷 > 其他）
  const sortedDebts = [...existingDebts].sort((a, b) => {
    const priority: { [key: string]: number } = {
      credit_card: 1,
      personal: 2,
      car: 3,
      ptptn: 4,
      housing: 5,
      other: 6
    };
    return priority[a.type] - priority[b.type];
  });
  
  // 方案1：清付信用卡
  const creditCards = sortedDebts.filter(d => d.type === 'credit_card');
  if (creditCards.length > 0) {
    const totalCreditCardUsed = creditCards.reduce(
      (sum, card) => sum + (card.creditCardUsed || 0),
      0
    );
    const creditCardCommitment = totalCreditCardUsed * 0.05;
    const dsrReduction = (creditCardCommitment / netIncome) * 100;
    
    plan.push({
      action: 'clear_credit_cards',
      description: `清付所有信用卡余额（总计 RM ${totalCreditCardUsed.toFixed(2)}）`,
      dsrImpact: -dsrReduction,
      timeline: '1-3个月',
      priority: 'high'
    });
  }
  
  // 方案2：清付个人贷款
  const personalLoans = sortedDebts.filter(d => d.type === 'personal');
  if (personalLoans.length > 0) {
    const totalPersonalLoan = personalLoans.reduce(
      (sum, loan) => sum + loan.monthlyPayment,
      0
    );
    const dsrReduction = (totalPersonalLoan / netIncome) * 100;
    
    plan.push({
      action: 'clear_personal_loans',
      description: `清付个人贷款（月供 RM ${totalPersonalLoan.toFixed(2)}）`,
      dsrImpact: -dsrReduction,
      timeline: '3-6个月',
      priority: 'high'
    });
  }
  
  // 方案3：减少新贷款额
  plan.push({
    action: 'reduce_loan_amount',
    description: '减少新申请贷款的金额',
    dsrImpact: -5,
    timeline: '立即',
    priority: 'medium'
  });
  
  // 方案4：延长贷款期限
  plan.push({
    action: 'extend_loan_tenure',
    description: '选择更长的贷款期限以降低月供',
    dsrImpact: -3,
    timeline: '立即',
    priority: 'low'
  });
  
  // 方案5：换银行
  plan.push({
    action: 'switch_bank',
    description: '选择DSR限制更宽松的银行',
    dsrImpact: -10,
    timeline: '立即',
    priority: 'high'
  });
  
  return plan;
}

/**
 * 财务健康评分（0-100）
 */
export function calculateFinancialHealthScore(
  dsr: number,
  netIncome: number,
  totalAssets?: number,
  creditScore?: number
): {
  score: number;
  grade: 'A+' | 'A' | 'B' | 'C' | 'D' | 'F';
  assessment: string;
} {
  let score = 100;
  
  // DSR影响（50分）
  if (dsr <= 30) {
    score -= 0;
  } else if (dsr <= 50) {
    score -= (dsr - 30) * 0.5;
  } else if (dsr <= 70) {
    score -= 10 + (dsr - 50) * 1.0;
  } else {
    score -= 30 + (dsr - 70) * 2.0;
  }
  
  // 收入水平影响（20分）
  if (netIncome >= 10000) {
    // 无扣分
  } else if (netIncome >= 5000) {
    score -= 5;
  } else if (netIncome >= 3000) {
    score -= 10;
  } else {
    score -= 20;
  }
  
  // 资产影响（15分）
  if (totalAssets !== undefined) {
    const assetToIncomeRatio = totalAssets / (netIncome * 12);
    if (assetToIncomeRatio >= 5) {
      // 无扣分
    } else if (assetToIncomeRatio >= 2) {
      score -= 5;
    } else if (assetToIncomeRatio >= 1) {
      score -= 10;
    } else {
      score -= 15;
    }
  }
  
  // 信用评分影响（15分）
  if (creditScore !== undefined) {
    if (creditScore >= 750) {
      // 无扣分
    } else if (creditScore >= 650) {
      score -= 5;
    } else if (creditScore >= 550) {
      score -= 10;
    } else {
      score -= 15;
    }
  }
  
  // 确保分数在0-100之间
  score = Math.max(0, Math.min(100, score));
  
  // 评级
  let grade: 'A+' | 'A' | 'B' | 'C' | 'D' | 'F';
  let assessment: string;
  
  if (score >= 90) {
    grade = 'A+';
    assessment = '财务健康状况优秀';
  } else if (score >= 80) {
    grade = 'A';
    assessment = '财务健康状况良好';
  } else if (score >= 70) {
    grade = 'B';
    assessment = '财务健康状况尚可';
  } else if (score >= 60) {
    grade = 'C';
    assessment = '财务健康状况一般，需改善';
  } else if (score >= 50) {
    grade = 'D';
    assessment = '财务健康状况偏差，需要重视';
  } else {
    grade = 'F';
    assessment = '财务健康状况堪忧，建议寻求专业咨询';
  }
  
  return { score, grade, assessment };
}

export default {
  calculateNetIncome,
  calculateMonthlyCommitments,
  calculateDSR,
  performDSRCalculation,
  calculateFlatRateMonthlyPayment,
  calculateDiminishingRateMonthlyPayment,
  generateDSROptimizationPlan,
  calculateFinancialHealthScore
};
