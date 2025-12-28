import Header from '@/components/Header'
import Hero from '@/components/Hero'
import ProductCards from '@/components/ProductCards'
import ContentSection from '@/components/ContentSection'
import NewsSection from '@/components/NewsSection'
import Footer from '@/components/Footer'
import ScrollProgress from '@/components/ScrollProgress'
import ScrollIndicator from '@/components/ScrollIndicator'

export default function Home() {
  return (
    <>
      <ScrollProgress />
      <ScrollIndicator />
      <main className="min-h-screen relative z-10">
        <Header />
        
        {/* Hero Section - Full Screen */}
        <section id="hero" className="snap-section">
          <Hero />
        </section>
        
        {/* Products Section - Full Screen */}
        <section id="products" className="snap-section">
          <ProductCards />
        </section>
        
        {/* Features Section - Full Screen */}
        <section id="features" className="snap-section">
          <ContentSection />
        </section>
        
        {/* News Section - Full Screen */}
        <section id="news" className="snap-section">
          <NewsSection />
        </section>
        
        {/* Footer Section */}
        <section id="contact" className="snap-section">
          <Footer />
        </section>
      </main>
    </>
  )
}