'use client'

import { useEffect, useRef, ReactNode } from 'react'

interface ParallaxContainerProps {
  children: ReactNode
  speed?: 'slow' | 'medium' | 'fast'
  className?: string
}

export default function ParallaxContainer({ 
  children, 
  speed = 'medium',
  className = ''
}: ParallaxContainerProps) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const element = ref.current
    if (!element) return

    const handleScroll = () => {
      const rect = element.getBoundingClientRect()
      const scrollProgress = (window.innerHeight - rect.top) / (window.innerHeight + rect.height)
      
      const speedMultiplier = {
        slow: 0.2,
        medium: 0.4,
        fast: 0.6
      }[speed]

      const translateY = scrollProgress * -100 * speedMultiplier
      element.style.transform = `translateY(${translateY}px)`
    }

    window.addEventListener('scroll', handleScroll, { passive: true })
    handleScroll() // 初始调用

    return () => window.removeEventListener('scroll', handleScroll)
  }, [speed])

  return (
    <div 
      ref={ref} 
      className={`parallax ${className}`}
      style={{ 
        willChange: 'transform',
        transition: 'transform 0.1s linear'
      }}
    >
      {children}
    </div>
  )
}
