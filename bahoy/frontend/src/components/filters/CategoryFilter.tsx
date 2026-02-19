'use client'

import { useState } from 'react'
import { ChevronDown } from 'lucide-react'
import { cn } from '@/lib/utils'

interface SubCategoria {
  id: string
  label: string
}

interface Categoria {
  id: string
  label: string
  emoji: string
  subcategorias?: SubCategoria[]
}

const CATEGORIAS: Categoria[] = [
  {
    id: 'teatro',
    label: 'Teatro',
    emoji: '🎭',
    subcategorias: [
      { id: 'teatro-obra', label: 'Obra de teatro' },
      { id: 'teatro-musical', label: 'Musical' },
      { id: 'teatro-comedia', label: 'Comedia' },
    ],
  },
  {
    id: 'musica',
    label: 'Música',
    emoji: '🎵',
    subcategorias: [
      { id: 'musica-rock', label: 'Rock' },
      { id: 'musica-jazz', label: 'Jazz & Blues' },
      { id: 'musica-clasica', label: 'Clásica' },
      { id: 'musica-folklore', label: 'Folklore' },
    ],
  },
  {
    id: 'arte',
    label: 'Arte',
    emoji: '🎨',
    subcategorias: [
      { id: 'arte-exposicion', label: 'Exposición' },
      { id: 'arte-fotografia', label: 'Fotografía' },
      { id: 'arte-instalacion', label: 'Instalación' },
    ],
  },
  { id: 'cine',        label: 'Cine',        emoji: '🎬' },
  { id: 'danza',       label: 'Danza',       emoji: '💃' },
  { id: 'gastronomia', label: 'Gastronomía', emoji: '🍽️' },
  { id: 'deportes',    label: 'Deportes',    emoji: '⚽' },
  { id: 'literatura',  label: 'Literatura',  emoji: '📚' },
  { id: 'infantil',    label: 'Infantil',    emoji: '🧒' },
  { id: 'stand-up',   label: 'Stand-up',    emoji: '🎤' },
]

interface CategoryFilterProps {
  selected: string[]
  onChange: (categories: string[]) => void
  counts?: Record<string, number>
}

export default function CategoryFilter({
  selected,
  onChange,
  counts = {},
}: CategoryFilterProps) {
  const [expanded, setExpanded] = useState<string[]>([])

  const toggleExpand = (id: string) => {
    setExpanded((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    )
  }

  const toggleCategory = (id: string) => {
    onChange(
      selected.includes(id)
        ? selected.filter((c) => c !== id)
        : [...selected, id],
    )
  }

  return (
    <div>
      <p className="font-sans font-semibold text-secondary-800 text-sm mb-3">Categoría</p>
      <div className="space-y-0.5">
        {CATEGORIAS.map((cat) => {
          const isSelected = selected.includes(cat.id)
          const isExpanded = expanded.includes(cat.id)
          const hasSubs = !!cat.subcategorias?.length
          const count = counts[cat.id]

          return (
            <div key={cat.id}>
              <div
                className={cn(
                  'flex items-center rounded-lg transition-colors duration-150',
                  isSelected ? 'bg-primary-50' : 'hover:bg-gray-100',
                )}
              >
                <button
                  onClick={() => toggleCategory(cat.id)}
                  className="flex items-center gap-2.5 flex-1 px-3 py-2 text-sm font-medium text-left"
                >
                  <span className="text-base leading-none">{cat.emoji}</span>
                  <span
                    className={cn(
                      isSelected ? 'text-primary-700 font-semibold' : 'text-gray-600',
                    )}
                  >
                    {cat.label}
                  </span>
                  {count !== undefined ? (
                    <span
                      className={cn(
                        'ml-auto text-xs px-1.5 py-0.5 rounded-full',
                        isSelected
                          ? 'bg-primary-100 text-primary-600'
                          : 'bg-gray-100 text-gray-500',
                      )}
                    >
                      {count}
                    </span>
                  ) : (
                    isSelected && (
                      <span className="ml-auto w-2 h-2 rounded-full bg-primary-500" />
                    )
                  )}
                </button>

                {hasSubs && (
                  <button
                    onClick={() => toggleExpand(cat.id)}
                    className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                    aria-label={isExpanded ? 'Contraer' : 'Expandir subcategorías'}
                  >
                    <ChevronDown
                      className={cn(
                        'w-3.5 h-3.5 transition-transform duration-200',
                        isExpanded && 'rotate-180',
                      )}
                    />
                  </button>
                )}
              </div>

              {/* Subcategorías */}
              {hasSubs && isExpanded && (
                <div className="ml-8 mt-0.5 space-y-0.5">
                  {cat.subcategorias!.map((sub) => {
                    const isSubSelected = selected.includes(sub.id)
                    return (
                      <button
                        key={sub.id}
                        onClick={() => toggleCategory(sub.id)}
                        className={cn(
                          'w-full flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium text-left transition-colors duration-150',
                          isSubSelected
                            ? 'bg-primary-50 text-primary-700'
                            : 'text-gray-500 hover:bg-gray-100 hover:text-gray-700',
                        )}
                      >
                        <span
                          className={cn(
                            'w-1.5 h-1.5 rounded-full shrink-0',
                            isSubSelected ? 'bg-primary-500' : 'bg-gray-300',
                          )}
                        />
                        {sub.label}
                      </button>
                    )
                  })}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
