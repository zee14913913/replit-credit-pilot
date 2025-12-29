/**
 * Product Matching Algorithm
 * Matches customers with suitable financial products based on income and commitments
 */

import { 
  BankStandard, 
  bankStandards, 
  calculateDSR, 
  checkDSRRequirement,
  calculateMaxLoanAmount,
  calculateMonthlyPayment 
} from './bankStandards';
import { FinancialProduct, ProductMatchResult } from './productLoader';

// Re-export for convenience
export type { ProductMatchResult } from './productLoader';

export interface CustomerProfile {
  monthlyIncome: number;
  monthlyCommitment: number;
  desiredLoanAmount?: number;
  loanTenure?: number;  // in months
  productType: 'personalLoan' | 'mortgage' | 'creditCard' | 'businessLoan';
  preferredBanks?: string[];  // Optional: filter by specific banks
}

/**
 * Match customer with suitable products
 */
export function matchProducts(
  customer: CustomerProfile,
  products: FinancialProduct[]
): ProductMatchResult[] {
  const results: ProductMatchResult[] = [];
  
  // Calculate customer's current DSR
  const currentDSR = calculateDSR(customer.monthlyCommitment, customer.monthlyIncome);
  
  // Check each bank's requirements
  for (const bankStandard of bankStandards) {
    // Skip if customer has preferred banks and this isn't one of them
    if (customer.preferredBanks && customer.preferredBanks.length > 0) {
      if (!customer.preferredBanks.some(b => 
        b.toLowerCase() === bankStandard.bankName.toLowerCase() ||
        b.toLowerCase() === bankStandard.bankCode.toLowerCase()
      )) {
        continue;
      }
    }
    
    // Check DSR requirement
    const dsrCheck = checkDSRRequirement(
      customer.monthlyCommitment,
      customer.monthlyIncome,
      customer.productType,
      bankStandard
    );
    
    // Check minimum income requirement
    let minIncomeReq = 0;
    if (customer.productType === 'personalLoan') {
      minIncomeReq = bankStandard.minIncome.personalLoan;
    } else if (customer.productType === 'mortgage') {
      minIncomeReq = bankStandard.minIncome.mortgage;
    } else if (customer.productType === 'creditCard') {
      minIncomeReq = bankStandard.minIncome.creditCardBasic;
    } else if (customer.productType === 'businessLoan') {
      minIncomeReq = bankStandard.minIncome.businessLoan;
    }
    
    const meetsIncomeReq = customer.monthlyIncome >= minIncomeReq;
    
    // Calculate maximum loan amount (if applicable)
    let maxLoanAmount = 0;
    let estimatedMonthlyPayment = 0;
    
    if (customer.productType === 'personalLoan' || customer.productType === 'mortgage') {
      // Use a default interest rate of 4% and tenure of 7 years (84 months) for estimation
      const defaultRate = 4;
      const defaultTenure = customer.loanTenure || 84;
      
      maxLoanAmount = calculateMaxLoanAmount(
        customer.monthlyIncome,
        customer.monthlyCommitment,
        customer.productType,
        bankStandard,
        defaultRate,
        defaultTenure
      );
      
      // Cap by bank's maximum loan limit
      if (customer.productType === 'personalLoan') {
        maxLoanAmount = Math.min(maxLoanAmount, bankStandard.loanLimits.personalLoanMax);
      }
      
      // If customer has a desired loan amount, calculate monthly payment
      if (customer.desiredLoanAmount && customer.desiredLoanAmount > 0) {
        estimatedMonthlyPayment = calculateMonthlyPayment(
          customer.desiredLoanAmount,
          defaultRate,
          defaultTenure
        );
      }
    }
    
    // Find matching products from the database
    const matchingProducts = products.filter(p => 
      p.company.toLowerCase().includes(bankStandard.bankName.toLowerCase()) ||
      p.company.toLowerCase().includes(bankStandard.bankCode.toLowerCase())
    );
    
    // Calculate match score (0-100)
    let matchScore = 0;
    if (dsrCheck.eligible) matchScore += 40;
    if (meetsIncomeReq) matchScore += 30;
    if (maxLoanAmount >= (customer.desiredLoanAmount || 0)) matchScore += 30;
    
    // Determine eligibility
    const eligible = dsrCheck.eligible && meetsIncomeReq;
    
    // Build reason string
    let reason = '';
    if (!dsrCheck.eligible) {
      reason += `DSR ${dsrCheck.dsr.toFixed(1)}% exceeds maximum ${dsrCheck.maxDSR}%. `;
    }
    if (!meetsIncomeReq) {
      reason += `Monthly income RM${customer.monthlyIncome.toLocaleString()} is below minimum RM${minIncomeReq.toLocaleString()}. `;
    }
    if (eligible) {
      reason = `Eligible for up to RM${maxLoanAmount.toLocaleString(undefined, {maximumFractionDigits: 0})}`;
    }
    
    // If there are matching products, add each one
    if (matchingProducts.length > 0) {
      for (const product of matchingProducts) {
        results.push({
          ...product,
          matchScore,
          eligible,
          reason,
          bankStandard,
          estimatedLoanAmount: maxLoanAmount,
          estimatedMonthlyPayment
        });
      }
    } else {
      // Add a generic result for this bank even if no specific product found
      results.push({
        source: 'Bank Standards Database',
        company: bankStandard.bankName,
        productName: `${bankStandard.bankName} - ${customer.productType}`,
        productType: customer.productType,
        category: customer.productType === 'personalLoan' ? 'Personal' : 
                  customer.productType === 'mortgage' ? 'Personal' : 
                  customer.productType === 'businessLoan' ? 'Business' : 'Personal',
        requiredDocuments: 'Payslip, EPF Statement, Bank Statement',
        features: `Max DSR: ${bankStandard.dsr[customer.productType]}%`,
        benefits: '',
        fees: '',
        interestRate: '~4%',
        tenure: '1-10 years',
        applicationLink: '',
        notes: `Estimated based on ${bankStandard.bankName} lending criteria`,
        matchScore,
        eligible,
        reason,
        bankStandard,
        estimatedLoanAmount: maxLoanAmount,
        estimatedMonthlyPayment
      });
    }
  }
  
  // Sort by match score (highest first)
  results.sort((a, b) => b.matchScore - a.matchScore);
  
  return results;
}

/**
 * Get recommended products (top matches)
 */
export function getRecommendedProducts(
  customer: CustomerProfile,
  products: FinancialProduct[],
  limit: number = 5
): ProductMatchResult[] {
  const allMatches = matchProducts(customer, products);
  return allMatches.slice(0, limit);
}

/**
 * Calculate affordability score (0-100)
 */
export function calculateAffordabilityScore(
  monthlyIncome: number,
  monthlyCommitment: number
): { score: number; rating: string; description: string } {
  const dsr = calculateDSR(monthlyCommitment, monthlyIncome);
  
  let score = 0;
  let rating = '';
  let description = '';
  
  if (dsr <= 30) {
    score = 100;
    rating = 'Excellent';
    description = 'Very healthy financial position. Eligible for all loan products with best rates.';
  } else if (dsr <= 40) {
    score = 85;
    rating = 'Very Good';
    description = 'Strong financial position. Eligible for most loan products with competitive rates.';
  } else if (dsr <= 50) {
    score = 70;
    rating = 'Good';
    description = 'Healthy financial position. Eligible for standard loan products.';
  } else if (dsr <= 60) {
    score = 55;
    rating = 'Fair';
    description = 'Moderate financial position. Some loan products may be available.';
  } else if (dsr <= 70) {
    score = 35;
    rating = 'Limited';
    description = 'Limited borrowing capacity. Consider debt consolidation to improve DSR.';
  } else {
    score = 15;
    rating = 'Very Limited';
    description = 'Very high DSR. Strongly recommend debt restructuring before taking new loans.';
  }
  
  return { score, rating, description };
}
