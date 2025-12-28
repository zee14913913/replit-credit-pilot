'use client'

import { useEffect } from 'react'

export default function ForceVisible() {
  useEffect(() => {
    // 强制显示所有初始隐藏的内容
    const forceShow = () => {
      // 等待 DOM 完全加载
      setTimeout(() => {
        const elements = document.querySelectorAll('.opacity-0')
        elements.forEach((el) => {
          if (el instanceof HTMLElement) {
            el.style.opacity = '1'
            el.style.transform = 'translateY(0)'
          }
        })
        
        // 标记页面已加载
        document.documentElement.classList.add('is-loaded')
      }, 100)
    }

    // 立即执行
    forceShow()

    // 也在 load 事件时执行
    window.addEventListener('load', forceShow)

    return () => {
      window.removeEventListener('load', forceShow)
    }
  }, [])

  return null
}
