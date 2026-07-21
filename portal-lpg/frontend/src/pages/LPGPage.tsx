import { useEffect, useState, useCallback } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { fetchLPGSummary, fetchLPGMonthly, fetchLGPDistricts, fetchLPGCompare } from '@/lib/api'
import type { LPGSummary } from '@/lib/types'
import KPIAnalysis from './KPIAnalysis'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend, LineChart, Line, AreaChart, Area, Cell } from 'recharts'
import { TrendingUp, TrendingDown, Minus, Filter, CalendarDays, Database, MapPin } from 'lucide-react'

const MONTH_NAMES: Record<string, string> = {
  '01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr', '05': 'Mei', '06': 'Jun',
  '07': 'Jul', '08': 'Agu', '09': 'Sep', '10': 'Okt', '11': 'Nov', '12': 'Des',
}
const MONTHS = Array.from({ length: 12 }, (_, i) => String(i + 1).padStart(2, '0'))

function fmt(v: number): string { return v.toLocaleString('id', { maximumFractionDigits: 0 }) }
function fmt1(v: number): string { return v.toLocaleString('id', { maximumFractionDigits: 1 }) }

// ── Custom Recharts Tooltip ──────────────────────────────────
function ChartTooltip({ active, payload, label, formatter }: any) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-card border border-border rounded-xl px-3 py-2.5 shadow-xl text-xs space-y-1">
      <p className="text-muted-foreground font-medium mb-1">{label}</p>
      {payload.map((entry: any, i: number) => (
        <div key={i} className="flex items-center justify-between gap-4">
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full" style={{ background: entry.color }} />
            {entry.name}
          </span>
          <span className="font-semibold tabular-nums">
            {formatter ? formatter(entry.value) : fmt(entry.value)}
          </span>
        </div>
      ))}
    </div>
  )
}

// ── Gradient defs for charts ──────────────────────────────────
function ChartDefs() {
  return (
    <defs>
      <linearGradient id="gradBlue" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stopColor="var(--primary)" stopOpacity={0.3} />
        <stop offset="100%" stopColor="var(--primary)" stopOpacity={0.02} />
      </linearGradient>
      <linearGradient id="gradGray" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stopColor="var(--muted-foreground)" stopOpacity={0.2} />
        <stop offset="100%" stopColor="var(--muted-foreground)" stopOpacity={0.02} />
      </linearGradient>
    </defs>
  )
}

// ── Filter label component ──────────────────────────────────
function FilterLabel({ icon: Icon, label }: { icon: any; label: string }) {
  return (
    <span className="flex items-center gap-1.5 text-[11px] font-medium text-muted-foreground shrink-0 min-w-[4rem]">
      <Icon className="h-3 w-3" />
      {label}
    </span>
  )
}

// =============================================================
// MAIN PAGE
// =============================================================
export default function LPGPage() {
  const [year, setYear] = useState('all')
  const [month, setMonth] = useState('all')
  const [district, setDistrict] = useState('all')
  const [type, setType] = useState('all')
  const [summary, setSummary] = useState<LPGSummary | null>(null)

  useEffect(() => { fetchLPGSummary().then(setSummary).catch(console.error) }, [])

  const buildParams = useCallback((extra?: string) => {
    const p = new URLSearchParams()
    if (year !== 'all') p.set('year', year)
    if (month !== 'all') p.set('month', month)
    if (district !== 'all') p.set('district', district)
    if (type !== 'all') p.set('type', type)
    const qs = p.toString()
    return qs ? `?${qs}${extra || ''}` : extra ? `?${extra}` : ''
  }, [year, month, district, type])

  return (
    <div className="space-y-4 md:space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl md:text-2xl font-bold">Analisis Realisasi LPG</h1>
        <p className="text-xs md:text-sm text-muted-foreground mt-1">
          Perbandingan YTD, MoM, dan tren realisasi LPG Kalimantan Barat
        </p>
      </div>

      {/* ── Filter Bar ───────────────────────────────────── */}
      <Card className="bg-card border-border shadow-sm">
        <CardContent className="p-4 md:p-5">
          <div className="flex flex-wrap items-end gap-x-6 gap-y-3">
            {/* Tahun */}
            <div className="min-w-0">
              <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-1.5 block">Tahun</label>
              <Select value={year} onValueChange={(v) => v && setYear(v)}>
                <SelectTrigger className="w-28 h-8 text-xs bg-secondary/40 border-border/60 hover:border-border transition-colors">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-card border-border">
                  <SelectItem value="all">Semua</SelectItem>
                  <SelectItem value="2025">2025</SelectItem>
                  <SelectItem value="2026">2026</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Bulan */}
            <div className="min-w-0">
              <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-1.5 block">Bulan</label>
              <Select value={month} onValueChange={(v) => v && setMonth(v)}>
                <SelectTrigger className="w-32 h-8 text-xs bg-secondary/40 border-border/60 hover:border-border transition-colors">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-card border-border max-h-60">
                  <SelectItem value="all">Semua Bulan</SelectItem>
                  {MONTHS.map(m => (
                    <SelectItem key={m} value={m}>{MONTH_NAMES[m]}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Tipe */}
            <div className="min-w-0">
              <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-1.5 block">Tipe</label>
              <Select value={type} onValueChange={(v) => v && setType(v)}>
                <SelectTrigger className="w-36 h-8 text-xs bg-secondary/40 border-border/60 hover:border-border transition-colors">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-card border-border">
                  <SelectItem value="all">Semua Tipe</SelectItem>
                  <SelectItem value="PSO">LPG 3Kg (PSO)</SelectItem>
                  <SelectItem value="NPSO_RT">Bright Gas (NPSO RT)</SelectItem>
                  <SelectItem value="NPSO_NRT">Non-RT (NPSO)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Distrik */}
            <div className="min-w-0">
              <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-1.5 block">Distrik</label>
              <Select value={district} onValueChange={(v) => v && setDistrict(v)}>
                <SelectTrigger className="w-44 h-8 text-xs bg-secondary/40 border-border/60 hover:border-border transition-colors">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-card border-border max-h-60">
                  <SelectItem value="all">Semua Distrik</SelectItem>
                  {summary?.districts?.map(d => (
                    <SelectItem key={d} value={d}>{d}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ── Tabs ───────────────────────────────────────── */}
      <Tabs defaultValue="ytd" className="space-y-4">
        <TabsList className="bg-card border-border overflow-x-auto flex-nowrap w-full justify-start p-1 gap-0.5">
          <TabsTrigger value="ytd" className="text-xs md:text-sm data-[state=active]:bg-primary/10">📊 YTD</TabsTrigger>
          <TabsTrigger value="kpi" className="text-xs md:text-sm data-[state=active]:bg-primary/10">🎯 KPI</TabsTrigger>
          <TabsTrigger value="trend" className="text-xs md:text-sm data-[state=active]:bg-primary/10">📈 Tren</TabsTrigger>
          <TabsTrigger value="yoy" className="text-xs md:text-sm data-[state=active]:bg-primary/10">🔄 YoY</TabsTrigger>
          <TabsTrigger value="districts" className="text-xs md:text-sm data-[state=active]:bg-primary/10">🗺️ Distrik</TabsTrigger>
          <TabsTrigger value="segments" className="text-xs md:text-sm data-[state=active]:bg-primary/10">📦 Segmen</TabsTrigger>
        </TabsList>

        <TabsContent value="ytd"><YTDAnalysis params={buildParams} /></TabsContent>
        <TabsContent value="kpi"><KPIAnalysis params={buildParams} /></TabsContent>
        <TabsContent value="trend"><TrendAnalysis params={buildParams} year={year} /></TabsContent>
        <TabsContent value="yoy"><YoYAnalysis /></TabsContent>
        <TabsContent value="districts"><DistrictAnalysis params={buildParams} /></TabsContent>
        <TabsContent value="segments"><SegmentAnalysis params={buildParams} /></TabsContent>
      </Tabs>
    </div>
  )
}

// =============================================================
// YTD COMPARISON
// =============================================================
function YTDAnalysis({ params }: { params: (x?: string) => string }) {
  const [data, setData] = useState<any>(null); const [loading, setLoading] = useState(true)
  useEffect(() => {
    setLoading(true)
    Promise.all([fetchLPGCompare(params('')), fetchLPGMonthly(params(''))])
      .then(([cmp, mon]) => setData({ ...cmp, monthly: mon }))
      .catch(console.error).finally(() => setLoading(false))
  }, [params])

  if (loading) return <Skeleton className="h-80 bg-card rounded-xl" />
  if (!data?.ytd?.years) return <p className="text-muted-foreground text-sm py-8 text-center">Pilih tahun 2025 & 2026 untuk lihat YTD</p>

  const { ytd } = data; const y1 = ytd.years[0]; const y2 = ytd.years[1]
  const y1Total = ytd.totals[y1]; const y2Total = ytd.totals[y2]
  const growth = y1Total > 0 ? ((y2Total - y1Total) / y1Total * 100) : 0
  const chartData = ytd.months.map((m: string, i: number) => ({
    month: MONTH_NAMES[m] || m, [y1]: ytd.data[y1][i]?.mt || 0, [y2]: ytd.data[y2][i]?.mt || 0,
  }))
  const cumData = ytd.months.map((m: string, i: number) => {
    const c1 = ytd.data[y1].slice(0, i + 1).reduce((s: number, x: any) => s + (x?.mt || 0), 0)
    const c2 = ytd.data[y2].slice(0, i + 1).reduce((s: number, x: any) => s + (x?.mt || 0), 0)
    return { month: MONTH_NAMES[m] || m, [`${y1}`]: Math.round(c1), [`${y2}`]: Math.round(c2) }
  })

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[{ l: `YTD ${y1}`, v: `${fmt(y1Total)} MT`, c: '' },
          { l: `YTD ${y2}`, v: `${fmt(y2Total)} MT`, c: 'text-primary' },
          { l: 'Pertumbuhan YoY', v: `${growth >= 0 ? '+' : ''}${growth.toFixed(2)}%`, c: growth >= 0 ? 'text-chart-2' : 'text-destructive', i: growth >= 0 ? TrendingUp : TrendingDown },
          { l: 'Selisih', v: `${growth >= 0 ? '+' : ''}${fmt(y2Total - y1Total)} MT`, c: growth >= 0 ? 'text-chart-2' : 'text-destructive' },
        ].map((s, idx) => (
          <Card key={idx} className="bg-card border-border">
            <CardContent className="p-4">
              <p className="text-[11px] text-muted-foreground">{s.l}</p>
              <p className={`text-lg font-bold mt-0.5 flex items-center gap-1.5 ${s.c}`}>
                {s.i && <s.i className="h-4 w-4" />}{s.v}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card className="bg-card border-border">
          <CardHeader className="pb-2"><CardTitle className="text-sm font-semibold">Realisasi per Bulan</CardTitle></CardHeader>
          <CardContent className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                <XAxis dataKey="month" tick={{ fill: 'var(--muted-foreground)', fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: 'var(--muted-foreground)', fontSize: 11 }} axisLine={false} tickLine={false} width={55} />
                <Tooltip content={<ChartTooltip formatter={(v: number) => `${fmt(v)} MT`} />} />
                <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 12, paddingTop: 8 }} />
                <Bar dataKey={y1} fill="var(--muted-foreground)" radius={[4, 4, 0, 0]} opacity={0.5} maxBarSize={32} />
                <Bar dataKey={y2} fill="var(--primary)" radius={[4, 4, 0, 0]} maxBarSize={32} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardHeader className="pb-2"><CardTitle className="text-sm font-semibold">Kumulatif YTD</CardTitle></CardHeader>
          <CardContent className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={cumData}>
                <defs>
                  <linearGradient id={`cum${y1}`} x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="var(--muted-foreground)" stopOpacity={0.25}/><stop offset="100%" stopColor="var(--muted-foreground)" stopOpacity={0.02}/></linearGradient>
                  <linearGradient id={`cum${y2}`} x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="var(--primary)" stopOpacity={0.25}/><stop offset="100%" stopColor="var(--primary)" stopOpacity={0.02}/></linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                <XAxis dataKey="month" tick={{ fill: 'var(--muted-foreground)', fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: 'var(--muted-foreground)', fontSize: 11 }} axisLine={false} tickLine={false} width={55} />
                <Tooltip content={<ChartTooltip formatter={(v: number) => `${fmt(v)} MT`} />} />
                <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 12, paddingTop: 8 }} />
                <Area type="monotone" dataKey={y1} stroke="var(--muted-foreground)" fill={`url(#cum${y1})`} strokeWidth={2} />
                <Area type="monotone" dataKey={y2} stroke="var(--primary)" fill={`url(#cum${y2})`} strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Table */}
      <Card className="bg-card border-border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs md:text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/30">
                <th className="text-left p-3 font-semibold text-muted-foreground">Bulan</th>
                <th className="text-right p-3 font-semibold text-muted-foreground">{y1}</th>
                <th className="text-right p-3 font-semibold text-muted-foreground">{y2}</th>
                <th className="text-right p-3 font-semibold text-muted-foreground">Δ MT</th>
                <th className="text-right p-3 font-semibold text-muted-foreground">Growth</th>
              </tr>
            </thead>
            <tbody>
              {ytd.months.map((m: string, i: number) => {
                const v1 = ytd.data[y1][i]?.mt || 0; const v2 = ytd.data[y2][i]?.mt || 0
                const diff = v2 - v1; const pct = v1 > 0 ? (diff / v1 * 100) : 0
                return (
                  <tr key={m} className="border-b border-border hover:bg-accent/40 transition-colors">
                    <td className="p-3 font-medium">{MONTH_NAMES[m]}</td>
                    <td className="p-3 text-right tabular-nums">{fmt(v1)}</td>
                    <td className="p-3 text-right font-semibold tabular-nums">{fmt(v2)}</td>
                    <td className={`p-3 text-right font-semibold tabular-nums ${diff > 0 ? 'text-chart-2' : diff < 0 ? 'text-destructive' : ''}`}>
                      {diff > 0 ? '+' : ''}{fmt(diff)}
                    </td>
                    <td className={`p-3 text-right font-semibold tabular-nums ${pct > 0 ? 'text-chart-2' : pct < 0 ? 'text-destructive' : ''}`}>
                      <span className="inline-flex items-center gap-1">{pct > 0 ? <TrendingUp className="h-3 w-3" /> : pct < 0 ? <TrendingDown className="h-3 w-3" /> : null}{pct.toFixed(1)}%</span>
                    </td>
                  </tr>
                )
              })}
              <tr className="border-t-2 border-border bg-primary/5">
                <td className="p-3 font-bold">Total YTD</td>
                <td className="p-3 text-right font-bold tabular-nums">{fmt(y1Total)}</td>
                <td className="p-3 text-right font-bold tabular-nums">{fmt(y2Total)}</td>
                <td className={`p-3 text-right font-bold tabular-nums ${growth > 0 ? 'text-chart-2' : 'text-destructive'}`}>
                  {growth > 0 ? '+' : ''}{fmt(y2Total - y1Total)}
                </td>
                <td className={`p-3 text-right font-bold tabular-nums ${growth > 0 ? 'text-chart-2' : 'text-destructive'}`}>
                  {growth > 0 ? '+' : ''}{growth.toFixed(1)}%
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}

// =============================================================
// TREND ANALYSIS
// =============================================================
function TrendAnalysis({ params, year }: { params: (x?: string) => string; year: string }) {
  const [data, setData] = useState<any>(null); const [loading, setLoading] = useState(true)
  useEffect(() => {
    setLoading(true)
    fetchLPGCompare(params('')).then(setData).catch(console.error).finally(() => setLoading(false))
  }, [params])

  if (loading) return <Skeleton className="h-80 bg-card rounded-xl" />
  if (!data?.monthly) return <p className="text-muted-foreground text-sm py-8 text-center">Tidak ada data untuk filter ini</p>

  // Sort chronologically: all monthly entries by year then month
  const sorted = (Object.entries(data.monthly) as [string, { mt: number; tb: number }][]).sort(([a], [b]) => {
    const [mA, yA] = a.split('.')
    const [mB, yB] = b.split('.')
    return parseInt(yA) - parseInt(yB) || parseInt(mA) - parseInt(mB)
  })

  const chartData = sorted.map(([ym, v]) => ({
    label: `${MONTH_NAMES[ym.slice(0, 2)] || ym.slice(0, 2)} ${ym.slice(3)}`, MT: Math.round(v.mt),
  }))

  // Calculate MoM
  const momData = sorted.slice(1).map(([ym, v], i) => {
    const prev = sorted[i][1]
    const diff = v.mt - prev.mt
    return { ym, month: chartData[i + 1].label, current: Math.round(v.mt), previous: Math.round(prev.mt), change: Math.round(diff), change_pct: prev.mt > 0 ? (diff / prev.mt) * 100 : 0 }
  })

  const mtValues = sorted.map(([_, v]) => v.mt)
  const avgMT = mtValues.reduce((a: number, b: number) => a + b, 0) / mtValues.length
  const maxMT = Math.max(...mtValues); const minMT = Math.min(...mtValues)
  const maxIdx = mtValues.indexOf(maxMT); const minIdx = mtValues.indexOf(minMT)

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[{ l: 'Rata-rata / Bulan', v: `${fmt(avgMT)} MT` },
          { l: 'Tertinggi', v: `${fmt(maxMT)} MT`, sub: sorted[maxIdx]?.[0] || '', c: 'text-chart-2' },
          { l: 'Terendah', v: `${fmt(minMT)} MT`, sub: sorted[minIdx]?.[0] || '', c: 'text-destructive' },
          { l: 'Total Periode', v: `${sorted.length} bulan`, sub: `${fmt(mtValues.reduce((a, b) => a + b, 0))} MT` },
        ].map((s, i) => (
          <Card key={i} className="bg-card border-border">
            <CardContent className="p-4">
              <p className="text-[11px] text-muted-foreground">{s.l}</p>
              <p className={`text-lg font-bold mt-0.5 ${s.c || ''}`}>{s.v}</p>
              {s.sub && <p className="text-[10px] text-muted-foreground mt-0.5">{s.sub}</p>}
            </CardContent>
          </Card>
        ))}
      </div>

      <Card className="bg-card border-border">
        <CardHeader className="pb-2"><CardTitle className="text-sm font-semibold">Tren Realisasi Bulanan (MT)</CardTitle></CardHeader>
        <CardContent className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <defs><linearGradient id="trendGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="var(--primary)" stopOpacity={0.3}/><stop offset="100%" stopColor="var(--primary)" stopOpacity={0.02}/></linearGradient></defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis dataKey="label" tick={{ fill: 'var(--muted-foreground)', fontSize: 10 }} axisLine={false} tickLine={false} angle={-35} textAnchor="end" height={55} interval={0} />
              <YAxis tick={{ fill: 'var(--muted-foreground)', fontSize: 11 }} axisLine={false} tickLine={false} width={55} />
              <Tooltip content={<ChartTooltip formatter={(v: number) => `${fmt(v)} MT`} />} />
              <Area type="monotone" dataKey="MT" stroke="var(--primary)" strokeWidth={2.5} fill="url(#trendGrad)" dot={{ r: 3, fill: 'var(--primary)', stroke: 'var(--card)', strokeWidth: 2 }} />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card className="bg-card border-border overflow-hidden">
        <CardHeader className="pb-2"><CardTitle className="text-sm font-semibold">Month-over-Month (MoM)</CardTitle></CardHeader>
        <div className="overflow-x-auto">
          <table className="w-full text-xs md:text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/30">
                <th className="text-left p-3 font-semibold text-muted-foreground">Periode</th>
                <th className="text-right p-3 font-semibold text-muted-foreground">Current (MT)</th>
                <th className="text-right p-3 font-semibold text-muted-foreground">Previous</th>
                <th className="text-right p-3 font-semibold text-muted-foreground">Δ MT</th>
                <th className="text-right p-3 font-semibold text-muted-foreground">Δ %</th>
                <th className="text-center p-3 font-semibold text-muted-foreground" style={{width:32}}></th>
              </tr>
            </thead>
            <tbody>
              {momData.slice().reverse().map(d => (
                <tr key={d.ym} className="border-b border-border hover:bg-accent/40 transition-colors">
                  <td className="p-3 font-medium">{d.month}</td>
                  <td className="p-3 text-right font-medium tabular-nums">{fmt(d.current)}</td>
                  <td className="p-3 text-right text-muted-foreground tabular-nums">{fmt(d.previous)}</td>
                  <td className={`p-3 text-right font-medium tabular-nums ${d.change > 0 ? 'text-chart-2' : d.change < 0 ? 'text-destructive' : ''}`}>
                    {d.change > 0 ? '+' : ''}{fmt(d.change)}
                  </td>
                  <td className={`p-3 text-right font-medium tabular-nums ${d.change_pct > 0 ? 'text-chart-2' : d.change_pct < 0 ? 'text-destructive' : ''}`}>
                    {d.change_pct > 0 ? '+' : ''}{d.change_pct.toFixed(2)}%
                  </td>
                  <td className="p-3 text-center">
                    {d.change_pct > 1 ? <TrendingUp className="h-3.5 w-3.5 text-chart-2 inline" /> :
                     d.change_pct < -1 ? <TrendingDown className="h-3.5 w-3.5 text-destructive inline" /> :
                     <Minus className="h-3.5 w-3.5 text-muted-foreground inline" />}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}

// =============================================================
// YoY ANALYSIS
// =============================================================
function YoYAnalysis() {
  const [data, setData] = useState<any>(null); const [loading, setLoading] = useState(true)
  useEffect(() => { fetchLPGCompare().then(setData).catch(console.error).finally(() => setLoading(false)) }, [])

  if (loading) return <Skeleton className="h-80 bg-card rounded-xl" />
  if (!data?.years) return <p className="text-muted-foreground text-sm py-8 text-center">Data belum tersedia</p>

  const { years, monthly } = data
  const sortedYears = Object.entries(years as Record<string, { mt: number; tb: number }>).sort()
  const allChartData = (Object.entries(monthly) as [string, { mt: number; tb: number }][]).sort(([a], [b]) => {
    const [mA, yA] = a.split('.').reverse(); const [mB, yB] = b.split('.').reverse()
    return yA.localeCompare(yB) || mA.localeCompare(mB)
  }).map(([ym, v]) => ({
    month: `${MONTH_NAMES[ym.slice(0, 2)]} ${ym.slice(3)}`, MT: Math.round(v.mt), year: ym.slice(3),
  }))
  const colors = ['var(--muted-foreground)', 'var(--primary)', 'var(--chart-3)', 'var(--chart-4)']

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {sortedYears.map(([yr, v], i) => (
          <Card key={yr} className="bg-card border-border">
            <CardHeader className="p-4 pb-1"><CardTitle className="text-sm font-semibold">Tahun {yr}</CardTitle></CardHeader>
            <CardContent className="p-4 pt-2">
              <p className="text-2xl font-bold">{fmt(v.mt)} <span className="text-sm font-normal text-muted-foreground">MT</span></p>
              <p className="text-xs text-muted-foreground mt-1">{fmt(v.tb)} tabung</p>
            </CardContent>
          </Card>
        ))}
        {sortedYears.length >= 2 && (() => {
          const [y1d, y2d] = [sortedYears[0][1], sortedYears[1][1]]
          const growth = y1d.mt > 0 ? ((y2d.mt - y1d.mt) / y1d.mt * 100) : 0
          return (
            <Card className="bg-card border-border">
              <CardHeader className="p-4 pb-1"><CardTitle className="text-sm font-semibold">Pertumbuhan</CardTitle></CardHeader>
              <CardContent className="p-4 pt-2">
                <p className={`text-2xl font-bold flex items-center gap-2 ${growth >= 0 ? 'text-chart-2' : 'text-destructive'}`}>
                  {growth >= 0 ? <TrendingUp className="h-5 w-5" /> : <TrendingDown className="h-5 w-5" />}
                  {growth >= 0 ? '+' : ''}{growth.toFixed(2)}%
                </p>
                <p className="text-xs text-muted-foreground mt-1">{fmt(Math.abs(y2d.mt - y1d.mt))} MT ({growth >= 0 ? 'naik' : 'turun'})</p>
              </CardContent>
            </Card>
          )
        })()}
      </div>

      <Card className="bg-card border-border">
        <CardHeader className="pb-2"><CardTitle className="text-sm font-semibold">Semua Data Bulanan</CardTitle></CardHeader>
        <CardContent className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={allChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis dataKey="month" tick={{ fill: 'var(--muted-foreground)', fontSize: 9 }} axisLine={false} tickLine={false} angle={-60} textAnchor="end" height={65} />
              <YAxis tick={{ fill: 'var(--muted-foreground)', fontSize: 11 }} axisLine={false} tickLine={false} width={55} />
              <Tooltip content={<ChartTooltip formatter={(v: number) => `${fmt(v)} MT`} />} />
              <Bar dataKey="MT" radius={[3, 3, 0, 0]} maxBarSize={24}>
                {allChartData.map((entry, i) => (
                  <Cell key={i} fill={entry.year === '2026' ? 'var(--primary)' : 'var(--muted-foreground)'} opacity={entry.year === '2026' ? 1 : 0.45} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card className="bg-card border-border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs md:text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/30">
                <th className="text-left p-3 font-semibold text-muted-foreground">Periode</th>
                <th className="text-right p-3 font-semibold text-muted-foreground">MT</th>
                <th className="text-right p-3 font-semibold text-muted-foreground">Tabung</th>
                <th className="text-right p-3 font-semibold text-muted-foreground">Ø MT/Hari</th>
              </tr>
            </thead>
            <tbody>
              {allChartData.map((d, i) => {
                const days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][parseInt(allChartData[i]?.month?.slice(0, 2) || '0') - 1] || 30
                return (
                  <tr key={i} className="border-b border-border hover:bg-accent/40 transition-colors">
                    <td className="p-3 font-medium">{d.month}</td>
                    <td className="p-3 text-right tabular-nums">{fmt(d.MT)}</td>
                    <td className="p-3 text-right text-muted-foreground tabular-nums">{fmt((monthly as any)[Object.keys(monthly).sort()[i]]?.tb || 0)}</td>
                    <td className="p-3 text-right text-muted-foreground tabular-nums">{fmt(d.MT / days)}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}

// =============================================================
// DISTRICT ANALYSIS
// =============================================================
function DistrictAnalysis({ params }: { params: (x?: string) => string }) {
  const [data, setData] = useState<any>(null); const [loading, setLoading] = useState(true)
  useEffect(() => {
    setLoading(true)
    fetchLGPDistricts(params('')).then(setData).catch(console.error).finally(() => setLoading(false))
  }, [params])

  if (loading) return <Skeleton className="h-80 bg-card rounded-xl" />
  if (!data) return <p className="text-muted-foreground text-sm py-8 text-center">Tidak ada data</p>

  const chartData = (Object.entries(data) as [string, { mt: number; tb: number }][]).sort((a, b) => b[1].mt - a[1].mt)
    .map(([name, v]) => ({ name: name.replace('Kab ', '').replace('Kota ', ''), MT: Math.round(v.mt), TB: v.tb }))
  const totalMT = chartData.reduce((s, d) => s + d.MT, 0)

  const barColors = ['var(--primary)', 'var(--chart-2)', 'var(--chart-3)', 'var(--chart-4)', 'var(--chart-5)',
    '#60a5fa', '#34d399', '#fb923c', '#a78bfa', '#f472b6', '#22d3ee', '#fbbf24', '#e879f9', '#6ee7b7']

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <Card className="bg-card border-border">
        <CardHeader className="pb-2"><CardTitle className="text-sm font-semibold">Realisasi per Distrik</CardTitle></CardHeader>
        <CardContent className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
              <XAxis type="number" tick={{ fill: 'var(--muted-foreground)', fontSize: 11 }} axisLine={false} tickLine={false} width={55} />
              <YAxis type="category" dataKey="name" width={85} tick={{ fill: 'var(--muted-foreground)', fontSize: 10 }} axisLine={false} tickLine={false} />
              <Tooltip content={<ChartTooltip formatter={(v: number) => `${fmt(v)} MT`} />} />
              <Bar dataKey="MT" radius={[0, 6, 6, 0]} maxBarSize={20}>
                {chartData.map((_, i) => <Cell key={i} fill={barColors[i % barColors.length]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
      <Card className="bg-card border-border overflow-hidden">
        <div className="overflow-x-auto max-h-[22rem]">
          <table className="w-full text-xs md:text-sm">
            <thead className="sticky top-0 bg-card z-10">
              <tr className="border-b border-border bg-muted/30">
                <th className="text-left p-3 font-semibold text-muted-foreground">Distrik</th>
                <th className="text-right p-3 font-semibold text-muted-foreground">MT</th>
                <th className="text-right p-3 font-semibold text-muted-foreground">% Share</th>
                <th className="text-right p-3 font-semibold text-muted-foreground">Tabung</th>
              </tr>
            </thead>
            <tbody>
              {chartData.map((d, i) => (
                <tr key={d.name} className="border-b border-border hover:bg-accent/40 transition-colors">
                  <td className="p-3 font-medium flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full shrink-0" style={{ background: barColors[i % barColors.length] }} />
                    {d.name}
                  </td>
                  <td className="p-3 text-right font-medium tabular-nums">{fmt(d.MT)}</td>
                  <td className="p-3 text-right text-muted-foreground tabular-nums">{totalMT > 0 ? (d.MT / totalMT * 100).toFixed(1) : 0}%</td>
                  <td className="p-3 text-right text-muted-foreground tabular-nums">{fmt(d.TB)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}

// =============================================================
// SEGMENT ANALYSIS
// =============================================================
function SegmentAnalysis({ params }: { params: (x?: string) => string }) {
  const [data, setData] = useState<any>(null); const [loading, setLoading] = useState(true)
  useEffect(() => {
    setLoading(true)
    fetchLPGSummary(params('')).then(setData).catch(console.error).finally(() => setLoading(false))
  }, [params])

  if (loading) return <Skeleton className="h-80 bg-card rounded-xl" />
  if (!data) return <p className="text-muted-foreground text-sm py-8 text-center">Tidak ada data</p>

  const { segments, materials, total_mt, types } = data
  const segColor: Record<string, string> = { PSO: 'var(--primary)', NPSO_RT: 'var(--chart-2)', NPSO_NRT: 'var(--chart-3)' }
  const segChart = segments.map((s: any) => ({
    name: s.name.replace(/_/g, ' '), MT: Math.round(s.mt), share: total_mt > 0 ? (s.mt / total_mt * 100).toFixed(1) : 0,
    trans: s.trans, tb: s.tb, fill: segColor[s.name] || 'var(--muted-foreground)',
  }))

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card className="bg-card border-border">
          <CardHeader className="pb-2"><CardTitle className="text-sm font-semibold">Komposisi Segmen</CardTitle></CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={segChart}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                <XAxis dataKey="name" tick={{ fill: 'var(--muted-foreground)', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: 'var(--muted-foreground)', fontSize: 11 }} axisLine={false} tickLine={false} width={55} />
                <Tooltip content={<ChartTooltip formatter={(v: number) => `${fmt(v)} MT`} />} />
                <Bar dataKey="MT" radius={[6, 6, 0, 0]} maxBarSize={48}>
                  {segChart.map((s: any, i: number) => <Cell key={i} fill={s.fill} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
        <Card className="bg-card border-border">
          <CardHeader className="pb-2"><CardTitle className="text-sm font-semibold">Material Teratas</CardTitle></CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={materials.slice(0, 8).map((m: any) => ({
                name: m.name.length > 28 ? m.name.slice(0, 28) + '…' : m.name, MT: Math.round(m.mt),
              }))} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
                <XAxis type="number" tick={{ fill: 'var(--muted-foreground)', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis type="category" dataKey="name" width={130} tick={{ fill: 'var(--muted-foreground)', fontSize: 9 }} axisLine={false} tickLine={false} />
                <Tooltip content={<ChartTooltip formatter={(v: number) => `${fmt(v)} MT`} />} />
                <Bar dataKey="MT" fill="var(--chart-2)" radius={[0, 6, 6, 0]} maxBarSize={16} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <Card className="bg-card border-border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs md:text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/30">
                <th className="text-left p-3 font-semibold text-muted-foreground">Segmen</th>
                <th className="text-right p-3 font-semibold text-muted-foreground">MT</th>
                <th className="text-right p-3 font-semibold text-muted-foreground">Share</th>
                <th className="text-right p-3 font-semibold text-muted-foreground">Tabung</th>
                <th className="text-right p-3 font-semibold text-muted-foreground">Transaksi</th>
              </tr>
            </thead>
            <tbody>
              {segChart.map((s: any) => (
                <tr key={s.name} className="border-b border-border hover:bg-accent/40 transition-colors">
                  <td className="p-3 font-medium flex items-center gap-2">
                    <span className="h-2.5 w-2.5 rounded-sm shrink-0" style={{ background: s.fill }} />
                    {s.name}
                  </td>
                  <td className="p-3 text-right font-medium tabular-nums">{fmt(s.MT)}</td>
                  <td className="p-3 text-right text-muted-foreground tabular-nums">{s.share}%</td>
                  <td className="p-3 text-right text-muted-foreground tabular-nums">{fmt(s.tb)}</td>
                  <td className="p-3 text-right text-muted-foreground tabular-nums">{s.trans.toLocaleString('id')}</td>
                </tr>
              ))}
              {types?.filter((_: any, i: number) => i > 0).map((t: any, i: number) => (
                <tr key={i} className="border-b border-border hover:bg-accent/40 transition-colors">
                  <td className="p-3 text-muted-foreground pl-8 text-[11px]">└ {t.name}</td>
                  <td className={`p-3 text-right text-muted-foreground tabular-nums`}>{fmt(t.mt)}</td>
                  <td className="p-3 text-right text-muted-foreground tabular-nums">
                    {total_mt > 0 ? (t.mt / total_mt * 100).toFixed(1) : 0}%
                  </td>
                  <td className="p-3 text-right text-muted-foreground tabular-nums">{fmt(t.tb)}</td>
                  <td className="p-3 text-right text-muted-foreground tabular-nums">—</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}
