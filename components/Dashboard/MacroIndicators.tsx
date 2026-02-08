'use client'

import { indicatorTranslations } from './indicatorTranslations'

interface MacroIndicator {
    country: string
    indicator: string
    importance: string
    actual: number | null
    forecast: number | null
    previous: number | null
}

interface MacroIndicatorsProps {
    selectedDate: string | null
    indicators: MacroIndicator[]
}

// 국가명 한글 번역
const countryTranslations: Record<string, string> = {
    'United States': '미국',
    'China': '중국',
    'united states': '미국',
    'china': '중국',
}

// 번역 함수 (매칭되지 않으면 원문 반환)
function translateIndicator(indicator: string): string {
    // 월/분기 정보 제거 (예: "CPI (Dec)" -> "CPI", "GDP (Q3)" -> "GDP")
    const baseIndicator = indicator.replace(/\s+\([A-Za-z0-9]+\)\s*$/, '').trim()

    // 번역 시도
    const translated = indicatorTranslations[baseIndicator]

    if (translated) {
        // 번역이 있으면 원래 월/분기 정보 추가
        const monthMatch = indicator.match(/\s+(\([A-Za-z0-9]+\))\s*$/)
        return translated + (monthMatch ? ' ' + monthMatch[1] : '')
    }

    // 번역이 없으면 원문 반환
    return indicator
}

function translateCountry(country: string): string {
    return countryTranslations[country] || country
}

export default function MacroIndicators({ selectedDate, indicators }: MacroIndicatorsProps) {
    if (!selectedDate) {
        return (
            <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 p-6">
                <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-4">
                    📈 거시 경제 지표
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-8">
                    차트에서 날짜를 클릭하면 해당일의 경제 지표를 확인할 수 있습니다.
                </p>
            </div>
        )
    }

    if (indicators.length === 0) {
        return (
            <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 p-6">
                <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-4">
                    📈 거시 경제 지표
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                    선택한 날짜: <span className="font-semibold">{selectedDate}</span>
                </p>
                <p className="text-sm text-gray-400 dark:text-gray-500 text-center py-8">
                    이 날짜에 발표된 high importance 지표가 없습니다.
                </p>
            </div>
        )
    }

    return (
        <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-6">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">📈 거시 경제 지표</h3>
                <span className="text-sm text-gray-500 dark:text-gray-400">{selectedDate}</span>
            </div>

            <div className="space-y-4">
                {indicators.map((item, index) => (
                    <div
                        key={index}
                        className="border-l-4 border-blue-500 bg-gray-50 dark:bg-gray-700/50 p-4 rounded-r-lg"
                    >
                        {/* 국가 및 지표명 */}
                        <div className="flex items-start justify-between mb-3">
                            <div>
                                <span className="inline-block px-2 py-1 text-xs font-semibold rounded bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 mr-2">
                                    {translateCountry(item.country)}
                                </span>
                                <span className="text-sm font-bold text-gray-900 dark:text-gray-100">
                                    {translateIndicator(item.indicator)}
                                </span>
                            </div>
                            <span className="text-xs text-yellow-600 dark:text-yellow-400 font-semibold">
                                ⭐ {item.importance.toUpperCase()}
                            </span>
                        </div>

                        {/* 지표 값 */}
                        <div className="grid grid-cols-3 gap-4">
                            <div>
                                <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">예상치</p>
                                <p className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                                    {item.forecast !== null ? item.forecast : 'N/A'}
                                </p>
                            </div>
                            <div>
                                <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">실제치</p>
                                <p
                                    className={`text-sm font-bold ${item.actual !== null && item.forecast !== null
                                        ? item.actual > item.forecast
                                            ? 'text-green-600 dark:text-green-400'
                                            : item.actual < item.forecast
                                                ? 'text-red-600 dark:text-red-400'
                                                : 'text-gray-700 dark:text-gray-300'
                                        : 'text-gray-700 dark:text-gray-300'
                                        }`}
                                >
                                    {item.actual !== null ? item.actual : 'N/A'}
                                </p>
                            </div>
                            <div>
                                <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">이전</p>
                                <p className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                                    {item.previous !== null ? item.previous : 'N/A'}
                                </p>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}
