'use client'

import { useState } from 'react'
import { Search, ChevronDown, X } from 'lucide-react'
import { cn } from '@/lib/utils'

const BARRIOS = [
  'Almagro', 'Balvanera', 'Barracas', 'Belgrano', 'Boedo',
  'Caballito', 'Chacarita', 'Coghlan', 'Colegiales', 'Constitución',
  'Devoto', 'Flores', 'Floresta', 'La Boca', 'La Paternal',
  'Liniers', 'Mataderos', 'Monte Castro', 'Monserrat', 'Nueva Pompeya',
  'Núñez', 'Palermo', 'Parque Chacabuco', 'Parque Chas', 'Puerto Madero',
  'Recoleta', 'Retiro', 'Saavedra', 'San Cristóbal', 'San Nicolás',
  'San Telmo', 'Versalles', 'Villa Crespo', 'Villa del Parque', 'Villa Devoto',
  'Villa General Mitre', 'Villa Lugano', 'Villa Luro', 'Villa Ortúzar',
  'Villa Pueyrredón', 'Villa Real', 'Villa Riachuelo', 'Villa Santa Rita',
  'Villa Soldati', 'Villa Urquiza',
]

interface BarrioFilterProps {
  selected: string
  onChange: (barrio: string) => void
}

export default function BarrioFilter({ selected, onChange }: BarrioFilterProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [search, setSearch] = useState('')

  const filtered = BARRIOS.filter((b) =>
    b.toLowerCase().includes(search.toLowerCase()),
  )

  const handleSelect = (barrio: string) => {
    onChange(barrio)
    setIsOpen(false)
    setSearch('')
  }

  return (
    <div>
      <p className="font-sans font-semibold text-secondary-800 text-sm mb-3">Barrio</p>
      <div className="relative">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className={cn(
            'w-full flex items-center justify-between px-3 py-2 rounded-lg border text-sm transition-colors text-left',
            selected
              ? 'border-primary-400 text-primary-700 bg-primary-50'
              : 'border-gray-200 text-gray-600 hover:border-primary-300',
          )}
        >
          <span>{selected || 'Todos los barrios'}</span>
          <div className="flex items-center gap-1 shrink-0">
            {selected && (
              <button
                onClick={(e) => { e.stopPropagation(); onChange('') }}
                className="text-primary-400 hover:text-primary-700 transition-colors"
                aria-label="Limpiar barrio"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
            <ChevronDown
              className={cn(
                'w-4 h-4 text-gray-400 transition-transform duration-200',
                isOpen && 'rotate-180',
              )}
            />
          </div>
        </button>

        {isOpen && (
          <>
            {/* Backdrop */}
            <div
              className="fixed inset-0 z-10"
              onClick={() => setIsOpen(false)}
            />
            {/* Dropdown */}
            <div className="absolute z-20 top-full mt-1 w-full bg-white border border-gray-200 rounded-xl shadow-lg overflow-hidden">
              <div className="p-2 border-b border-gray-100">
                <div className="flex items-center gap-2 px-2 py-1.5 bg-gray-50 rounded-lg">
                  <Search className="w-3.5 h-3.5 text-gray-400 shrink-0" />
                  <input
                    type="text"
                    placeholder="Buscar barrio..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="flex-1 bg-transparent text-sm outline-none text-gray-700 placeholder:text-gray-400"
                    autoFocus
                  />
                </div>
              </div>
              <div className="max-h-52 overflow-y-auto py-1">
                {filtered.length === 0 ? (
                  <p className="text-xs text-gray-400 text-center py-4">Sin resultados</p>
                ) : (
                  filtered.map((barrio) => (
                    <button
                      key={barrio}
                      onClick={() => handleSelect(barrio)}
                      className={cn(
                        'w-full text-left px-3 py-2 text-sm transition-colors',
                        selected === barrio
                          ? 'bg-primary-50 text-primary-700 font-medium'
                          : 'text-gray-700 hover:bg-gray-50',
                      )}
                    >
                      {barrio}
                    </button>
                  ))
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
