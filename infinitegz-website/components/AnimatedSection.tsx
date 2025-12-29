'use client'

import { motion } from 'framer-motion'
import { useScrollAnimation } from '@/hooks/useScrollAnimation'
import { ReactNode } from 'react'

interface AnimatedSectionProps {
  children: ReactNode
  className?: string
  delay?: number
  direction?: 'up' | 'down' | 'left' | 'right' | 'fade'
  threshold?: number
}

export default function AnimatedSection({
  children,
  className = '',
  delay = 0,
  direction = 'up',
  threshold = 0.1
}: AnimatedSectionProps) {
  const { elementRef, isVisible } = useScrollAnimation({ threshold, triggerOnce: true })

  // 定义不同方向的初始状态
  const variants = {
    hidden: {
      opacity: 0,
      y: direction === 'up' ? 40 : direction === 'down' ? -40 : 0,
      x: direction === 'left' ? 40 : direction === 'right' ? -40 : 0,
      scale: direction === 'fade' ? 0.95 : 1
    },
    visible: {
      opacity: 1,
      y: 0,
      x: 0,
      scale: 1,
      transition: {
        duration: 0.8,
        delay,
        ease: [0.165, 0.84, 0.44, 1] as any // Ethnocare 的缓动曲线
      }
    }
  }

  return (
    <motion.div
      ref={elementRef as any}
      className={className}
      initial="hidden"
      animate={isVisible ? 'visible' : 'hidden'}
      variants={variants}
    >
      {children}
    </motion.div>
  )
}
