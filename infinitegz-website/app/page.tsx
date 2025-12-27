import Header from '@/components/Header'
import Hero from '@/components/Hero'
import ProductCards from '@/components/ProductCards'
import ContentSection from '@/components/ContentSection'
import NewsSection from '@/components/NewsSection'
import Footer from '@/components/Footer'

export default function Home() {
  return (
    <main className="min-h-screen">
      <Header />
      <Hero />
      <ProductCards />
      <ContentSection />
      <NewsSection />
      <Footer />
    </main>
  )
}
