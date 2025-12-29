'use client';

import React, { useState, useEffect } from 'react';
import { 
  Calculator, 
  TrendingUp, 
  AlertCircle, 
  CheckCircle, 
  XCircle,
  Download,
  BarChart3,
  Target,
  Clock,
  DollarSign,
  Sparkles,
  Shield
} from 'lucide-react';

// 身份类型
const IDENTITY_TYPES = [
  { value: 'citizen', label: 'Malaysian Citizen', labelZh: '马来西亚公民', labelMs: 'Warganegara Malaysia' },
  { value: 'pr', label: 'Permanent Resident', labelZh: '永久居民', labelMs: 'Pemastautin Tetap' },
  { value: 'civil_servant', label: 'Civil Servant', labelZh: '公务员', labelMs: 'Penjawat Awam' },
  { value: 'glc', label: 'GLC Employee', labelZh: 'GLC员工', labelMs: 'Pekerja GLC' },
  { value: 'self_employed', label: 'Self-Employed', labelZh: '自雇企业主', labelMs: 'Bekerja Sendiri' },
  { value: 'foreigner', label: 'Foreigner', labelZh: '外国人', labelMs: 'Warga Asing' },
];

// 就业类型
const EMPLOYMENT_TYPES = [
  { value: 'salaried', label: 'Salaried Employee', labelZh: '受薪员工', labelMs: 'Pekerja Bergaji' },
  { value: 'self_employed', label: 'Self-Employed', labelZh: '自雇', labelMs: 'Bekerja Sendiri' },
  { value: 'government', label: 'Government', labelZh: '政府公务员', labelMs: 'Kerajaan' },
  { value: 'contract', label: 'Contract', labelZh: '合约工', labelMs: 'Kontrak' },
];

// 贷款类型
const LOAN_TYPES = [
  { value: 'personal', label: 'Personal Loan', labelZh: '个人贷款', labelMs: 'Pinjaman Peribadi' },
  { value: 'housing', label: 'Housing Loan', labelZh: '房屋贷款', labelMs: 'Pinjaman Perumahan' },
  { value: 'auto', label: 'Auto Loan', labelZh: '汽车贷款', labelMs: 'Pinjaman Kereta' },
  { value: 'business', label: 'Business Loan', labelZh: '营运资金', labelMs: 'Pinjaman Perniagaan' },
];

// 银行标准（简化版，完整版应该从 bankStandardsReal2025.ts 导入）
const BANK_STANDARDS = [
  { code: 'MBB', name: 'Maybank', dsrLow: 40, dsrHigh: 70, selfEmployedRate: 0.7 },
  { code: 'CIMB', name: 'CIMB', dsrLow: 65, dsrHigh: 75, selfEmployedRate: 0.8 },
  { code: 'RHB', name: 'RHB', dsrLow: 55, dsrHigh: 60, selfEmployedRate: 0.6 },
  { code: 'HLB', name: 'Hong Leong', dsrLow: 60, dsrHigh: 80, selfEmployedRate: 0.9 },
  { code: 'PBB', name: 'Public Bank', dsrLow: 60, dsrHigh: 70, selfEmployedRate: 0.75 },
  { code: 'HSBC', name: 'HSBC', dsrLow: 60, dsrHigh: 70, selfEmployedRate: 0.75 },
  { code: 'BSN', name: 'BSN', dsrLow: 60, dsrHigh: 75, selfEmployedRate: 0.7 },
  { code: 'BIMB', name: 'Bank Islam', dsrLow: 50, dsrHigh: 70, selfEmployedRate: 0.7 },
];

interface DSRCalculatorProps {
  language?: 'en' | 'zh' | 'ms';
}

export default function DSRCalculator({ language = 'en' }: DSRCalculatorProps) {
  // 状态管理
  const [step, setStep] = useState(1);
  const [identityType, setIdentityType] = useState('citizen');
  const [employmentType, setEmploymentType] = useState('salaried');
  const [businessYears, setBusinessYears] = useState(3);
  
  // 收入信息
  const [grossSalary, setGrossSalary] = useState(6000);
  const [epfDeduction, setEpfDeduction] = useState(480);
  const [incomeTax, setIncomeTax] = useState(300);
  const [socso, setSocso] = useState(50);
  const [netIncome, setNetIncome] = useState(5170);
  
  // 现有债务
  const [housingLoan, setHousingLoan] = useState(0);
  const [autoLoan, setAutoLoan] = useState(0);
  const [personalLoan, setPersonalLoan] = useState(0);
  const [ptptn, setPtptn] = useState(0);
  const [creditCards, setCreditCards] = useState<Array<{ used: number; limit: number }>>([]);
  
  // 贷款需求
  const [loanType, setLoanType] = useState('personal');
  const [loanAmount, setLoanAmount] = useState(100000);
  const [loanYears, setLoanYears] = useState(5);
  const [interestRate, setInterestRate] = useState(7);
  
  // 计算结果
  const [totalCommitments, setTotalCommitments] = useState(0);
  const [newMonthlyPayment, setNewMonthlyPayment] = useState(0);
  const [dsr, setDsr] = useState(0);
  const [bankResults, setBankResults] = useState<any[]>([]);
  const [recommendations, setRecommendations] = useState<any[]>([]);

  // 自动计算净收入
  useEffect(() => {
    const calculated = grossSalary - epfDeduction - incomeTax - socso;
    setNetIncome(calculated);
  }, [grossSalary, epfDeduction, incomeTax, socso]);

  // 自动计算EPF（8%）
  useEffect(() => {
    setEpfDeduction(grossSalary * 0.08);
  }, [grossSalary]);

  // 计算总承诺
  useEffect(() => {
    let total = housingLoan + autoLoan + personalLoan + ptptn;
    creditCards.forEach(card => {
      total += card.used * 0.05; // 5%规则
    });
    setTotalCommitments(total);
  }, [housingLoan, autoLoan, personalLoan, ptptn, creditCards]);

  // 计算新贷款月供（平息法简化）
  useEffect(() => {
    const monthlyInterest = (loanAmount * interestRate * loanYears) / 100 / 12 / loanYears;
    const monthlyPrincipal = loanAmount / (loanYears * 12);
    setNewMonthlyPayment(monthlyPrincipal + monthlyInterest);
  }, [loanAmount, loanYears, interestRate]);

  // 计算DSR
  useEffect(() => {
    if (netIncome > 0) {
      const totalWithNewLoan = totalCommitments + newMonthlyPayment;
      const calculatedDsr = (totalWithNewLoan / netIncome) * 100;
      setDsr(calculatedDsr);
    }
  }, [totalCommitments, newMonthlyPayment, netIncome]);

  // 评估8家银行
  useEffect(() => {
    const results = BANK_STANDARDS.map(bank => {
      // 根据收入决定DSR限制
      const dsrLimit = netIncome < 3000 ? bank.dsrLow : bank.dsrHigh;
      
      // 根据就业类型调整收入认定
      let recognizedIncome = netIncome;
      if (employmentType === 'self_employed') {
        recognizedIncome = netIncome * bank.selfEmployedRate;
      }
      
      // 重新计算DSR
      const adjustedDsr = netIncome > 0 ? ((totalCommitments + newMonthlyPayment) / recognizedIncome) * 100 : 0;
      
      // 评估状态
      let status = 'rejected';
      let statusColor = 'red';
      if (adjustedDsr <= dsrLimit) {
        status = 'approved';
        statusColor = 'green';
      } else if (adjustedDsr <= dsrLimit + 10) {
        status = 'risky';
        statusColor = 'yellow';
      }
      
      return {
        ...bank,
        dsrLimit,
        recognizedIncome,
        adjustedDsr,
        status,
        statusColor,
        margin: dsrLimit - adjustedDsr,
      };
    });
    
    setBankResults(results);
    
    // 生成推荐（排序）
    const approved = results
      .filter(r => r.status === 'approved')
      .sort((a, b) => b.margin - a.margin);
    
    setRecommendations(approved);
  }, [dsr, netIncome, employmentType, totalCommitments, newMonthlyPayment]);

  // 添加信用卡
  const addCreditCard = () => {
    setCreditCards([...creditCards, { used: 0, limit: 5000 }]);
  };

  // 移除信用卡
  const removeCreditCard = (index: number) => {
    setCreditCards(creditCards.filter((_, i) => i !== index));
  };

  // 更新信用卡
  const updateCreditCard = (index: number, field: 'used' | 'limit', value: number) => {
    const updated = [...creditCards];
    updated[index][field] = value;
    setCreditCards(updated);
  };

  // DSR状态颜色
  const getDsrStatusColor = () => {
    if (dsr <= 30) return 'text-green-500';
    if (dsr <= 50) return 'text-blue-500';
    if (dsr <= 70) return 'text-yellow-500';
    return 'text-red-500';
  };

  // DSR状态文本
  const getDsrStatusText = () => {
    if (dsr <= 30) return 'Excellent';
    if (dsr <= 50) return 'Good';
    if (dsr <= 70) return 'Fair';
    return 'High Risk';
  };

  return (
    <div className="w-full max-w-7xl mx-auto">
      {/* 进度指示器 */}
      <div className="mb-8 flex items-center justify-between">
        {[1, 2, 3, 4].map((s) => (
          <div key={s} className="flex items-center flex-1">
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
                step >= s ? 'bg-primary text-black' : 'bg-muted text-muted-foreground'
              }`}
            >
              {s}
            </div>
            {s < 4 && (
              <div
                className={`flex-1 h-1 mx-2 ${
                  step > s ? 'bg-primary' : 'bg-muted'
                }`}
              />
            )}
          </div>
        ))}
      </div>

      {/* Step 1: 身份与就业信息 */}
      {step === 1 && (
        <div className="space-y-6">
          <h2 className="text-2xl font-bold">Step 1: Identity & Employment</h2>
          
          <div>
            <label className="block mb-2 font-medium">Identity Type</label>
            <select
              value={identityType}
              onChange={(e) => setIdentityType(e.target.value)}
              className="w-full p-3 rounded-lg bg-muted border border-border"
            >
              {IDENTITY_TYPES.map(type => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block mb-2 font-medium">Employment Type</label>
            <select
              value={employmentType}
              onChange={(e) => setEmploymentType(e.target.value)}
              className="w-full p-3 rounded-lg bg-muted border border-border"
            >
              {EMPLOYMENT_TYPES.map(type => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          {employmentType === 'self_employed' && (
            <div>
              <label className="block mb-2 font-medium">Business Operating Years</label>
              <input
                type="number"
                value={businessYears}
                onChange={(e) => setBusinessYears(Number(e.target.value))}
                className="w-full p-3 rounded-lg bg-muted border border-border"
                min="0"
              />
            </div>
          )}

          <button
            onClick={() => setStep(2)}
            className="w-full py-3 rounded-lg bg-primary text-black font-bold hover:bg-primary/90 transition"
          >
            Next: Income Information
          </button>
        </div>
      )}

      {/* Step 2: 收入信息 */}
      {step === 2 && (
        <div className="space-y-6">
          <h2 className="text-2xl font-bold">Step 2: Income Information</h2>
          
          <div>
            <label className="block mb-2 font-medium">Gross Monthly Salary (RM)</label>
            <input
              type="number"
              value={grossSalary}
              onChange={(e) => setGrossSalary(Number(e.target.value))}
              className="w-full p-3 rounded-lg bg-muted border border-border"
            />
          </div>

          <div>
            <label className="block mb-2 font-medium">EPF Deduction (8%) (RM)</label>
            <input
              type="number"
              value={epfDeduction}
              disabled
              className="w-full p-3 rounded-lg bg-muted border border-border opacity-60"
            />
          </div>

          <div>
            <label className="block mb-2 font-medium">Income Tax (RM)</label>
            <input
              type="number"
              value={incomeTax}
              onChange={(e) => setIncomeTax(Number(e.target.value))}
              className="w-full p-3 rounded-lg bg-muted border border-border"
            />
          </div>

          <div>
            <label className="block mb-2 font-medium">SOCSO (RM)</label>
            <input
              type="number"
              value={socso}
              onChange={(e) => setSocso(Number(e.target.value))}
              className="w-full p-3 rounded-lg bg-muted border border-border"
            />
          </div>

          <div className="p-4 rounded-lg bg-primary/10 border border-primary">
            <div className="flex items-center justify-between">
              <span className="font-bold">Net Income:</span>
              <span className="text-2xl font-bold text-primary">
                RM {netIncome.toLocaleString()}
              </span>
            </div>
          </div>

          <div className="flex gap-4">
            <button
              onClick={() => setStep(1)}
              className="flex-1 py-3 rounded-lg bg-muted text-foreground font-bold hover:bg-muted/80 transition"
            >
              Back
            </button>
            <button
              onClick={() => setStep(3)}
              className="flex-1 py-3 rounded-lg bg-primary text-black font-bold hover:bg-primary/90 transition"
            >
              Next: Existing Debts
            </button>
          </div>
        </div>
      )}

      {/* Step 3: 现有债务 */}
      {step === 3 && (
        <div className="space-y-6">
          <h2 className="text-2xl font-bold">Step 3: Existing Debts</h2>
          
          <div>
            <label className="block mb-2 font-medium">Housing Loan (RM/month)</label>
            <input
              type="number"
              value={housingLoan}
              onChange={(e) => setHousingLoan(Number(e.target.value))}
              className="w-full p-3 rounded-lg bg-muted border border-border"
            />
          </div>

          <div>
            <label className="block mb-2 font-medium">Auto Loan (RM/month)</label>
            <input
              type="number"
              value={autoLoan}
              onChange={(e) => setAutoLoan(Number(e.target.value))}
              className="w-full p-3 rounded-lg bg-muted border border-border"
            />
          </div>

          <div>
            <label className="block mb-2 font-medium">Personal Loan (RM/month)</label>
            <input
              type="number"
              value={personalLoan}
              onChange={(e) => setPersonalLoan(Number(e.target.value))}
              className="w-full p-3 rounded-lg bg-muted border border-border"
            />
          </div>

          <div>
            <label className="block mb-2 font-medium">PTPTN (RM/month)</label>
            <input
              type="number"
              value={ptptn}
              onChange={(e) => setPtptn(Number(e.target.value))}
              className="w-full p-3 rounded-lg bg-muted border border-border"
            />
          </div>

          {/* 信用卡 */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <label className="font-medium">Credit Cards</label>
              <button
                onClick={addCreditCard}
                className="px-4 py-2 rounded-lg bg-primary text-black text-sm font-bold hover:bg-primary/90 transition"
              >
                + Add Card
              </button>
            </div>

            {creditCards.map((card, index) => (
              <div key={index} className="mb-4 p-4 rounded-lg bg-muted border border-border">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium">Card {index + 1}</span>
                  <button
                    onClick={() => removeCreditCard(index)}
                    className="text-red-500 hover:text-red-400 text-sm"
                  >
                    Remove
                  </button>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm mb-1">Used Amount (RM)</label>
                    <input
                      type="number"
                      value={card.used}
                      onChange={(e) => updateCreditCard(index, 'used', Number(e.target.value))}
                      className="w-full p-2 rounded bg-background border border-border"
                    />
                  </div>
                  <div>
                    <label className="block text-sm mb-1">Credit Limit (RM)</label>
                    <input
                      type="number"
                      value={card.limit}
                      onChange={(e) => updateCreditCard(index, 'limit', Number(e.target.value))}
                      className="w-full p-2 rounded bg-background border border-border"
                    />
                  </div>
                </div>
                <div className="mt-2 text-sm text-primary">
                  Monthly Commitment: RM {(card.used * 0.05).toFixed(2)} (5% rule)
                </div>
              </div>
            ))}
          </div>

          <div className="p-4 rounded-lg bg-primary/10 border border-primary">
            <div className="flex items-center justify-between">
              <span className="font-bold">Total Existing Commitments:</span>
              <span className="text-2xl font-bold text-primary">
                RM {totalCommitments.toFixed(2)}
              </span>
            </div>
          </div>

          <div className="flex gap-4">
            <button
              onClick={() => setStep(2)}
              className="flex-1 py-3 rounded-lg bg-muted text-foreground font-bold hover:bg-muted/80 transition"
            >
              Back
            </button>
            <button
              onClick={() => setStep(4)}
              className="flex-1 py-3 rounded-lg bg-primary text-black font-bold hover:bg-primary/90 transition"
            >
              Next: Loan Requirement
            </button>
          </div>
        </div>
      )}

      {/* Step 4: 贷款需求 & 结果 */}
      {step === 4 && (
        <div className="space-y-6">
          <h2 className="text-2xl font-bold">Step 4: Loan Requirement</h2>
          
          <div>
            <label className="block mb-2 font-medium">Loan Type</label>
            <select
              value={loanType}
              onChange={(e) => setLoanType(e.target.value)}
              className="w-full p-3 rounded-lg bg-muted border border-border"
            >
              {LOAN_TYPES.map(type => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block mb-2 font-medium">Loan Amount (RM)</label>
            <input
              type="number"
              value={loanAmount}
              onChange={(e) => setLoanAmount(Number(e.target.value))}
              className="w-full p-3 rounded-lg bg-muted border border-border"
            />
          </div>

          <div>
            <label className="block mb-2 font-medium">Loan Period (Years)</label>
            <input
              type="number"
              value={loanYears}
              onChange={(e) => setLoanYears(Number(e.target.value))}
              className="w-full p-3 rounded-lg bg-muted border border-border"
              min="1"
              max="35"
            />
          </div>

          <div>
            <label className="block mb-2 font-medium">Interest Rate (%)</label>
            <input
              type="number"
              step="0.1"
              value={interestRate}
              onChange={(e) => setInterestRate(Number(e.target.value))}
              className="w-full p-3 rounded-lg bg-muted border border-border"
            />
          </div>

          <div className="p-4 rounded-lg bg-primary/10 border border-primary">
            <div className="flex items-center justify-between">
              <span className="font-bold">Estimated Monthly Payment:</span>
              <span className="text-2xl font-bold text-primary">
                RM {newMonthlyPayment.toFixed(2)}
              </span>
            </div>
          </div>

          {/* DSR结果显示 */}
          <div className="mt-8 p-6 rounded-lg bg-gradient-to-br from-primary/20 to-accent/20 border-2 border-primary">
            <h3 className="text-2xl font-bold mb-4 flex items-center gap-2">
              <Calculator className="w-8 h-8" />
              Your DSR Analysis
            </h3>
            
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="text-center">
                <div className="text-sm text-muted-foreground mb-1">Net Income</div>
                <div className="text-xl font-bold">RM {netIncome.toLocaleString()}</div>
              </div>
              <div className="text-center">
                <div className="text-sm text-muted-foreground mb-1">Total Commitments</div>
                <div className="text-xl font-bold">RM {(totalCommitments + newMonthlyPayment).toFixed(2)}</div>
              </div>
              <div className="text-center">
                <div className="text-sm text-muted-foreground mb-1">Your DSR</div>
                <div className={`text-3xl font-bold ${getDsrStatusColor()}`}>
                  {dsr.toFixed(2)}%
                </div>
                <div className="text-sm font-medium">{getDsrStatusText()}</div>
              </div>
            </div>
          </div>

          {/* 8家银行对比表 */}
          <div className="mt-8">
            <h3 className="text-2xl font-bold mb-4">8 Banks Comparison</h3>
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="bg-muted">
                    <th className="p-3 text-left border border-border">Bank</th>
                    <th className="p-3 text-center border border-border">DSR Limit</th>
                    <th className="p-3 text-center border border-border">Your DSR</th>
                    <th className="p-3 text-center border border-border">Margin</th>
                    <th className="p-3 text-center border border-border">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {bankResults.map((bank) => (
                    <tr key={bank.code} className="hover:bg-muted/50">
                      <td className="p-3 border border-border font-bold">{bank.name}</td>
                      <td className="p-3 text-center border border-border">{bank.dsrLimit}%</td>
                      <td className="p-3 text-center border border-border">{bank.adjustedDsr.toFixed(2)}%</td>
                      <td className={`p-3 text-center border border-border font-bold ${
                        bank.margin > 0 ? 'text-green-500' : 'text-red-500'
                      }`}>
                        {bank.margin > 0 ? '+' : ''}{bank.margin.toFixed(2)}%
                      </td>
                      <td className="p-3 text-center border border-border">
                        {bank.status === 'approved' && (
                          <span className="inline-flex items-center gap-1 text-green-500 font-bold">
                            <CheckCircle className="w-4 h-4" /> Approved
                          </span>
                        )}
                        {bank.status === 'risky' && (
                          <span className="inline-flex items-center gap-1 text-yellow-500 font-bold">
                            <AlertCircle className="w-4 h-4" /> Risky
                          </span>
                        )}
                        {bank.status === 'rejected' && (
                          <span className="inline-flex items-center gap-1 text-red-500 font-bold">
                            <XCircle className="w-4 h-4" /> Rejected
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* 推荐银行 */}
          {recommendations.length > 0 && (
            <div className="mt-8">
              <h3 className="text-2xl font-bold mb-4 flex items-center gap-2">
                <Sparkles className="w-8 h-8 text-primary" />
                Recommended Banks
              </h3>
              <div className="space-y-4">
                {recommendations.slice(0, 3).map((bank, index) => (
                  <div
                    key={bank.code}
                    className="p-6 rounded-lg bg-gradient-to-r from-primary/10 to-accent/10 border border-primary"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <div className="text-2xl font-bold flex items-center gap-2">
                          {index + 1}. {bank.name}
                          <span className="text-primary">
                            {'⭐'.repeat(5 - index)}
                          </span>
                        </div>
                        <div className="text-sm text-muted-foreground">
                          DSR Limit: {bank.dsrLimit}% | Your DSR: {bank.adjustedDsr.toFixed(2)}%
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-3xl font-bold text-green-500">
                          +{bank.margin.toFixed(1)}%
                        </div>
                        <div className="text-sm text-muted-foreground">Safety Margin</div>
                      </div>
                    </div>
                    <div className="mt-4 space-y-2">
                      <div className="flex items-center gap-2 text-sm">
                        <CheckCircle className="w-4 h-4 text-green-500" />
                        <span>
                          {employmentType === 'self_employed' 
                            ? `Self-employed income recognition: ${(bank.selfEmployedRate * 100).toFixed(0)}%`
                            : 'Standard income recognition'}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 text-sm">
                        <CheckCircle className="w-4 h-4 text-green-500" />
                        <span>Approval probability: {bank.margin > 15 ? 'Very High' : bank.margin > 10 ? 'High' : 'Moderate'}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex gap-4 mt-8">
            <button
              onClick={() => setStep(3)}
              className="flex-1 py-3 rounded-lg bg-muted text-foreground font-bold hover:bg-muted/80 transition"
            >
              Back
            </button>
            <button
              onClick={() => window.print()}
              className="flex-1 py-3 rounded-lg bg-primary text-black font-bold hover:bg-primary/90 transition flex items-center justify-center gap-2"
            >
              <Download className="w-5 h-5" />
              Download Report
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
