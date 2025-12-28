'use client'

import { useEffect, useRef, useState } from 'react'

export default function NaturalLighting() {
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
      canvas.height = window.innerHeight * 2
    }
    resizeCanvas()
    window.addEventListener('resize', resizeCanvas)

    let time = 0
    let animationFrame: number

    const animate = () => {
      time += 0.005
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      // 创建多层缓慢移动的光影
      // 光影1 - 左上角的淡银色光晕
      const light1X = canvas.width * 0.2 + Math.sin(time * 0.3) * 100
      const light1Y = canvas.height * 0.15 + Math.cos(time * 0.2) * 80
      
      const gradient1 = ctx.createRadialGradient(
        light1X, light1Y, 0,
        light1X, light1Y, canvas.width * 0.4
      )
      gradient1.addColorStop(0, 'rgba(220, 230, 240, 0.08)')
      gradient1.addColorStop(0.3, 'rgba(200, 215, 230, 0.04)')
      gradient1.addColorStop(0.6, 'rgba(180, 200, 220, 0.02)')
      gradient1.addColorStop(1, 'rgba(180, 200, 220, 0)')

      ctx.fillStyle = gradient1
      ctx.fillRect(0, 0, canvas.width, canvas.height)

      // 光影2 - 右下角的暖银色光晕
      const light2X = canvas.width * 0.75 + Math.cos(time * 0.25) * 120
      const light2Y = canvas.height * 0.6 + Math.sin(time * 0.35) * 90
      
      const gradient2 = ctx.createRadialGradient(
        light2X, light2Y, 0,
        light2X, light2Y, canvas.width * 0.45
      )
      gradient2.addColorStop(0, 'rgba(230, 235, 245, 0.06)')
      gradient2.addColorStop(0.3, 'rgba(210, 220, 235, 0.03)')
      gradient2.addColorStop(0.6, 'rgba(190, 205, 225, 0.015)')
      gradient2.addColorStop(1, 'rgba(190, 205, 225, 0)')

      ctx.fillStyle = gradient2
      ctx.fillRect(0, 0, canvas.width, canvas.height)

      // 光影3 - 中间的柔和扫光
      const light3X = canvas.width * 0.5 + Math.sin(time * 0.15) * 150
      const light3Y = canvas.height * 0.4 + Math.cos(time * 0.18) * 100
      
      const gradient3 = ctx.createRadialGradient(
        light3X, light3Y, 0,
        light3X, light3Y, canvas.width * 0.5
      )
      gradient3.addColorStop(0, 'rgba(240, 245, 255, 0.05)')
      gradient3.addColorStop(0.4, 'rgba(220, 230, 245, 0.025)')
      gradient3.addColorStop(0.7, 'rgba(200, 215, 235, 0.01)')
      gradient3.addColorStop(1, 'rgba(200, 215, 235, 0)')

      ctx.fillStyle = gradient3
      ctx.fillRect(0, 0, canvas.width, canvas.height)

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
      {/* 动态光影层 */}
      <canvas
        ref={canvasRef}
        className="absolute top-0 left-0 w-full h-full"
        style={{
          transform: `translateY(${scrollY * 0.2}px)`,
          transition: 'transform 0.1s linear',
          mixBlendMode: 'screen',
          opacity: 0.6
        }}
      />

      {/* 静态光泽层 - 顶部 */}
      <div 
        className="absolute top-0 left-0 right-0 h-[50vh]"
        style={{
          background: `
            radial-gradient(
              ellipse 80% 50% at 50% 0%, 
              rgba(220, 230, 240, 0.12) 0%, 
              rgba(200, 215, 230, 0.06) 30%,
              rgba(180, 200, 220, 0.03) 60%,
              transparent 100%
            )
          `,
          transform: `translateY(${scrollY * 0.15}px)`,
          transition: 'transform 0.1s linear'
        }}
      />

      {/* 静态光泽层 - 左侧 */}
      <div 
        className="absolute top-0 left-0 bottom-0 w-[40vw]"
        style={{
          background: `
            radial-gradient(
              ellipse 60% 80% at 0% 50%, 
              rgba(210, 225, 240, 0.08) 0%, 
              rgba(190, 210, 230, 0.04) 40%,
              rgba(170, 195, 220, 0.02) 70%,
              transparent 100%
            )
          `,
          transform: `translateX(${-scrollY * 0.1}px)`,
          transition: 'transform 0.1s linear'
        }}
      />

      {/* 静态光泽层 - 右下角 */}
      <div 
        className="absolute bottom-0 right-0 w-[50vw] h-[60vh]"
        style={{
          background: `
            radial-gradient(
              ellipse 70% 60% at 100% 100%, 
              rgba(230, 240, 250, 0.1) 0%, 
              rgba(210, 225, 240, 0.05) 35%,
              rgba(190, 210, 230, 0.025) 65%,
              transparent 100%
            )
          `,
          transform: `translate(${scrollY * 0.08}px, ${scrollY * 0.12}px)`,
          transition: 'transform 0.1s linear'
        }}
      />

      {/* 柔和的扫光效果 - 斜角 */}
      <div 
        className="absolute inset-0"
        style={{
          background: `
            linear-gradient(
              135deg,
              rgba(240, 245, 255, 0.04) 0%,
              transparent 30%,
              transparent 70%,
              rgba(220, 235, 250, 0.03) 100%
            )
          `,
          opacity: 0.7
        }}
      />

      {/* 微妙的光斑 - 中心 */}
      <div 
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[60vw] h-[60vh]"
        style={{
          background: `
            radial-gradient(
              ellipse 100% 100% at 50% 50%, 
              rgba(235, 242, 252, 0.06) 0%, 
              rgba(215, 228, 245, 0.03) 40%,
              transparent 70%
            )
          `,
          filter: 'blur(60px)',
          transform: `scale(${1 + scrollY * 0.0005})`,
          transition: 'transform 0.1s linear'
        }}
      />
    </div>
  )
}
