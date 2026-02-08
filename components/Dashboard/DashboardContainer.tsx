'use client'

import { useState, useEffect } from 'react'
import MarketChart from './MarketChart'
import MacroIndicators from './MacroIndicators'
import BlogPostsList from './BlogPostsList'

interface DashboardData {
    lastUpdated: string
    metadata: {
        startDate: string
        endDate: string
        totalDays: number
        dataSource: {
            btc: string
            btc_dominance: string
            macro: string
        }
        version: string
    }
    priceData: Array<{
        date: string
        btc: number | null
        btc_dominance: number | null
    }>
    macroIndicators: Record<
        string,
        Array<{
            country: string
            indicator: string
            importance: string
            actual: number | null
            forecast: number | null
            previous: number | null
        }>
    >
    blogPosts: Record<
        string,
        Array<{
            slug: string
            title: string
            category: string
        }>
    >
}

export default function DashboardContainer() {
    const [data, setData] = useState<DashboardData | null>(null)
    const [selectedDate, setSelectedDate] = useState<string | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    // 데이터 로드
    useEffect(() => {
        fetch('/data/dashboard-data.json')
            .then((res) => {
                if (!res.ok) throw new Error('데이터를 불러올 수 없습니다.')
                return res.json()
            })
            .then((jsonData) => {
                setData(jsonData)
                setLoading(false)
            })
            .catch((err) => {
                setError(err.message)
                setLoading(false)
            })
    }, [])

    if (loading) {
        return (
            <div className="py-12 text-center">
                <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary-500 border-r-transparent"></div>
                <p className="mt-4 text-gray-600 dark:text-gray-400">대시보드 데이터 로딩 중...</p>
            </div>
        )
    }

    if (error || !data) {
        return (
            <div className="py-12 text-center">
                <p className="text-red-600 dark:text-red-400">⚠️ {error || '데이터를 불러올 수 없습니다.'}</p>
            </div>
        )
    }

    // 선택된 날짜의 데이터 가져오기
    const selectedMacroIndicators = selectedDate ? data.macroIndicators[selectedDate] || [] : []
    const selectedBlogPosts = selectedDate ? data.blogPosts[selectedDate] || [] : []

    return (
        <div className="space-y-8">
            {/* 헤더 */}
            <div className="border-b border-gray-200 dark:border-gray-700 pb-4">
                <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                    📊 Market Dashboard
                </h2>
                <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                    {data.metadata.startDate} ~ {data.metadata.endDate} ({data.metadata.totalDays}일)
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                    마지막 업데이트: {new Date(data.lastUpdated).toLocaleString('ko-KR')}
                </p>
            </div>

            {/* 차트 */}
            <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-6">
                <MarketChart
                    data={data.priceData}
                    onDateClick={setSelectedDate}
                    selectedDate={selectedDate}
                />
            </div>

            {/* 데이터 소스 정보 */}
            <div className="text-xs text-gray-500 dark:text-gray-500 flex items-center gap-4 flex-wrap">
                <span className="font-semibold">데이터 소스:</span>
                <span>BTC: {data.metadata.dataSource.btc}</span>
                <span>•</span>
                <span>Dominance: {data.metadata.dataSource.btc_dominance}</span>
                <span>•</span>
                <span>거시지표: {data.metadata.dataSource.macro}</span>
            </div>

            {/* 거시지표 + 블로그 글 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <MacroIndicators selectedDate={selectedDate} indicators={selectedMacroIndicators} />
                <BlogPostsList selectedDate={selectedDate} posts={selectedBlogPosts} />
            </div>
        </div>
    )
}
