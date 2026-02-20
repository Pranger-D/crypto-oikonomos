"use client"

import React, { useEffect, useState } from 'react'
import {
    AreaChart, Area, LineChart, Line, BarChart, Bar,
    XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
    ComposedChart, ReferenceLine, Brush
} from 'recharts'

interface LiquiditySnapshot {
    date: string
    value: number
}

interface LiquidityDataMap {
    [key: string]: LiquiditySnapshot
}

interface LiquidityDataset {
    latest_snapshot: LiquidityDataMap
    last_updated: string
    history: any[]
}

const formatBillionToTrillion = (val: number) => `${(val / 1000).toFixed(2)}T`
const formatBillion = (val: number) => `${val.toFixed(2)}B`
const formatPercent = (val: number) => `${val.toFixed(2)}%`

export default function LiquidityMonitor() {
    const [data, setData] = useState<LiquidityDataset | null>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetch('/data/liquidity-data.json')
            .then(res => res.json())
            .then(json => {
                // 단위 조정을 위한 전처리 (백만 달러 -> 십억 달러 변환 등)
                const processedHistory = json.history.map((item: any) => ({
                    ...item,
                    RESERVES_B: item.RESERVES > 10000 ? item.RESERVES / 1000 : item.RESERVES,
                    TGA_B: item.TGA > 10000 ? item.TGA / 1000 : item.TGA,
                }))

                setData({
                    ...json,
                    history: processedHistory
                })
                setLoading(false)
            })
            .catch(err => {
                console.error("Failed to load liquidity data", err)
                setLoading(false)
            })
    }, [])

    if (loading) return <div className="p-4 rounded-xl bg-gray-50 dark:bg-gray-800 animate-pulse h-64 flex items-center justify-center">Loading Liquidity Data...</div>
    if (!data || !data.history.length) return <div className="p-4 rounded-xl bg-red-50 text-red-500">Failed to load liquidity data.</div>

    const latest = data.latest_snapshot
    const spreadsInfo = latest.SPREAD_SOFR_IORB

    // 전체 상태 판단 (간소화)
    let status = "정상"
    let statusColor = "bg-green-500"
    if (spreadsInfo && spreadsInfo.value >= 0) {
        status = "긴급 (SOFR 역전)"
        statusColor = "bg-red-500"
    } else if (latest.RESERVES && latest.RESERVES.value < 2900000) {
        status = "경고 (지준 부족)"
        statusColor = "bg-orange-500"
    }

    return (
        <div className="w-full my-8 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl overflow-hidden shadow-sm">
            <div className="p-4 sm:p-6 border-b border-gray-100 dark:border-gray-800">
                {/* 상단 라인: 제목과 시스템 상태 */}
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-2">
                    <h3 className="text-xl font-bold flex items-center gap-2 m-0 text-gray-900 dark:text-white">
                        <span className="text-2xl">🌊</span> 유동성 리스크 모니터
                    </h3>
                    <div className="flex items-center gap-2 bg-gray-50 dark:bg-gray-800 px-3 py-1.5 rounded-full border border-gray-200 dark:border-gray-700">
                        <span className="text-xs font-medium text-gray-500">시스템 상태:</span>
                        <div className="flex items-center gap-1.5">
                            <div className={`w-2.5 h-2.5 rounded-full ${statusColor} animate-pulse`} />
                            <span className="text-sm font-bold text-gray-700 dark:text-gray-200">{status}</span>
                        </div>
                    </div>
                </div>

                {/* 하단 라인: 설명 텍스트와 타임라인 브러시 */}
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4 mt-2">
                    <p className="text-sm text-gray-500 m-0">
                        FRED 공식 데이터 기반 실시간 시스템 유동성 추적 (마지막 업데이트: {data.last_updated})
                    </p>
                    <div className="w-full sm:w-2/5 h-8">
                        <ResponsiveContainer width="100%" height="100%">
                            <ComposedChart syncId="liquidity-monitor" data={data.history}>
                                <Brush
                                    dataKey="date"
                                    height={25}
                                    stroke="#94A3B8"
                                    fill="#F8FAFC"
                                    tickFormatter={(v) => v}
                                    startIndex={Math.max(0, data.history.length - 120)}
                                    endIndex={data.history.length - 1}
                                />
                            </ComposedChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            {/* Charts Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-px bg-gray-100 dark:bg-gray-800">

                {/* Chart 1: System Liquidity Volume */}
                <div className="bg-white dark:bg-gray-900 p-4 sm:p-6">
                    <div className="mb-4">
                        <h4 className="flex items-center gap-1.5 text-base font-semibold text-gray-800 dark:text-gray-200 m-0">
                            차트 1: 시중 유동성 풀 (Quantity)
                            <span
                                className="inline-flex items-center justify-center w-4 h-4 rounded-full bg-gray-100 dark:bg-gray-700 text-[10px] text-gray-500 cursor-help"
                                title="파란 면적(Reserves)이 줄어들고 붉은 선(TGA)이 오르면 시중 유동성이 정부로 흡수되는 중입니다."
                            >
                                ?
                            </span>
                        </h4>
                        <div className="flex flex-wrap gap-4 mt-2 text-sm">
                            <div className="flex flex-col">
                                <span className="text-gray-500 text-xs">지준 총량 (Reserves)</span>
                                <span className="font-mono font-medium text-blue-600">
                                    {latest.RESERVES ? formatBillionToTrillion(latest.RESERVES.value / 1000) : 'N/A'}
                                </span>
                            </div>
                            <div className="flex flex-col">
                                <span className="text-gray-500 text-xs">정부 계좌 (TGA)</span>
                                <span className="font-mono font-medium text-red-500">
                                    {latest.TGA ? formatBillion(latest.TGA.value / 1000) : 'N/A'}
                                </span>
                            </div>
                            <div className="flex flex-col">
                                <span className="text-gray-500 text-xs">역레포 (ON RRP)</span>
                                <span className="font-mono font-medium text-gray-500">
                                    {latest.ON_RRP ? formatBillion(latest.ON_RRP.value) : 'N/A'}
                                </span>
                            </div>
                        </div>
                    </div>

                    <div className="h-64 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <ComposedChart syncId="liquidity-monitor" data={data.history} margin={{ top: 5, right: 0, left: -20, bottom: 0 }}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                                <XAxis dataKey="date" tick={{ fontSize: 10 }} tickMargin={10} minTickGap={20} />
                                <YAxis yAxisId="left" tickFormatter={formatBillionToTrillion} tick={{ fontSize: 10 }} width={60} />
                                <YAxis yAxisId="right" orientation="right" tickFormatter={formatBillion} tick={{ fontSize: 10 }} width={40} />
                                <Tooltip
                                    formatter={(value: number, name: string) => {
                                        if (name === '지준 총량 (R)') return [formatBillion(value), name]
                                        return [formatBillion(value), name]
                                    }}
                                    labelStyle={{ color: 'black' }}
                                />
                                <Legend iconType="circle" wrapperStyle={{ fontSize: '11px' }} />
                                <Area yAxisId="left" type="monotone" dataKey="RESERVES_B" name="지준 총량 (R)" fill="#3B82F6" stroke="#2563EB" fillOpacity={0.2} />
                                <Line yAxisId="right" type="monotone" dataKey="TGA_B" name="TGA (R)" stroke="#EF4444" strokeWidth={2} dot={false} />
                                <Line yAxisId="right" type="monotone" dataKey="ON_RRP" name="ON RRP (R)" stroke="#6B7280" strokeWidth={2} dot={false} strokeDasharray="5 5" />
                            </ComposedChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Chart 2: Money Market Stress */}
                <div className="bg-white dark:bg-gray-900 p-4 sm:p-6">
                    <div className="mb-4">
                        <h4 className="flex items-center gap-1.5 text-base font-semibold text-gray-800 dark:text-gray-200 m-0">
                            차트 2: 단기시장 스트레스 (Price & Emergency)
                            <span
                                className="inline-flex items-center justify-center w-4 h-4 rounded-full bg-gray-100 dark:bg-gray-700 text-[10px] text-gray-500 cursor-help"
                                title="노란 선(스프레드)이 빨간 점선(0%)을 넘거나, 붉은 막대(D.W)가 솟구치면 자금 경색 위험 신호입니다."
                            >
                                ?
                            </span>
                        </h4>
                        <div className="flex flex-wrap gap-4 mt-2 text-sm">
                            <div className="flex flex-col">
                                <span className="text-gray-500 text-xs">SOFR 스프레드</span>
                                <span className={`font-mono font-medium ${spreadsInfo && spreadsInfo.value >= 0 ? 'text-red-500' : 'text-orange-500'}`}>
                                    {spreadsInfo ? formatPercent(spreadsInfo.value) : 'N/A'}
                                </span>
                            </div>
                            {/* D.W. removed based on phase 2 plan */}
                        </div>
                    </div>

                    <div className="h-64 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <ComposedChart syncId="liquidity-monitor" data={data.history} margin={{ top: 5, right: 0, left: -20, bottom: 0 }}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                                <XAxis dataKey="date" tick={{ fontSize: 10 }} tickMargin={10} minTickGap={20} />
                                <YAxis yAxisId="left" tickFormatter={formatPercent} tick={{ fontSize: 10 }} width={50} />
                                <YAxis yAxisId="right" orientation="right" tickFormatter={formatBillion} tick={{ fontSize: 10 }} width={40} />
                                <Tooltip
                                    formatter={(value: number, name: string) => {
                                        if (name === 'SOFR - IORB (%)') return [formatPercent(value), name]
                                        return [formatBillion(value), name]
                                    }}
                                    labelStyle={{ color: 'black' }}
                                />
                                <Legend iconType="circle" wrapperStyle={{ fontSize: '11px' }} />
                                <ReferenceLine y={0} yAxisId="left" stroke="#EF4444" strokeWidth={1} strokeDasharray="3 3" />
                                <Line yAxisId="left" type="monotone" dataKey="SPREAD_SOFR_IORB" name="SOFR - IORB (%)" stroke="#F59E0B" strokeWidth={2.5} dot={false} />
                                <Bar yAxisId="right" dataKey="SRF" name="SRF (R)" fill="#9333EA" barSize={20} opacity={0.8} />
                            </ComposedChart>
                        </ResponsiveContainer>
                    </div>
                </div>

            </div>

        </div>
    )
}
