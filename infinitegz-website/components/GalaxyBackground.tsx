'use client'

import { useEffect, useRef, useState } from 'react'

interface Star {
  x: number
  y: number
  radius: number
  opacity: number
  twinkleSpeed: number
  driftX: number
  driftY: number
}

export default function GalaxyBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [scrollY, setScrollY] = useState(0)

  useEffect(() => {
    const handleScroll = () => {
      setScrollY(window.scrollY)
    }

    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const resizeCanvas = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight * 3
    }
    resizeCanvas()
    window.addEventListener('resize', resizeCanvas)

    // 创建更少、更自然的星星 - 200颗
    const stars: Star[] = []
    for (let i = 0; i < 200; i++) {
      stars.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        radius: Math.random() * 1.2 + 0.3, // 0.3-1.5px - 更小
        opacity: Math.random() * 0.3 + 0.15, // 0.15-0.45 - 更淡
        twinkleSpeed: Math.random() * 0.01 + 0.005, // 更慢的闪烁
        driftX: (Math.random() - 0.5) * 0.02, // 极慢的漂移
        driftY: (Math.random() - 0.5) * 0.02
      })
    }

    let time = 0
    let animationFrame: number

    const animate = () => {
      time += 0.01
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      // 绘制星星 - 极简风格
      stars.forEach(star => {
        // 更新位置 - 缓慢漂移
        star.x += star.driftX
        star.y += star.driftY
        
        // 边界循环
        if (star.x < 0) star.x = canvas.width
        if (star.x > canvas.width) star.x = 0
        if (star.y < 0) star.y = canvas.height
        if (star.y > canvas.height) star.y = 0
        
        // 微弱闪烁
        const twinkle = Math.abs(Math.sin(time * star.twinkleSpeed)) * 0.2 + 0.6 // 0.6-0.8 范围
        const currentOpacity = star.opacity * twinkle
        const size = star.radius * (0.9 + twinkle * 0.1) // 微小的大小变化

        // 只绘制星星本体，不要光晕
        ctx.beginPath()
        ctx.arc(star.x, star.y, size, 0, Math.PI * 2)
        
        // 使用非常淡的银灰色
        ctx.fillStyle = `rgba(190, 200, 210, ${currentOpacity * 0.5})`
        ctx.fill()
      })

      // 极少量的银粉 - 只有30个
      const silverDustCount = 30
      for (let i = 0; i < silverDustCount; i++) {
        const x = (Math.random() * canvas.width + time * 3 * (i % 3)) % canvas.width
        const y = (Math.random() * canvas.height + time * 2 * (i % 2)) % canvas.height
        const dustOpacity = Math.random() * 0.08 // 非常淡
        
        ctx.beginPath()
        ctx.arc(x, y, 0.4, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(180, 190, 200, ${dustOpacity})`
        ctx.fill()
      }

      animationFrame = requestAnimationFrame(animate)
    }

    animate()

    return () => {
      window.removeEventListener('resize', resizeCanvas)
      cancelAnimationFrame(animationFrame)
    }
  }, [])

  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden">
      {/* 主银河 Canvas - 极简星空 */}
      <canvas
        ref={canvasRef}
        className="absolute top-0 left-0 w-full h-full"
        style={{
          transform: `translateY(${scrollY * 0.3}px)`,
          transition: 'transform 0.05s linear',
          opacity: 0.7 // 整体降低透明度
        }}
      />

      {/* 移除所有光泽层 - 保持纯粹墨黑 */}
    </div>
  )
}
