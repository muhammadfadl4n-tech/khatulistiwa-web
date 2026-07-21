export interface LPGSummary {
  total_mt: number
  total_tabung: number
  total_rows: number
  total_months: number
  total_districts: number
  total_plants: number
  months: string[]
  districts: string[]
  materials: { name: string; mt: number; tb: number }[]
  types: { name: string; mt: number; tb: number }[]
  segments: { name: string; mt: number; tb: number; trans: number }[]
  date_from: string | null
  date_to: string | null
  last_data_date: string | null
  last_update: string | null
  pso_agents: number
  npso_agents: number
}

export interface MonthlyData {
  [ym: string]: { mt: number; tb: number }
}

export interface DistrictData {
  [name: string]: { mt: number; tb: number }
}

export interface PerformaRow {
  wilayah: string
  alokasi: number
  realisasi_mt: number
  realisasi_tabung: number
  agen_count: number
  pct_realisasi: number
  selisih_mt: number
  status: string
}

export interface PerformaData {
  summary: {
    total_wilayah: number
    total_alokasi: number
    total_realisasi: number
    avg_pct: number
    over_perform_count: number
    threshold: number
    tahun: number
    alokasi_loaded: boolean
  }
  prognosis: {
    tahun: number
    total_realisasi_ytd: number
    bulan_terakhir: number
    bulan_berjalan: number
    rata_rata_per_bulan: number
    sisa_bulan: number
    prognosa_akhir_tahun: number
    total_alokasi_tahunan: number
    prognosa_vs_alokasi_pct: number
    selisih_prognosa: number
  }
  data: PerformaRow[]
}

export interface RekapData {
  summary: {
    total_agen: number
    total_mt: number
    total_tabung: number
    months: string[]
  }
  data: RekapRow[]
}

export interface RekapRow {
  nama_agen: string
  sold_to: string
  wilayah: string
  monthly: Record<string, { mt: number; tb: number }>
  total_mt: number
  total_tabung: number
}

export interface AgenData {
  id?: number
  no?: number
  sold_to: string
  nama_agen: string
  wilayah: string
  rayon_sbm: string
  alokasi: string
  pengusaha: string
  no_pengusaha: string
  pic: string
  no_pic: string
  alamat_kantor: string
  alamat_gudang: string
  desa_kel: string
  kecamatan: string
  latitude: string
  longitude: string
  afiliasi: string
  kepemilikan_armada_truk: string
  kepemilikan_armada_pick_up: string
  support_pertamina: string
  background: string
  lo_harian: string
  created_at?: string
  updated_at: string
  [key: string]: unknown
}

export interface AgenStats {
  total: number
  kabupaten_count: number
  tw3_count: number
}

export interface PangkalanStats {
  total_pangkalan: number
  kota_kosong_count: number
  koordinat_kosong_count: number
  duplicate_registrasi_count: number
}

export interface PangkalanRow {
  id: number
  id_registrasi: string
  nama_pangkalan: string
  nama_agen: string
  kota: string
  kecamatan: string
  latitude: string
  longitude: string
  status: string
  alamat: string
}
