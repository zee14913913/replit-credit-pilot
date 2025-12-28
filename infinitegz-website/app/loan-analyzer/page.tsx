'use client'

import { useState } from 'react'
import Header from '@/components/Header'
import Footer from '@/components/Footer'
import ScrollProgress from '@/components/ScrollProgress'
import { useLanguage } from '@/contexts/LanguageContext'
import { 
  calculateNetIncome, 
  calculateMonthlyCommitments, 
  performDSRCalculation,
  type IncomeInfo,
  type DebtCommitment 
} from '@/lib/dsrCalculator'
import { 
  getRecommendedBanks,
  type ApplicantIdentity,
  type EmploymentType 
} from '@/lib/bankStandardsReal2025'

export default function LoanAnalyzerPage() {
  const { t } = useLanguage()
  
  // 步骤状态
  const [currentStep, setCurrentStep] = useState(1)
  
  // 用户输入数据
  const [identity, setIdentity] = useState<ApplicantIdentity>('malaysian_citizen')
  const [employmentType, setEmploymentType] = useState<EmploymentType>('salaried')
  const [businessYears, setBusinessYears] = useState<number>(0)
  
  // 收入信息
  const [incomeInfo, setIncomeInfo] = useState<IncomeInfo>({
    grossSalary: 0,
    epfDeduction: 0,
    incomeTax: 0,
    socso: 0,
    allowances: 0,
    bonusMonthly: 0
  })
  
  // 现有债务
  const [debts, setDebts] = useState<DebtCommitment[]>([])
  
  // 新贷款
  const [newLoanAmount, setNewLoanAmount] = useState<number>(0)
  const [newLoanYears, setNewLoanYears] = useState<number>(5)
  
  // 计算结果
  const [result, setResult] = useState<any>(null)
  const [recommendations, setRecommendations] = useState<any[]>([])
  
  // 自动计算 EPF (8%)
  const handleGrossSalaryChange = (value: number) => {
    setIncomeInfo(prev => ({
      ...prev,
      grossSalary: value,
      epfDeduction: value * 0.08
    }))
  }
  
  // 添加债务
  const addDebt = () => {
    setDebts([...debts, {
      type: 'personal',
      monthlyPayment: 0
    }])
  }
  
  // 更新债务
  const updateDebt = (index: number, field: string, value: any) => {
    const newDebts = [...debts]
    newDebts[index] = { ...newDebts[index], [field]: value }
    setDebts(newDebts)
  }
  
  // 删除债务
  const removeDebt = (index: number) => {
    setDebts(debts.filter((_, i) => i !== index))
  }
  
  // 计算分析
  const performAnalysis = () => {
    // 估算新贷款月供（平息法）
    const estimatedMonthly = newLoanAmount > 0 
      ? ((newLoanAmount * newLoanYears * 0.07) + newLoanAmount) / (newLoanYears * 12)
      : 0
    
    // 执行 DSR 计算
    const dsrResult = performDSRCalculation(
      incomeInfo,
      debts,
      estimatedMonthly,
      70 // 默认 DSR 限制
    )
    
    setResult(dsrResult)
    
    // 获取银行推荐
    const bankRecs = getRecommendedBanks(
      identity,
      employmentType,
      dsrResult.netIncome,
      'personal'
    )
    
    setRecommendations(bankRecs)
  }
  
  return (
    <>
      <ScrollProgress />
      <main className="min-h-screen bg-[rgb(10,10,10)]">
        <Header />
        
        {/* Compact Hero Section */}
        <section className="border-b border-border pt-24 pb-12">
          <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl">
            <div className="text-center space-y-6">
              <div className="mono-tag text-secondary text-sm">
                [ SMART LOAN ANALYZER ]
              </div>
              
              <h1 className="text-primary text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight">
                智能贷款分析器
              </h1>
              
              <p className="text-secondary text-lg max-w-2xl mx-auto">
                基于2025年真实银行标准，精准匹配8家银行，个性化策略建议
              </p>
            </div>
          </div>
        </section>

        {/* Interactive Tool Section - Split Layout */}
        <section className="border-b border-border py-8">
          <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl">
            <div className="grid lg:grid-cols-2 gap-8">
              
              {/* LEFT SIDE - Input Form */}
              <div className="space-y-6">
                <div className="border border-border rounded-lg p-6 bg-gradient-to-b from-secondary/5 to-transparent">
                  
                  {/* Step 1: Identity */}
                  <div className="space-y-4 mb-8">
                    <div className="flex items-center justify-between">
                      <h3 className="text-primary text-lg font-semibold flex items-center gap-2">
                        <span className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary text-sm">1</span>
                        身份类型
                      </h3>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-3">
                      {[
                        { value: 'malaysian_citizen', label: '马来西亚公民' },
                        { value: 'permanent_resident', label: '永久居民 (PR)' },
                        { value: 'foreigner', label: '外国人' },
                        { value: 'government_employee', label: '公务员' },
                        { value: 'glc_employee', label: 'GLC员工' },
                        { value: 'self_employed', label: '自雇企业主' },
                      ].map((option) => (
                        <button
                          key={option.value}
                          onClick={() => setIdentity(option.value as ApplicantIdentity)}
                          className={`p-3 rounded-lg border text-sm transition-all ${
                            identity === option.value
                              ? 'border-primary bg-primary/10 text-primary'
                              : 'border-border bg-transparent text-secondary hover:border-primary/50'
                          }`}
                        >
                          {option.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Step 2: Employment Type */}
                  <div className="space-y-4 mb-8 pt-6 border-t border-border">
                    <h3 className="text-primary text-lg font-semibold flex items-center gap-2">
                      <span className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary text-sm">2</span>
                      就业类型
                    </h3>
                    
                    <div className="grid grid-cols-2 gap-3">
                      {[
                        { value: 'salaried', label: '受薪员工' },
                        { value: 'self_employed', label: '自雇' },
                        { value: 'government', label: '政府' },
                        { value: 'contract', label: '合约工' },
                      ].map((option) => (
                        <button
                          key={option.value}
                          onClick={() => setEmploymentType(option.value as EmploymentType)}
                          className={`p-3 rounded-lg border text-sm transition-all ${
                            employmentType === option.value
                              ? 'border-primary bg-primary/10 text-primary'
                              : 'border-border bg-transparent text-secondary hover:border-primary/50'
                          }`}
                        >
                          {option.label}
                        </button>
                      ))}
                    </div>
                    
                    {employmentType === 'self_employed' && (
                      <div className="mt-4">
                        <label className="text-secondary text-sm mb-2 block">营业年限</label>
                        <input
                          type="number"
                          value={businessYears}
                          onChange={(e) => setBusinessYears(Number(e.target.value))}
                          className="w-full px-4 py-3 rounded-lg border border-border bg-background text-primary focus:border-primary focus:outline-none"
                          placeholder="3"
                          min="0"
                        />
                      </div>
                    )}
                  </div>

                  {/* Step 3: Income */}
                  <div className="space-y-4 mb-8 pt-6 border-t border-border">
                    <h3 className="text-primary text-lg font-semibold flex items-center gap-2">
                      <span className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary text-sm">3</span>
                      收入信息
                    </h3>
                    
                    <div className="space-y-3">
                      <div>
                        <label className="text-secondary text-sm mb-2 block">月度总薪资 (RM)</label>
                        <input
                          type="number"
                          value={incomeInfo.grossSalary || ''}
                          onChange={(e) => handleGrossSalaryChange(Number(e.target.value))}
                          className="w-full px-4 py-3 rounded-lg border border-border bg-background text-primary focus:border-primary focus:outline-none"
                          placeholder="6000"
                        />
                      </div>
                      
                      <div>
                        <label className="text-secondary text-sm mb-2 block">EPF 扣除 (8%) - 自动计算</label>
                        <input
                          type="number"
                          value={incomeInfo.epfDeduction}
                          readOnly
                          className="w-full px-4 py-3 rounded-lg border border-border bg-secondary/5 text-secondary cursor-not-allowed"
                        />
                      </div>
                      
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="text-secondary text-sm mb-2 block">所得税 (RM)</label>
                          <input
                            type="number"
                            value={incomeInfo.incomeTax || ''}
                            onChange={(e) => setIncomeInfo({...incomeInfo, incomeTax: Number(e.target.value)})}
                            className="w-full px-4 py-3 rounded-lg border border-border bg-background text-primary focus:border-primary focus:outline-none"
                            placeholder="300"
                          />
                        </div>
                        
                        <div>
                          <label className="text-secondary text-sm mb-2 block">SOCSO (RM)</label>
                          <input
                            type="number"
                            value={incomeInfo.socso || ''}
                            onChange={(e) => setIncomeInfo({...incomeInfo, socso: Number(e.target.value)})}
                            className="w-full px-4 py-3 rounded-lg border border-border bg-background text-primary focus:border-primary focus:outline-none"
                            placeholder="50"
                          />
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Step 4: Existing Debts */}
                  <div className="space-y-4 mb-8 pt-6 border-t border-border">
                    <div className="flex items-center justify-between">
                      <h3 className="text-primary text-lg font-semibold flex items-center gap-2">
                        <span className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary text-sm">4</span>
                        现有债务
                      </h3>
                      <button
                        onClick={addDebt}
                        className="text-primary text-sm hover:underline"
                      >
                        + 添加债务
                      </button>
                    </div>
                    
                    {debts.length === 0 ? (
                      <p className="text-secondary text-sm">暂无债务</p>
                    ) : (
                      <div className="space-y-3">
                        {debts.map((debt, index) => (
                          <div key={index} className="p-4 border border-border rounded-lg space-y-3">
                            <div className="flex items-center justify-between">
                              <select
                                value={debt.type}
                                onChange={(e) => updateDebt(index, 'type', e.target.value)}
                                className="px-3 py-2 rounded border border-border bg-background text-primary text-sm"
                              >
                                <option value="housing">房贷</option>
                                <option value="car">车贷</option>
                                <option value="personal">个人贷</option>
                                <option value="ptptn">PTPTN</option>
                                <option value="credit_card">信用卡</option>
                              </select>
                              
                              <button
                                onClick={() => removeDebt(index)}
                                className="text-red-500 text-sm hover:underline"
                              >
                                删除
                              </button>
                            </div>
                            
                            {debt.type === 'credit_card' ? (
                              <div>
                                <label className="text-secondary text-xs mb-1 block">已用额度 (RM)</label>
                                <input
                                  type="number"
                                  value={debt.creditCardUsed || ''}
                                  onChange={(e) => updateDebt(index, 'creditCardUsed', Number(e.target.value))}
                                  className="w-full px-3 py-2 rounded border border-border bg-background text-primary text-sm"
                                  placeholder="2000"
                                />
                                <p className="text-xs text-secondary mt-1">月度承诺 = 已用额度 × 5%</p>
                              </div>
                            ) : (
                              <div>
                                <label className="text-secondary text-xs mb-1 block">月供 (RM)</label>
                                <input
                                  type="number"
                                  value={debt.monthlyPayment || ''}
                                  onChange={(e) => updateDebt(index, 'monthlyPayment', Number(e.target.value))}
                                  className="w-full px-3 py-2 rounded border border-border bg-background text-primary text-sm"
                                  placeholder="800"
                                />
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Step 5: New Loan */}
                  <div className="space-y-4 mb-8 pt-6 border-t border-border">
                    <h3 className="text-primary text-lg font-semibold flex items-center gap-2">
                      <span className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary text-sm">5</span>
                      新贷款申请
                    </h3>
                    
                    <div className="space-y-3">
                      <div>
                        <label className="text-secondary text-sm mb-2 block">贷款金额 (RM)</label>
                        <input
                          type="number"
                          value={newLoanAmount || ''}
                          onChange={(e) => setNewLoanAmount(Number(e.target.value))}
                          className="w-full px-4 py-3 rounded-lg border border-border bg-background text-primary focus:border-primary focus:outline-none"
                          placeholder="50000"
                        />
                      </div>
                      
                      <div>
                        <label className="text-secondary text-sm mb-2 block">贷款期限（年）</label>
                        <input
                          type="number"
                          value={newLoanYears}
                          onChange={(e) => setNewLoanYears(Number(e.target.value))}
                          className="w-full px-4 py-3 rounded-lg border border-border bg-background text-primary focus:border-primary focus:outline-none"
                          placeholder="5"
                          min="1"
                          max="7"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Calculate Button */}
                  <button
                    onClick={performAnalysis}
                    className="w-full py-4 rounded-lg bg-primary text-background font-semibold hover:bg-primary/90 transition-all"
                  >
                    开始分析
                  </button>
                </div>
              </div>

              {/* RIGHT SIDE - Results */}
              <div className="space-y-6">
                {!result ? (
                  <div className="border border-border rounded-lg p-8 text-center space-y-4">
                    <div className="w-16 h-16 mx-auto rounded-full bg-secondary/10 flex items-center justify-center">
                      <svg className="w-8 h-8 text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                      </svg>
                    </div>
                    <p className="text-secondary">填写左侧信息，点击"开始分析"查看结果</p>
                  </div>
                ) : (
                  <>
                    {/* DSR Dashboard */}
                    <div className="border border-border rounded-lg p-6 space-y-4">
                      <h3 className="text-primary text-xl font-semibold">财务概况</h3>
                      
                      <div className="grid grid-cols-2 gap-4">
                        <div className="p-4 rounded-lg bg-secondary/5">
                          <p className="text-secondary text-sm mb-1">净收入</p>
                          <p className="text-primary text-2xl font-bold">RM {result.netIncome.toFixed(0)}</p>
                        </div>
                        
                        <div className="p-4 rounded-lg bg-secondary/5">
                          <p className="text-secondary text-sm mb-1">总承诺</p>
                          <p className="text-primary text-2xl font-bold">RM {result.totalCommitments.toFixed(0)}</p>
                        </div>
                      </div>
                      
                      <div className="p-6 rounded-lg bg-gradient-to-br from-primary/10 to-transparent border border-primary/20">
                        <div className="flex items-center justify-between mb-2">
                          <p className="text-secondary text-sm">债务服务比 (DSR)</p>
                          <p className={`text-3xl font-bold ${
                            result.assessment.status === 'excellent' ? 'text-green-500' :
                            result.assessment.status === 'good' ? 'text-blue-500' :
                            result.assessment.status === 'fair' ? 'text-yellow-500' :
                            result.assessment.status === 'risky' ? 'text-orange-500' :
                            'text-red-500'
                          }`}>
                            {result.projectedDSR.toFixed(1)}%
                          </p>
                        </div>
                        
                        <div className="w-full h-2 bg-secondary/20 rounded-full overflow-hidden">
                          <div 
                            className={`h-full transition-all ${
                              result.assessment.status === 'excellent' ? 'bg-green-500' :
                              result.assessment.status === 'good' ? 'bg-blue-500' :
                              result.assessment.status === 'fair' ? 'bg-yellow-500' :
                              result.assessment.status === 'risky' ? 'bg-orange-500' :
                              'bg-red-500'
                            }`}
                            style={{ width: `${Math.min(result.projectedDSR, 100)}%` }}
                          />
                        </div>
                        
                        <p className="text-secondary text-sm mt-2">{result.assessment.message}</p>
                      </div>
                      
                      {result.availableCommitment > 0 && (
                        <div className="p-4 rounded-lg border border-border">
                          <p className="text-secondary text-sm mb-1">可用额度（月供）</p>
                          <p className="text-primary text-xl font-semibold">RM {result.availableCommitment.toFixed(0)}</p>
                          {result.maxLoanAmount && (
                            <p className="text-secondary text-xs mt-1">约可贷 RM {result.maxLoanAmount.toFixed(0)}</p>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Bank Recommendations */}
                    <div className="border border-border rounded-lg p-6 space-y-4">
                      <h3 className="text-primary text-xl font-semibold">推荐银行</h3>
                      
                      {recommendations.length === 0 ? (
                        <p className="text-secondary text-sm">暂无推荐</p>
                      ) : (
                        <div className="space-y-3">
                          {recommendations.slice(0, 5).map((rec, index) => (
                            <div 
                              key={index}
                              className="p-4 rounded-lg border border-border hover:border-primary/50 transition-all cursor-pointer group"
                            >
                              <div className="flex items-start justify-between mb-2">
                                <div className="flex items-center gap-2">
                                  <span className="flex items-center justify-center w-6 h-6 rounded-full bg-primary/10 text-primary text-xs font-bold">
                                    {index + 1}
                                  </span>
                                  <h4 className="text-primary font-semibold group-hover:text-primary/80">
                                    {rec.bank.bankName}
                                  </h4>
                                </div>
                                <div className="flex gap-0.5">
                                  {[...Array(5)].map((_, i) => (
                                    <svg
                                      key={i}
                                      className={`w-4 h-4 ${i < Math.round(rec.score / 20) ? 'text-yellow-500' : 'text-secondary/30'}`}
                                      fill="currentColor"
                                      viewBox="0 0 20 20"
                                    >
                                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                                    </svg>
                                  ))}
                                </div>
                              </div>
                              
                              <div className="space-y-1 text-sm">
                                {rec.reasons.slice(0, 2).map((reason: string, i: number) => (
                                  <p key={i} className="text-secondary flex items-start gap-2">
                                    <span className="text-primary mt-0.5">•</span>
                                    <span>{reason}</span>
                                  </p>
                                ))}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Optimization Suggestions */}
                    {result.assessment.recommendations.length > 0 && (
                      <div className="border border-border rounded-lg p-6 space-y-4">
                        <h3 className="text-primary text-xl font-semibold">优化建议</h3>
                        
                        <div className="space-y-2">
                          {result.assessment.recommendations.map((rec: string, index: number) => (
                            <div key={index} className="flex items-start gap-3 p-3 rounded-lg bg-secondary/5">
                              <svg className="w-5 h-5 text-primary mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                              </svg>
                              <p className="text-secondary text-sm">{rec}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* CTA */}
                    <div className="border border-primary/20 rounded-lg p-6 text-center space-y-4 bg-gradient-to-b from-primary/5 to-transparent">
                      <h3 className="text-primary text-lg font-semibold">需要专业咨询？</h3>
                      <p className="text-secondary text-sm">联系我们的贷款顾问，获取完整个性化方案</p>
                      <div className="flex flex-wrap gap-3 justify-center">
                        <a
                          href="https://wa.me/60123456789"
                          className="px-6 py-3 rounded-full bg-primary text-background font-semibold hover:bg-primary/90 transition-all"
                        >
                          WhatsApp 咨询
                        </a>
                        <a
                          href="https://portal.infinitegz.com/advisory"
                          className="px-6 py-3 rounded-full border border-primary/30 text-primary hover:bg-primary/10 transition-all"
                        >
                          预约顾问
                        </a>
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        </section>

        <Footer />
      </main>
    </>
  )
}
