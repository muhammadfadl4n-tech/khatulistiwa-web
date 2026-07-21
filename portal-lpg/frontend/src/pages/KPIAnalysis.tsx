import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Skeleton } from '@/components/ui/skeleton'
import { TrendingUp, TrendingDown, Settings, CheckCircle2, AlertTriangle, Target, BarChart3, CalendarDays } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell } from 'recharts'

function fmt(v: number): string { return v.toLocaleString('id', { maximumFractionDigits: 0 }) }

const chartTooltipStyle = { background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--foreground)', fontSize: 12 }

// ── PSO Kuota Tab ──────────────────────────────────────────
export default function KPIAnalysis({ params }: { params: (x?: string) => string }) {
  const [psoData, setPsoData] = useState<any>(null)
  const [npsoData, setNpsoData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  const fetchData = async () => {
    setLoading(true)
    try {
      const [pso, npso] = await Promise.all([
        fetch(`/api/kpi/psokuota${params('')}`).then(r => r.json()),
        fetch(`/api/kpi/npsotargets${params('')}`).then(r => r.json()),
      ])
      setPsoData(pso)
      setNpsoData(npso)
    } catch (e) { console.error(e) } finally { setLoading(false) }
  }

  useEffect(() => { fetchData() }, [params])

  if (loading) return <div className="space-y-4">{[1,2,3].map(i => <Skeleton key={i} className="h-32 bg-card rounded-xl" />)}</div>

  return (
    <div className="space-y-5">
      {/* ── NPSO RT & NRT vs Target ──────────────────── */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold flex items-center gap-1.5">
            <Target className="h-4 w-4 text-chart-2" />
            NPSO vs Target — <span className="text-muted-foreground font-normal">semakin tinggi semakin baik</span>
          </h3>
          <EditTargetDialog onSaved={fetchData} />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {npsoData?.segments?.map((seg: any) => {
            const isGood = seg.pct_realisasi > 50 // Above 50% toward target = good for NPSO
            return (
              <Card key={seg.label} className="bg-card border-border">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <p className="text-sm font-semibold">{seg.label === 'NPSO_RT' ? 'NPSO RT (Bright Gas)' : 'NPSO NRT (50kg, Mixed, dll)'}</p>
                      <p className="text-[11px] text-muted-foreground mt-0.5">Target 2026: {fmt(seg.target_tahunan)} MT</p>
                    </div>
                    <Badge className={isGood ? 'bg-chart-2/15 text-chart-2 border-0' : 'bg-chart-3/15 text-chart-3 border-0'}>
                      {seg.pct_realisasi.toFixed(1)}%
                    </Badge>
                  </div>
                  {/* Progress bar */}
                  <div className="h-2.5 rounded-full bg-muted overflow-hidden mb-2">
                    <div className="h-full rounded-full bg-chart-2 transition-all duration-500"
                      style={{ width: `${Math.min(seg.pct_realisasi, 100)}%` }} />
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-muted-foreground">Realisasi: <span className="font-semibold text-foreground">{fmt(seg.realisasi_mt)} MT</span></span>
                    <span className={isGood ? 'text-chart-2' : 'text-chart-3'}>
                      {isGood ? <TrendingUp className="h-3 w-3 inline" /> : <TrendingDown className="h-3 w-3 inline" />}
                      {' '}Sisa {fmt(seg.target_tahunan - seg.realisasi_mt)} MT
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-[10px] text-muted-foreground mt-1.5 pt-1.5 border-t border-border/50">
                    <span>Proyeksi akhir thn: <span className={`font-semibold ${seg.proyeksi_akhir_tahun > seg.target_tahunan ? 'text-destructive' : 'text-chart-2'}`}>
                      {fmt(seg.proyeksi_akhir_tahun)} MT
                    </span></span>
                    <span>{npsoData.bulan_berjalan}/12 bln</span>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      </section>

      {/* ── PSO Realisasi vs Kuota per Wilayah ──────────── */}
      <section>
        <div className="flex items-center gap-1.5 mb-3">
          <CheckCircle2 className="h-4 w-4 text-primary" />
          <h3 className="text-sm font-semibold">PSO Realisasi vs Kuota 2026</h3>
          <span className="text-[11px] text-muted-foreground ml-1">
            — di bawah kuota = <span className="text-chart-2">terkendali ✅</span>
          </span>
        </div>

        {/* Summary */}
        {psoData && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-4">
            <Card className="bg-card border-border">
              <CardContent className="p-3 md:p-4">
                <p className="text-[10px] md:text-xs text-muted-foreground">Total Realisasi</p>
                <p className="text-base md:text-lg font-bold">{fmt(psoData.total_realisasi)} <span className="text-xs font-normal text-muted-foreground">MT</span></p>
              </CardContent>
            </Card>
            <Card className="bg-card border-border">
              <CardContent className="p-3 md:p-4">
                <p className="text-[10px] md:text-xs text-muted-foreground">Total Kuota</p>
                <p className="text-base md:text-lg font-bold">{fmt(psoData.total_kuota)} <span className="text-xs font-normal text-muted-foreground">MT</span></p>
              </CardContent>
            </Card>
            <Card className="bg-card border-border">
              <CardContent className="p-3 md:p-4">
                <p className="text-[10px] md:text-xs text-muted-foreground">Sisa Kuota</p>
                <p className="text-base md:text-lg font-bold text-chart-2">{fmt(psoData.total_kuota - psoData.total_realisasi)} <span className="text-xs font-normal text-muted-foreground">MT</span></p>
              </CardContent>
            </Card>
            <Card className="bg-card border-border">
              <CardContent className="p-3 md:p-4">
                <p className="text-[10px] md:text-xs text-muted-foreground">Penyerapan</p>
                <p className="text-base md:text-lg font-bold">{psoData.total_kuota > 0 ? (psoData.total_realisasi / psoData.total_kuota * 100).toFixed(1) : 0}%</p>
              </CardContent>
            </Card>
            <Card className="bg-card border-border">
              <CardContent className="p-3 md:p-4">
                <p className="text-[10px] md:text-xs text-muted-foreground">Proyeksi Akhir Thn</p>
                <p className={`text-base md:text-lg font-bold ${psoData.proyeksi_akhir_tahun > psoData.total_kuota ? 'text-destructive' : 'text-chart-2'}`}>
                  {fmt(psoData.proyeksi_akhir_tahun)} <span className="text-xs font-normal text-muted-foreground">MT</span>
                </p>
                {psoData.total_kuota > 0 && (
                  <p className="text-[10px] text-muted-foreground mt-0.5">
                    vs kuota {fmt(psoData.total_kuota)} MT ({psoData.bulan_berjalan}/12 bln)
                  </p>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {/* Chart */}
        <Card className="bg-card border-border mb-3">
          <CardContent className="h-80 p-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={
                psoData?.data?.map((d: any) => ({
                  name: d.wilayah.replace('Kab ', '').replace('Kota ', ''),
                  realisasi: Math.round(d.realisasi_mt),
                  kuota: Math.round(d.kuota_tahunan),
                  status: d.status,
                })) || []
              }>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                <XAxis dataKey="name" tick={{ fill: 'var(--muted-foreground)', fontSize: 9 }} axisLine={false} tickLine={false} angle={-35} textAnchor="end" height={55} />
                <YAxis tick={{ fill: 'var(--muted-foreground)', fontSize: 11 }} axisLine={false} tickLine={false} width={55} />
                <Tooltip contentStyle={chartTooltipStyle} />
                <Bar dataKey="kuota" fill="var(--muted-foreground)" radius={[4, 4, 0, 0]} opacity={0.3} maxBarSize={20} name="Kuota" />
                <Bar dataKey="realisasi" radius={[4, 4, 0, 0]} maxBarSize={20} name="Realisasi">
                  {psoData?.data?.map((d: any, i: number) => (
                    <Cell key={i} fill={d.status === 'aman' ? 'var(--chart-2)' : 'var(--chart-3)'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Table */}
        <Card className="bg-card border-border overflow-hidden">
          <div className="overflow-x-auto overflow-y-auto max-h-[28rem]">
            <table className="w-full text-xs md:text-sm">
              <thead className="sticky top-0 z-10 bg-card">
                <tr className="border-b border-border bg-muted/30">
                  <th className="text-left p-2.5 font-semibold text-muted-foreground">Wilayah</th>
                  <th className="text-right p-2.5 font-semibold text-muted-foreground">Realisasi</th>
                  <th className="text-right p-2.5 font-semibold text-muted-foreground">Kuota</th>
                  <th className="text-right p-2.5 font-semibold text-muted-foreground">%</th>
                  <th className="text-right p-2.5 font-semibold text-muted-foreground">Sisa</th>
                  <th className="text-right p-2.5 font-semibold text-muted-foreground">Proyeksi</th>
                  <th className="text-center p-2.5 font-semibold text-muted-foreground">Status</th>
                </tr>
              </thead>
              <tbody>
                {psoData?.data?.map((d: any) => (
                  <tr key={d.wilayah} className="border-b border-border hover:bg-accent/40 transition-colors">
                    <td className="p-2.5 font-medium whitespace-nowrap">{d.wilayah}</td>
                    <td className="p-2.5 text-right tabular-nums">{fmt(d.realisasi_mt)}</td>
                    <td className="p-2.5 text-right text-muted-foreground tabular-nums">{fmt(d.kuota_tahunan)}</td>
                    <td className={`p-2.5 text-right font-semibold tabular-nums ${d.pct_realisasi <= 100 ? 'text-chart-2' : 'text-destructive'}`}>
                      {d.pct_realisasi}%
                    </td>
                    <td className="p-2.5 text-right tabular-nums">{fmt(d.kuota_tahunan - d.realisasi_mt)}</td>
                    <td className={`p-2.5 text-right tabular-nums ${d.proyeksi_akhir_tahun > d.kuota_tahunan ? 'text-destructive' : 'text-chart-2'}`}>
                      {fmt(d.proyeksi_akhir_tahun)}
                    </td>
                    <td className="p-2.5 text-center">
                      <Badge className={`border-0 text-[10px] ${d.status === 'aman' ? 'bg-chart-2/10 text-chart-2' : 'bg-chart-3/10 text-chart-3'}`}>
                        {d.status === 'aman' ? '✅ Aman' : '⚠️ Perhatian'}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </section>
    </div>
  )
}

// ── Edit Target Dialog ─────────────────────────────────────
function EditTargetDialog({ onSaved }: { onSaved: () => void }) {
  const [open, setOpen] = useState(false)
  const [rt, setRt] = useState('40000')
  const [nrt, setNrt] = useState('600')
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState('')

  const load = async () => {
    const r = await fetch('/api/settings/targets', { credentials: 'include' })
    const d = await r.json()
    setRt(String(d.NPSO_RT || 40000))
    setNrt(String(d.NPSO_NRT || 600))
  }

  useEffect(() => { if (open) load() }, [open])

  const save = async () => {
    setSaving(true); setMsg('')
    try {
      const r = await fetch('/api/settings/targets', {
        method: 'PUT', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ NPSO_RT: parseFloat(rt), NPSO_NRT: parseFloat(nrt) }),
      })
      const d = await r.json()
      if (d.success) { setMsg('✅ Tersimpan!'); setTimeout(() => { setOpen(false); onSaved() }, 800) }
      else setMsg('❌ ' + d.error)
    } catch (e: any) { setMsg('❌ ' + e.message) } finally { setSaving(false) }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger>
        <Button variant="outline" size="sm" className="h-7 text-xs border-border">
          <Settings className="h-3 w-3 mr-1" /> Atur Target
        </Button>
      </DialogTrigger>
      <DialogContent className="bg-card border-border text-foreground max-w-sm">
        <DialogHeader><DialogTitle className="text-sm">Target NPSO 2026 (MT)</DialogTitle></DialogHeader>
        <div className="space-y-4">
          <div>
            <label className="text-xs text-muted-foreground mb-1 block">NPSO RT (Bright Gas)</label>
            <Input value={rt} onChange={e => setRt(e.target.value)} type="number" className="bg-secondary/50 border-border" />
          </div>
          <div>
            <label className="text-xs text-muted-foreground mb-1 block">NPSO NRT (50kg, Mixed, dll)</label>
            <Input value={nrt} onChange={e => setNrt(e.target.value)} type="number" className="bg-secondary/50 border-border" />
          </div>
          {msg && <p className="text-xs text-center">{msg}</p>}
          <Button onClick={save} className="w-full" disabled={saving}>
            {saving ? 'Menyimpan...' : 'Simpan Target'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
