'use client'

import { cn } from '@/lib/utils'

type DateOption = 'hoy' | 'manana' | 'semana' | 'mes' | ''

const DATE_OPTIONS: Array<{ value: DateOption; label: string }> = [
  { value: 'hoy',    label: 'Hoy' },
  { value: 'manana', label: 'Mañana' },
  { value: 'semana', label: 'Esta semana' },
  { value: 'mes',    label: 'Este mes' },
]

interface DateFilterProps {
  selected: DateOption
  onChange: (value: DateOption) => void
}

export default function DateFilter({ selected, onChange }: DateFilterProps) {
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
    </div>
  )
}
