'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { Search, X, Clock, MapPin, Tag, Loader2, ChevronRight } from 'lucide-react'
import Link from 'next/link'
import { cn } from '@/lib/utils'
import { eventsApi, type EventSummary } from '@/lib/api'

// ─── Constants ────────────────────────────────────────────────────────────────

const HISTORY_KEY = 'bahoy_search_history'
const MAX_HISTORY = 5

const CATEGORIAS_LIST = [
  'Teatro',
  'Música',
  'Arte',
  'Cine',
  'Danza',
  'Gastronomía',
  'Deportes',
  'Literatura',
  'Infantil',
  'Stand-up',
  'Tango',
  'Jazz',
  'Rock',
  'Folklore',
]

const BARRIO_MAP: Record<string, string> = {
  palermo: 'Palermo',
  'san telmo': 'San Telmo',
  'la boca': 'La Boca',
  recoleta: 'Recoleta',
  belgrano: 'Belgrano',
  almagro: 'Almagro',
  caballito: 'Caballito',
  'villa crespo': 'Villa Crespo',
  'puerto madero': 'Puerto Madero',
  microcentro: 'Microcentro',
  montserrat: 'Montserrat',
  barracas: 'Barracas',
  floresta: 'Floresta',
  colegiales: 'Colegiales',
  chacarita: 'Chacarita',
  'villa urquiza': 'Villa Urquiza',
  boedo: 'Boedo',
  flores: 'Flores',
  liniers: 'Liniers',
  mataderos: 'Mataderos',
  'san cristobal': 'San Cristóbal',
  balvanera: 'Balvanera',
  'villa del parque': 'Villa del Parque',
}

// ─── Natural language parser ──────────────────────────────────────────────────

interface ParsedQuery {
  cleanQuery: string
  barrio?: string
  precio?: 'gratis'
  fecha?: 'hoy' | 'manana' | 'semana'
  categoria?: string
}

function parseNaturalLanguage(raw: string): ParsedQuery {
  let q = raw
  const result: ParsedQuery = { cleanQuery: q }

  // Price: "gratis", "gratuito", "sin costo"
  if (/\b(gratis|gratuito|gratuita|sin costo)\b/i.test(q)) {
    result.precio = 'gratis'
    q = q.replace(/\b(gratis|gratuito|gratuita|sin costo)\b/gi, '').trim()
  }

  // Family / children → Infantil category
  if (/\b(ni[ñn]os?|familiar|familia|infantil|nenes?|chicos?)\b/i.test(q)) {
    result.categoria = 'Infantil'
    q = q.replace(/\b(ni[ñn]os?|familiar|familia|infantil|nenes?|chicos?)\b/gi, '').trim()
  }

  // Date: tonight / today
  if (/\b(esta noche|hoy)\b/i.test(q)) {
    result.fecha = 'hoy'
    q = q.replace(/\b(esta noche|hoy)\b/gi, '').trim()
  } else if (/\bma[ñn]ana\b/i.test(q)) {
    result.fecha = 'manana'
    q = q.replace(/\bma[ñn]ana\b/gi, '').trim()
  } else if (/\b(esta semana|semana)\b/i.test(q)) {
    result.fecha = 'semana'
    q = q.replace(/\b(esta semana|semana)\b/gi, '').trim()
  }

  // Barrio: "en palermo", "de san telmo", etc.
  for (const [key, value] of Object.entries(BARRIO_MAP)) {
    const pattern = new RegExp(`\\b(en|de)\\s+${key}\\b`, 'i')
    if (pattern.test(q)) {
      result.barrio = value
      q = q.replace(pattern, '').trim()
      break
    }
  }

  result.cleanQuery = q.replace(/\s+/g, ' ').trim()
  return result
}

function buildExplorarUrl(raw: string, parsed: ParsedQuery): string {
  const params = new URLSearchParams()
  const q = parsed.cleanQuery || raw.trim()
  if (q) params.set('q', q)
  if (parsed.barrio) params.set('barrio', parsed.barrio)
  if (parsed.precio) params.set('precio', parsed.precio)
  if (parsed.fecha) params.set('fecha', parsed.fecha)
  if (parsed.categoria) params.set('categoria', parsed.categoria)
  const qs = params.toString()
  return qs ? `/explorar?${qs}` : '/explorar'
}

// ─── History helpers ──────────────────────────────────────────────────────────

function getHistory(): string[] {
  try {
    return JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]')
  } catch {
    return []
  }
}

function saveToHistory(query: string) {
  if (!query.trim()) return
  const history = getHistory().filter((h) => h !== query)
  history.unshift(query)
  localStorage.setItem(HISTORY_KEY, JSON.stringify(history.slice(0, MAX_HISTORY)))
}

// ─── Component ────────────────────────────────────────────────────────────────

interface SearchBarProps {
  initialQuery?: string
  placeholder?: string
  size?: 'sm' | 'md' | 'lg'
  className?: string
  onSearch?: (query: string) => void
}

interface Suggestions {
  events: EventSummary[]
  venues: string[]
  categorias: string[]
}

export default function SearchBar({
  initialQuery = '',
  placeholder = 'Buscar eventos, artistas, venues...',
  size = 'md',
  className,
  onSearch,
}: SearchBarProps) {
  const [query, setQuery] = useState(initialQuery)
  const [isOpen, setIsOpen] = useState(false)
  const [isMobile, setIsMobile] = useState(false)
  const [loading, setLoading] = useState(false)
  const [suggestions, setSuggestions] = useState<Suggestions>({
    events: [],
    venues: [],
    categorias: [],
  })
  const [history, setHistory] = useState<string[]>([])

  const router = useRouter()
  const inputRef = useRef<HTMLInputElement>(null)
  const mobileInputRef = useRef<HTMLInputElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const debounceRef = useRef<ReturnType<typeof setTimeout>>()

  // ── Effects ───────────────────────────────────────────────────────────────

  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < 640)
    check()
    window.addEventListener('resize', check)
    return () => window.removeEventListener('resize', check)
  }, [])

  useEffect(() => {
    setHistory(getHistory())
  }, [])

  // Lock body scroll when mobile overlay is open
  useEffect(() => {
    if (isMobile && isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => {
      document.body.style.overflow = ''
    }
  }, [isMobile, isOpen])

  // Close on click outside (desktop only)
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setIsOpen(false)
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [])

  // ── Suggestions fetch (debounced) ─────────────────────────────────────────

  const fetchSuggestions = useCallback((q: string) => {
    clearTimeout(debounceRef.current)
    if (q.length < 2) {
      setSuggestions({ events: [], venues: [], categorias: [] })
      setLoading(false)
      return
    }

    setLoading(true)
    debounceRef.current = setTimeout(async () => {
      try {
        const { items } = await eventsApi.list({ q, size: 6 })

        // Unique venues from results
        const venueSet = new Set<string>()
        items.forEach((e) => {
          if (e.venue?.nombre) venueSet.add(e.venue.nombre)
        })

        // Static categories that match the query
        const qLower = q.toLowerCase()
        const matchedCats = CATEGORIAS_LIST.filter((c) =>
          c.toLowerCase().includes(qLower),
        ).slice(0, 3)

        setSuggestions({
          events: items.slice(0, 4),
          venues: Array.from(venueSet).slice(0, 3),
          categorias: matchedCats,
        })
      } catch {
        setSuggestions({ events: [], venues: [], categorias: [] })
      } finally {
        setLoading(false)
      }
    }, 300)
  }, [])

  // ── Handlers ──────────────────────────────────────────────────────────────

  const handleChange = (val: string) => {
    setQuery(val)
    setIsOpen(true)
    fetchSuggestions(val)
  }

  const handleFocus = () => {
    setHistory(getHistory())
    setIsOpen(true)
  }

  const navigate = (q: string) => {
    const parsed = parseNaturalLanguage(q)
    router.push(buildExplorarUrl(q, parsed))
  }

  const commit = (q: string) => {
    if (!q.trim()) return
    saveToHistory(q.trim())
    setHistory(getHistory())
    setIsOpen(false)
    if (onSearch) {
      onSearch(q.trim())
    } else {
      navigate(q.trim())
    }
  }

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault()
    commit(query)
  }

  const handleClear = () => {
    setQuery('')
    setSuggestions({ events: [], venues: [], categorias: [] })
    inputRef.current?.focus()
    mobileInputRef.current?.focus()
    if (onSearch) onSearch('')
  }

  // ── Derived values ────────────────────────────────────────────────────────

  const parsed = query.trim().length >= 2 ? parseNaturalLanguage(query.trim()) : null
  const hasFilters = parsed && (parsed.barrio || parsed.precio || parsed.fecha || parsed.categoria)
  const exploreUrl = query.trim()
    ? buildExplorarUrl(query.trim(), parsed ?? { cleanQuery: query.trim() })
    : '/explorar'

  const showHistory = query.length < 2 && history.length > 0
  const hasSuggestions =
    suggestions.events.length > 0 ||
    suggestions.venues.length > 0 ||
    suggestions.categorias.length > 0
  const showDropdown = isOpen && (showHistory || query.length >= 2)

  const sizeClasses = {
    sm: { input: 'py-2 pl-9 pr-8 text-sm', icon: 'w-4 h-4 left-2.5', btn: 'text-xs px-3 py-1.5' },
    md: { input: 'py-3 pl-11 pr-10 text-base', icon: 'w-5 h-5 left-3.5', btn: 'text-sm px-5 py-3' },
    lg: { input: 'py-4 pl-12 pr-12 text-lg', icon: 'w-6 h-6 left-4', btn: 'text-base px-7 py-4' },
  }
  const sz = sizeClasses[size]

  // ── Shared dropdown content ───────────────────────────────────────────────

  const dropdownContent = (
    <div className="py-1">
      {/* Natural language filter hints */}
      {hasFilters && (
        <div className="px-4 py-2 flex flex-wrap items-center gap-1.5 border-b border-gray-100">
          <span className="text-xs text-gray-400">Detectado:</span>
          {parsed?.barrio && (
            <span className="inline-flex items-center gap-1 text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full">
              <MapPin className="w-3 h-3" />
              {parsed.barrio}
            </span>
          )}
          {parsed?.precio && (
            <span className="text-xs bg-green-50 text-green-700 px-2 py-0.5 rounded-full">
              Gratis
            </span>
          )}
          {parsed?.fecha && (
            <span className="text-xs bg-orange-50 text-orange-700 px-2 py-0.5 rounded-full">
              {parsed.fecha === 'hoy' ? 'Hoy' : parsed.fecha === 'manana' ? 'Mañana' : 'Esta semana'}
            </span>
          )}
          {parsed?.categoria && (
            <span className="inline-flex items-center gap-1 text-xs bg-primary-50 text-primary-700 px-2 py-0.5 rounded-full">
              <Tag className="w-3 h-3" />
              {parsed.categoria}
            </span>
          )}
        </div>
      )}

      {/* "Ver todos los resultados" — shown when query has 2+ chars */}
      {query.length >= 2 && (
        <Link
          href={exploreUrl}
          onClick={() => {
            saveToHistory(query.trim())
            setIsOpen(false)
          }}
          className="flex items-center justify-between px-4 py-2.5 hover:bg-gray-50 transition-colors border-b border-gray-100 group"
        >
          <span className="flex items-center gap-2 text-sm">
            <Search className="w-4 h-4 text-primary-400 shrink-0" />
            <span>
              <span className="text-gray-400">Buscar </span>
              <span className="font-semibold text-secondary-800">"{query}"</span>
            </span>
          </span>
          <span className="flex items-center gap-0.5 text-xs text-primary-500 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap ml-2">
            Ver todos <ChevronRight className="w-3.5 h-3.5" />
          </span>
        </Link>
      )}

      {/* Recent searches */}
      {showHistory && (
        <div>
          <div className="px-4 pt-2 pb-1">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
              Búsquedas recientes
            </span>
          </div>
          {history.map((term) => (
            <button
              key={term}
              onClick={() => commit(term)}
              className="w-full flex items-center gap-3 px-4 py-2 hover:bg-gray-50 transition-colors text-left"
            >
              <Clock className="w-4 h-4 text-gray-300 shrink-0" />
              <span className="text-sm text-gray-700 truncate">{term}</span>
            </button>
          ))}
        </div>
      )}

      {/* Loading */}
      {loading && query.length >= 2 && (
        <div className="flex items-center gap-2 px-4 py-3 text-sm text-gray-400">
          <Loader2 className="w-4 h-4 animate-spin" />
          Buscando sugerencias...
        </div>
      )}

      {/* Events group */}
      {suggestions.events.length > 0 && (
        <div>
          <div className="px-4 pt-2 pb-1">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
              Eventos
            </span>
          </div>
          {suggestions.events.map((event) => (
            <Link
              key={event.id}
              href={`/evento/${event.id}`}
              onClick={() => setIsOpen(false)}
              className="flex items-center gap-3 px-4 py-2 hover:bg-gray-50 transition-colors"
            >
              <div className="w-9 h-9 rounded-lg bg-secondary-100 overflow-hidden shrink-0">
                {event.imagen_url ? (
                  <img src={event.imagen_url} alt="" className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full bg-secondary-200 flex items-center justify-center font-bold text-secondary-400 text-sm">
                    {event.titulo.charAt(0)}
                  </div>
                )}
              </div>
              <div className="min-w-0">
                <p className="text-sm text-secondary-800 font-medium truncate leading-snug">
                  {event.titulo}
                </p>
                {event.venue && (
                  <p className="text-xs text-gray-400 truncate">
                    {event.venue.nombre}
                    {event.venue.barrio ? ` · ${event.venue.barrio}` : ''}
                  </p>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}

      {/* Venues group */}
      {suggestions.venues.length > 0 && (
        <div>
          <div className="px-4 pt-2 pb-1">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
              Lugares
            </span>
          </div>
          {suggestions.venues.map((venue) => (
            <Link
              key={venue}
              href={`/explorar?q=${encodeURIComponent(venue)}`}
              onClick={() => setIsOpen(false)}
              className="flex items-center gap-3 px-4 py-2 hover:bg-gray-50 transition-colors"
            >
              <MapPin className="w-4 h-4 text-gray-300 shrink-0" />
              <span className="text-sm text-gray-700 truncate">{venue}</span>
            </Link>
          ))}
        </div>
      )}

      {/* Categories group */}
      {suggestions.categorias.length > 0 && (
        <div>
          <div className="px-4 pt-2 pb-1">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
              Categorías
            </span>
          </div>
          {suggestions.categorias.map((cat) => (
            <Link
              key={cat}
              href={`/explorar?categoria=${encodeURIComponent(cat)}`}
              onClick={() => setIsOpen(false)}
              className="flex items-center gap-3 px-4 py-2 hover:bg-gray-50 transition-colors"
            >
              <Tag className="w-4 h-4 text-gray-300 shrink-0" />
              <span className="text-sm text-gray-700">{cat}</span>
            </Link>
          ))}
        </div>
      )}

      {/* No results */}
      {query.length >= 2 && !loading && !hasSuggestions && (
        <p className="px-4 py-3 text-sm text-gray-400 text-center">
          Sin sugerencias para &quot;{query}&quot;
        </p>
      )}
    </div>
  )

  // ── Mobile full-screen overlay ────────────────────────────────────────────

  const mobileOverlay = isMobile && isOpen && (
    <div className="fixed inset-0 z-50 bg-white flex flex-col">
      {/* Search header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-100 bg-white">
        <div className="relative flex-1">
          {loading && query.length >= 2 ? (
            <Loader2 className="absolute top-1/2 -translate-y-1/2 left-3 w-5 h-5 text-primary-400 pointer-events-none animate-spin" />
          ) : (
            <Search className="absolute top-1/2 -translate-y-1/2 left-3 w-5 h-5 text-gray-400 pointer-events-none" />
          )}
          <input
            ref={mobileInputRef}
            // eslint-disable-next-line jsx-a11y/no-autofocus
            autoFocus
            type="search"
            value={query}
            onChange={(e) => handleChange(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
            placeholder={placeholder}
            autoComplete="off"
            className="w-full py-2.5 pl-10 pr-8 text-base rounded-xl border border-gray-200 bg-gray-50 font-sans focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent placeholder:text-gray-400"
          />
          {query && (
            <button
              type="button"
              onClick={handleClear}
              className="absolute top-1/2 -translate-y-1/2 right-3 text-gray-400 hover:text-gray-600 transition-colors"
              aria-label="Limpiar"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
        <button
          type="button"
          onClick={() => setIsOpen(false)}
          className="text-sm text-primary-600 font-semibold whitespace-nowrap px-1 py-2"
        >
          Cancelar
        </button>
      </div>

      {/* Scrollable suggestions */}
      <div className="flex-1 overflow-y-auto">{dropdownContent}</div>
    </div>
  )

  // ── Desktop render ────────────────────────────────────────────────────────

  return (
    <>
      {mobileOverlay}

      <div ref={containerRef} className={cn('flex gap-2 relative', className)}>
        <form onSubmit={handleSubmit} className="flex gap-2 flex-1">
          <div className="relative flex-1">
            {loading && query.length >= 2 ? (
              <Loader2
                className={cn(
                  'absolute top-1/2 -translate-y-1/2 text-primary-400 pointer-events-none animate-spin',
                  sz.icon,
                )}
              />
            ) : (
              <Search
                className={cn(
                  'absolute top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none',
                  sz.icon,
                )}
              />
            )}
            <input
              ref={inputRef}
              type="search"
              value={query}
              onChange={(e) => handleChange(e.target.value)}
              onFocus={handleFocus}
              placeholder={placeholder}
              autoComplete="off"
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

        {/* Desktop dropdown */}
        {!isMobile && showDropdown && (
          <div className="absolute top-full left-0 right-0 mt-1.5 bg-white rounded-xl border border-gray-100 shadow-lg z-30 overflow-hidden animate-fade-in max-h-[80vh] overflow-y-auto">
            {dropdownContent}
          </div>
        )}
      </div>
    </>
  )
}
