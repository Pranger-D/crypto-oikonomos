'use client'

import { useEffect, useState } from 'react'

export default function ScrollProgressBar() {
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    const updateProgress = () => {
      // 전체 스크롤 가능한 높이에서 현재 위치 계산
      const currentScroll = window.scrollY
      const scrollHeight = document.documentElement.scrollHeight - window.innerHeight
      
      if (scrollHeight) {
        setProgress(Number((currentScroll / scrollHeight).toFixed(3)) * 100)
      }
    }

    window.addEventListener('scroll', updateProgress)
    return () => window.removeEventListener('scroll', updateProgress)
  }, [])

  return (
    // 상단에 고정된 얇은 회색 배경 바
    <div className="fixed top-0 left-0 z-50 h-[4px] w-full bg-gray-100">
      {/* 스크롤에 따라 차오르는 진한 회색 바 */}
      <div
        style={{ width: `${progress}%` }}
        className="h-full bg-gray-600 transition-all duration-150 ease-out"
      />
    </div>
  )
}