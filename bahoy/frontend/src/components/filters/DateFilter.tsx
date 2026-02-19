'use client'

import { cn } from '@/lib/utils'

export type DateOption = 'hoy' | 'manana' | 'finde' | 'semana' | 'mes' | ''

const DATE_OPTIONS: Array<{ value: Exclude<DateOption, ''>; label: string }> = [
  { value: 'hoy',    label: 'Hoy' },
  { value: 'manana', label: 'Mañana' },
  { value: 'finde',  label: 'Este fin de semana' },
  { value: 'semana', label: 'Esta semana' },
  { value: 'mes',    label: 'Este mes' },
]

interface DateFilterProps {
  selected: DateOption
  onChange: (value: DateOption) => void
  fechaDesde?: string
  fechaHasta?: string
  onFechaDesde?: (date: string) => void
  onFechaHasta?: (date: string) => void
}

export default function DateFilter({
  selected,
  onChange,
  fechaDesde = '',
  fechaHasta = '',
  onFechaDesde,
  onFechaHasta,
}: DateFilterProps) {
  return (
    <div>
      <p className="font-sans font-semibold text-secondary-800 text-sm mb-3">Cuándo</p>
      <div className="space-y-1.5">
        {DATE_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            onClick={() => onChange(selected === opt.value ? '' : opt.value)}
            className={cn(
              'w-full px-3 py-2 rounded-lg text-sm font-medium transition-colors duration-150 text-left',
              selected === opt.value
                ? 'bg-primary-50 text-primary-700 font-semibold'
                : 'text-gray-600 hover:bg-gray-100',
            )}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {/* Optional date range picker */}
      {onFechaDesde && onFechaHasta && (
        <div className="mt-4 space-y-2">
          <p className="text-xs text-gray-400 font-medium">O elegí un rango</p>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="text-xs text-gray-500 block mb-1">Desde</label>
              <input
                type="date"
                value={fechaDesde}
                onChange={(e) => {
                  onFechaDesde(e.target.value)
                  onChange('')
                }}
                className="w-full px-2 py-1.5 border border-gray-200 rounded-lg text-xs text-gray-700 focus:outline-none focus:border-primary-400"
              />
            </div>
            <div>
              <label className="text-xs text-gray-500 block mb-1">Hasta</label>
              <input
                type="date"
                value={fechaHasta}
                onChange={(e) => {
                  onFechaHasta(e.target.value)
                  onChange('')
                }}
                className="w-full px-2 py-1.5 border border-gray-200 rounded-lg text-xs text-gray-700 focus:outline-none focus:border-primary-400"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
