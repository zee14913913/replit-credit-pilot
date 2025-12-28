'use client'

import { useEffect, useRef, useState } from 'react'

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

    // 设置 canvas 尺寸
    const resizeCanvas = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight * 3 // 3倍高度用于滚动视差
    }
    resizeCanvas()
    window.addEventListener('resize', resizeCanvas)

    // 银色星星粒子系统
    interface Star {
      x: number
      y: number
      z: number
      radius: number
      opacity: number
      twinkleSpeed: number
      twinklePhase: number
      vx: number
      vy: number
    }

    const stars: Star[] = []
    
    // 创建银色星星 (300颗)
    for (let i = 0; i < 300; i++) {
      stars.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        z: Math.random() * 3,
        radius: Math.random() * 1.5 + 0.3,
        opacity: Math.random() * 0.8 + 0.2,
        twinkleSpeed: Math.random() * 0.02 + 0.01,
        twinklePhase: Math.random() * Math.PI * 2,
        vx: (Math.random() - 0.5) * 0.1,
        vy: (Math.random() - 0.5) * 0.1
      })
    }

    let animationFrame: number
    let time = 0

    const animate = () => {
      time += 0.01
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      // 绘制银色星星
      stars.forEach((star) => {
        // 更新位置（轻微漂移）
        star.x += star.vx
        star.y += star.vy

        // 边界循环
        if (star.x < 0) star.x = canvas.width
        if (star.x > canvas.width) star.x = 0
        if (star.y < 0) star.y = canvas.height
        if (star.y > canvas.height) star.y = 0

        // 闪烁效果
        star.twinklePhase += star.twinkleSpeed
        const twinkle = (Math.sin(star.twinklePhase) + 1) / 2
        const currentOpacity = star.opacity * (0.5 + twinkle * 0.5)

        // 根据深度调整大小
        const size = star.radius * (1 + star.z * 0.5)

        // 绘制星星（银色）
        ctx.beginPath()
        ctx.arc(star.x, star.y, size, 0, Math.PI * 2)
        
        // 创建星星的放射状渐变（银色光晕）
        const starGradient = ctx.createRadialGradient(
          star.x, star.y, 0,
          star.x, star.y, size * 3
        )
        starGradient.addColorStop(0, `rgba(255, 255, 255, ${currentOpacity})`)
        starGradient.addColorStop(0.3, `rgba(220, 220, 230, ${currentOpacity * 0.6})`)
        starGradient.addColorStop(0.6, `rgba(192, 192, 210, ${currentOpacity * 0.3})`)
        starGradient.addColorStop(1, `rgba(192, 192, 210, 0)`)
        
        ctx.fillStyle = starGradient
        ctx.fill()

        // 添加额外的亮点（银色闪光）
        if (star.radius > 1 && twinkle > 0.7) {
          ctx.beginPath()
          ctx.arc(star.x, star.y, size * 0.5, 0, Math.PI * 2)
          ctx.fillStyle = `rgba(255, 255, 255, ${currentOpacity * 1.5})`
          ctx.fill()
        }
      })

      // 添加细微的银粉闪烁层
      const silverDustCount = 100
      for (let i = 0; i < silverDustCount; i++) {
        const x = (Math.random() * canvas.width + time * 10 * (i % 3)) % canvas.width
        const y = (Math.random() * canvas.height + time * 5 * (i % 2)) % canvas.height
        const dustOpacity = Math.random() * 0.15
        
        ctx.beginPath()
        ctx.arc(x, y, 0.5, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(210, 210, 220, ${dustOpacity})`
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
      {/* 主银河 Canvas */}
      <canvas
        ref={canvasRef}
        className="absolute top-0 left-0 w-full h-full"
        style={{
          transform: `translateY(${scrollY * 0.3}px)`,
          transition: 'transform 0.05s linear'
        }}
      />
      
      {/* 墨黑色光泽渐变叠加 */}
      <div 
        className="absolute inset-0 opacity-40"
        style={{
          background: `
            radial-gradient(ellipse at 20% 30%, rgba(30, 30, 50, 0.3) 0%, transparent 50%),
            radial-gradient(ellipse at 80% 70%, rgba(40, 40, 60, 0.2) 0%, transparent 50%),
            radial-gradient(ellipse at 50% 50%, rgba(20, 20, 40, 0.15) 0%, transparent 70%)
          `,
          transform: `translateY(${scrollY * 0.15}px)`,
          transition: 'transform 0.1s linear'
        }}
      />

      {/* 顶部光泽效果 */}
      <div 
        className="absolute top-0 left-0 right-0 h-96 opacity-20"
        style={{
          background: 'linear-gradient(180deg, rgba(192, 192, 210, 0.15) 0%, transparent 100%)',
        }}
      />
    </div>
  )
}
