import { useEffect, useState } from 'react'
import { fetchPangkalanStats, fetchPangkalanList } from '@/lib/api'
import type { PangkalanStats, PangkalanRow } from '@/lib/types'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Search, MapPin, AlertTriangle, Layers, Crosshair } from 'lucide-react'

export default function PangkalanPage() {
  const [stats, setStats] = useState<PangkalanStats | null>(null)
  const [list, setList] = useState<PangkalanRow[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [issueFilter, setIssueFilter] = useState('')

  const loadData = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (search) params.set('search', search)
      if (issueFilter) params.set('issue', issueFilter)
      const qs = params.toString()
      const [s, l] = await Promise.all([
        fetchPangkalanStats(),
        fetchPangkalanList(qs ? `?${qs}` : ''),
      ])
      setStats(s)
      setList(l)
    } catch (err) { console.error(err) } finally { setLoading(false) }
  }

  useEffect(() => { loadData() }, [])

  const handleSearch = (e: React.FormEvent) => { e.preventDefault(); loadData() }

  const issueCards = stats ? [
    { label: 'Total Pangkalan', value: stats.total_pangkalan, icon: MapPin, color: 'text-primary', bg: 'bg-primary/10' },
    { label: 'Kota Kosong', value: stats.kota_kosong_count, icon: AlertTriangle, color: 'text-chart-3', bg: 'bg-chart-3/10', filter: 'kota_kosong' },
    { label: 'Koordinat Kosong', value: stats.koordinat_kosong_count, icon: Crosshair, color: 'text-destructive', bg: 'bg-destructive/10', filter: 'koordinat_kosong' },
    { label: 'Duplikat', value: stats.duplicate_registrasi_count, icon: Layers, color: 'text-chart-4', bg: 'bg-chart-4/10', filter: 'duplikat' },
  ] : []

  return (
    <div className="space-y-4 md:space-y-6">
      <div>
        <h1 className="text-xl md:text-2xl font-bold">Pangkalan</h1>
        <p className="text-xs md:text-sm text-muted-foreground mt-0.5">Data pangkalan LPG dan quality check</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 md:gap-3">
        {!stats ? [1,2,3,4].map(i => <Skeleton key={i} className="h-16 md:h-20 bg-card" />)
          : issueCards.map(s => (
              <Card
                key={s.label}
                className={`bg-card border-border cursor-pointer transition-all hover:border-primary/30 ${issueFilter === s.filter ? 'ring-1 ring-primary' : ''}`}
                onClick={() => { if (s.filter) setIssueFilter(issueFilter === s.filter ? '' : s.filter) }}
              >
                <CardContent className="p-3 md:p-4 flex items-center gap-2 md:gap-3">
                  <div className={`h-8 w-8 md:h-10 md:w-10 rounded-lg ${s.bg} flex items-center justify-center shrink-0`}>
                    <s.icon className={`h-4 md:h-5 w-4 md:w-5 ${s.color}`} />
                  </div>
                  <div className="min-w-0">
                    <div className="text-[10px] md:text-xs text-muted-foreground">{s.label}</div>
                    <div className="text-base md:text-xl font-bold">{s.value}</div>
                  </div>
                </CardContent>
              </Card>
            ))
        }
      </div>

      {issueFilter && (
        <div className="flex items-center gap-2 text-xs md:text-sm">
          <Badge className="bg-primary/15 text-primary border-primary/30">
            Filter: {issueFilter.replace(/_/g, ' ')}
          </Badge>
          <Button variant="ghost" size="sm" onClick={() => { setIssueFilter(''); loadData() }} className="text-muted-foreground h-7 md:h-8">
            Reset
          </Button>
        </div>
      )}

      <form onSubmit={handleSearch} className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-2.5 md:left-3 top-1/2 -translate-y-1/2 h-3.5 md:h-4 w-3.5 md:w-4 text-muted-foreground" />
          <Input
            placeholder="Cari nama pangkalan atau ID registrasi..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="bg-card border-border text-foreground pl-8 md:pl-9 text-xs md:text-sm"
          />
        </div>
        <Button type="submit" variant="secondary" size="sm" className="md:hidden">Cari</Button>
        <Button type="submit" variant="secondary" className="hidden md:flex">Cari</Button>
      </form>

      <Card className="bg-card border-border">
        <div className="overflow-x-auto max-h-[50vh] md:max-h-[65vh]">
          <table className="w-full text-xs md:text-sm">
            <thead className="sticky top-0 bg-card z-10">
              <tr className="border-b border-border text-muted-foreground">
                <th className="text-left p-2 md:p-3 font-medium whitespace-nowrap">Nama Pangkalan</th>
                <th className="text-left p-2 md:p-3 font-medium hidden md:table-cell">Agen</th>
                <th className="text-left p-2 md:p-3 font-medium hidden lg:table-cell">ID Registrasi</th>
                <th className="text-left p-2 md:p-3 font-medium">Kota</th>
                <th className="text-center p-2 md:p-3 font-medium">Koor</th>
              </tr>
            </thead>
            <tbody>
              {loading ? Array(10).fill(0).map((_, i) => (
                <tr key={i} className="border-b border-border"><td colSpan={5} className="p-2 md:p-3"><Skeleton className="h-4 md:h-5 bg-muted" /></td></tr>
              )) : list.map(p => (
                <tr key={p.id} className="border-b border-border hover:bg-accent/50">
                  <td className="p-2 md:p-3 font-medium max-w-[130px] md:max-w-none truncate">{p.nama_pangkalan}</td>
                  <td className="p-2 md:p-3 text-muted-foreground hidden md:table-cell truncate max-w-[120px]">{p.nama_agen}</td>
                  <td className="p-2 md:p-3 font-mono text-[10px] text-muted-foreground hidden lg:table-cell">{p.id_registrasi || '-'}</td>
                  <td className="p-2 md:p-3">
                    {p.kota ? (
                      <Badge variant="outline" className="border-border text-foreground text-[10px] md:text-xs">{p.kota}</Badge>
                    ) : (
                      <Badge className="bg-chart-3/10 text-chart-3 border-0 text-[10px] md:text-xs">Kosong</Badge>
                    )}
                  </td>
                  <td className="p-2 md:p-3 text-center">
                    {p.latitude && p.longitude && parseFloat(p.latitude) !== 0 ? (
                      <Badge variant="outline" className="border-border text-chart-2 text-[10px] md:text-xs">✓</Badge>
                    ) : (
                      <Badge className="bg-destructive/10 text-destructive border-0 text-[10px] md:text-xs">✗</Badge>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
      {!loading && (
        <p className="text-[10px] md:text-xs text-muted-foreground">{list.length} pangkalan ditampilkan</p>
      )}
    </div>
  )
}
