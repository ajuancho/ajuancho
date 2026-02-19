'use client'

import { X } from 'lucide-react'
import CategoryFilter from './CategoryFilter'
import DateFilter, { type DateOption } from './DateFilter'
import BarrioFilter from './BarrioFilter'
import PriceRangeFilter from './PriceRangeFilter'
import TagsFilter from './TagsFilter'
import Button from '@/components/ui/Button'

export interface Filters {
  categorias: string[]
  fecha: DateOption
  precio: 'gratis' | 'pagos' | ''
  barrio: string
  tags: string[]
  precio_min: number
  precio_max: number
  solo_gratis: boolean
  fecha_desde: string
  fecha_hasta: string
}

export const EMPTY_FILTERS: Filters = {
  categorias: [],
  fecha: '',
  precio: '',
  barrio: '',
  tags: [],
  precio_min: 0,
  precio_max: 10000,
  solo_gratis: false,
  fecha_desde: '',
  fecha_hasta: '',
}

interface FilterSidebarProps {
  filters: Filters
  onChange: (filters: Filters) => void
  className?: string
  categoryCounts?: Record<string, number>
}

export default function FilterSidebar({
  filters,
  onChange,
  className,
  categoryCounts,
}: FilterSidebarProps) {
  const activeCount =
    filters.categorias.length +
    (filters.fecha ? 1 : 0) +
    (filters.barrio ? 1 : 0) +
    filters.tags.length +
    (filters.solo_gratis ? 1 : 0) +
    (filters.precio && !filters.solo_gratis ? 1 : 0) +
    (filters.fecha_desde || filters.fecha_hasta ? 1 : 0) +
    (filters.precio_min > 0 || filters.precio_max < 10000 ? 1 : 0)

  const handleReset = () => onChange(EMPTY_FILTERS)

  return (
    <aside className={className}>
      <div className="bg-white rounded-xl shadow-card p-5 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h2 className="font-display font-semibold text-secondary-800">Filtros</h2>
          {activeCount > 0 && (
            <button
              onClick={handleReset}
              className="flex items-center gap-1 text-xs text-primary-500 hover:text-primary-700 font-medium transition-colors"
            >
              <X className="w-3.5 h-3.5" />
              Limpiar ({activeCount})
            </button>
          )}
        </div>

        <hr className="border-gray-100" />

        {/* Categorías */}
        <CategoryFilter
          selected={filters.categorias}
          onChange={(categorias) => onChange({ ...filters, categorias })}
          counts={categoryCounts}
        />

        <hr className="border-gray-100" />

        {/* Fechas */}
        <DateFilter
          selected={filters.fecha}
          onChange={(fecha) => onChange({ ...filters, fecha })}
          fechaDesde={filters.fecha_desde}
          fechaHasta={filters.fecha_hasta}
          onFechaDesde={(fecha_desde) => onChange({ ...filters, fecha_desde, fecha: '' })}
          onFechaHasta={(fecha_hasta) => onChange({ ...filters, fecha_hasta, fecha: '' })}
        />

        <hr className="border-gray-100" />

        {/* Barrios */}
        <BarrioFilter
          selected={filters.barrio}
          onChange={(barrio) => onChange({ ...filters, barrio })}
        />

        <hr className="border-gray-100" />

        {/* Precio */}
        <PriceRangeFilter
          min={filters.precio_min}
          max={filters.precio_max}
          soloGratis={filters.solo_gratis}
          onChange={(precio_min, precio_max, solo_gratis) =>
            onChange({ ...filters, precio_min, precio_max, solo_gratis })
          }
        />

        <hr className="border-gray-100" />

        {/* Tags */}
        <TagsFilter
          selected={filters.tags}
          onChange={(tags) => onChange({ ...filters, tags })}
        />

        {activeCount > 0 && (
          <>
            <hr className="border-gray-100" />
            <Button variant="outline" size="sm" className="w-full" onClick={handleReset}>
              Limpiar filtros
            </Button>
          </>
        )}
      </div>
    </aside>
  )
}
