'use client'

import { cn } from '@/lib/utils'

const TAGS = [
  { id: 'familiar',      label: 'Familiar',      emoji: '👨‍👩‍👧' },
  { id: 'al-aire-libre', label: 'Al aire libre',  emoji: '🌳' },
  { id: 'nocturno',      label: 'Nocturno',       emoji: '🌙' },
  { id: 'cultural',      label: 'Cultural',       emoji: '🏛️' },
  { id: 'gastronomico',  label: 'Gastronómico',   emoji: '🍽️' },
]

interface TagsFilterProps {
  selected: string[]
  onChange: (tags: string[]) => void
}

export default function TagsFilter({ selected, onChange }: TagsFilterProps) {
  const toggle = (id: string) => {
    onChange(
      selected.includes(id)
        ? selected.filter((t) => t !== id)
        : [...selected, id],
    )
  }

  return (
    <div>
      <p className="font-sans font-semibold text-secondary-800 text-sm mb-3">Tags</p>
      <div className="flex flex-wrap gap-2">
        {TAGS.map((tag) => {
          const isSelected = selected.includes(tag.id)
          return (
            <button
              key={tag.id}
              onClick={() => toggle(tag.id)}
              className={cn(
                'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border transition-all duration-150',
                isSelected
                  ? 'bg-primary-500 text-white border-primary-500 shadow-sm'
                  : 'bg-white text-gray-600 border-gray-200 hover:border-primary-300 hover:text-primary-600',
              )}
            >
              <span>{tag.emoji}</span>
              {tag.label}
            </button>
          )
        })}
      </div>
    </div>
  )
}
