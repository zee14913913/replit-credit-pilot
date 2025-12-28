'use client'

import { useState, useEffect, useRef } from 'react'
import { useScrollAnimation } from '../hooks/useScrollAnimation'
import { useLanguage } from '@/contexts/LanguageContext'

export default function FeatureShowcase() {
  const { t } = useLanguage()
  const { ref: sectionRef, isVisible } = useScrollAnimation(0.1)
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 })
  const cardRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (cardRef.current) {
        const rect = cardRef.current.getBoundingClientRect()
        const x = (e.clientX - rect.left - rect.width / 2) / 25
        const y = (e.clientY - rect.top - rect.height / 2) / 25
        setMousePosition({ x, y })
      }
    }

    window.addEventListener('mousemove', handleMouseMove)
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [])

  return (
    <section 
      id="showcase" 
      ref={sectionRef as any}
      className="min-h-screen flex items-center py-16 sm:py-32 bg-background snap-section relative overflow-hidden"
    >
      {/* 顶部激光分隔线 */}
      <div className="absolute top-0 left-0 right-0">
        <div className="laser-divider"></div>
      </div>
      
      <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          {/* 左侧：3D 卡片展示 */}
          <div className="relative h-[600px] flex items-center justify-center perspective-1000">
            <div
              ref={cardRef}
              className={`relative w-full max-w-md transition-all duration-700 ${
                isVisible ? 'opacity-100' : 'opacity-0'
              }`}
              style={{
                transform: isVisible 
                  ? `perspective(1000px) rotateY(${mousePosition.x}deg) rotateX(${-mousePosition.y}deg) scale(1)`
                  : 'perspective(1000px) rotateY(0deg) rotateX(0deg) scale(0.8)',
                transformStyle: 'preserve-3d'
              }}
            >
              {/* 3D 卡片 - 信用卡/银行卡风格 */}
              <div 
                className="relative w-full aspect-[1.6/1] rounded-3xl overflow-hidden shadow-2xl"
                style={{
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  boxShadow: `
                    0 20px 60px rgba(102, 126, 234, 0.4),
                    0 0 100px rgba(118, 75, 162, 0.2)
                  `
                }}
              >
                {/* 光泽效果 */}
                <div 
                  className="absolute inset-0 opacity-30"
                  style={{
                    background: 'linear-gradient(135deg, rgba(255,255,255,0.4) 0%, transparent 50%, rgba(255,255,255,0.2) 100%)'
                  }}
                />
                
                {/* 卡片内容 */}
                <div className="relative z-10 p-8 h-full flex flex-col justify-between">
                  {/* Logo/品牌 */}
                  <div className="flex justify-between items-start">
                    <div className="w-12 h-12 rounded-full bg-white/20 backdrop-blur-md flex items-center justify-center">
                      <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                    </div>
                    <div className="text-white/80 font-mono text-xs">INFINITE GZ</div>
                  </div>

                  {/* 中间装饰 */}
                  <div className="space-y-2">
                    <div className="w-16 h-12 rounded-lg bg-gradient-to-br from-amber-300/30 to-amber-500/30 backdrop-blur-md"></div>
                  </div>

                  {/* 底部信息 */}
                  <div className="space-y-4">
                    <div className="font-mono text-2xl text-white tracking-wider">
                      •••• •••• •••• 8888
                    </div>
                    <div className="flex justify-between items-end">
                      <div>
                        <div className="text-white/60 text-xs font-mono">CARDHOLDER</div>
                        <div className="text-white font-mono text-sm">CREDIT PILOT USER</div>
                      </div>
                      <div>
                        <div className="text-white/60 text-xs font-mono">EXPIRES</div>
                        <div className="text-white font-mono text-sm">12/28</div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* 磨砂玻璃纹理 */}
                <div 
                  className="absolute inset-0 opacity-10"
                  style={{
                    backgroundImage: 'radial-gradient(circle at 20% 50%, rgba(255,255,255,0.8) 0%, transparent 50%)',
                    filter: 'blur(40px)'
                  }}
                />
              </div>

              {/* 后面的卡片 - 3D 层叠效果 */}
              <div 
                className="absolute inset-0 w-full aspect-[1.6/1] rounded-3xl -z-10"
                style={{
                  background: 'linear-gradient(135deg, #764ba2 0%, #667eea 100%)',
                  transform: 'translateZ(-50px) translateY(20px)',
                  opacity: 0.6,
                  filter: 'blur(8px)'
                }}
              />
              <div 
                className="absolute inset-0 w-full aspect-[1.6/1] rounded-3xl -z-20"
                style={{
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  transform: 'translateZ(-100px) translateY(40px)',
                  opacity: 0.3,
                  filter: 'blur(16px)'
                }}
              />
            </div>
          </div>

          {/* 右侧：文字内容 */}
          <div className={`space-y-8 transition-all duration-700 delay-200 ${
            isVisible ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-8'
          }`}>
            <div className="space-y-4">
              <div className="mono-tag text-secondary text-sm">
                SMART FINANCIAL TOOL
              </div>
              
              <h2 className="text-4xl md:text-5xl lg:text-6xl tracking-tight text-primary font-bold">
                Your Digital
                <br />
                Financial Card
              </h2>
              
              <p className="text-secondary text-lg leading-relaxed max-w-lg">
                Experience seamless loan management with our intelligent CreditPilot system. Get instant analysis, best rates, and zero upfront fees.
              </p>
            </div>

            {/* 特性列表 */}
            <div className="space-y-4">
              {[
                { icon: '⚡', title: 'Instant Analysis', desc: 'Real-time DSR calculation' },
                { icon: '🎯', title: 'Best Rates', desc: 'From all Malaysian banks' },
                { icon: '💎', title: 'Premium Features', desc: '8 complementary services' }
              ].map((feature, idx) => (
                <div key={idx} className="flex gap-4 items-start group cursor-pointer">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary/10 to-secondary/5 flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">
                    {feature.icon}
                  </div>
                  <div>
                    <div className="text-primary font-medium">{feature.title}</div>
                    <div className="text-secondary text-sm">{feature.desc}</div>
                  </div>
                </div>
              ))}
            </div>

            {/* CTA */}
            <div className="pt-4">
              <a 
                href="https://portal.infinitegz.com" 
                className="btn-xai btn-xai-primary text-base py-3 px-8 inline-flex"
              >
                Get Your Card
              </a>
            </div>
          </div>
        </div>
      </div>
      
      {/* 底部激光分隔线 */}
      <div className="absolute bottom-0 left-0 right-0">
        <div className="laser-divider"></div>
      </div>
    </section>
  )
}
