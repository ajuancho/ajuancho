import axios from 'axios'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

export const api = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  timeout: 10_000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ─── Tipos ──────────────────────────────────────────────────────────────────

export interface EventSummary {
  id: number
  titulo: string
  descripcion: string
  fecha_inicio: string
  fecha_fin?: string
  precio_min?: number
  precio_max?: number
  es_gratuito: boolean
  imagen_url?: string
  venue?: { nombre: string; barrio?: string }
  categorias?: Array<{ nombre: string }>
}

export interface EventDetail extends EventSummary {
  descripcion_larga?: string
  url_entradas?: string
  url_fuente?: string
  tags?: string[]
  venue?: {
    nombre: string
    direccion?: string
    barrio?: string
    ciudad?: string
    lat?: number
    lng?: number
  }
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

export interface EventFilters {
  q?: string
  categorias?: string[]
  fecha?: 'hoy' | 'manana' | 'semana' | 'mes'
  precio?: 'gratis' | 'pagos'
  barrio?: string
  page?: number
  size?: number
}

export interface Category {
  id: number
  nombre: string
  slug: string
}

export interface UserProfile {
  id: number
  email: string
  nombre?: string
  preferencias?: string[]
  historial_categorias?: Array<{ categoria: string; count: number }>
}

// ─── Eventos ─────────────────────────────────────────────────────────────────

export const eventsApi = {
  list: async (filters: EventFilters = {}): Promise<PaginatedResponse<EventSummary>> => {
    const params = new URLSearchParams()
    if (filters.q)      params.set('q', filters.q)
    if (filters.fecha)  params.set('fecha', filters.fecha)
    if (filters.precio) params.set('precio', filters.precio)
    if (filters.barrio) params.set('barrio', filters.barrio)
    if (filters.page)   params.set('page', String(filters.page))
    if (filters.size)   params.set('size', String(filters.size))
    filters.categorias?.forEach((c) => params.append('categoria', c))

    const { data } = await api.get<PaginatedResponse<EventSummary>>('/eventos', { params })
    return data
  },

  getById: async (id: number): Promise<EventDetail> => {
    const { data } = await api.get<EventDetail>(`/eventos/${id}`)
    return data
  },

  search: async (
    q: string,
    filters: Omit<EventFilters, 'q'> = {},
  ): Promise<PaginatedResponse<EventSummary>> => {
    return eventsApi.list({ ...filters, q })
  },

  getFeatured: async (): Promise<EventSummary[]> => {
    const { data } = await api.get<EventSummary[]>('/eventos/destacados')
    return data
  },
}

// ─── Categorías ──────────────────────────────────────────────────────────────

export const categoriesApi = {
  list: async (): Promise<Category[]> => {
    const { data } = await api.get<Category[]>('/categorias')
    return data
  },
}

// ─── Usuarios ────────────────────────────────────────────────────────────────

export const usersApi = {
  getProfile: async (userId: number): Promise<UserProfile> => {
    const { data } = await api.get<UserProfile>(`/usuarios/${userId}`)
    return data
  },

  getRecommendations: async (userId: number): Promise<EventSummary[]> => {
    const { data } = await api.get<EventSummary[]>(`/recomendaciones/${userId}`)
    return data
  },
}

// ─── Interacciones ───────────────────────────────────────────────────────────

export const interactionsApi = {
  recordView: async (userId: number, eventId: number): Promise<void> => {
    await api.post('/interacciones', { usuario_id: userId, evento_id: eventId, tipo: 'vista' })
  },

  recordClick: async (userId: number, eventId: number): Promise<void> => {
    await api.post('/interacciones', { usuario_id: userId, evento_id: eventId, tipo: 'click' })
  },
}
