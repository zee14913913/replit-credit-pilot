'use client'

import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

export default function Preloader() {
  const [isLoading, setIsLoading] = useState(true)
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    // 模拟加载进度
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval)
          return 100
        }
        return prev + Math.random() * 15
      })
    }, 100)

    // 最小显示时间 1.5 秒
    const timer = setTimeout(() => {
      setIsLoading(false)
      document.documentElement.classList.add('is-loaded')
    }, 1500)

    return () => {
      clearInterval(interval)
      clearTimeout(timer)
    }
  }, [])

  return (
    <AnimatePresence>
      {isLoading && (
        <motion.div
          className="fixed inset-0 z-[9999] flex flex-col items-center justify-center bg-background"
          initial={{ opacity: 1 }}
          exit={{ 
            opacity: 0,
            transition: { 
              duration: 0.6, 
              ease: [0.165, 0.84, 0.44, 1] // Ethnocare 的缓动函数
            } 
          }}
        >
          {/* 圆形加载器 - Ethnocare 风格 */}
          <div className="relative w-20 h-20 mb-8">
            {/* 外圈 */}
            <motion.div
              className="absolute inset-0 rounded-full border-2 border-primary/20"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3 }}
            />
            
            {/* 旋转的线 */}
            <motion.div
              className="absolute inset-0 overflow-hidden"
              style={{ transformOrigin: '100% 50%' }}
              animate={{ rotate: 360 }}
              transition={{
                duration: 0.8,
                repeat: Infinity,
                ease: 'linear'
              }}
            >
              <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-primary border-r-primary" />
            </motion.div>

            {/* 中心点 */}
            <motion.div
              className="absolute inset-0 flex items-center justify-center"
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.2, duration: 0.4 }}
            >
              <div className="w-2 h-2 rounded-full bg-primary" />
            </motion.div>
          </div>

          {/* 加载进度 */}
          <motion.div
            className="text-primary font-mono text-sm tracking-wider"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            {Math.min(Math.floor(progress), 100)}%
          </motion.div>

          {/* Logo 或品牌名称 */}
          <motion.div
            className="absolute top-1/3 text-primary/40 font-mono text-xs tracking-widest uppercase"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
          >
            INFINITE GZ
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
