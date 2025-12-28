import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import ScrollProgress from '../components/ScrollProgress'
import PageIndicator from '../components/PageIndicator'
import Preloader from '../components/Preloader'
import GalaxyBackground from '../components/GalaxyBackground'
import ForceVisible from '../components/ForceVisible'
import { LanguageProvider } from '@/contexts/LanguageContext'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'INFINITE GZ - Loans & Financial Optimization',
  description: 'One-stop solution for loans, financial optimization, and digital advisory services in Malaysia',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="scroll-smooth">
      <body className={inter.className}>
        <LanguageProvider>
          <ForceVisible />
          <Preloader />
          <GalaxyBackground />
          <ScrollProgress />
          <PageIndicator />
          {children}
        </LanguageProvider>
      </body>
    </html>
  )
}