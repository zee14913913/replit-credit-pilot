import Header from '@/components/Header'
import Footer from '@/components/Footer'
import ScrollProgress from '@/components/ScrollProgress'
import Link from 'next/link'

export const metadata = {
  title: 'Resources | INFINITE GZ',
  description: 'We go further, faster. Unprecedented scale and capabilities to transform Malaysian business financing.',
}

export default function ResourcesPage() {
  return (
    <>
      <ScrollProgress />
      <main className="min-h-screen bg-background">
        <Header />
        
        {/* Hero Section */}
        <section className="min-h-screen flex items-center justify-center border-b border-primary/10 pt-[78px]">
          <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl py-16 sm:py-32">
            <div className="max-w-5xl mx-auto text-center space-y-12">
              <h1 className="text-4xl md:text-6xl lg:text-7xl tracking-tight text-primary leading-tight">
                We Go Further, Faster
              </h1>
              
              <p className="text-xl md:text-2xl text-secondary max-w-4xl mx-auto leading-relaxed">
                We Were Told It Would Take 24 Months To Build. So We Took The Project Into Our Own Hands, Questioned Everything, Removed Whatever Was Unnecessary, And Accomplished Our Goal In Four Months.
              </p>
            </div>
          </div>
        </section>

        {/* Unprecedented Scale */}
        <section className="py-16 sm:py-32 border-b border-primary/10">
          <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl space-y-16">
            <div className="max-w-4xl">
              <h2 className="text-3xl md:text-5xl lg:text-6xl tracking-tight text-primary">
                Unprecedented Scale
              </h2>
              <p className="text-xl md:text-2xl text-secondary mt-8">
                We Doubled Our Capacity At An Unprecedented Rate, With A Roadmap To Serve 1M Businesses. Progress In Fintech Is Driven By Scale And No One Has Come Close To Building At This Magnitude And Speed.
              </p>
            </div>

            {/* Statistics Grid */}
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
              <div className="space-y-4 p-8 border border-primary/10">
                <div className="mono-tag text-secondary text-sm">
                  Partner Institutions
                </div>
                <div className="text-4xl md:text-5xl font-normal text-primary">
                  50+
                </div>
                <div className="text-sm text-secondary">
                  Financial Institutions
                </div>
              </div>

              <div className="space-y-4 p-8 border border-primary/10">
                <div className="mono-tag text-secondary text-sm">
                  Total Loans Facilitated
                </div>
                <div className="text-4xl md:text-5xl font-normal text-primary">
                  RM 500M+
                </div>
                <div className="text-sm text-secondary">
                  Loans Disbursed
                </div>
              </div>

              <div className="space-y-4 p-8 border border-primary/10">
                <div className="mono-tag text-secondary text-sm">
                  Analysis Speed
                </div>
                <div className="text-4xl md:text-5xl font-normal text-primary">
                  2 Min
                </div>
                <div className="text-sm text-secondary">
                  Average Processing Time
                </div>
              </div>

              <div className="space-y-4 p-8 border border-primary/10">
                <div className="mono-tag text-secondary text-sm">
                  Client Satisfaction
                </div>
                <div className="text-4xl md:text-5xl font-normal text-primary">
                  98%
                </div>
                <div className="text-sm text-secondary">
                  Success Rate
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Our Path of Progress */}
        <section className="py-16 sm:py-32 border-b border-primary/10">
          <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl space-y-16">
            <div className="max-w-4xl">
              <h2 className="text-3xl md:text-5xl lg:text-6xl tracking-tight text-primary">
                Our Path Of Progress
              </h2>
              <p className="text-xl md:text-2xl text-secondary mt-8">
                We're Moving Toward A Future Where We Will Harness Our Platform's Full Power To Solve Intractable Financial Problems. What's One Seemingly Impossible Question You'd Answer For Malaysian Businesses?
              </p>
            </div>

            {/* Timeline */}
            <div className="space-y-8">
              {[
                {
                  year: '2020',
                  title: 'Company Founded',
                  description: 'Started with a mission to democratize access to financial services in Malaysia.',
                },
                {
                  year: '2021',
                  title: 'CreditPilot Launch',
                  description: 'Launched AI-powered loan matching platform, serving first 500 businesses.',
                },
                {
                  year: '2022',
                  title: 'Service Expansion',
                  description: 'Expanded to digital transformation, accounting, and advisory services.',
                },
                {
                  year: '2023',
                  title: 'RM 500M Milestone',
                  description: 'Facilitated over RM 500 million in loans with 50+ partner institutions.',
                },
                {
                  year: '2024',
                  title: 'Innovation & Scale',
                  description: 'Serving 5,000+ businesses nationwide with advanced AI capabilities.',
                },
              ].map((item, index) => (
                <div key={index} className="grid md:grid-cols-[200px,1fr] gap-8 border-l border-primary/20 pl-8 pb-8">
                  <div className="mono-tag text-2xl md:text-3xl text-primary">
                    {item.year}
                  </div>
                  <div className="space-y-4">
                    <h3 className="text-2xl md:text-3xl tracking-tight text-primary">
                      {item.title}
                    </h3>
                    <p className="text-lg text-secondary">
                      {item.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Latest News Section */}
        <section className="py-16 sm:py-32 border-b border-primary/10">
          <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl space-y-16">
            <h2 className="text-3xl md:text-5xl lg:text-6xl tracking-tight text-primary">
              Latest News
            </h2>

            <div className="grid md:grid-cols-3 gap-8">
              {[
                {
                  date: 'December 20, 2024',
                  title: 'CreditPilot 4.1 Release',
                  category: 'Product Update',
                },
                {
                  date: 'December 15, 2024',
                  title: 'RM 500M Milestone',
                  category: 'Company News',
                },
                {
                  date: 'December 10, 2024',
                  title: 'OPR Rate Changes',
                  category: 'Market Update',
                },
              ].map((news, index) => (
                <Link
                  key={index}
                  href="/news"
                  className="group space-y-4 p-6 border border-primary/10 hover:border-primary/30 transition-colors duration-200"
                >
                  <div className="mono-tag text-xs text-secondary">
                    {news.date}
                  </div>
                  <h3 className="text-xl md:text-2xl tracking-tight text-primary group-hover:text-secondary transition-colors">
                    {news.title}
                  </h3>
                  <div className="mono-tag text-xs text-secondary">
                    {news.category}
                  </div>
                </Link>
              ))}
            </div>

            <div className="text-center">
              <Link href="/news" className="btn-xai">
                View All News
              </Link>
            </div>
          </div>
        </section>

        {/* Final CTA */}
        <section className="py-16 sm:py-32">
          <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl">
            <div className="max-w-4xl mx-auto text-center space-y-8">
              <h2 className="text-3xl md:text-5xl lg:text-6xl tracking-tight text-primary">
                Ready To Experience Unprecedented Scale?
              </h2>
              <p className="text-xl md:text-2xl text-secondary max-w-3xl mx-auto">
                Join 5,000+ Malaysian Businesses Transforming Their Financial Future With INFINITE GZ.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center pt-8">
                <Link href="https://portal.infinitegz.com" className="btn-xai btn-xai-primary">
                  Get Started Now
                </Link>
                <Link href="/solutions" className="btn-xai">
                  Explore Solutions
                </Link>
              </div>
            </div>
          </div>
        </section>

        <Footer />
      </main>
    </>
  )
}
