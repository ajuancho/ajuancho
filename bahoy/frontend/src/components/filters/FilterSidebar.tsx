'use client'

import { X } from 'lucide-react'
import CategoryFilter from './CategoryFilter'
import DateFilter from './DateFilter'
import PriceFilter from './PriceFilter'
import Button from '@/components/ui/Button'

export interface Filters {
  categorias: string[]
  fecha: 'hoy' | 'manana' | 'semana' | 'mes' | ''
  precio: 'gratis' | 'pagos' | ''
}

const EMPTY_FILTERS: Filters = {
  categorias: [],
  fecha: '',
  precio: '',
}

interface FilterSidebarProps {
  filters: Filters
  onChange: (filters: Filters) => void
  className?: string
}

export default function FilterSidebar({ filters, onChange, className }: FilterSidebarProps) {
  const activeCount =
    filters.categorias.length +
    (filters.fecha ? 1 : 0) +
    (filters.precio ? 1 : 0)

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

        {/* Divider */}
        <hr className="border-gray-100" />

        <CategoryFilter
          selected={filters.categorias}
          onChange={(categorias) => onChange({ ...filters, categorias })}
        />

        <hr className="border-gray-100" />

        <DateFilter
          selected={filters.fecha}
          onChange={(fecha) => onChange({ ...filters, fecha })}
        />

        <hr className="border-gray-100" />

        <PriceFilter
          selected={filters.precio}
          onChange={(precio) => onChange({ ...filters, precio })}
        />

        {activeCount > 0 && (
          <>
            <hr className="border-gray-100" />
            <Button variant="primary" size="sm" className="w-full" onClick={handleReset}>
              Limpiar filtros
            </Button>
          </>
        )}
      </div>
    </aside>
  )
}
