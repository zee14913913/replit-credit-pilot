'use client'

import Link from 'next/link'

const products = [
  {
    title: 'CreditPilot',
    description: 'Intelligent loan analysis system that finds the best loan products from all Malaysian banks and fintech companies.',
    features: ['DSR Beautification', 'Best Rate Matching', 'Smart Recommendations'],
    cta: 'USE NOW',
    link: 'https://portal.infinitegz.com/creditpilot',
  },
  {
    title: 'Loan Advisory',
    description: 'Professional consultation for all types of loans - housing, automotive, and business financing with zero upfront fees.',
    features: ['Zero Upfront Cost', 'Expert Guidance', 'Success-based Fee'],
    cta: 'CONSULT NOW',
    link: 'https://portal.infinitegz.com/advisory',
  },
  {
    title: 'Digitalization & Accounting',
    description: 'Complete digital transformation for traditional businesses including e-commerce setup, accounting, and tax optimization.',
    features: ['Online Store Setup', 'Tax Optimization', 'Accounting Services'],
    cta: 'LEARN MORE',
    link: 'https://portal.infinitegz.com/digital',
  },
]

export default function ProductCards() {
  return (
    <section id="products" className="py-20 bg-infinitegz-black">
      <div className="container mx-auto px-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {products.map((product, index) => (
            <div
              key={index}
              className="group bg-infinitegz-dark border border-infinitegz-gray rounded-2xl p-8 hover:border-infinitegz-accent transition-all duration-300 hover:scale-105 transform"
            >
              {/* Title */}
              <h3 className="text-2xl font-bold mb-4">{product.title}</h3>

              {/* Description */}
              <p className="text-infinitegz-silver mb-6 leading-relaxed">
                {product.description}
              </p>

              {/* Features */}
              <ul className="mb-8 space-y-2">
                {product.features.map((feature, idx) => (
                  <li key={idx} className="flex items-center text-sm text-infinitegz-silver">
                    <span className="w-1.5 h-1.5 bg-infinitegz-accent rounded-full mr-3"></span>
                    {feature}
                  </li>
                ))}
              </ul>

              {/* CTA Button */}
              <Link
                href={product.link}
                className="inline-block w-full text-center bg-infinitegz-white text-infinitegz-black px-6 py-3 rounded-full font-medium hover:bg-infinitegz-accent transition-all group-hover:scale-105 transform"
              >
                {product.cta}
              </Link>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
