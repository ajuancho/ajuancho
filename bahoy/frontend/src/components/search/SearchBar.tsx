'use client'

import { useState, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { Search, X } from 'lucide-react'
import { cn } from '@/lib/utils'

interface SearchBarProps {
  initialQuery?: string
  placeholder?: string
  size?: 'sm' | 'md' | 'lg'
  className?: string
  onSearch?: (query: string) => void
}

export default function SearchBar({
  initialQuery = '',
  placeholder = 'Buscar eventos, artistas, venues...',
  size = 'md',
  className,
  onSearch,
}: SearchBarProps) {
  const [query, setQuery] = useState(initialQuery)
  const router = useRouter()
  const inputRef = useRef<HTMLInputElement>(null)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    if (onSearch) {
      onSearch(query.trim())
    } else {
      router.push(`/buscar?q=${encodeURIComponent(query.trim())}`)
    }
  }

  const handleClear = () => {
    setQuery('')
    inputRef.current?.focus()
    if (onSearch) onSearch('')
  }

  const sizeClasses = {
    sm: { input: 'py-2 pl-9 pr-8 text-sm', icon: 'w-4 h-4 left-2.5', btn: 'text-xs px-3 py-1.5' },
    md: { input: 'py-3 pl-11 pr-10 text-base', icon: 'w-5 h-5 left-3.5', btn: 'text-sm px-5 py-3' },
    lg: { input: 'py-4 pl-12 pr-12 text-lg', icon: 'w-6 h-6 left-4', btn: 'text-base px-7 py-4' },
  }

  const sz = sizeClasses[size]

  return (
    <form onSubmit={handleSubmit} className={cn('flex gap-2', className)}>
      <div className="relative flex-1">
        <Search
          className={cn(
            'absolute top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none',
            sz.icon,
          )}
        />
        <input
          ref={inputRef}
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={placeholder}
          className={cn(
            'w-full rounded-xl border border-gray-200 bg-white font-sans',
            'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
            'placeholder:text-gray-400 transition-all duration-200',
            sz.input,
          )}
        />
        {query && (
          <button
            type="button"
            onClick={handleClear}
            className="absolute top-1/2 -translate-y-1/2 right-3 text-gray-400 hover:text-gray-600 transition-colors"
            aria-label="Limpiar búsqueda"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      <button
        type="submit"
        className={cn(
          'bg-primary-500 hover:bg-primary-600 text-white font-semibold rounded-xl',
          'transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
          'whitespace-nowrap',
          sz.btn,
        )}
      >
        Buscar
      </button>
    </form>
  )
}
