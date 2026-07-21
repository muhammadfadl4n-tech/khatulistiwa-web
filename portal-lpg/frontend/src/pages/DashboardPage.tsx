import { useEffect, useState } from 'react'
import { fetchLPGSummary } from '@/lib/api'
import type { LPGSummary } from '@/lib/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Fuel, Package, BarChart3, Building2, MapPin, Users, TrendingUp,
} from 'lucide-react'

const iconMap = {
  total_mt: { icon: TrendingUp, color: 'text-primary', bg: 'bg-primary/10' },
  total_tabung: { icon: Package, color: 'text-chart-2', bg: 'bg-chart-2/10' },
  total_districts: { icon: MapPin, color: 'text-chart-3', bg: 'bg-chart-3/10' },
  total_plants: { icon: Building2, color: 'text-chart-4', bg: 'bg-chart-4/10' },
  pso_agents: { icon: Users, color: 'text-chart-2', bg: 'bg-chart-2/10' },
  npso_agents: { icon: Fuel, color: 'text-chart-3', bg: 'bg-chart-3/10' },
  total_months: { icon: BarChart3, color: 'text-chart-5', bg: 'bg-chart-5/10' },
}

export default function DashboardPage() {
  const [summary, setSummary] = useState<LPGSummary | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchLPGSummary()
      .then(setSummary)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const stats = summary ? [
    { label: 'Total MT', value: summary.total_mt.toLocaleString('id'), key: 'total_mt' as const },
    { label: 'Total Tabung', value: summary.total_tabung.toLocaleString('id'), key: 'total_tabung' as const },
    { label: 'Distrik', value: summary.total_districts.toString(), key: 'total_districts' as const },
    { label: 'Plant', value: summary.total_plants.toString(), key: 'total_plants' as const },
    { label: 'Agen PSO', value: summary.pso_agents.toString(), key: 'pso_agents' as const },
    { label: 'Agen NPSO', value: summary.npso_agents.toString(), key: 'npso_agents' as const },
    { label: 'Bulan Data', value: summary.total_months.toString(), key: 'total_months' as const },
  ] : []

  return (
    <div className="space-y-4 md:space-y-6">
      <div>
        <h1 className="text-xl md:text-2xl font-bold">Dashboard</h1>
        <p className="text-xs md:text-sm text-muted-foreground mt-0.5">Overview data LPG Kalimantan Barat</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-7 gap-2 md:gap-3">
        {loading
          ? Array(7).fill(0).map((_, i) => (
              <Card key={i} className="bg-card border-border">
                <CardContent className="p-3 md:p-4">
                  <Skeleton className="h-3 w-16 mb-2 bg-muted" />
                  <Skeleton className="h-5 md:h-6 w-20 bg-muted" />
                </CardContent>
              </Card>
            ))
          : stats.map((stat) => {
              const meta = iconMap[stat.key]
              const Icon = meta.icon
              return (
                <Card key={stat.key} className="bg-card border-border">
                  <CardContent className="p-3 md:p-4">
                    <div className="flex items-center justify-between mb-1.5 md:mb-2">
                      <span className="text-[10px] md:text-xs text-muted-foreground font-medium truncate">{stat.label}</span>
                      <div className={`h-6 w-6 md:h-7 md:w-7 rounded-lg ${meta.bg} flex items-center justify-center shrink-0`}>
                        <Icon className={`h-3 md:h-3.5 w-3 md:w-3.5 ${meta.color}`} />
                      </div>
                    </div>
                    <div className="text-base md:text-xl font-bold tracking-tight">{stat.value}</div>
                  </CardContent>
                </Card>
              )
            })
        }
      </div>

      {/* Segments + Materials */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 md:gap-4">
        <Card className="bg-card border-border">
          <CardHeader className="p-3 md:p-4">
            <CardTitle className="text-sm font-semibold">Segmen LPG</CardTitle>
          </CardHeader>
          <CardContent className="p-3 md:p-4 pt-0 md:pt-0">
            {loading ? (
              <div className="space-y-2">
                {[1,2,3].map(i => <Skeleton key={i} className="h-8 bg-muted" />)}
              </div>
            ) : (
              <div className="space-y-1.5">
                {summary?.segments.map((seg) => (
                  <div key={seg.name} className="flex items-center justify-between py-1.5 md:py-2 px-2.5 md:px-3 rounded-lg bg-accent/50">
                    <div className="min-w-0">
                      <span className="text-xs md:text-sm font-medium capitalize truncate block">{seg.name.replace(/_/g, ' ')}</span>
                      <span className="text-[10px] md:text-xs text-muted-foreground">{seg.trans} trans</span>
                    </div>
                    <div className="text-right shrink-0 ml-2">
                      <div className="text-xs md:text-sm font-semibold">{seg.mt.toLocaleString('id')} MT</div>
                      <div className="text-[10px] md:text-xs text-muted-foreground">{seg.tb.toLocaleString('id')} tb</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardHeader className="p-3 md:p-4">
            <CardTitle className="text-sm font-semibold">Material Teratas</CardTitle>
          </CardHeader>
          <CardContent className="p-3 md:p-4 pt-0 md:pt-0">
            {loading ? (
              <div className="space-y-2">
                {[1,2,3,4].map(i => <Skeleton key={i} className="h-8 bg-muted" />)}
              </div>
            ) : (
              <div className="space-y-1.5">
                {summary?.materials.slice(0, 8).map((mat) => (
                  <div key={mat.name} className="flex items-center justify-between py-1.5 md:py-2 px-2.5 md:px-3 rounded-lg bg-accent/50">
                    <span className="text-xs md:text-sm truncate max-w-[55%]">{mat.name}</span>
                    <div className="text-right shrink-0 ml-2">
                      <div className="text-xs md:text-sm font-semibold">{mat.mt.toLocaleString('id')} MT</div>
                      <div className="text-[10px] md:text-xs text-muted-foreground">{mat.tb.toLocaleString('id')} tb</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Data Info */}
      {summary && (
        <Card className="bg-card border-border">
          <CardContent className="p-3 md:p-4 text-[10px] md:text-xs text-muted-foreground flex flex-wrap gap-x-4 gap-y-1">
            <span>📅 {summary.date_from} — {summary.date_to}</span>
            {summary.last_data_date && <span>📊 {summary.last_data_date}</span>}
            {summary.last_update && <span>🔄 {summary.last_update}</span>}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
