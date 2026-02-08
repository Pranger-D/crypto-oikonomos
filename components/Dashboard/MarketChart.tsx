'use client'

import { useState, useMemo } from 'react'
import {
    LineChart,
    Line,
    Area,
    AreaChart,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    ComposedChart,
} from 'recharts'
import { format, parseISO } from 'date-fns'

interface PriceData {
    date: string
    btc: number | null
    btc_dominance: number | null
}

interface MarketChartProps {
    data: PriceData[]
    onDateClick: (date: string) => void
    selectedDate: string | null
}

export default function MarketChart({ data, onDateClick, selectedDate }: MarketChartProps) {
    // 기본 표시 범위: 최근 90일
    const [dateRange, setDateRange] = useState<[number, number]>([
        Math.max(0, data.length - 90),
        data.length - 1,
    ])

    // 표시할 데이터 필터링
    const displayData = useMemo(() => {
        return data.slice(dateRange[0], dateRange[1] + 1).map((item) => ({
            ...item,
            btcFormatted: item.btc ? `$${item.btc.toLocaleString()}` : 'N/A',
            dominanceFormatted: item.btc_dominance ? `${item.btc_dominance.toFixed(1)}%` : 'N/A',
        }))
    }, [data, dateRange])

    // 동적 Y축 범위 계산
    const yAxisDomains = useMemo(() => {
        const btcValues = displayData.map((d) => d.btc).filter((v): v is number => v !== null)
        const dominanceValues = displayData
            .map((d) => d.btc_dominance)
            .filter((v): v is number => v !== null)

        const btcMin = Math.min(...btcValues)
        const btcMax = Math.max(...btcValues)
        const dominanceMin = Math.min(...dominanceValues)
        const dominanceMax = Math.max(...dominanceValues)

        // 여유 공간 10% 추가
        const btcPadding = (btcMax - btcMin) * 0.1
        const dominancePadding = (dominanceMax - dominanceMin) * 0.1

        return {
            btc: [Math.max(0, btcMin - btcPadding), btcMax + btcPadding],
            dominance: [
                Math.max(0, dominanceMin - dominancePadding),
                Math.min(100, dominanceMax + dominancePadding),
            ],
        }
    }, [displayData])

    // 커스텀 툴팁
    const CustomTooltip = ({ active, payload }: any) => {
        if (active && payload && payload.length) {
            const data = payload[0].payload
            return (
                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
                    <p className="font-semibold text-gray-900 dark:text-gray-100 mb-2">
                        {format(parseISO(data.date), 'yyyy-MM-dd')}
                    </p>
                    <p className="text-sm text-blue-600 dark:text-blue-400">
                        BTC: {data.btcFormatted}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                        Dominance: {data.dominanceFormatted}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                        클릭하여 상세 정보 보기
                    </p>
                </div>
            )
        }
        return null
    }

    // 차트 클릭 핸들러
    const handleClick = (data: any) => {
        if (data && data.activePayload && data.activePayload[0]) {
            const clickedDate = data.activePayload[0].payload.date
            onDateClick(clickedDate)
        }
    }

    // Zoom 컨트롤
    const handleZoomIn = () => {
        const currentRange = dateRange[1] - dateRange[0]
        const newRange = Math.max(30, Math.floor(currentRange * 0.7))
        const center = Math.floor((dateRange[0] + dateRange[1]) / 2)
        const newStart = Math.max(0, center - Math.floor(newRange / 2))
        const newEnd = Math.min(data.length - 1, newStart + newRange)
        setDateRange([newStart, newEnd])
    }

    const handleZoomOut = () => {
        const currentRange = dateRange[1] - dateRange[0]
        const newRange = Math.min(data.length, Math.floor(currentRange * 1.5))
        const center = Math.floor((dateRange[0] + dateRange[1]) / 2)
        const newStart = Math.max(0, center - Math.floor(newRange / 2))
        const newEnd = Math.min(data.length - 1, newStart + newRange)
        setDateRange([newStart, newEnd])
    }

    const handleReset = () => {
        setDateRange([Math.max(0, data.length - 90), data.length - 1])
    }

    const handleShowAll = () => {
        setDateRange([0, data.length - 1])
    }

    return (
        <div className="space-y-4">
            {/* 컨트롤 버튼 */}
            <div className="flex items-center justify-between">
                <div className="flex gap-2">
                    <button
                        onClick={handleZoomIn}
                        className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 transition"
                    >
                        Zoom In
                    </button>
                    <button
                        onClick={handleZoomOut}
                        className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 transition"
                    >
                        Zoom Out
                    </button>
                    <button
                        onClick={handleReset}
                        className="px-3 py-1 text-sm bg-gray-500 text-white rounded hover:bg-gray-600 transition"
                    >
                        90일
                    </button>
                    <button
                        onClick={handleShowAll}
                        className="px-3 py-1 text-sm bg-gray-500 text-white rounded hover:bg-gray-600 transition"
                    >
                        전체
                    </button>
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                    {format(parseISO(displayData[0]?.date || data[0].date), 'yyyy-MM-dd')} ~{' '}
                    {format(
                        parseISO(displayData[displayData.length - 1]?.date || data[data.length - 1].date),
                        'yyyy-MM-dd'
                    )}
                </div>
            </div>

            {/* 차트 */}
            <ResponsiveContainer width="100%" height={400}>
                <ComposedChart data={displayData} onClick={handleClick}>
                    <defs>
                        <linearGradient id="colorBtc" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
                            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.1} />
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis
                        dataKey="date"
                        tickFormatter={(date) => format(parseISO(date), 'MM/dd')}
                        stroke="#6b7280"
                    />
                    <YAxis
                        yAxisId="left"
                        domain={yAxisDomains.btc}
                        tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                        stroke="#6b7280"
                    />
                    <YAxis
                        yAxisId="right"
                        orientation="right"
                        domain={yAxisDomains.dominance}
                        tickFormatter={(value) => `${value.toFixed(0)}%`}
                        stroke="#6b7280"
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend />
                    <Area
                        yAxisId="left"
                        type="monotone"
                        dataKey="btc"
                        stroke="#3b82f6"
                        strokeWidth={2}
                        fill="url(#colorBtc)"
                        fillOpacity={0.8}
                        activeDot={{
                            r: 6,
                            fill: '#3b82f6',
                            stroke: '#fff',
                            strokeWidth: 2,
                            cursor: 'pointer',
                            onClick: (e: any, payload: any) => onDateClick(payload.payload.date),
                        }}
                        name="BTC Price"
                        connectNulls
                    />
                    <Line
                        yAxisId="right"
                        type="monotone"
                        dataKey="btc_dominance"
                        stroke="#9ca3af"
                        strokeWidth={2}
                        dot={false}
                        activeDot={{
                            r: 6,
                            fill: '#9ca3af',
                            stroke: '#fff',
                            strokeWidth: 2,
                            cursor: 'pointer',
                            onClick: (e: any, payload: any) => onDateClick(payload.payload.date),
                        }}
                        name="BTC Dominance (%)"
                        connectNulls
                    />
                </ComposedChart>
            </ResponsiveContainer>
        </div>
    )
}
