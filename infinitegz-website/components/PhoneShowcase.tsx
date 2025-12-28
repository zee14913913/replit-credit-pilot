'use client'

import { useState, useEffect, useRef } from 'react'
import { useScrollAnimation } from '../hooks/useScrollAnimation'

export default function PhoneShowcase() {
  const { ref: sectionRef, isVisible } = useScrollAnimation(0.1)
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 })
  const phoneRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (phoneRef.current) {
        const rect = phoneRef.current.getBoundingClientRect()
        const x = (e.clientX - rect.left - rect.width / 2) / 30
        const y = (e.clientY - rect.top - rect.height / 2) / 30
        setMousePosition({ x, y })
      }
    }

    window.addEventListener('mousemove', handleMouseMove)
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [])

  return (
    <section 
      id="phone-showcase" 
      ref={sectionRef as any}
      className="min-h-screen flex items-center py-16 sm:py-32 bg-background snap-section relative overflow-hidden"
    >
      {/* 顶部激光分隔线 */}
      <div className="absolute top-0 left-0 right-0">
        <div className="laser-divider"></div>
      </div>
      
      <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          {/* 左侧：文字内容 */}
          <div className={`space-y-8 transition-all duration-700 ${
            isVisible ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-8'
          }`}>
            <div className="space-y-4">
              <div className="mono-tag text-secondary text-sm">
                MOBILE FIRST EXPERIENCE
              </div>
              
              <h2 className="text-4xl md:text-5xl lg:text-6xl tracking-tight text-primary font-bold">
                Access Anywhere,
                <br />
                Anytime
              </h2>
              
              <p className="text-secondary text-lg leading-relaxed max-w-lg">
                Manage your loans and financial services on the go. Full-featured mobile experience with instant notifications and real-time updates.
              </p>
            </div>

            {/* 特性网格 */}
            <div className="grid grid-cols-2 gap-4">
              {[
                { emoji: '📱', title: 'Mobile App', desc: 'iOS & Android' },
                { emoji: '🔔', title: 'Push Alerts', desc: 'Real-time updates' },
                { emoji: '🔒', title: 'Secure', desc: 'Bank-level security' },
                { emoji: '⚡', title: 'Fast', desc: 'Instant access' }
              ].map((feature, idx) => (
                <div key={idx} className="p-4 rounded-xl border border-primary/5 hover:border-primary/20 hover:bg-secondary/5 transition-all">
                  <div className="text-3xl mb-2">{feature.emoji}</div>
                  <div className="text-primary font-medium text-sm">{feature.title}</div>
                  <div className="text-secondary text-xs">{feature.desc}</div>
                </div>
              ))}
            </div>

            {/* App Store 按钮 */}
            <div className="flex gap-4 pt-4">
              <button className="btn-xai px-6">
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"/>
                </svg>
                App Store
              </button>
              <button className="btn-xai px-6">
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M3,20.5V3.5C3,2.91 3.34,2.39 3.84,2.15L13.69,12L3.84,21.85C3.34,21.6 3,21.09 3,20.5M16.81,15.12L6.05,21.34L14.54,12.85L16.81,15.12M20.16,10.81C20.5,11.08 20.75,11.5 20.75,12C20.75,12.5 20.53,12.9 20.18,13.18L17.89,14.5L15.39,12L17.89,9.5L20.16,10.81M6.05,2.66L16.81,8.88L14.54,11.15L6.05,2.66Z"/>
                </svg>
                Play Store
              </button>
            </div>
          </div>

          {/* 右侧：3D 手机展示 */}
          <div className="relative h-[700px] flex items-center justify-center perspective-1000">
            <div
              ref={phoneRef}
              className={`relative transition-all duration-700 ${
                isVisible ? 'opacity-100' : 'opacity-0'
              }`}
              style={{
                transform: isVisible 
                  ? `perspective(1000px) rotateY(${mousePosition.x}deg) rotateX(${-mousePosition.y}deg) scale(1)`
                  : 'perspective(1000px) rotateY(0deg) rotateX(0deg) scale(0.8)',
                transformStyle: 'preserve-3d'
              }}
            >
              {/* 手机框架 */}
              <div 
                className="relative w-[280px] h-[580px] rounded-[3rem] overflow-hidden shadow-2xl"
                style={{
                  background: 'linear-gradient(145deg, #1a1a1a 0%, #2d2d2d 100%)',
                  border: '8px solid #1a1a1a',
                  boxShadow: `
                    0 30px 80px rgba(0, 0, 0, 0.5),
                    0 0 0 1px rgba(255, 255, 255, 0.1),
                    inset 0 0 0 1px rgba(255, 255, 255, 0.05)
                  `
                }}
              >
                {/* 手机屏幕 */}
                <div className="relative w-full h-full bg-gradient-to-br from-gray-900 to-black p-4">
                  {/* 状态栏 */}
                  <div className="flex justify-between items-center text-white/60 text-xs mb-6">
                    <span>9:41</span>
                    <div className="flex gap-1 items-center">
                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M1 9l2 2c4.97-4.97 13.03-4.97 18 0l2-2C16.93 2.93 7.08 2.93 1 9zm8 8l3 3 3-3c-1.65-1.66-4.34-1.66-6 0zm-4-4l2 2c2.76-2.76 7.24-2.76 10 0l2-2C15.14 9.14 8.87 9.14 5 13z"/>
                      </svg>
                      <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M15.67 4H14V2h-4v2H8.33C7.6 4 7 4.6 7 5.33v15.33C7 21.4 7.6 22 8.33 22h7.33c.74 0 1.34-.6 1.34-1.33V5.33C17 4.6 16.4 4 15.67 4z"/>
                      </svg>
                    </div>
                  </div>

                  {/* App 内容 */}
                  <div className="space-y-4">
                    {/* 余额卡片 */}
                    <div className="rounded-2xl p-6" style={{
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                    }}>
                      <div className="text-white/80 text-xs mb-2">Total Balance</div>
                      <div className="text-white text-3xl font-bold mb-4">RM 125,890</div>
                      <div className="flex gap-2">
                        <div className="flex-1 bg-white/20 backdrop-blur-sm rounded-lg px-3 py-2 text-white text-xs">
                          ↑ +12.5%
                        </div>
                        <div className="flex-1 bg-white/20 backdrop-blur-sm rounded-lg px-3 py-2 text-white text-xs">
                          Last 30d
                        </div>
                      </div>
                    </div>

                    {/* 快捷功能 */}
                    <div className="grid grid-cols-4 gap-3">
                      {['Send', 'Receive', 'Loan', 'More'].map((label) => (
                        <div key={label} className="flex flex-col items-center gap-2">
                          <div className="w-12 h-12 rounded-xl bg-white/10 backdrop-blur-sm flex items-center justify-center">
                            <div className="w-6 h-6 bg-white/20 rounded"></div>
                          </div>
                          <span className="text-white/60 text-xs">{label}</span>
                        </div>
                      ))}
                    </div>

                    {/* 交易列表 */}
                    <div className="space-y-2">
                      {[1, 2, 3].map((i) => (
                        <div key={i} className="flex items-center gap-3 bg-white/5 backdrop-blur-sm rounded-xl p-3">
                          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600"></div>
                          <div className="flex-1">
                            <div className="text-white text-sm">Transaction {i}</div>
                            <div className="text-white/40 text-xs">Today, 10:30 AM</div>
                          </div>
                          <div className="text-green-400 text-sm font-medium">+RM 500</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* 底部导航栏 */}
                <div className="absolute bottom-0 left-0 right-0 h-20 bg-black/80 backdrop-blur-xl border-t border-white/10 flex items-center justify-around px-8">
                  {[1, 2, 3, 4].map((i) => (
                    <div key={i} className="w-6 h-6 rounded-full bg-white/20"></div>
                  ))}
                </div>
              </div>

              {/* 手机背后的影子/模糊层 */}
              <div 
                className="absolute inset-0 w-[280px] h-[580px] rounded-[3rem] -z-10"
                style={{
                  background: 'linear-gradient(145deg, #2d2d2d 0%, #1a1a1a 100%)',
                  transform: 'translateZ(-30px) scale(0.95)',
                  opacity: 0.5,
                  filter: 'blur(20px)'
                }}
              />
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
