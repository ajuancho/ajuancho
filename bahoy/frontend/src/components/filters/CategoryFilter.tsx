'use client'

import { cn } from '@/lib/utils'

const CATEGORIAS = [
  { id: 'teatro',       label: 'Teatro',       emoji: '🎭' },
  { id: 'musica',       label: 'Música',        emoji: '🎵' },
  { id: 'arte',         label: 'Arte',          emoji: '🎨' },
  { id: 'cine',         label: 'Cine',          emoji: '🎬' },
  { id: 'danza',        label: 'Danza',         emoji: '💃' },
  { id: 'gastronomia',  label: 'Gastronomía',   emoji: '🍽️' },
  { id: 'deportes',     label: 'Deportes',      emoji: '⚽' },
  { id: 'literatura',   label: 'Literatura',    emoji: '📚' },
  { id: 'infantil',     label: 'Infantil',      emoji: '🧒' },
  { id: 'stand-up',     label: 'Stand-up',      emoji: '🎤' },
]

interface CategoryFilterProps {
  selected: string[]
  onChange: (categories: string[]) => void
}

export default function CategoryFilter({ selected, onChange }: CategoryFilterProps) {
  const toggle = (id: string) => {
    onChange(
      selected.includes(id)
        ? selected.filter((c) => c !== id)
        : [...selected, id],
    )
  }

  return (
    <div>
      <p className="font-sans font-semibold text-secondary-800 text-sm mb-3">Categoría</p>
      <div className="space-y-1.5">
        {CATEGORIAS.map((cat) => {
          const isSelected = selected.includes(cat.id)
          return (
            <button
              key={cat.id}
              onClick={() => toggle(cat.id)}
              className={cn(
                'w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors duration-150 text-left',
                isSelected
                  ? 'bg-primary-50 text-primary-700 font-semibold'
                  : 'text-gray-600 hover:bg-gray-100',
              )}
            >
              <span className="text-base leading-none">{cat.emoji}</span>
              {cat.label}
              {isSelected && (
                <span className="ml-auto w-2 h-2 rounded-full bg-primary-500" />
              )}
            </button>
          )
        })}
      </div>
    </div>
  )
}
