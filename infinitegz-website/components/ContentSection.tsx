'use client'

export default function ContentSection() {
  return (
    <section id="solutions" className="py-32 bg-infinitegz-black">
      <div className="container mx-auto px-6">
        {/* Main Content Block */}
        <div className="max-w-5xl mx-auto text-center mb-20">
          <h2 className="text-4xl md:text-6xl font-bold mb-8">
            Understand Your Finances
          </h2>
          <p className="text-xl text-infinitegz-silver leading-relaxed">
            INFINITE GZ provides comprehensive financial analysis and optimization services.
            We help you navigate the complex world of banking and finance in Malaysia,
            ensuring you get the best deals and maintain optimal financial health.
          </p>
        </div>

        {/* Feature Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-20">
          {[
            {
              title: 'DSR Beautification',
              description: 'Optimize your Debt Service Ratio to improve loan approval chances',
            },
            {
              title: 'Debt Consolidation',
              description: 'Merge multiple debts into one manageable payment with lower interest',
            },
            {
              title: 'Tax Optimization',
              description: '15% tax deduction strategies for individuals and businesses',
            },
            {
              title: 'Credit Score',
              description: 'Improve your credit rating with strategic financial planning',
            },
          ].map((feature, index) => (
            <div
              key={index}
              className="bg-infinitegz-dark border border-infinitegz-gray rounded-xl p-6 hover:border-infinitegz-accent transition-all"
            >
              <h3 className="text-xl font-bold mb-3">{feature.title}</h3>
              <p className="text-infinitegz-silver text-sm leading-relaxed">
                {feature.description}
              </p>
            </div>
          ))}
        </div>

        {/* CreditPilot Details */}
        <div className="max-w-4xl mx-auto bg-infinitegz-dark border border-infinitegz-gray rounded-2xl p-12">
          <h3 className="text-3xl font-bold mb-6">Do more with CreditPilot</h3>
          <div className="space-y-6 text-infinitegz-silver">
            <p className="leading-relaxed">
              <strong className="text-infinitegz-white">Smart Loan Matching:</strong> Our AI-powered system analyzes your financial profile 
              and matches you with the best loan products from all legitimate banks, digital banks, and fintech companies in Malaysia.
            </p>
            <p className="leading-relaxed">
              <strong className="text-infinitegz-white">Comprehensive Services:</strong> Beyond loans, we offer 8 complementary services 
              including business planning, insurance consultation, e-commerce setup, accounting, and credit card management - all free for loan clients.
            </p>
            <p className="leading-relaxed">
              <strong className="text-infinitegz-white">Zero Upfront Fees:</strong> We only charge upon successful loan approval. 
              Our success-based model ensures we're fully committed to getting you the best possible outcome.
            </p>
            <p className="leading-relaxed">
              <strong className="text-infinitegz-white">100% Legal & Compliant:</strong> We only work with licensed financial institutions. 
              No loan sharks, no illegal lending - your financial safety is our priority.
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}
