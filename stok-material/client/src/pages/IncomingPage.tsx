import { ArrowDownToLine, CheckCircle2, TriangleAlert } from "lucide-react"
import { useEffect, useState, type FormEvent } from "react"
import { useNavigate } from "react-router-dom"
import { api } from "../api"
import type { Material } from "../types"

const today = new Date().toISOString().slice(0, 10)

function IncomingPage() {
  const navigate = useNavigate()
  const [materials, setMaterials] = useState<Material[]>([])
  const [materialId, setMaterialId] = useState("")
  const [qty, setQty] = useState("")
  const [date, setDate] = useState(today)
  const [source, setSource] = useState("")
  const [notes, setNotes] = useState("")
  const [error, setError] = useState("")
  const [toast, setToast] = useState("")
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    const fetchMaterials = async () => {
      try {
        const response = await api.get<Material[] | { data: Material[] }>("/api/materials")
        setMaterials(Array.isArray(response) ? response : response.data)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Gagal mengambil data material")
      }
    }
    void fetchMaterials()
  }, [])

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError("")
    const numericQty = Number(qty)

    if (!materialId) { setError("Material wajib dipilih"); return }
    if (!numericQty || numericQty <= 0) { setError("Jumlah harus lebih dari 0"); return }

    setSaving(true)
    try {
      await api.post("/api/mutations/in", { material_id: materialId, qty: numericQty, date, source, notes })
      setToast("Stok masuk berhasil dicatat")
      window.setTimeout(() => navigate("/mutations"), 700)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal mencatat stok masuk")
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h2 className="text-xl font-extrabold text-white sm:text-2xl">Barang Masuk</h2>
        <p className="mt-0.5 text-sm text-slate-400">Catat penambahan stok material promosi dari pusat/supplier.</p>
      </div>

      {toast && (
        <div className="animate-fade-in flex items-center gap-2 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm font-semibold text-emerald-200">
          <CheckCircle2 size={18} /> {toast}
        </div>
      )}
      {error && (
        <div className="animate-fade-in flex items-center gap-2 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
          <TriangleAlert size={18} /> {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="rounded-xl border border-slate-700/50 bg-[#1e293b] p-5 shadow-lg shadow-black/10 sm:p-6">
        <div className="grid gap-5">
          <div>
            <label className="mb-2 block text-sm font-semibold text-slate-300">Material</label>
            <select value={materialId} onChange={(e) => setMaterialId(e.target.value)}
              className="w-full rounded-xl border border-slate-600 bg-slate-900/50 px-4 py-3 text-sm text-white outline-none transition-all focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20">
              <option value="">Pilih material</option>
              {materials.map((m) => (
                <option key={m.id} value={m.id}>{m.name} (stok: {m.stock.toLocaleString("id-ID")} {m.unit || "pcs"})</option>
              ))}
            </select>
          </div>

          <div className="grid gap-5 sm:grid-cols-2">
            <div>
              <label className="mb-2 block text-sm font-semibold text-slate-300">Jumlah</label>
              <input value={qty} onChange={(e) => setQty(e.target.value)} type="number" min="1"
                className="w-full rounded-xl border border-slate-600 bg-slate-900/50 px-4 py-3 text-sm text-white outline-none transition-all focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20" required />
            </div>
            <div>
              <label className="mb-2 block text-sm font-semibold text-slate-300">Tanggal</label>
              <input value={date} onChange={(e) => setDate(e.target.value)} type="date" required
                className="w-full rounded-xl border border-slate-600 bg-slate-900/50 px-4 py-3 text-sm text-white outline-none transition-all focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20" />
            </div>
          </div>

          <div>
            <label className="mb-2 block text-sm font-semibold text-slate-300">Sumber / Asal</label>
            <input value={source} onChange={(e) => setSource(e.target.value)}
              className="w-full rounded-xl border border-slate-600 bg-slate-900/50 px-4 py-3 text-sm text-white outline-none transition-all placeholder:text-slate-600 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
              placeholder="Pusat / Supplier" />
          </div>

          <div>
            <label className="mb-2 block text-sm font-semibold text-slate-300">Keterangan</label>
            <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={3}
              className="w-full resize-none rounded-xl border border-slate-600 bg-slate-900/50 px-4 py-3 text-sm text-white outline-none transition-all placeholder:text-slate-600 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20" />
          </div>
        </div>

        <div className="mt-6 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
          <button type="button" onClick={() => navigate(-1)}
            className="rounded-xl border border-slate-600 px-5 py-3 text-sm font-bold text-slate-300 transition-all hover:bg-slate-800">
            Batal
          </button>
          <button type="submit" disabled={saving}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-emerald-500 to-green-600 px-6 py-3 text-sm font-bold text-white shadow-lg shadow-emerald-500/20 transition-all hover:from-emerald-400 hover:to-green-500 active:scale-[0.98] disabled:opacity-60">
            <ArrowDownToLine size={17} />
            {saving ? "Menyimpan..." : "Simpan Barang Masuk"}
          </button>
        </div>
      </form>
    </div>
  )
}

export default IncomingPage
