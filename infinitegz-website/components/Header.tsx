'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

export default function Header() {
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20)
    }
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <header 
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled ? 'bg-infinitegz-black/90 backdrop-blur-md border-b border-infinitegz-gray' : 'bg-transparent'
      }`}
    >
      <nav className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <Link href="/" className="text-2xl font-bold tracking-tight hover:opacity-80 transition-opacity">
            INFINITE GZ
          </Link>

          {/* Navigation Menu */}
          <div className="hidden md:flex items-center space-x-8">
            <Link href="/" className="text-sm hover:text-infinitegz-accent transition-colors">
              Home
            </Link>
            <Link href="#products" className="text-sm hover:text-infinitegz-accent transition-colors">
              Products
            </Link>
            <Link href="#solutions" className="text-sm hover:text-infinitegz-accent transition-colors">
              Solutions
            </Link>
            <Link href="#company" className="text-sm hover:text-infinitegz-accent transition-colors">
              Company
            </Link>
            <Link href="#resources" className="text-sm hover:text-infinitegz-accent transition-colors">
              Resources
            </Link>
            <Link href="#contact" className="text-sm hover:text-infinitegz-accent transition-colors">
              Contact
            </Link>
          </div>

          {/* CTA Button */}
          <Link 
            href="https://portal.infinitegz.com" 
            className="bg-infinitegz-white text-infinitegz-black px-6 py-2.5 rounded-full text-sm font-medium hover:bg-infinitegz-accent transition-all hover:scale-105 transform"
          >
            Start Loan Evaluation
          </Link>
        </div>
      </nav>
    </header>
  )
}
