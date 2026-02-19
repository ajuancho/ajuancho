'use client'

import { formatPrice } from '@/lib/utils'

const MAX_PRICE = 10000

interface PriceRangeFilterProps {
  min: number
  max: number
  soloGratis: boolean
  onChange: (min: number, max: number, soloGratis: boolean) => void
}

export default function PriceRangeFilter({
  min,
  max,
  soloGratis,
  onChange,
}: PriceRangeFilterProps) {
  return (
    <div>
      <p className="font-sans font-semibold text-secondary-800 text-sm mb-3">Precio</p>

      {/* Solo gratuitos */}
      <label className="flex items-center gap-2.5 cursor-pointer mb-4 group">
        <input
          type="checkbox"
          checked={soloGratis}
          onChange={(e) => onChange(min, max, e.target.checked)}
          className="w-4 h-4 rounded accent-primary-500"
        />
        <span className="text-sm text-gray-700 font-medium group-hover:text-primary-600 transition-colors">
          Solo gratuitos
        </span>
      </label>

      {!soloGratis && (
        <div className="space-y-4">
          {/* Price display */}
          <div className="flex justify-between text-xs font-medium text-gray-600">
            <span>{formatPrice(min)}</span>
            <span>{max >= MAX_PRICE ? 'Sin límite' : formatPrice(max)}</span>
          </div>

          {/* Min range */}
          <div className="space-y-1">
            <span className="text-xs text-gray-400">Mínimo</span>
            <input
              type="range"
              min={0}
              max={MAX_PRICE}
              step={500}
              value={min}
              onChange={(e) => {
                const v = Number(e.target.value)
                onChange(Math.min(v, max - 500), max, soloGratis)
              }}
              className="w-full h-1.5 rounded-full accent-primary-500 cursor-pointer"
            />
          </div>

          {/* Max range */}
          <div className="space-y-1">
            <span className="text-xs text-gray-400">Máximo</span>
            <input
              type="range"
              min={0}
              max={MAX_PRICE}
              step={500}
              value={max}
              onChange={(e) => {
                const v = Number(e.target.value)
                onChange(min, Math.max(v, min + 500), soloGratis)
              }}
              className="w-full h-1.5 rounded-full accent-primary-500 cursor-pointer"
            />
          </div>
        </div>
      )}
    </div>
  )
}
