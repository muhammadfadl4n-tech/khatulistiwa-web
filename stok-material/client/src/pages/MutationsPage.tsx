import { ChevronLeft, ChevronRight, Filter, RotateCcw, Search, X } from "lucide-react"
import { useEffect, useMemo, useState } from "react"
import { api } from "../api"
import type { StockMutation } from "../types"

type Filters = { type: "" | "in" | "out"; material_id: string; start_date: string; end_date: string; search: string }
const emptyFilters: Filters = { type: "", material_id: "", start_date: "", end_date: "", search: "" }

function formatDate(value: string) {
  return new Intl.DateTimeFormat("id-ID", { dateStyle: "medium" }).format(new Date(value))
}

function MutationsPage() {
  const [mutations, setMutations] = useState<StockMutation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [filters, setFilters] = useState<Filters>(emptyFilters)
  const [showFilters, setShowFilters] = useState(false)
  const limit = 20

  const fetchMutations = async (p: number) => {
    setLoading(true)
    setError("")
    try {
      const params: Record<string, string | number> = { page: p, limit }
      if (filters.type) params.type = filters.type
      if (filters.material_id) params.material_id = filters.material_id
      if (filters.start_date) params.start_date = filters.start_date
      if (filters.end_date) params.end_date = filters.end_date
      if (filters.search) params.search = filters.search
      const response = await api.get<{ data: StockMutation[]; total: number; page: number }>("/api/mutations", params)
      setMutations(response.data)
      setTotal(response.total)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal mengambil data mutasi")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { void fetchMutations(page) }, [page])

  const totalPages = useMemo(() => Math.max(1, Math.ceil(total / limit)), [total, limit])

  const handleSearch = () => { setPage(1); void fetchMutations(1) }
  const handleReset = () => { setFilters(emptyFilters); setPage(1) }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-extrabold text-white sm:text-2xl">Histori Mutasi</h2>
          <p className="mt-0.5 text-sm text-slate-400">Riwayat barang masuk dan keluar.</p>
        </div>
        <div className="flex gap-2">
          <button type="button" onClick={() => setShowFilters((v) => !v)}
            className="inline-flex items-center gap-2 rounded-xl border border-slate-600 px-4 py-2.5 text-sm font-bold text-slate-300 transition-all hover:bg-slate-800">
            <Filter size={16} /> Filter
            {(filters.type || filters.material_id || filters.start_date || filters.end_date) && (
              <span className="flex h-5 w-5 items-center justify-center rounded-full bg-blue-500 text-[10px] font-bold text-white">
                {[filters.type, filters.material_id, filters.start_date, filters.end_date].filter(Boolean).length}
              </span>
            )}
          </button>
          <button type="button" onClick={handleReset}
            className="inline-flex items-center gap-2 rounded-xl border border-slate-600 px-4 py-2.5 text-sm font-bold text-slate-300 transition-all hover:bg-slate-800">
            <RotateCcw size={16} /> Reset
          </button>
        </div>
      </div>

      {/* Filters panel */}
      {showFilters && (
        <div className="animate-fade-in rounded-xl border border-slate-700/50 bg-[#1e293b] p-5 shadow-lg shadow-black/10">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            <div>
              <label className="mb-1.5 block text-xs font-semibold text-slate-400">Tipe</label>
              <select value={filters.type} onChange={(e) => setFilters((f) => ({ ...f, type: e.target.value as "" | "in" | "out" }))}
                className="w-full rounded-xl border border-slate-600 bg-slate-900/50 px-3 py-2.5 text-sm text-white outline-none focus:border-blue-500">
                <option value="">Semua</option>
                <option value="in">Barang Masuk</option>
                <option value="out">Barang Keluar</option>
              </select>
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-semibold text-slate-400">Material ID</label>
              <input value={filters.material_id} onChange={(e) => setFilters((f) => ({ ...f, material_id: e.target.value }))}
                className="w-full rounded-xl border border-slate-600 bg-slate-900/50 px-3 py-2.5 text-sm text-white outline-none focus:border-blue-500"
                placeholder="ID material" type="number" min="1" />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-semibold text-slate-400">Dari Tanggal</label>
              <input value={filters.start_date} onChange={(e) => setFilters((f) => ({ ...f, start_date: e.target.value }))}
                className="w-full rounded-xl border border-slate-600 bg-slate-900/50 px-3 py-2.5 text-sm text-white outline-none focus:border-blue-500" type="date" />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-semibold text-slate-400">Sampai Tanggal</label>
              <input value={filters.end_date} onChange={(e) => setFilters((f) => ({ ...f, end_date: e.target.value }))}
                className="w-full rounded-xl border border-slate-600 bg-slate-900/50 px-3 py-2.5 text-sm text-white outline-none focus:border-blue-500" type="date" />
            </div>
            <div className="flex items-end">
              <button type="button" onClick={handleSearch}
                className="w-full rounded-xl bg-gradient-to-r from-blue-500 to-blue-600 px-4 py-2.5 text-sm font-bold text-white shadow-lg shadow-blue-500/20 transition-all hover:from-blue-400 hover:to-blue-500">
                Terapkan Filter
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Search bar */}
      <div className="flex items-center gap-3 rounded-xl border border-slate-700/50 bg-[#1e293b] px-4 py-3 shadow-lg shadow-black/10">
        <Search size={18} className="text-slate-500" />
        <input value={filters.search} onChange={(e) => setFilters((f) => ({ ...f, search: e.target.value }))}
          onKeyDown={(e) => { if (e.key === "Enter") handleSearch() }}
          className="w-full bg-transparent text-sm text-white outline-none placeholder:text-slate-500"
          placeholder="Cari nama material, sumber, tujuan..." />
        {filters.search && (
          <button type="button" onClick={() => { setFilters((f) => ({ ...f, search: "" })); handleSearch() }}
            className="rounded p-1 text-slate-500 transition-all hover:text-white"><X size={16} /></button>
        )}
      </div>

      {error && <div className="animate-fade-in rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">{error}</div>}

      {/* Table */}
      <div className="overflow-hidden rounded-xl border border-slate-700/50 bg-[#1e293b] shadow-lg shadow-black/5">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[700px] text-left text-sm">
            <thead className="bg-slate-900/50 text-[11px] uppercase tracking-wider text-slate-500">
              <tr>
                <th className="px-4 py-3 font-semibold sm:px-5">Tanggal</th>
                <th className="px-4 py-3 font-semibold sm:px-5">Material</th>
                <th className="px-4 py-3 font-semibold sm:px-5">Tipe</th>
                <th className="px-4 py-3 font-semibold sm:px-5">Jumlah</th>
                <th className="hidden px-4 py-3 font-semibold sm:table-cell sm:px-5">Sumber/Tujuan</th>
                <th className="hidden px-4 py-3 font-semibold lg:table-cell lg:px-5">Keterangan</th>
                <th className="hidden px-4 py-3 font-semibold lg:table-cell lg:px-5">Admin</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {loading ? (
                <tr><td colSpan={7} className="px-5 py-8 text-center text-slate-400">Memuat mutasi...</td></tr>
              ) : (
                mutations.map((mutation) => (
                  <tr key={mutation.id} className="transition-colors hover:bg-slate-800/30">
                    <td className="px-4 py-3.5 text-slate-300 sm:px-5">{formatDate(mutation.date)}</td>
                    <td className="px-4 py-3.5 font-semibold text-white sm:px-5">
                      {mutation.material?.name ?? mutation.material_name}
                    </td>
                    <td className="px-4 py-3.5 sm:px-5">
                      <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-bold ${
                        mutation.type === "in" ? "bg-emerald-500/15 text-emerald-300" : "bg-rose-500/15 text-rose-300"}`}>
                        {mutation.type === "in" ? "Masuk" : "Keluar"}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 font-semibold text-slate-200 sm:px-5">{mutation.qty.toLocaleString("id-ID")}</td>
                    <td className="hidden max-w-[140px] truncate px-4 py-3.5 text-slate-300 sm:table-cell sm:px-5"
                      title={mutation.source || mutation.destination}>
                      {mutation.source || mutation.destination || "-"}
                    </td>
                    <td className="hidden max-w-[160px] truncate px-5 py-3.5 text-slate-400 lg:table-cell"
                      title={mutation.notes}>{mutation.notes || "-"}
                    </td>
                    <td className="hidden px-5 py-3.5 text-slate-400 lg:table-cell">
                      {mutation.created_by || mutation.admin || "-"}
                    </td>
                  </tr>
                ))
              )}
              {!loading && !mutations.length && (
                <tr><td colSpan={7} className="px-5 py-10 text-center text-sm text-slate-400">Tidak ada mutasi.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-slate-700/50 bg-[#1e293b] px-5 py-3 shadow-lg shadow-black/5">
          <p className="text-sm text-slate-400">Halaman {page} dari {totalPages} ({total} total)</p>
          <div className="flex gap-2">
            <button type="button" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1}
              className="inline-flex items-center gap-1 rounded-xl border border-slate-600 px-3 py-2 text-sm font-bold text-slate-300 transition-all hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-40">
              <ChevronLeft size={16} /> Sebelumnya
            </button>
            <button type="button" onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page >= totalPages}
              className="inline-flex items-center gap-1 rounded-xl border border-slate-600 px-3 py-2 text-sm font-bold text-slate-300 transition-all hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-40">
              Berikutnya <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default MutationsPage
