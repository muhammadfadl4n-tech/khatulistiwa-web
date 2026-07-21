import { useEffect, useState } from 'react'
import { fetchAgenList, fetchAgenStats, fetchAgenDetail } from '@/lib/api'
import type { AgenData, AgenStats } from '@/lib/types'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Skeleton } from '@/components/ui/skeleton'
import { Search, Users, Building2, Store, ExternalLink, Navigation } from 'lucide-react'

export default function AgenPage() {
  const [agenList, setAgenList] = useState<AgenData[]>([])
  const [stats, setStats] = useState<AgenStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [detailAgen, setDetailAgen] = useState<AgenData | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)

  const loadData = async (q?: string) => {
    setLoading(true)
    try {
      const [list, s] = await Promise.all([
        fetchAgenList(q ? `?q=${encodeURIComponent(q)}` : ''),
        fetchAgenStats(),
      ])
      setAgenList(list)
      setStats(s)
    } catch (err) { console.error(err) } finally { setLoading(false) }
  }

  useEffect(() => { loadData() }, [])

  const handleSearch = (e: React.FormEvent) => { e.preventDefault(); loadData(search) }

  const openDetail = async (nama: string) => {
    setDetailLoading(true)
    try { setDetailAgen(await fetchAgenDetail(nama)) } catch (err) { console.error(err) } finally { setDetailLoading(false) }
  }

  const statsCards = stats ? [
    { label: 'Total Agen', value: stats.total, icon: Users, color: 'text-primary', bg: 'bg-primary/10' },
    { label: 'Kabupaten', value: stats.kabupaten_count, icon: Building2, color: 'text-chart-2', bg: 'bg-chart-2/10' },
    { label: 'Dengan Alokasi', value: stats.tw3_count, icon: Store, color: 'text-chart-3', bg: 'bg-chart-3/10' },
  ] : []

  return (
    <div className="space-y-4 md:space-y-6">
      <div>
        <h1 className="text-xl md:text-2xl font-bold">Data Agen</h1>
        <p className="text-xs md:text-sm text-muted-foreground mt-0.5">Informasi agen LPG Kalimantan Barat</p>
      </div>

      <div className="grid grid-cols-3 gap-2 md:gap-3">
        {!stats ? [1,2,3].map(i => <Skeleton key={i} className="h-16 md:h-20 bg-card" />)
          : statsCards.map(s => (
              <Card key={s.label} className="bg-card border-border">
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

      <form onSubmit={handleSearch} className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-2.5 md:left-3 top-1/2 -translate-y-1/2 h-3.5 md:h-4 w-3.5 md:w-4 text-muted-foreground" />
          <Input
            placeholder="Cari agen, afiliasi, pengusaha..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="bg-card border-border text-foreground pl-8 md:pl-9 text-xs md:text-sm"
          />
        </div>
        <Button type="submit" variant="secondary" size="sm" className="md:hidden">Cari</Button>
        <Button type="submit" variant="secondary" className="hidden md:flex">Cari</Button>
      </form>

      <Card className="bg-card border-border">
        <div className="overflow-x-auto max-h-[60vh] md:max-h-[70vh]">
          <table className="w-full text-xs md:text-sm">
            <thead className="sticky top-0 bg-card z-10">
              <tr className="border-b border-border text-muted-foreground">
                <th className="text-left p-2 md:p-3 font-medium whitespace-nowrap">Nama Agen</th>
                <th className="text-left p-2 md:p-3 font-medium whitespace-nowrap">Sold To</th>
                <th className="text-left p-2 md:p-3 font-medium hidden md:table-cell">Wilayah</th>
                <th className="text-left p-2 md:p-3 font-medium hidden lg:table-cell">Rayon</th>
                <th className="text-left p-2 md:p-3 font-medium hidden md:table-cell">Pengusaha</th>
                <th className="text-center p-2 md:p-3 w-8 md:w-16">Det</th>
              </tr>
            </thead>
            <tbody>
              {loading ? Array(8).fill(0).map((_, i) => (
                <tr key={i} className="border-b border-border"><td colSpan={6} className="p-2 md:p-3"><Skeleton className="h-4 md:h-5 bg-muted" /></td></tr>
              )) : agenList.map(a => (
                <tr key={a.sold_to} className="border-b border-border hover:bg-accent/50">
                  <td className="p-2 md:p-3 font-medium max-w-[120px] md:max-w-none truncate">{a.nama_agen}</td>
                  <td className="p-2 md:p-3 text-muted-foreground font-mono text-[10px] md:text-xs">{a.sold_to}</td>
                  <td className="p-2 md:p-3 hidden md:table-cell whitespace-nowrap">{a.wilayah}</td>
                  <td className="p-2 md:p-3 text-muted-foreground hidden lg:table-cell">{a.rayon_sbm || '-'}</td>
                  <td className="p-2 md:p-3 hidden md:table-cell truncate max-w-[100px]">{a.pengusaha || '-'}</td>
                  <td className="p-2 md:p-3 text-center">
                    <Dialog>
                      <DialogTrigger onClick={() => openDetail(a.nama_agen)}>
                        <Button variant="ghost" size="icon" className="h-7 w-7 md:h-8 md:w-8 text-muted-foreground">
                          <ExternalLink className="h-3 md:h-3.5 w-3 md:w-3.5" />
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="bg-card border-border text-foreground w-[95vw] max-w-lg md:max-w-2xl lg:max-w-3xl max-h-[85vh] overflow-y-auto p-4 md:p-6">
                        <DialogHeader>
                          <DialogTitle className="text-sm md:text-base">{detailAgen?.nama_agen || 'Loading...'}</DialogTitle>
                        </DialogHeader>
                        {detailLoading ? (
                          <div className="space-y-2">{[1,2,3,4,5].map(i => <Skeleton key={i} className="h-5 md:h-6 bg-muted" />)}</div>
                        ) : detailAgen ? (
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 md:gap-x-6 gap-y-3 text-xs md:text-sm">
                            {/* Row 1 */}
                            <div>
                              <div className="text-[10px] md:text-xs text-muted-foreground">ID</div>
                              <div className="font-medium">{detailAgen.id ?? '-'}</div>
                            </div>
                            <div>
                              <div className="text-[10px] md:text-xs text-muted-foreground">Nomor</div>
                              <div className="font-medium">{detailAgen.no ?? '-'}</div>
                            </div>
                            {/* Row 2 */}
                            <div>
                              <div className="text-[10px] md:text-xs text-muted-foreground">Wilayah</div>
                              <div className="font-medium">{detailAgen.wilayah || '-'}</div>
                            </div>
                            <div>
                              <div className="text-[10px] md:text-xs text-muted-foreground">Rayon SBM</div>
                              <div className="font-medium">{detailAgen.rayon_sbm || '-'}</div>
                            </div>
                            {/* Row 3 */}
                            <div className="col-span-2">
                              <div className="text-[10px] md:text-xs text-muted-foreground">Nama Agen</div>
                              <div className="font-medium">{detailAgen.nama_agen || '-'}</div>
                            </div>
                            {/* Row 4 */}
                            <div>
                              <div className="text-[10px] md:text-xs text-muted-foreground">Sold To</div>
                              <div className="font-medium font-mono">{detailAgen.sold_to ?? '-'}</div>
                            </div>
                            <div>
                              <div className="text-[10px] md:text-xs text-muted-foreground">Alokasi (MT)</div>
                              <div className="font-medium">{detailAgen.alokasi ? Number(detailAgen.alokasi).toLocaleString('id') : '-'}</div>
                            </div>
                            {/* Row 5 */}
                            <div className="col-span-2">
                              <div className="text-[10px] md:text-xs text-muted-foreground">Alamat Kantor</div>
                              <div className="font-medium">{detailAgen.alamat_kantor || '-'}</div>
                            </div>
                            {/* Row 6 */}
                            <div>
                              <div className="text-[10px] md:text-xs text-muted-foreground">Desa/Kelurahan</div>
                              <div className="font-medium">{detailAgen.desa_kel || '-'}</div>
                            </div>
                            <div>
                              <div className="text-[10px] md:text-xs text-muted-foreground">Kecamatan</div>
                              <div className="font-medium">{detailAgen.kecamatan || '-'}</div>
                            </div>
                            {/* Row 7 */}
                            <div>
                              <div className="text-[10px] md:text-xs text-muted-foreground">Latitude</div>
                              <div className="font-medium font-mono text-[10px]">
                                {detailAgen.latitude ? (
                                  <a href={`https://www.google.com/maps/dir/?api=1&destination=${detailAgen.latitude},${detailAgen.longitude}`}
                                     target="_blank" rel="noopener noreferrer"
                                     className="text-primary hover:underline inline-flex items-center gap-1">
                                    {detailAgen.latitude} <Navigation className="h-2.5 w-2.5" />
                                  </a>
                                ) : '-'}
                              </div>
                            </div>
                            <div>
                              <div className="text-[10px] md:text-xs text-muted-foreground">Longitude</div>
                              <div className="font-medium font-mono text-[10px]">
                                {detailAgen.longitude ? (
                                  <a href={`https://www.google.com/maps/dir/?api=1&destination=${detailAgen.latitude},${detailAgen.longitude}`}
                                     target="_blank" rel="noopener noreferrer"
                                     className="text-primary hover:underline inline-flex items-center gap-1">
                                    {detailAgen.longitude} <Navigation className="h-2.5 w-2.5" />
                                  </a>
                                ) : '-'}
                              </div>
                            </div>
                            {/* Row 8 */}
                            <div>
                              <div className="text-[10px] md:text-xs text-muted-foreground">Pengusaha</div>
                              <div className="font-medium">{detailAgen.pengusaha || '-'}</div>
                            </div>
                            <div>
                              <div className="text-[10px] md:text-xs text-muted-foreground">No. Pengusaha</div>
                              <div className="font-medium font-mono">{detailAgen.no_pengusaha || '-'}</div>
                            </div>
                            {/* Row 9 */}
                            <div>
                              <div className="text-[10px] md:text-xs text-muted-foreground">PIC</div>
                              <div className="font-medium">{detailAgen.pic || '-'}</div>
                            </div>
                            <div>
                              <div className="text-[10px] md:text-xs text-muted-foreground">No. PIC</div>
                              <div className="font-medium font-mono">{detailAgen.no_pic || '-'}</div>
                            </div>
                            {/* Row 10 */}
                            <div>
                              <div className="text-[10px] md:text-xs text-muted-foreground">Armada Truk</div>
                              <div className="font-medium">{detailAgen.kepemilikan_armada_truk ?? '-'}</div>
                            </div>
                            <div>
                              <div className="text-[10px] md:text-xs text-muted-foreground">Armada Pick Up</div>
                              <div className="font-medium">{detailAgen.kepemilikan_armada_pick_up ?? '-'}</div>
                            </div>
                            {/* Row 11 */}
                            <div>
                              <div className="text-[10px] md:text-xs text-muted-foreground">Support Pertamina</div>
                              <Badge className={`border-0 text-[10px] mt-0.5 ${detailAgen.support_pertamina === 'Iya' ? 'bg-chart-2/15 text-chart-2' : 'bg-muted/50 text-muted-foreground'}`}>
                                {detailAgen.support_pertamina || '-'}
                              </Badge>
                            </div>
                            <div>
                              <div className="text-[10px] md:text-xs text-muted-foreground">Background</div>
                              <div className="font-medium">{detailAgen.background || '-'}</div>
                            </div>
                            {/* Row 12 */}
                            <div>
                              <div className="text-[10px] md:text-xs text-muted-foreground">Afiliasi</div>
                              <div className="font-medium">{detailAgen.afiliasi || '-'}</div>
                            </div>
                            <div>
                              <div className="text-[10px] md:text-xs text-muted-foreground">LO Harian</div>
                              <div className="font-medium">{String(detailAgen.lo_harian ?? '-')}</div>
                            </div>
                            {/* Row 13 */}
                            <div className="col-span-2">
                              <div className="text-[10px] md:text-xs text-muted-foreground">Alamat Gudang</div>
                              <div className="font-medium text-xs">{detailAgen.alamat_gudang || '-'}</div>
                            </div>
                            {/* Row 14 */}
                            <div>
                              <div className="text-[10px] md:text-xs text-muted-foreground">Dibuat</div>
                              <div className="font-medium">{detailAgen.created_at || '-'}</div>
                            </div>
                            <div>
                              <div className="text-[10px] md:text-xs text-muted-foreground">Diperbarui</div>
                              <div className="font-medium">{detailAgen.updated_at || '-'}</div>
                            </div>
                          </div>
                        ) : <p className="text-muted-foreground">Gagal memuat detail</p>}
                      </DialogContent>
                    </Dialog>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
      {!loading && (
        <p className="text-[10px] md:text-xs text-muted-foreground">{agenList.length} agen ditemukan</p>
      )}
    </div>
  )
}
