/**
 * Product Database Loader
 * Loads and filters financial products from the database
 */

import { BankStandard } from './bankStandards';

export interface FinancialProduct {
  source: string;
  company: string;
  productName: string;
  productType: string;
  category: string;
  requiredDocuments: string;
  features: string;
  benefits: string;
  fees: string;
  interestRate: string;
  tenure: string;
  applicationLink: string;
  notes: string;
}

export interface ProductMatchResult extends FinancialProduct {
  matchScore: number;
  eligible: boolean;
  reason: string;
  bankStandard?: BankStandard;
  estimatedLoanAmount?: number;
  estimatedMonthlyPayment?: number;
}

// This would normally load from the Excel file
// For now, we'll create a mock loader that will be replaced with actual Excel parsing
export async function loadProducts(): Promise<FinancialProduct[]> {
  // TODO: Implement actual Excel file loading using xlsx library
  // For now, return empty array
  console.warn('Product loader not yet implemented - needs xlsx library');
  return [];
}

/**
 * Filter products by category
 */
export function filterByCategory(
  products: FinancialProduct[],
  category: string
): FinancialProduct[] {
  return products.filter(p => 
    p.category.toLowerCase().includes(category.toLowerCase())
  );
}

/**
 * Filter products by company
 */
export function filterByCompany(
  products: FinancialProduct[],
  company: string
): FinancialProduct[] {
  return products.filter(p => 
    p.company.toLowerCase().includes(company.toLowerCase())
  );
}

/**
 * Search products by keyword
 */
export function searchProducts(
  products: FinancialProduct[],
  keyword: string
): FinancialProduct[] {
  const lowerKeyword = keyword.toLowerCase();
  return products.filter(p => 
    p.productName.toLowerCase().includes(lowerKeyword) ||
    p.company.toLowerCase().includes(lowerKeyword) ||
    p.features.toLowerCase().includes(lowerKeyword) ||
    p.benefits.toLowerCase().includes(lowerKeyword)
  );
}
