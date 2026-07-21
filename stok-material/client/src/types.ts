export type Material = {
  id: string | number
  name: string
  category?: string
  unit?: string
  stock: number
  min_stock: number
  image?: string
}

export type MutationType = "in" | "out"

export type StockMutation = {
  id: string | number
  date: string
  material?: Material
  material_id?: string | number
  material_name?: string
  type: MutationType
  qty: number
  source?: string
  destination?: string
  admin?: string
  notes?: string
}

export type PaginatedResponse<T> = {
  data: T[]
  page?: number
  totalPages?: number
  total_pages?: number
  total?: number
}
