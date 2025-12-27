'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

export default function Hero() {
  const [currentSlide, setCurrentSlide] = useState(0)

  // Auto-rotate carousel every 5 seconds
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % 3)
    }, 5000)
    return () => clearInterval(timer)
  }, [])

  return (
    <section className="relative min-h-screen flex items-center justify-center pt-20">
      {/* Background Carousel Placeholder */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="relative w-full h-full">
          {/* Placeholder for future image/video carousel */}
          <div className="absolute inset-0 bg-gradient-to-b from-infinitegz-dark via-infinitegz-black to-infinitegz-black">
            <div className="absolute inset-0 opacity-20">
              {/* Animated gradient background */}
              <div className={`absolute inset-0 transition-opacity duration-1000 ${currentSlide === 0 ? 'opacity-100' : 'opacity-0'}`}>
                <div className="w-full h-full bg-gradient-to-br from-blue-900/20 to-purple-900/20"></div>
              </div>
              <div className={`absolute inset-0 transition-opacity duration-1000 ${currentSlide === 1 ? 'opacity-100' : 'opacity-0'}`}>
                <div className="w-full h-full bg-gradient-to-br from-purple-900/20 to-pink-900/20"></div>
              </div>
              <div className={`absolute inset-0 transition-opacity duration-1000 ${currentSlide === 2 ? 'opacity-100' : 'opacity-0'}`}>
                <div className="w-full h-full bg-gradient-to-br from-green-900/20 to-blue-900/20"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="relative z-10 container mx-auto px-6 text-center">
        {/* Top Badge */}
        <div className="mb-8 animate-fade-in">
          <Link 
            href="https://portal.infinitegz.com" 
            className="inline-block bg-infinitegz-gray hover:bg-infinitegz-light-gray border border-infinitegz-light-gray rounded-full px-6 py-2 text-sm transition-all hover:scale-105 transform"
          >
            Use CreditPilot
          </Link>
        </div>

        {/* Main Headline */}
        <h1 className="text-5xl md:text-7xl lg:text-8xl font-bold mb-6 animate-slide-up">
          Loans & Financial
          <br />
          Optimization for Your
          <br />
          Businesses
        </h1>

        {/* Subtitle */}
        <p className="text-xl md:text-2xl text-infinitegz-silver max-w-3xl mx-auto mb-12 animate-slide-up">
          Your one-stop solution for loans, financial optimization, and digital advisory services in Malaysia
        </p>

        {/* Carousel Indicators */}
        <div className="flex justify-center gap-2 mb-8">
          {[0, 1, 2].map((index) => (
            <button
              key={index}
              onClick={() => setCurrentSlide(index)}
              className={`w-2 h-2 rounded-full transition-all ${
                currentSlide === index ? 'bg-infinitegz-white w-8' : 'bg-infinitegz-light-gray'
              }`}
              aria-label={`Go to slide ${index + 1}`}
            />
          ))}
        </div>
      </div>

      {/* Scroll Indicator */}
      <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 animate-bounce">
        <div className="w-6 h-10 border-2 border-infinitegz-silver rounded-full flex justify-center">
          <div className="w-1 h-3 bg-infinitegz-silver rounded-full mt-2"></div>
        </div>
      </div>
    </section>
  )
}
