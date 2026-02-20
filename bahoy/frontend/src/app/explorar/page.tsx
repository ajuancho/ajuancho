'use client'

import { useState, useEffect, useMemo, useCallback } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import FilterSidebar, { type Filters } from '@/components/filters/FilterSidebar'
import EventGrid from '@/components/events/EventGrid'
import EventList from '@/components/events/EventList'
import SearchBar from '@/components/search/SearchBar'
import {
  SlidersHorizontal,
  X,
  Grid3X3,
  List,
  ChevronLeft,
  ChevronRight,
  MapPin,
} from 'lucide-react'
import { eventsApi, type EventSummary } from '@/lib/api'
import { cn } from '@/lib/utils'

// ─── Types ────────────────────────────────────────────────────────────────────

type SortOrder = 'fecha' | 'precio' | 'relevancia'
type ViewMode  = 'grid' | 'lista'

// ─── Constants ────────────────────────────────────────────────────────────────

const ORDEN_LABELS: Record<SortOrder, string> = {
  fecha:      'Fecha',
  precio:     'Precio',
  relevancia: 'Relevancia',
}

const FECHA_LABELS: Record<string, string> = {
  hoy:    'Hoy',
  manana: 'Mañana',
  finde:  'Este fin de semana',
  semana: 'Esta semana',
  mes:    'Este mes',
}

// ─── URL helpers ──────────────────────────────────────────────────────────────

function parseFiltersFromParams(params: Pick<URLSearchParams, 'get' | 'getAll'>): Filters {
  return {
    categorias:  params.getAll('categoria'),
    fecha:       (params.get('fecha') as Filters['fecha']) ?? '',
    precio:      (params.get('precio') as Filters['precio']) ?? '',
    barrio:      params.get('barrio') ?? '',
    tags:        params.getAll('tag'),
    precio_min:  Number(params.get('precio_min') ?? 0),
    precio_max:  Number(params.get('precio_max') ?? 10000),
    solo_gratis: params.get('gratis') === 'true',
    fecha_desde: params.get('fecha_desde') ?? '',
    fecha_hasta: params.get('fecha_hasta') ?? '',
  }
}

// ─── Pagination range ─────────────────────────────────────────────────────────

function getPaginationRange(current: number, total: number): (number | '...')[] {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)
  if (current <= 4)         return [1, 2, 3, 4, 5, '...', total]
  if (current >= total - 3) return [1, '...', total - 4, total - 3, total - 2, total - 1, total]
  return [1, '...', current - 1, current, current + 1, '...', total]
}

// ─── Active filter count ──────────────────────────────────────────────────────

function countActiveFilters(f: Filters, q: string): number {
  return (
    f.categorias.length +
    (f.fecha ? 1 : 0) +
    (f.barrio ? 1 : 0) +
    f.tags.length +
    (f.solo_gratis ? 1 : 0) +
    (f.precio && !f.solo_gratis ? 1 : 0) +
    ((f.fecha_desde || f.fecha_hasta) ? 1 : 0) +
    (f.precio_min > 0 || f.precio_max < 10000 ? 1 : 0) +
    (q ? 1 : 0)
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function ExplorarPage() {
  const searchParams = useSearchParams()
  const router       = useRouter()

  // State
  const [events,      setEvents]      = useState<EventSummary[]>([])
  const [total,       setTotal]       = useState(0)
  const [totalPages,  setTotalPages]  = useState(1)
  const [loading,     setLoading]     = useState(true)
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const [filters, setFilters] = useState<Filters>(() => parseFiltersFromParams(searchParams))
  const [query,   setQuery]   = useState<string>(() => searchParams.get('q') ?? '')
  const [orden,   setOrden]   = useState<SortOrder>(() => (searchParams.get('orden') as SortOrder) || 'relevancia')
  const [vista,   setVista]   = useState<ViewMode>(() => (searchParams.get('vista') as ViewMode) || 'grid')
  const [page,    setPage]    = useState<number>(() => Number(searchParams.get('page') ?? 1))

  // Sync state → URL (share-friendly links)
  useEffect(() => {
    const params = new URLSearchParams()
    if (query) params.set('q', query)
    filters.categorias.forEach((c) => params.append('categoria', c))
    if (filters.barrio) params.set('barrio', filters.barrio)
    if (filters.fecha)  params.set('fecha', filters.fecha)
    if (filters.solo_gratis) params.set('gratis', 'true')
    else if (filters.precio) params.set('precio', filters.precio)
    filters.tags.forEach((t) => params.append('tag', t))
    if (filters.precio_min > 0)     params.set('precio_min', String(filters.precio_min))
    if (filters.precio_max < 10000) params.set('precio_max', String(filters.precio_max))
    if (filters.fecha_desde) params.set('fecha_desde', filters.fecha_desde)
    if (filters.fecha_hasta) params.set('fecha_hasta', filters.fecha_hasta)
    if (orden !== 'relevancia') params.set('orden', orden)
    if (vista !== 'grid')       params.set('vista', vista)
    if (page > 1)               params.set('page', String(page))

    const qs = params.toString()
    router.replace(qs ? `/explorar?${qs}` : '/explorar', { scroll: false })
  }, [filters, query, orden, vista, page, router])

  // Fetch events from API
  useEffect(() => {
    let cancelled = false
    setLoading(true)

    eventsApi
      .list({
        q:          query || undefined,
        categorias: filters.categorias.length ? filters.categorias : undefined,
        // 'finde' maps to 'semana' – backend doesn't have a weekend-specific filter
        fecha:
          filters.fecha === 'finde'
            ? 'semana'
            : (filters.fecha as 'hoy' | 'manana' | 'semana' | 'mes' | undefined) || undefined,
        precio:  filters.solo_gratis ? 'gratis' : (filters.precio || undefined),
        barrio:  filters.barrio || undefined,
        page,
        size:    vista === 'grid' ? 12 : 20,
      })
      .then((res) => {
        if (!cancelled) {
          setEvents(res.items)
          setTotal(res.total)
          setTotalPages(res.pages)
        }
      })
      .catch(() => {
        if (!cancelled) {
          setEvents([])
          setTotal(0)
          setTotalPages(1)
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => { cancelled = true }
  }, [filters, query, vista, page])

  // Client-side sort (complementary to backend relevance)
  const sortedEvents = useMemo(() => {
    if (orden === 'relevancia') return events
    const sorted = [...events]
    if (orden === 'fecha') {
      sorted.sort(
        (a, b) => new Date(a.fecha_inicio).getTime() - new Date(b.fecha_inicio).getTime(),
      )
    } else if (orden === 'precio') {
      sorted.sort((a, b) => {
        const aP = a.es_gratuito ? 0 : (a.precio_min ?? Infinity)
        const bP = b.es_gratuito ? 0 : (b.precio_min ?? Infinity)
        return aP - bP
      })
    }
    return sorted
  }, [events, orden])

  // Stable callbacks
  const handleFiltersChange = useCallback((f: Filters) => {
    setFilters(f)
    setPage(1)
  }, [])

  const handleQueryChange = useCallback((q: string) => {
    setQuery(q)
    setPage(1)
  }, [])

  const activeCount = countActiveFilters(filters, query)

  return (
    <div className="container-custom py-8">

      {/* ── Header ──────────────────────────────────────────────────────────── */}
      <div className="mb-8">
        <h1 className="font-display text-3xl font-bold text-secondary-800 mb-1">
          Explorar eventos
        </h1>
        <p className="font-sans text-sm text-gray-400 mb-5">
          Descubrí lo que pasa en Buenos Aires
        </p>

        <SearchBar
          initialQuery={query}
          placeholder="Buscar en el catálogo..."
          size="md"
          onSearch={handleQueryChange}
        />

        {/* Active filter chips */}
        {activeCount > 0 && (
          <div className="flex flex-wrap gap-2 mt-3">
            {query && (
              <FilterChip label={`"${query}"`} onRemove={() => handleQueryChange('')} />
            )}
            {filters.categorias.map((c) => (
              <FilterChip
                key={c}
                label={c}
                onRemove={() =>
                  handleFiltersChange({ ...filters, categorias: filters.categorias.filter((x) => x !== c) })
                }
              />
            ))}
            {filters.barrio && (
              <FilterChip
                label={filters.barrio}
                onRemove={() => handleFiltersChange({ ...filters, barrio: '' })}
              />
            )}
            {filters.fecha && (
              <FilterChip
                label={FECHA_LABELS[filters.fecha] ?? filters.fecha}
                onRemove={() => handleFiltersChange({ ...filters, fecha: '' })}
              />
            )}
            {(filters.fecha_desde || filters.fecha_hasta) && (
              <FilterChip
                label={`${filters.fecha_desde || '…'} → ${filters.fecha_hasta || '…'}`}
                onRemove={() => handleFiltersChange({ ...filters, fecha_desde: '', fecha_hasta: '' })}
              />
            )}
            {filters.tags.map((t) => (
              <FilterChip
                key={t}
                label={t}
                onRemove={() =>
                  handleFiltersChange({ ...filters, tags: filters.tags.filter((x) => x !== t) })
                }
              />
            ))}
            {(filters.solo_gratis || filters.precio) && (
              <FilterChip
                label={filters.solo_gratis ? 'Solo gratis' : 'Con costo'}
                onRemove={() => handleFiltersChange({ ...filters, solo_gratis: false, precio: '' })}
              />
            )}
            {(filters.precio_min > 0 || filters.precio_max < 10000) && (
              <FilterChip
                label={`$${filters.precio_min.toLocaleString('es-AR')} – $${filters.precio_max.toLocaleString('es-AR')}`}
                onRemove={() => handleFiltersChange({ ...filters, precio_min: 0, precio_max: 10000 })}
              />
            )}
          </div>
        )}
      </div>

      {/* ── Two-column layout ────────────────────────────────────────────────── */}
      <div className="flex gap-6 items-start">

        {/* Sidebar – desktop, sticky */}
        <div className="hidden md:block w-60 shrink-0">
          <div className="sticky top-4">
            <FilterSidebar filters={filters} onChange={handleFiltersChange} />
          </div>
        </div>

        {/* Results area */}
        <div className="flex-1 min-w-0">

          {/* Controls bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
            <p className="font-sans text-sm text-gray-500">
              {loading
                ? 'Buscando…'
                : `${total.toLocaleString('es-AR')} evento${total !== 1 ? 's' : ''} encontrado${total !== 1 ? 's' : ''}`}
            </p>

            <div className="flex items-center gap-3">
              {/* Sort controls */}
              <div className="flex items-center gap-2">
                <span className="text-gray-400 text-xs hidden sm:block">Ordenar:</span>
                <div className="flex rounded-lg border border-gray-200 overflow-hidden">
                  {(Object.keys(ORDEN_LABELS) as SortOrder[]).map((o) => (
                    <button
                      key={o}
                      onClick={() => setOrden(o)}
                      className={cn(
                        'px-3 py-1.5 text-xs font-medium transition-colors',
                        orden === o
                          ? 'bg-primary-500 text-white'
                          : 'text-gray-600 hover:bg-gray-50',
                      )}
                    >
                      {ORDEN_LABELS[o]}
                    </button>
                  ))}
                </div>
              </div>

              {/* View mode */}
              <div className="flex rounded-lg border border-gray-200 overflow-hidden">
                <button
                  onClick={() => setVista('grid')}
                  className={cn(
                    'p-1.5 transition-colors',
                    vista === 'grid' ? 'bg-primary-500 text-white' : 'text-gray-500 hover:bg-gray-50',
                  )}
                  aria-label="Vista cuadrícula"
                >
                  <Grid3X3 className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setVista('lista')}
                  className={cn(
                    'p-1.5 transition-colors',
                    vista === 'lista' ? 'bg-primary-500 text-white' : 'text-gray-500 hover:bg-gray-50',
                  )}
                  aria-label="Vista lista"
                >
                  <List className="w-4 h-4" />
                </button>
                <button
                  disabled
                  className="p-1.5 text-gray-300 cursor-not-allowed"
                  aria-label="Vista mapa (próximamente)"
                  title="Vista mapa – próximamente"
                >
                  <MapPin className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>

          {/* Event grid / list */}
          {vista === 'grid' ? (
            <EventGrid
              events={sortedEvents}
              loading={loading}
              emptyMessage="Probá cambiando los filtros o ampliando la búsqueda."
            />
          ) : (
            <EventList
              events={sortedEvents}
              loading={loading}
              emptyMessage="Probá cambiando los filtros o ampliando la búsqueda."
            />
          )}

          {/* Pagination */}
          {!loading && totalPages > 1 && (
            <nav className="flex items-center justify-center gap-2 mt-10" aria-label="Paginación">
              <button
                onClick={() => { setPage((p) => Math.max(1, p - 1)); window.scrollTo({ top: 0, behavior: 'smooth' }) }}
                disabled={page <= 1}
                className="flex items-center gap-1 px-3 py-2 rounded-lg border border-gray-200 text-sm text-gray-600 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
                <span className="hidden sm:block">Anterior</span>
              </button>

              <div className="flex items-center gap-1">
                {getPaginationRange(page, totalPages).map((item, i) =>
                  item === '...' ? (
                    <span key={`dots-${i}`} className="px-2 text-gray-400 text-sm select-none">…</span>
                  ) : (
                    <button
                      key={item}
                      onClick={() => { setPage(item as number); window.scrollTo({ top: 0, behavior: 'smooth' }) }}
                      className={cn(
                        'w-9 h-9 rounded-lg text-sm font-medium transition-colors',
                        page === item ? 'bg-primary-500 text-white' : 'text-gray-600 hover:bg-gray-100',
                      )}
                      aria-current={page === item ? 'page' : undefined}
                    >
                      {item}
                    </button>
                  ),
                )}
              </div>

              <button
                onClick={() => { setPage((p) => Math.min(totalPages, p + 1)); window.scrollTo({ top: 0, behavior: 'smooth' }) }}
                disabled={page >= totalPages}
                className="flex items-center gap-1 px-3 py-2 rounded-lg border border-gray-200 text-sm text-gray-600 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                <span className="hidden sm:block">Siguiente</span>
                <ChevronRight className="w-4 h-4" />
              </button>
            </nav>
          )}
        </div>
      </div>

      {/* ── Mobile: floating "Filtros (N)" button ─────────────────────────────── */}
      <div className="fixed bottom-6 left-1/2 -translate-x-1/2 md:hidden z-30">
        <button
          onClick={() => setSidebarOpen(true)}
          className="flex items-center gap-2.5 px-5 py-3 bg-secondary-800 text-white rounded-full shadow-lg hover:bg-secondary-900 transition-colors font-semibold text-sm"
        >
          <SlidersHorizontal className="w-4 h-4" />
          Filtros
          {activeCount > 0 && (
            <span className="bg-primary-500 text-white text-xs font-bold w-5 h-5 rounded-full flex items-center justify-center">
              {activeCount}
            </span>
          )}
        </button>
      </div>

      {/* ── Mobile: slide-in drawer ────────────────────────────────────────────── */}
      {sidebarOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/50 z-40 md:hidden"
            onClick={() => setSidebarOpen(false)}
          />
          {/* Panel */}
          <div className="fixed inset-y-0 left-0 w-80 max-w-[90vw] bg-gray-50 z-50 md:hidden flex flex-col shadow-2xl">
            <div className="flex items-center justify-between px-4 py-3 bg-white border-b border-gray-100 shrink-0">
              <h2 className="font-display font-bold text-secondary-800 text-lg">Filtros</h2>
              <button
                onClick={() => setSidebarOpen(false)}
                className="p-2 rounded-lg hover:bg-gray-100 transition-colors text-gray-500"
                aria-label="Cerrar filtros"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4">
              <FilterSidebar filters={filters} onChange={handleFiltersChange} />
            </div>

            <div className="p-4 bg-white border-t border-gray-100 shrink-0">
              <button
                onClick={() => setSidebarOpen(false)}
                className="w-full py-3 bg-primary-500 text-white rounded-xl font-semibold hover:bg-primary-600 transition-colors text-sm"
              >
                {loading
                  ? 'Buscando…'
                  : `Ver ${total.toLocaleString('es-AR')} evento${total !== 1 ? 's' : ''}`}
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

// ─── Filter chip ──────────────────────────────────────────────────────────────

function FilterChip({ label, onRemove }: { label: string; onRemove: () => void }) {
  return (
    <span className="inline-flex items-center gap-1 px-3 py-1 bg-primary-50 text-primary-700 text-sm rounded-full font-medium">
      {label}
      <button
        onClick={onRemove}
        className="text-primary-400 hover:text-primary-700 transition-colors"
        aria-label={`Quitar filtro "${label}"`}
      >
        <X className="w-3.5 h-3.5" />
      </button>
    </span>
  )
}

