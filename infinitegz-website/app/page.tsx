import Header from '@/components/Header'
import Hero from '@/components/Hero'
import ProductCards from '@/components/ProductCards'
import ContentSection from '@/components/ContentSection'
import NewsSection from '@/components/NewsSection'
import Footer from '@/components/Footer'
import ScrollProgress from '@/components/ScrollProgress'
import ScrollIndicator from '@/components/ScrollIndicator'
import AnimatedSection from '@/components/AnimatedSection'

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
        
        {/* Products Section - Full Screen with Animation */}
        <AnimatedSection className="snap-section" id="products" direction="up" threshold={0.2}>
          <ProductCards />
        </AnimatedSection>
        
        {/* Features Section - Full Screen with Animation */}
        <AnimatedSection className="snap-section" id="features" direction="up" threshold={0.2} delay={0.1}>
          <ContentSection />
        </AnimatedSection>
        
        {/* News Section - Full Screen with Animation */}
        <AnimatedSection className="snap-section" id="news" direction="up" threshold={0.2} delay={0.2}>
          <NewsSection />
        </AnimatedSection>
        
        {/* Footer Section with Animation */}
        <AnimatedSection className="snap-section" id="contact" direction="fade" threshold={0.1}>
          <Footer />
        </AnimatedSection>
      </main>
    </>
  )
}