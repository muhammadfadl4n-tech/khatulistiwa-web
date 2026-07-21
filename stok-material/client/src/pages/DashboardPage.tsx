import { ArrowDownToLine, ArrowUpFromLine, Boxes, Package, RefreshCw } from "lucide-react"
import { useEffect, useMemo, useState } from "react"
import { api } from "../api"
import type { Material, StockMutation } from "../types"

type DashboardData = {
  total_material?: number
  totalMaterial?: number
  total_stock?: number
  totalStock?: number
  stock_in_today?: number
  stockInToday?: number
  stock_out_today?: number
  stockOutToday?: number
  low_stock?: Material[]
  lowStock?: Material[]
  recent_mutations?: StockMutation[]
  recentMutations?: StockMutation[]
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("id-ID", { dateStyle: "medium" }).format(new Date(value))
}

const todayLabel = new Date().toLocaleDateString("id-ID", { weekday: "long", day: "numeric", month: "long", year: "numeric" })

const statCards = [
  {
    label: "Total Material",
    key: "total_material" as const,
    altKey: "totalMaterial" as const,
    icon: Package,
    border: "border-blue-500/20",
    iconBg: "bg-blue-500/15",
    iconColor: "text-blue-300",
  },
  {
    label: "Total Stok",
    key: "total_stock" as const,
    altKey: "totalStock" as const,
    icon: Boxes,
    border: "border-violet-500/20",
    iconBg: "bg-violet-500/15",
    iconColor: "text-violet-300",
  },
  {
    label: "Stok Masuk Hari Ini",
    key: "stock_in_today" as const,
    altKey: "stockInToday" as const,
    icon: ArrowDownToLine,
    border: "border-emerald-500/20",
    iconBg: "bg-emerald-500/15",
    iconColor: "text-emerald-300",
  },
  {
    label: "Stok Keluar Hari Ini",
    key: "stock_out_today" as const,
    altKey: "stockOutToday" as const,
    icon: ArrowUpFromLine,
    border: "border-rose-500/20",
    iconBg: "bg-rose-500/15",
    iconColor: "text-rose-300",
  },
]

function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  const fetchData = async (showLoading = true) => {
    if (showLoading) setLoading(true)
    setError("")
    try {
      setData(await api.get<DashboardData>("/api/dashboard"))
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal mengambil data")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void fetchData()
    const timer = window.setInterval(() => void fetchData(false), 60000)
    return () => window.clearInterval(timer)
  }, [])

  const lowStock = useMemo(() => data?.low_stock ?? data?.lowStock ?? [], [data])
  const recentMutations = useMemo(() => data?.recent_mutations ?? data?.recentMutations ?? [], [data])

  if (loading) {
    return (
      <div className="space-y-5">
        <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="h-24 animate-pulse rounded-xl bg-slate-800" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-5">
      {/* Header bar */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold text-white sm:text-xl">Dashboard</h2>
          <p className="mt-0.5 text-xs text-slate-500 sm:text-sm">{todayLabel}</p>
        </div>
        <button
          type="button"
          onClick={() => void fetchData()}
          className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-3 py-2 text-xs font-semibold text-white transition-colors hover:bg-blue-500 active:bg-blue-700 sm:px-4 sm:py-2 sm:text-sm"
        >
          <RefreshCw size={14} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-xs text-red-200 sm:text-sm">
          {error}
        </div>
      )}

      {/* Stat cards — simple and clean */}
      <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
        {statCards.map((card) => {
          const Icon = card.icon
          const value = data?.[card.key] ?? data?.[card.altKey] ?? 0
          return (
            <div
              key={card.label}
              className={`rounded-xl border ${card.border} bg-[#1e293b] p-4 shadow-sm transition-colors hover:bg-[#243447] sm:p-5`}
            >
              <div className={`mb-3 flex h-9 w-9 items-center justify-center rounded-lg ${card.iconBg} ${card.iconColor}`}>
                <Icon size={18} />
              </div>
              <p className="text-xl font-bold text-white sm:text-2xl">{Number(value).toLocaleString("id-ID")}</p>
              <p className="mt-0.5 text-xs text-slate-400 sm:text-sm">{card.label}</p>
            </div>
          )
        })}
      </div>

      {/* Bottom sections */}
      <div className="grid gap-5 xl:grid-cols-2">
        {/* Low stock */}
        <section className="rounded-xl border border-slate-700/50 bg-[#1e293b] shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-700/50 px-4 py-3 sm:px-5 sm:py-4">
            <h3 className="text-sm font-bold text-white sm:text-base">Stok Hampir Habis</h3>
            {lowStock.length > 0 && (
              <span className="rounded-full bg-orange-500/15 px-2 py-0.5 text-xs font-bold text-orange-300">
                {lowStock.length}
              </span>
            )}
          </div>
          {lowStock.length > 0 ? (
            <div className="divide-y divide-slate-700/50">
              {lowStock.map((m) => (
                <div key={m.id} className="flex items-center justify-between px-4 py-3 sm:px-5 sm:py-3.5">
                  <div className="min-w-0 flex-1 pr-3">
                    <p className="truncate text-sm font-semibold text-white">{m.name}</p>
                    <p className="truncate text-xs text-slate-400">{m.category || "—"}</p>
                  </div>
                  <span className="shrink-0 rounded-md bg-orange-500/15 px-2.5 py-1 text-xs font-bold text-orange-300">
                    {m.stock}/{m.min_stock} {m.unit || "pcs"}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center px-4 py-8 text-center sm:px-5 sm:py-10">
              <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-full bg-emerald-500/10">
                <Package size={20} className="text-emerald-400" />
              </div>
              <p className="text-sm font-medium text-slate-400">Semua stok aman</p>
              <p className="text-xs text-slate-500">Tidak ada material dengan stok rendah</p>
            </div>
          )}
        </section>

        {/* Recent mutations */}
        <section className="rounded-xl border border-slate-700/50 bg-[#1e293b] shadow-sm">
          <div className="border-b border-slate-700/50 px-4 py-3 sm:px-5 sm:py-4">
            <h3 className="text-sm font-bold text-white sm:text-base">Mutasi Terbaru</h3>
          </div>
          {recentMutations.length > 0 ? (
            <div className="divide-y divide-slate-700/50">
              {recentMutations.slice(0, 8).map((m) => (
                <div key={m.id} className="flex items-center gap-3 px-4 py-2.5 text-sm sm:px-5 sm:py-3">
                  <span className="shrink-0 w-16 text-xs text-slate-500">{formatDate(m.date).slice(0, 6)}</span>
                  <span
                    className={`shrink-0 rounded px-1.5 py-0.5 text-[10px] font-bold ${
                      m.type === "in" ? "bg-emerald-500/15 text-emerald-300" : "bg-rose-500/15 text-rose-300"
                    }`}
                  >
                    {m.type === "in" ? "IN" : "OUT"}
                  </span>
                  <span className="min-w-0 flex-1 truncate font-medium text-white">
                    {m.material?.name ?? m.material_name}
                  </span>
                  <span className="shrink-0 text-xs font-semibold text-slate-300">
                    {m.qty.toLocaleString("id-ID")}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="px-4 py-8 text-center text-xs text-slate-400 sm:px-5 sm:py-10 sm:text-sm">
              Belum ada mutasi.
            </div>
          )}
        </section>
      </div>
    </div>
  )
}

export default DashboardPage
