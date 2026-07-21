import { Edit3, ImagePlus, PackagePlus, Search, Trash2, X } from "lucide-react"
import { useEffect, useMemo, useState, type FormEvent } from "react"
import { api } from "../api"
import type { Material } from "../types"

type MaterialForm = {
  name: string
  category: string
  unit: string
  min_stock: string
  image: string
}

const emptyForm: MaterialForm = {
  name: "",
  category: "",
  unit: "pcs",
  min_stock: "0",
  image: "",
}

const BASE = ""

function MaterialsPage() {
  const [materials, setMaterials] = useState<Material[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [search, setSearch] = useState("")
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Material | null>(null)
  const [form, setForm] = useState<MaterialForm>(emptyForm)
  const [saving, setSaving] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [preview, setPreview] = useState<string | null>(null)
  const [detail, setDetail] = useState<Material | null>(null)

  const fetchMaterials = async () => {
    setLoading(true)
    setError("")
    try {
      const response = await api.get<Material[] | { data: Material[] }>("/api/materials")
      setMaterials(Array.isArray(response) ? response : response.data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal mengambil data material")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void fetchMaterials()
  }, [])

  const filteredMaterials = useMemo(
    () => materials.filter((m) => m.name.toLowerCase().includes(search.toLowerCase())),
    [materials, search],
  )

  const openCreate = () => {
    setEditing(null)
    setForm(emptyForm)
    setPreview(null)
    setModalOpen(true)
  }

  const openEdit = (material: Material) => {
    setEditing(material)
    setForm({
      name: material.name,
      category: material.category ?? "",
      unit: material.unit ?? "pcs",
      min_stock: String(material.min_stock ?? 0),
      image: material.image ?? "",
    })
    setPreview(material.image ? `${BASE}${material.image}` : null)
    setModalOpen(true)
  }

  const handleImageUpload = async (file: File) => {
    setUploading(true)
    try {
      const fd = new FormData()
      fd.append("image", file)
      const res = await fetch(`${BASE}/api/upload`, {
        method: "POST",
        credentials: "include",
        body: fd,
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.error || "Upload gagal")
      }
      const data = await res.json()
      setForm((f) => ({ ...f, image: data.url }))
      setPreview(data.url)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload gagal")
    } finally {
      setUploading(false)
    }
  }

  const removeImage = () => {
    setForm((f) => ({ ...f, image: "" }))
    setPreview(null)
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setSaving(true)
    setError("")

    const payload: Record<string, unknown> = {
      name: form.name.trim(),
      category: form.category.trim(),
      unit: form.unit.trim() || "pcs",
      min_stock: Number(form.min_stock) || 0,
      image: form.image,
    }

    if (editing && !payload.image) {
      payload.delete_image = true
    }

    try {
      if (editing) {
        await api.put(`/api/materials/${editing.id}`, payload)
      } else {
        await api.post("/api/materials", payload)
      }
      setModalOpen(false)
      await fetchMaterials()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal menyimpan material")
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (material: Material) => {
    if (!window.confirm(`Hapus material "${material.name}"?`)) return
    setError("")
    try {
      await api.del(`/api/materials/${material.id}`)
      await fetchMaterials()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal menghapus material")
    }
  }

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold text-white sm:text-xl">Materials</h2>
          <p className="mt-0.5 text-xs text-slate-400 sm:text-sm">Kelola master material promosi dan dokumentasi gambar.</p>
        </div>
        <button
          type="button"
          onClick={openCreate}
          className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-3 py-2 text-xs font-semibold text-white transition-colors hover:bg-blue-500 active:bg-blue-700 sm:px-4 sm:py-2 sm:text-sm"
        >
          <PackagePlus size={15} />
          Tambah Material
        </button>
      </div>

      {/* Search */}
      <div className="flex items-center gap-3 rounded-xl border border-slate-700/50 bg-[#1e293b] px-4 py-3 shadow-sm">
        <Search size={18} className="text-slate-500" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full bg-transparent text-sm text-white outline-none placeholder:text-slate-500"
          placeholder="Cari nama material"
        />
      </div>

      {error && <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-xs text-red-200 sm:text-sm">{error}</div>}

      {/* Table */}
      <div className="overflow-hidden rounded-xl border border-slate-700/50 bg-[#1e293b] shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[820px] text-left text-sm">
            <thead className="bg-slate-900/50 text-[11px] uppercase tracking-wider text-slate-500">
              <tr>
                <th className="w-12 px-4 py-3 sm:px-5">Foto</th>
                <th className="px-4 py-3 sm:px-5">Nama</th>
                <th className="px-4 py-3 sm:px-5">Kategori</th>
                <th className="px-4 py-3 sm:px-5">Unit</th>
                <th className="px-4 py-3 sm:px-5">Stok</th>
                <th className="px-4 py-3 sm:px-5">Min</th>
                <th className="px-4 py-3 text-right sm:px-5">Aksi</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {loading ? (
                <tr><td colSpan={7} className="px-5 py-8 text-center text-slate-400">Memuat material...</td></tr>
              ) : (
                filteredMaterials.map((material) => (
                  <tr key={material.id} className="transition-colors hover:bg-slate-800/30">
                    <td className="px-4 py-3 sm:px-5">
                      {material.image ? (
                        <button type="button" onClick={() => setDetail(material)} className="block">
                          <img
                            src={`${BASE}${material.image}`}
                            alt={material.name}
                            className="h-10 w-10 shrink-0 rounded-lg border border-slate-700 object-cover transition-opacity hover:opacity-80"
                            loading="lazy"
                          />
                        </button>
                      ) : (
                        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-slate-700 bg-slate-800 text-slate-600">
                          <ImagePlus size={16} />
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3 font-semibold text-white sm:px-5">{material.name}</td>
                    <td className="px-4 py-3 text-slate-300 sm:px-5">{material.category || "—"}</td>
                    <td className="px-4 py-3 text-slate-300 sm:px-5">{material.unit || "pcs"}</td>
                    <td className="px-4 py-3 text-slate-200 sm:px-5">{material.stock.toLocaleString("id-ID")}</td>
                    <td className="px-4 py-3 text-slate-300 sm:px-5">{material.min_stock.toLocaleString("id-ID")}</td>
                    <td className="px-4 py-3 text-right sm:px-5">
                      <div className="flex justify-end gap-1.5">
                        <button
                          type="button"
                          onClick={() => openEdit(material)}
                          className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-slate-600 text-slate-300 transition-colors hover:border-blue-400 hover:text-blue-300"
                          aria-label="Edit"
                        >
                          <Edit3 size={14} />
                        </button>
                        <button
                          type="button"
                          onClick={() => void handleDelete(material)}
                          className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-slate-600 text-slate-300 transition-colors hover:border-red-400 hover:text-red-300"
                          aria-label="Hapus"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
              {!loading && !filteredMaterials.length && (
                <tr><td colSpan={7} className="px-5 py-8 text-center text-slate-400">Material tidak ditemukan.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create/Edit Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/60 px-4 py-10">
          <form onSubmit={handleSubmit} className="animate-scale-in w-full max-w-lg rounded-xl border border-slate-700/50 bg-[#1e293b] p-6 shadow-2xl">
            <div className="mb-5 flex items-center justify-between">
              <h3 className="text-base font-bold text-white">{editing ? "Edit Material" : "Tambah Material"}</h3>
              <button type="button" onClick={() => setModalOpen(false)} className="rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-slate-800 hover:text-white">
                <X size={18} />
              </button>
            </div>

            {/* Image upload area */}
            <div className="mb-5">
              <label className="mb-2 block text-sm font-semibold text-slate-300">Foto Dokumentasi</label>
              {preview ? (
                <div className="relative inline-block">
                  <img src={preview} alt="Preview" className="h-28 w-28 rounded-xl border border-slate-600 object-cover" />
                  <button
                    type="button"
                    onClick={removeImage}
                    className="absolute -right-2 -top-2 flex h-6 w-6 items-center justify-center rounded-full bg-red-500 text-white shadow transition-colors hover:bg-red-400"
                  >
                    <X size={12} />
                  </button>
                </div>
              ) : (
                <label className="flex h-28 w-28 cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-600 bg-slate-900/50 transition-colors hover:border-blue-500 hover:bg-slate-900">
                  {uploading ? (
                    <div className="h-6 w-6 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
                  ) : (
                    <>
                      <ImagePlus size={24} className="text-slate-500" />
                      <span className="mt-1 text-[10px] text-slate-500">Upload</span>
                    </>
                  )}
                  <input
                    type="file"
                    accept="image/jpeg,image/png,image/webp,image/gif"
                    className="hidden"
                    disabled={uploading}
                    onChange={(e) => { const f = e.target.files?.[0]; if (f) void handleImageUpload(f) }}
                  />
                </label>
              )}
              <p className="mt-1.5 text-[11px] text-slate-500">JPG/PNG/WebP/GIF, maks 5MB</p>
            </div>

            <div className="grid gap-4">
              <div>
                <label className="mb-1.5 block text-sm font-semibold text-slate-300">Nama Material</label>
                <input
                  value={form.name}
                  onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                  className="w-full rounded-xl border border-slate-600 bg-slate-900/50 px-4 py-3 text-sm text-white outline-none transition-all focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                  required
                />
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-semibold text-slate-300">Kategori</label>
                <input
                  value={form.category}
                  onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))}
                  className="w-full rounded-xl border border-slate-600 bg-slate-900/50 px-4 py-3 text-sm text-white outline-none transition-all focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                />
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-1.5 block text-sm font-semibold text-slate-300">Satuan</label>
                  <input
                    value={form.unit}
                    onChange={(e) => setForm((f) => ({ ...f, unit: e.target.value }))}
                    className="w-full rounded-xl border border-slate-600 bg-slate-900/50 px-4 py-3 text-sm text-white outline-none transition-all focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                  />
                </div>
                <div>
                  <label className="mb-1.5 block text-sm font-semibold text-slate-300">Min. Stok</label>
                  <input
                    value={form.min_stock}
                    onChange={(e) => setForm((f) => ({ ...f, min_stock: e.target.value }))}
                    className="w-full rounded-xl border border-slate-600 bg-slate-900/50 px-4 py-3 text-sm text-white outline-none transition-all focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                    type="number"
                    min="0"
                  />
                </div>
              </div>
            </div>

            <div className="mt-6 flex justify-end gap-3">
              <button type="button" onClick={() => setModalOpen(false)}
                className="rounded-xl border border-slate-600 px-4 py-2.5 text-sm font-bold text-slate-300 transition-colors hover:bg-slate-800">
                Batal
              </button>
              <button type="submit" disabled={saving}
                className="rounded-xl bg-gradient-to-r from-blue-500 to-blue-600 px-4 py-2.5 text-sm font-bold text-white shadow-lg shadow-blue-500/20 transition-all hover:from-blue-400 hover:to-blue-500 active:scale-[0.98] disabled:opacity-60">
                {saving ? "Menyimpan..." : "Simpan"}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Image detail lightbox */}
      {detail && detail.image && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 px-4" onClick={() => setDetail(null)}>
          <button
            type="button"
            onClick={() => setDetail(null)}
            className="absolute right-4 top-4 flex h-10 w-10 items-center justify-center rounded-full bg-black/50 text-white backdrop-blur transition-colors hover:bg-black/70"
          >
            <X size={22} />
          </button>
          <img
            src={`${BASE}${detail.image}`}
            alt={detail.name}
            className="max-h-[85vh] max-w-full rounded-xl shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          />
          <p className="absolute bottom-6 left-1/2 -translate-x-1/2 rounded-lg bg-black/60 px-4 py-2 text-sm font-semibold text-white backdrop-blur">
            {detail.name}
          </p>
        </div>
      )}
    </div>
  )
}

export default MaterialsPage
