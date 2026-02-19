'use client'

import { useState, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import type { Metadata } from 'next'
import FilterSidebar, { type Filters } from '@/components/filters/FilterSidebar'
import EventGrid from '@/components/events/EventGrid'
import SearchBar from '@/components/search/SearchBar'
import { SlidersHorizontal, X } from 'lucide-react'
import { eventsApi, type EventSummary } from '@/lib/api'

const EMPTY_FILTERS: Filters = { categorias: [], fecha: '', precio: '' }

export default function ExplorarPage() {
  const searchParams = useSearchParams()

  const [events, setEvents] = useState<EventSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const [filters, setFilters] = useState<Filters>(() => ({
    categorias: searchParams.get('categoria') ? [searchParams.get('categoria')!] : [],
    fecha: '' as Filters['fecha'],
    precio: '' as Filters['precio'],
  }))

  const [query, setQuery] = useState(searchParams.get('q') ?? '')

  useEffect(() => {
    let cancelled = false
    setLoading(true)

    eventsApi
      .list({
        q: query || undefined,
        categorias: filters.categorias.length ? filters.categorias : undefined,
        fecha: filters.fecha || undefined,
        precio: filters.precio || undefined,
        size: 24,
      })
      .then((res) => {
        if (!cancelled) setEvents(res.items)
      })
      .catch(() => {
        if (!cancelled) setEvents([])
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => { cancelled = true }
  }, [filters, query])

  const activeCount =
    filters.categorias.length +
    (filters.fecha ? 1 : 0) +
    (filters.precio ? 1 : 0) +
    (query ? 1 : 0)

  return (
    <div className="container-custom py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="font-display text-3xl font-bold text-secondary-800 mb-4">
          Explorar eventos
        </h1>
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="flex-1">
            <SearchBar
              initialQuery={query}
              placeholder="Buscar en el catálogo..."
              size="md"
              onSearch={setQuery}
            />
          </div>

          {/* Mobile filter toggle */}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="md:hidden flex items-center gap-2 px-4 py-3 border-2 border-secondary-200 rounded-xl text-secondary-700 font-medium hover:border-primary-400 hover:text-primary-600 transition-colors"
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

        {/* Active filter chips */}
        {activeCount > 0 && (
          <div className="flex flex-wrap gap-2 mt-3">
            {query && (
              <Chip label={`"${query}"`} onRemove={() => setQuery('')} />
            )}
            {filters.categorias.map((c) => (
              <Chip
                key={c}
                label={c}
                onRemove={() =>
                  setFilters((f) => ({ ...f, categorias: f.categorias.filter((x) => x !== c) }))
                }
              />
            ))}
            {filters.fecha && (
              <Chip label={filters.fecha} onRemove={() => setFilters((f) => ({ ...f, fecha: '' }))} />
            )}
            {filters.precio && (
              <Chip label={filters.precio} onRemove={() => setFilters((f) => ({ ...f, precio: '' }))} />
            )}
          </div>
        )}
      </div>

      <div className="flex gap-8">
        {/* Sidebar – desktop always visible, mobile conditional */}
        <div className={`${sidebarOpen ? 'block' : 'hidden'} md:block w-full md:w-64 shrink-0`}>
          <FilterSidebar
            filters={filters}
            onChange={(f) => { setFilters(f); setSidebarOpen(false) }}
          />
        </div>

        {/* Grid */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-4">
            <p className="font-sans text-sm text-gray-500">
              {loading ? 'Buscando...' : `${events.length} eventos encontrados`}
            </p>
          </div>
          <EventGrid
            events={events}
            loading={loading}
            emptyMessage="Probá cambiando los filtros o ampliando la búsqueda."
          />
        </div>
      </div>
    </div>
  )
}

function Chip({ label, onRemove }: { label: string; onRemove: () => void }) {
  return (
    <span className="inline-flex items-center gap-1 px-3 py-1 bg-primary-50 text-primary-700 text-sm rounded-full font-medium">
      {label}
      <button onClick={onRemove} className="text-primary-400 hover:text-primary-700 transition-colors">
        <X className="w-3.5 h-3.5" />
      </button>
    </span>
  )
}
