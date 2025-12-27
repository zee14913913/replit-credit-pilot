'use client'

const newsItems = [
  {
    date: 'December 20, 2024',
    title: 'New OPR Rate Changes: How It Affects Your Loans',
    category: 'Policy Update',
    description: 'Bank Negara Malaysia announces new overnight policy rate. Learn how this impacts your existing and future loans.',
  },
  {
    date: 'December 15, 2024',
    title: 'Success Story: RM 2M Business Loan Approved',
    category: 'Case Study',
    description: 'How we helped a traditional manufacturing business secure financing for digital transformation and expansion.',
  },
  {
    date: 'December 10, 2024',
    title: 'Year-End Tax Planning Tips for 2024',
    category: 'Financial Tips',
    description: 'Maximize your tax relief claims and optimize your financial position before year-end deadline.',
  },
  {
    date: 'December 5, 2024',
    title: 'Digital Banks vs Traditional Banks: Loan Comparison',
    category: 'Guide',
    description: 'Comprehensive comparison of loan products from digital banks and traditional institutions in Malaysia.',
  },
  {
    date: 'November 28, 2024',
    title: 'Credit Card Debt Management Strategies',
    category: 'Financial Tips',
    description: 'Learn how to manage multiple credit cards, avoid late fees, and optimize your credit utilization ratio.',
  },
  {
    date: 'November 20, 2024',
    title: 'E-Commerce Success: Traditional Business Goes Digital',
    category: 'Case Study',
    description: 'How a 40-year-old retail business tripled revenue through digital transformation and online sales.',
  },
]

export default function NewsSection() {
  return (
    <section id="resources" className="py-32 bg-infinitegz-dark">
      <div className="container mx-auto px-6">
        {/* Section Header */}
        <div className="mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-4">Latest News & Updates</h2>
          <p className="text-xl text-infinitegz-silver">
            Stay informed with the latest financial news, loan policies, and success stories
          </p>
        </div>

        {/* News Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {newsItems.map((item, index) => (
            <article
              key={index}
              className="bg-infinitegz-black border border-infinitegz-gray rounded-xl p-6 hover:border-infinitegz-accent transition-all hover:scale-105 transform cursor-pointer"
            >
              {/* Date and Category */}
              <div className="flex items-center justify-between mb-4">
                <span className="text-sm text-infinitegz-silver">{item.date}</span>
                <span className="text-xs bg-infinitegz-light-gray text-infinitegz-accent px-3 py-1 rounded-full">
                  {item.category}
                </span>
              </div>

              {/* Title */}
              <h3 className="text-xl font-bold mb-3 hover:text-infinitegz-accent transition-colors">
                {item.title}
              </h3>

              {/* Description */}
              <p className="text-sm text-infinitegz-silver leading-relaxed">
                {item.description}
              </p>

              {/* Read More Link */}
              <div className="mt-4">
                <span className="text-sm text-infinitegz-accent hover:underline">
                  Read more →
                </span>
              </div>
            </article>
          ))}
        </div>

        {/* View All Button */}
        <div className="text-center mt-12">
          <button className="bg-infinitegz-white text-infinitegz-black px-8 py-3 rounded-full font-medium hover:bg-infinitegz-accent transition-all hover:scale-105 transform">
            View All News
          </button>
        </div>
      </div>
    </section>
  )
}
