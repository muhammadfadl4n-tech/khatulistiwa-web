import { useEffect, useState } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Search, MapPin, Navigation, Users, LocateFixed, Layers, MapIcon } from 'lucide-react'
import { fetchAgenList } from '@/lib/api'
import type { AgenData } from '@/lib/types'
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// Fix default marker icon (webpack/vite issue)
delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

const gmapsUrl = (lat: string, lng: string) =>
  `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`

function fmt(v: number): string { return v.toLocaleString('id') }

// Component to auto-fit bounds
function FitBounds({ agents }: { agents: AgenData[] }) {
  const map = useMap()
  useEffect(() => {
    const coords = agents
      .filter(a => a.latitude && a.longitude && parseFloat(a.latitude) !== 0)
      .map(a => [parseFloat(a.latitude), parseFloat(a.longitude)] as [number, number])
    if (coords.length > 0) {
      const bounds = L.latLngBounds(coords)
      map.fitBounds(bounds, { padding: [40, 40] })
    }
  }, [agents, map])
  return null
}

export default function MapPage() {
  const [agents, setAgents] = useState<AgenData[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [view, setView] = useState<'all' | 'with_coords'>('with_coords')
  const [selected, setSelected] = useState<AgenData | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)

  useEffect(() => {
    setLoading(true)
    fetchAgenList('')
      .then(setAgents)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const filtered = agents.filter(a => {
    const q = search.toLowerCase()
    const matchSearch = !q || a.nama_agen?.toLowerCase().includes(q) || a.wilayah?.toLowerCase().includes(q) || a.pengusaha?.toLowerCase().includes(q)
    const hasCoords = a.latitude && a.longitude && parseFloat(a.latitude) !== 0
    if (view === 'with_coords') return matchSearch && hasCoords
    return matchSearch
  })

  const withCoords = agents.filter(a => a.latitude && a.longitude && parseFloat(a.latitude) !== 0)

  // Custom marker icon (blue, pulsing-style)
  const icon = L.divIcon({
    className: 'custom-marker',
    html: `<div style="
      width: 24px; height: 24px;
      background: oklch(0.55 0.22 260);
      border: 2px solid white;
      border-radius: 50%;
      box-shadow: 0 2px 6px rgba(0,0,0,0.3);
      display: flex;
      align-items: center;
      justify-content: center;
    "><svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="white" stroke="none"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg></div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 24],
    popupAnchor: [0, -28],
  })

  return (
    <div className="h-[calc(100vh-1rem)] md:h-[calc(100vh-1rem)] flex flex-col gap-2 md:gap-3">
      {/* Header + Search row */}
      <div className="flex flex-wrap items-center gap-2 shrink-0 px-1">
        <div className="flex items-center gap-2 min-w-0 mr-auto">
          <h1 className="text-base md:text-lg font-bold leading-tight">Map — Agen</h1>
          <span className="text-[10px] md:text-xs text-muted-foreground whitespace-nowrap">
            {fmt(withCoords.length)} titik
          </span>
        </div>
        <div className="relative w-48 md:w-64">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3 w-3 md:h-3.5 md:w-3.5 text-muted-foreground" />
          <Input
            placeholder="Cari agen..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="bg-card border-border text-foreground pl-7 md:pl-8 text-xs h-8 md:h-9"
          />
        </div>
        <div className="flex gap-1">
          <Badge
            className={`cursor-pointer border-0 text-[10px] md:text-xs ${view === 'with_coords' ? 'bg-primary/15 text-primary' : 'bg-muted text-muted-foreground hover:bg-muted/80'}`}
            onClick={() => setView('with_coords')}
          >Berkoordinat</Badge>
          <Badge
            className={`cursor-pointer border-0 text-[10px] md:text-xs ${view === 'all' ? 'bg-primary/15 text-primary' : 'bg-muted text-muted-foreground hover:bg-muted/80'}`}
            onClick={() => setView('all')}
          >Semua</Badge>
        </div>
      </div>

      {/* Map */}
      {loading ? (
        <Skeleton className="flex-1 bg-card rounded-xl" />
      ) : (
        <div className="flex-1 rounded-xl overflow-hidden border border-border relative">
          <MapContainer
            center={[-0.02, 109.3]}
            zoom={8}
            className="h-full w-full"
            zoomControl={false}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <FitBounds agents={filtered} />
            {filtered
              .filter(a => a.latitude && a.longitude && parseFloat(a.latitude) !== 0)
              .map(a => (
                <Marker
                  key={a.sold_to}
                  position={[parseFloat(a.latitude), parseFloat(a.longitude)]}
                  icon={icon}
                  eventHandlers={{
                    click: () => {
                      setSelected(a)
                      setDialogOpen(true)
                    },
                  }}
                >
                  <Popup>
                    <div style={{ fontSize: 12, lineHeight: 1.4, maxWidth: 220 }}>
                      <strong style={{ fontSize: 13 }}>{a.nama_agen}</strong><br />
                      {a.wilayah}{a.rayon_sbm ? ` · ${a.rayon_sbm}` : ''}<br />
                      {a.pengusaha && <><span style={{ color: '#666' }}>👤 {a.pengusaha}</span><br /></>}
                      <div style={{ marginTop: 6 }}>
                        <a
                          href={gmapsUrl(a.latitude, a.longitude)}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{
                            display: 'inline-flex', alignItems: 'center', gap: 4,
                            background: 'oklch(0.55 0.22 260)',
                            color: 'white', padding: '4px 10px', borderRadius: 6,
                            fontSize: 11, fontWeight: 500, textDecoration: 'none',
                          }}
                        >
                          🧭 Direction
                        </a>
                      </div>
                    </div>
                  </Popup>
                </Marker>
              ))}
          </MapContainer>

          {/* Legend overlay */}
          <div className="absolute bottom-3 left-3 z-[1000] bg-card/90 backdrop-blur border border-border rounded-lg px-2.5 py-1.5 text-[10px] md:text-xs text-muted-foreground flex items-center gap-2">
            <MapPin className="h-3 w-3 text-primary" />
            {filtered.filter(a => a.latitude && parseFloat(a.latitude) !== 0).length} agen di peta
          </div>
        </div>
      )}

      {/* ── Detail Modal ── */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="bg-card border-border text-foreground w-[95vw] max-w-lg md:max-w-xl max-h-[85vh] overflow-y-auto p-4 md:p-6">
          <DialogHeader>
            <DialogTitle className="text-sm md:text-base">{selected?.nama_agen || 'Detail Agen'}</DialogTitle>
          </DialogHeader>
          {selected ? (
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-2.5 text-xs md:text-sm">
                <div>
                  <div className="text-[10px] text-muted-foreground">Wilayah</div>
                  <div className="font-medium">{selected.wilayah || '-'}</div>
                </div>
                <div>
                  <div className="text-[10px] text-muted-foreground">Rayon SBM</div>
                  <div className="font-medium">{selected.rayon_sbm || '-'}</div>
                </div>
                <div className="sm:col-span-2">
                  <div className="text-[10px] text-muted-foreground">Alamat Kantor</div>
                  <div className="font-medium text-xs">{selected.alamat_kantor || '-'}</div>
                </div>
                <div>
                  <div className="text-[10px] text-muted-foreground">Pengusaha</div>
                  <div className="font-medium">{selected.pengusaha || '-'}</div>
                </div>
                <div>
                  <div className="text-[10px] text-muted-foreground">Sold To</div>
                  <div className="font-medium font-mono">{selected.sold_to || '-'}</div>
                </div>
              </div>

              {selected.latitude && selected.longitude && parseFloat(selected.latitude) !== 0 ? (
                <div className="rounded-xl border border-border bg-secondary/30 p-3 md:p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <MapPin className="h-4 w-4 text-primary" />
                    <span className="text-xs font-semibold">Lokasi Agen</span>
                  </div>
                  <p className="text-[10px] md:text-xs text-muted-foreground mb-2">
                    {selected.latitude}, {selected.longitude}
                  </p>
                  <a
                    href={gmapsUrl(selected.latitude, selected.longitude)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 w-full justify-center bg-primary hover:bg-primary/90 text-primary-foreground text-xs md:text-sm font-medium rounded-lg px-3 py-2 md:py-2.5 transition-colors"
                  >
                    <Navigation className="h-4 w-4" />
                    Buka Google Maps — Direction
                  </a>
                </div>
              ) : (
                <div className="rounded-xl border border-border bg-muted/20 p-3 md:p-4 text-center text-muted-foreground text-xs">
                  <MapPin className="h-5 w-5 mx-auto mb-1 opacity-50" />
                  Koordinat belum tersedia untuk agen ini
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-2">{[1,2,3].map(i => <Skeleton key={i} className="h-5 bg-muted" />)}</div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
