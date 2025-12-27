import Header from '@/components/Header'
import Footer from '@/components/Footer'
import ScrollProgress from '@/components/ScrollProgress'
import Link from 'next/link'

export const metadata = {
  title: 'Solutions | INFINITE GZ',
  description: 'Transform your business with comprehensive financial solutions. From loan matching to digital transformation, we provide everything your business needs.',
}

export default function SolutionsPage() {
  return (
    <>
      <ScrollProgress />
      <main className="min-h-screen bg-background">
        <Header />
        
        {/* Hero Section */}
        <section className="min-h-screen flex items-center justify-center border-b border-primary/10 pt-[78px]">
          <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl py-16 sm:py-32">
            <div className="max-w-4xl mx-auto text-center space-y-12">
              <div className="mono-tag text-secondary">
                [ Ask Anything ]
              </div>
              
              <h1 className="text-4xl md:text-6xl lg:text-7xl tracking-tight text-primary leading-tight">
                Get Unfiltered Answers From CreditPilot
              </h1>
              
              <p className="text-xl md:text-2xl text-secondary max-w-3xl mx-auto leading-relaxed">
                Tap Into The Now With Real-Time Analysis, Pulling Fresh, Relevant Data From Malaysian Financial Institutions Instantly.
              </p>
              
              <div className="flex flex-col sm:flex-row gap-4 justify-center pt-8">
                <Link href="https://portal.infinitegz.com" className="btn-xai btn-xai-primary">
                  CreditPilot Web
                </Link>
                <Link href="https://wa.me/60123456789" className="btn-xai">
                  WhatsApp
                </Link>
              </div>
            </div>
          </div>
        </section>

        {/* Image Generation Section */}
        <section className="py-16 sm:py-32 border-b border-primary/10">
          <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl space-y-16">
            <div className="text-center space-y-8">
              <div className="mono-tag text-secondary">
                [ Loan Analysis ]
              </div>
              <h2 className="text-3xl md:text-5xl lg:text-6xl tracking-tight text-primary max-w-3xl mx-auto">
                Transform Requirements Into Financial Realities
              </h2>
            </div>
          </div>
        </section>

        {/* Core Services */}
        <section className="py-16 sm:py-32 border-b border-primary/10">
          <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl space-y-16 sm:space-y-32">
            <div className="max-w-3xl">
              <h2 className="text-3xl md:text-4xl lg:text-5xl tracking-tight text-primary">
                Productivity, Unhinged.
              </h2>
            </div>

            {/* Use Cases Grid */}
            <div className="grid md:grid-cols-3 gap-8">
              {/* Learn from trends */}
              <div className="space-y-6">
                <h3 className="text-2xl md:text-3xl tracking-tight text-primary">
                  Learn From Trends And Insights On 𝕏
                </h3>
                <p className="text-lg text-secondary leading-relaxed">
                  Gain Insights From Trends, Analyzing Real-Time Data And Market Sentiment Across Malaysian Financial Institutions.
                </p>
                <Link href="https://portal.infinitegz.com" className="text-secondary hover:text-primary transition-colors inline-flex items-center gap-2 group">
                  <span>What's New With CreditPilot?</span>
                  <span className="group-hover:translate-x-1 transition-transform">→</span>
                </Link>
              </div>

              {/* Summarize documents */}
              <div className="space-y-6">
                <h3 className="text-2xl md:text-3xl tracking-tight text-primary">
                  Summarize Documents
                </h3>
                <p className="text-lg text-secondary leading-relaxed">
                  Condense Lengthy Financial Documents Into Concise Summaries, Highlighting Key Points And Actionable Findings.
                </p>
                <Link href="https://portal.infinitegz.com" className="text-secondary hover:text-primary transition-colors inline-flex items-center gap-2 group">
                  <span>Analyze This Document</span>
                  <span className="group-hover:translate-x-1 transition-transform">→</span>
                </Link>
              </div>

              {/* Your coding sidekick */}
              <div className="space-y-6">
                <h3 className="text-2xl md:text-3xl tracking-tight text-primary">
                  Your Financial Sidekick
                </h3>
                <p className="text-lg text-secondary leading-relaxed">
                  Receive Financial Guidance, Solutions, And Best Practices For Your Business Without Complex Calculations.
                </p>
                <Link href="https://portal.infinitegz.com" className="text-secondary hover:text-primary transition-colors inline-flex items-center gap-2 group">
                  <span>Calculate My DSR</span>
                  <span className="group-hover:translate-x-1 transition-transform">→</span>
                </Link>
              </div>
            </div>

            {/* CTA Banner */}
            <div className="text-center space-y-8 py-16">
              <p className="text-xl text-secondary">
                Do More With CreditPilot.
              </p>
              <p className="text-2xl md:text-3xl text-primary">
                Unlock A Premium Subscription On INFINITE GZ
              </p>
              <Link href="https://portal.infinitegz.com" className="btn-xai btn-xai-primary inline-flex">
                Sign Up Now
              </Link>
            </div>
          </div>
        </section>

        {/* Deep Dive Features */}
        <section className="py-16 sm:py-32 border-b border-primary/10">
          <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl space-y-32">
            {/* DeepSearch */}
            <div className="space-y-8">
              <h2 className="text-3xl md:text-5xl lg:text-6xl tracking-tight text-primary max-w-4xl">
                Deep Dive With DeepSearch
              </h2>
              <p className="text-xl md:text-2xl text-secondary max-w-3xl">
                Explore The Depths Of Malaysian Financial Market With DeepSearch, Uncovering Hidden Opportunities And Buried Data Effortlessly.
              </p>
              <Link href="https://portal.infinitegz.com" className="btn-xai inline-flex">
                Search Now
              </Link>
            </div>

            {/* Grok Think */}
            <div className="space-y-8">
              <h2 className="text-3xl md:text-5xl lg:text-6xl tracking-tight text-primary max-w-4xl">
                Find Meaning With CreditPilot Think
              </h2>
              <p className="text-xl md:text-2xl text-secondary max-w-3xl">
                Discover Profound Financial Insights With CreditPilot Think, Connecting Dots And Revealing Truths In Complex Loan Structures.
              </p>
              <Link href="https://portal.infinitegz.com" className="btn-xai inline-flex">
                Find Answers
              </Link>
            </div>

            {/* Grok Voice */}
            <div className="space-y-8">
              <h2 className="text-3xl md:text-5xl lg:text-6xl tracking-tight text-primary max-w-4xl">
                Talk With CreditPilot Voice
              </h2>
              <p className="text-xl md:text-2xl text-secondary max-w-3xl">
                Engage In Seamless Conversations With CreditPilot Voice, Experiencing Natural, Fluid Dialogue Like Never Before.
              </p>
              <Link href="https://wa.me/60123456789" className="btn-xai inline-flex">
                Start Talking
              </Link>
            </div>
          </div>
        </section>

        {/* Final CTA */}
        <section className="py-16 sm:py-32">
          <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl">
            <div className="max-w-4xl mx-auto text-center space-y-8">
              <h2 className="text-3xl md:text-5xl lg:text-6xl tracking-tight text-primary">
                Ready To Transform Your Business?
              </h2>
              <p className="text-xl md:text-2xl text-secondary max-w-3xl mx-auto">
                Experience The Future Of Financial Services With INFINITE GZ.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center pt-8">
                <Link href="https://portal.infinitegz.com" className="btn-xai btn-xai-primary">
                  Try CreditPilot Now
                </Link>
                <Link href="https://wa.me/60123456789" className="btn-xai">
                  Contact Advisor
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
