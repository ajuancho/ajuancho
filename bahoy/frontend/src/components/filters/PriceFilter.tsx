'use client'

import { cn } from '@/lib/utils'

type PriceOption = 'gratis' | 'pagos' | ''

interface PriceFilterProps {
  selected: PriceOption
  onChange: (value: PriceOption) => void
}

export default function PriceFilter({ selected, onChange }: PriceFilterProps) {
  return (
    <div>
      <p className="font-sans font-semibold text-secondary-800 text-sm mb-3">Precio</p>
      <div className="flex gap-2">
        {(['gratis', 'pagos'] as PriceOption[]).map((opt) => (
          <button
            key={opt}
            onClick={() => onChange(selected === opt ? '' : opt)}
            className={cn(
              'flex-1 py-2 rounded-lg text-sm font-medium border transition-colors duration-150 capitalize',
              selected === opt
                ? 'bg-primary-500 text-white border-primary-500'
                : 'border-gray-200 text-gray-600 hover:border-primary-300 hover:text-primary-600',
            )}
          >
            {opt === 'gratis' ? 'Gratis' : 'Con costo'}
          </button>
        ))}
      </div>
    </div>
  )
}
