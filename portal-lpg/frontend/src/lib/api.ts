import type {
  LPGSummary, MonthlyData, DistrictData, PerformaData,
  RekapData, AgenData, AgenStats, PangkalanStats, PangkalanRow,
} from './types'

const BASE = ''

async function apiFetch<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    ...init,
  })
  if (res.status === 401) {
    window.location.href = '/login'
    throw new Error('Unauthorized')
  }
  const data = await res.json()
  if (data?.error) throw new Error(data.error)
  return data as T
}

// --- Auth ---
export const login = async (username: string, password: string): Promise<void> => {
  const form = new URLSearchParams({ username, password })
  const res = await fetch(`${BASE}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    credentials: 'include',
    body: form,
  })
  // If the server returned the login page again, credentials were wrong
  if (res.redirected && res.url.endsWith('/login')) {
    throw new Error('Login gagal — periksa username/password')
  }
  // On failure, the server sends the login HTML; on success it redirects
  if (!res.redirected && res.url.endsWith('/login')) {
    throw new Error('Login gagal — periksa username/password')
  }
}

export const checkAuth = async (): Promise<boolean> => {
  try {
    const res = await fetch(`${BASE}/api/auth/check`, { credentials: 'include' })
    return res.status === 200
  } catch {
    return false
  }
}

export const logout = (): void => {
  window.location.href = '/logout'
}

// --- LPG API ---
export const fetchLPGSummary = (params?: string) =>
  apiFetch<LPGSummary>(`/api/lpg/summary${params || ''}`)

export const fetchLPGMonthly = (params?: string) =>
  apiFetch<MonthlyData>(`/api/lpg/monthly${params || ''}`)

export const fetchLGPDistricts = (params?: string) =>
  apiFetch<DistrictData>(`/api/lpg/districts${params || ''}`)

export const fetchLPGPerforma = (params?: string) =>
  apiFetch<PerformaData>(`/api/lpg/performa${params || ''}`)

export const fetchLPGRekap = (params?: string) =>
  apiFetch<RekapData>(`/api/lpg/rekap${params || ''}`)

export const fetchLPGCompare = (params?: string) =>
  apiFetch<any>(`/api/lpg/compare${params || ''}`)

// --- Agen API ---
export const fetchAgenList = (params?: string) =>
  apiFetch<AgenData[]>(`/api/agen${params || ''}`)

export const fetchAgenStats = () =>
  apiFetch<AgenStats>('/api/agen/stats')

export const fetchAgenDetail = (nama: string) =>
  apiFetch<AgenData>(`/api/agen/detail?nama=${encodeURIComponent(nama)}`)

export const updateAgen = (data: Partial<AgenData> & { sold_to: string }) =>
  apiFetch<{ success: boolean; message: string }>('/api/agen/update', {
    method: 'PUT',
    body: JSON.stringify(data),
  })

// --- Pangkalan API ---
export const fetchPangkalanStats = () =>
  apiFetch<PangkalanStats>('/api/pangkalan/stats')

export const fetchPangkalanList = (params?: string) =>
  apiFetch<PangkalanRow[]>(`/api/pangkalan/list${params || ''}`)
