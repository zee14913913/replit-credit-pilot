'use client';

import { useState } from 'react';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import ScrollProgress from '@/components/ScrollProgress';
import { matchProducts, calculateAffordabilityScore, ProductMatchResult, CustomerProfile } from '@/lib/productMatcher';

export default function LoanMatcherPage() {
  const [monthlyIncome, setMonthlyIncome] = useState<string>('');
  const [monthlyCommitment, setMonthlyCommitment] = useState<string>('');
  const [desiredLoanAmount, setDesiredLoanAmount] = useState<string>('');
  const [loanTenure, setLoanTenure] = useState<string>('84'); // Default 7 years
  const [productType, setProductType] = useState<'personalLoan' | 'mortgage' | 'creditCard' | 'businessLoan'>('personalLoan');
  const [results, setResults] = useState<ProductMatchResult[]>([]);
  const [showResults, setShowResults] = useState(false);
  const [affordability, setAffordability] = useState<{ score: number; rating: string; description: string } | null>(null);

  const handleCalculate = () => {
    const income = parseFloat(monthlyIncome);
    const commitment = parseFloat(monthlyCommitment);
    const loanAmount = parseFloat(desiredLoanAmount) || 0;
    const tenure = parseInt(loanTenure);

    if (isNaN(income) || isNaN(commitment) || income <= 0) {
      alert('Please enter valid income and commitment values');
      return;
    }

    const customer: CustomerProfile = {
      monthlyIncome: income,
      monthlyCommitment: commitment,
      desiredLoanAmount: loanAmount > 0 ? loanAmount : undefined,
      loanTenure: tenure,
      productType: productType
    };

    // Calculate affordability score
    const affordabilityScore = calculateAffordabilityScore(income, commitment);
    setAffordability(affordabilityScore);

    // Match products (currently with empty product list - will be populated later)
    const matches = matchProducts(customer, []);
    setResults(matches);
    setShowResults(true);
  };

  const dsr = monthlyIncome && monthlyCommitment 
    ? ((parseFloat(monthlyCommitment) / parseFloat(monthlyIncome)) * 100).toFixed(1)
    : '0';

  return (
    <div className="min-h-screen bg-[#0A0E27]">
      <ScrollProgress />
      <Header />
      
      <main className="pt-20">
        {/* Hero Section */}
        <section className="relative py-20 overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-b from-blue-600/10 to-transparent pointer-events-none" />
          
          <div className="container mx-auto px-6 relative z-10">
            <div className="max-w-4xl mx-auto text-center">
              <span className="inline-block px-4 py-2 bg-blue-600/20 border border-blue-500/30 rounded-full text-sm text-blue-300 mb-6">
                Smart Loan Matching
              </span>
              <h1 className="text-5xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-blue-400 via-cyan-300 to-blue-400 text-transparent bg-clip-text">
                Find Your Best Loan Match
              </h1>
              <p className="text-xl text-gray-400 mb-8">
                Calculate your DSR and discover eligible loan products from 16+ Malaysian banks
              </p>
            </div>
          </div>
        </section>

        {/* Calculator Section */}
        <section className="py-16 container mx-auto px-6">
          <div className="max-w-4xl mx-auto">
            <div className="bg-white/5 border border-white/10 rounded-2xl p-8">
              <h2 className="text-3xl font-bold mb-8 text-white">Loan Eligibility Calculator</h2>
              
              <div className="grid md:grid-cols-2 gap-6 mb-8">
                {/* Monthly Income */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Monthly Income (RM)
                  </label>
                  <input
                    type="number"
                    value={monthlyIncome}
                    onChange={(e) => setMonthlyIncome(e.target.value)}
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-blue-500"
                    placeholder="5000"
                  />
                </div>

                {/* Monthly Commitment */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Monthly Commitment (RM)
                  </label>
                  <input
                    type="number"
                    value={monthlyCommitment}
                    onChange={(e) => setMonthlyCommitment(e.target.value)}
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-blue-500"
                    placeholder="2000"
                  />
                </div>

                {/* Product Type */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Loan Type
                  </label>
                  <select
                    value={productType}
                    onChange={(e) => setProductType(e.target.value as any)}
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="personalLoan">Personal Loan</option>
                    <option value="mortgage">Mortgage / Home Loan</option>
                    <option value="creditCard">Credit Card</option>
                    <option value="businessLoan">Business Loan</option>
                  </select>
                </div>

                {/* Desired Loan Amount */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Desired Loan Amount (RM) - Optional
                  </label>
                  <input
                    type="number"
                    value={desiredLoanAmount}
                    onChange={(e) => setDesiredLoanAmount(e.target.value)}
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-blue-500"
                    placeholder="50000"
                  />
                </div>

                {/* Loan Tenure */}
                {(productType === 'personalLoan' || productType === 'mortgage') && (
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Loan Tenure (Months)
                    </label>
                    <input
                      type="number"
                      value={loanTenure}
                      onChange={(e) => setLoanTenure(e.target.value)}
                      className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-blue-500"
                      placeholder="84"
                    />
                    <p className="text-sm text-gray-400 mt-2">
                      {parseInt(loanTenure) / 12} years
                    </p>
                  </div>
                )}
              </div>

              {/* DSR Display */}
              {monthlyIncome && monthlyCommitment && (
                <div className="mb-8 p-6 bg-blue-600/10 border border-blue-500/30 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-semibold text-white mb-1">Your Current DSR</h3>
                      <p className="text-gray-400 text-sm">Debt Service Ratio</p>
                    </div>
                    <div className="text-right">
                      <div className="text-4xl font-bold text-blue-400">{dsr}%</div>
                      <p className="text-sm text-gray-400 mt-1">
                        {parseFloat(dsr) <= 40 ? 'Excellent' : 
                         parseFloat(dsr) <= 50 ? 'Good' : 
                         parseFloat(dsr) <= 60 ? 'Fair' : 'High'}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Calculate Button */}
              <button
                onClick={handleCalculate}
                className="w-full px-8 py-4 bg-gradient-to-r from-blue-600 to-cyan-500 text-white font-semibold rounded-lg hover:shadow-lg hover:shadow-blue-500/50 transition-all"
              >
                Calculate & Find Matching Loans
              </button>
            </div>
          </div>
        </section>

        {/* Results Section */}
        {showResults && (
          <section className="py-16 container mx-auto px-6">
            <div className="max-w-6xl mx-auto">
              {/* Affordability Score */}
              {affordability && (
                <div className="mb-12 p-8 bg-white/5 border border-white/10 rounded-2xl">
                  <h2 className="text-3xl font-bold mb-6 text-white">Your Financial Profile</h2>
                  
                  <div className="grid md:grid-cols-3 gap-6">
                    <div className="text-center">
                      <div className="text-5xl font-bold bg-gradient-to-r from-blue-400 to-cyan-300 text-transparent bg-clip-text mb-2">
                        {affordability.score}
                      </div>
                      <div className="text-sm text-gray-400">Affordability Score</div>
                    </div>
                    
                    <div className="text-center">
                      <div className="text-3xl font-bold text-blue-400 mb-2">
                        {affordability.rating}
                      </div>
                      <div className="text-sm text-gray-400">Credit Rating</div>
                    </div>
                    
                    <div className="text-center">
                      <div className="text-3xl font-bold text-cyan-400 mb-2">
                        {results.filter(r => r.eligible).length}
                      </div>
                      <div className="text-sm text-gray-400">Eligible Banks</div>
                    </div>
                  </div>
                  
                  <div className="mt-6 p-4 bg-blue-600/10 border border-blue-500/30 rounded-lg">
                    <p className="text-gray-300">{affordability.description}</p>
                  </div>
                </div>
              )}

              {/* Matching Products */}
              <div className="space-y-6">
                <h2 className="text-3xl font-bold text-white mb-6">
                  Matching Banks & Products ({results.length})
                </h2>
                
                {results.map((result, index) => (
                  <div
                    key={index}
                    className={`p-6 rounded-xl border ${
                      result.eligible
                        ? 'bg-green-900/10 border-green-500/30'
                        : 'bg-red-900/10 border-red-500/30'
                    }`}
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h3 className="text-2xl font-bold text-white mb-2">
                          {result.company}
                        </h3>
                        <p className="text-gray-400">{result.productName}</p>
                      </div>
                      <div className="text-right">
                        <div className={`text-2xl font-bold ${
                          result.eligible ? 'text-green-400' : 'text-red-400'
                        }`}>
                          {result.matchScore}%
                        </div>
                        <div className="text-sm text-gray-400">Match Score</div>
                      </div>
                    </div>
                    
                    <div className={`inline-block px-4 py-2 rounded-full text-sm font-semibold mb-4 ${
                      result.eligible
                        ? 'bg-green-600/20 text-green-300'
                        : 'bg-red-600/20 text-red-300'
                    }`}>
                      {result.eligible ? '✓ Eligible' : '✗ Not Eligible'}
                    </div>
                    
                    <p className="text-gray-300 mb-4">{result.reason}</p>
                    
                    {result.estimatedLoanAmount && result.estimatedLoanAmount > 0 && (
                      <div className="grid md:grid-cols-2 gap-4 mt-4 p-4 bg-white/5 rounded-lg">
                        <div>
                          <div className="text-sm text-gray-400 mb-1">Maximum Loan Amount</div>
                          <div className="text-xl font-bold text-white">
                            RM {result.estimatedLoanAmount.toLocaleString(undefined, {maximumFractionDigits: 0})}
                          </div>
                        </div>
                        {result.estimatedMonthlyPayment && result.estimatedMonthlyPayment > 0 && (
                          <div>
                            <div className="text-sm text-gray-400 mb-1">Estimated Monthly Payment</div>
                            <div className="text-xl font-bold text-white">
                              RM {result.estimatedMonthlyPayment.toLocaleString(undefined, {maximumFractionDigits: 0})}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </section>
        )}

        {/* Info Section */}
        <section className="py-16 bg-white/5">
          <div className="container mx-auto px-6">
            <div className="max-w-4xl mx-auto">
              <h2 className="text-3xl font-bold mb-8 text-white text-center">
                Understanding DSR (Debt Service Ratio)
              </h2>
              
              <div className="grid md:grid-cols-2 gap-8">
                <div className="p-6 bg-white/5 border border-white/10 rounded-xl">
                  <h3 className="text-xl font-bold text-white mb-4">What is DSR?</h3>
                  <p className="text-gray-300">
                    DSR is the percentage of your monthly income used to service debts. Malaysian banks typically allow DSR up to 60-70% depending on the loan type.
                  </p>
                </div>
                
                <div className="p-6 bg-white/5 border border-white/10 rounded-xl">
                  <h3 className="text-xl font-bold text-white mb-4">DSR Formula</h3>
                  <p className="text-gray-300 mb-2">
                    DSR = (Monthly Commitments / Monthly Income) × 100%
                  </p>
                  <p className="text-gray-400 text-sm">
                    Lower DSR = Better loan eligibility & rates
                  </p>
                </div>
                
                <div className="p-6 bg-white/5 border border-white/10 rounded-xl">
                  <h3 className="text-xl font-bold text-white mb-4">Typical DSR Limits</h3>
                  <ul className="space-y-2 text-gray-300">
                    <li>• Personal Loans: 60%</li>
                    <li>• Home Loans: 70%</li>
                    <li>• Credit Cards: 60%</li>
                    <li>• Business Loans: 60%</li>
                  </ul>
                </div>
                
                <div className="p-6 bg-white/5 border border-white/10 rounded-xl">
                  <h3 className="text-xl font-bold text-white mb-4">How to Improve DSR</h3>
                  <ul className="space-y-2 text-gray-300">
                    <li>• Increase monthly income</li>
                    <li>• Pay off existing debts</li>
                    <li>• Debt consolidation</li>
                    <li>• Extend loan tenure</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
      
      <Footer />
    </div>
  );
}
