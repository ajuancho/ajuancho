'use client'

import { useState, useEffect, useRef } from 'react'
import Link from 'next/link'
import { ArrowRight, MapPin, ChevronLeft, ChevronRight } from 'lucide-react'
import SearchBar from '@/components/search/SearchBar'
import EventCard from '@/components/events/EventCard'
import { eventsApi, type EventSummary } from '@/lib/api'
import { SkeletonCard } from '@/components/ui/Loading'

// ─── Static data ─────────────────────────────────────────────────────────────

const CATEGORIAS_RAPIDAS = [
  { id: 'teatro',       label: 'Teatro',       emoji: '🎭', href: '/explorar?categoria=teatro' },
  { id: 'musica',       label: 'Música',        emoji: '🎵', href: '/explorar?categoria=musica' },
  { id: 'gastronomia',  label: 'Gastronomía',   emoji: '🍷', href: '/explorar?categoria=gastronomia' },
  { id: 'exposiciones', label: 'Exposiciones',  emoji: '🎨', href: '/explorar?categoria=exposiciones' },
  { id: 'danza',        label: 'Danza',         emoji: '💃', href: '/explorar?categoria=danza' },
  { id: 'cine',         label: 'Cine',          emoji: '🎬', href: '/explorar?categoria=cine' },
  { id: 'stand-up',     label: 'Stand-up',      emoji: '🎤', href: '/explorar?categoria=stand-up' },
  { id: 'deportes',     label: 'Deportes',      emoji: '⚽', href: '/explorar?categoria=deportes' },
]

// ─── Sub-components ───────────────────────────────────────────────────────────

interface SectionHeaderProps {
  title: string
  href?: string
}

function SectionHeader({ title, href }: SectionHeaderProps) {
  return (
    <div className="flex items-center justify-between mb-6">
      <h2 className="section-title">{title}</h2>
      {href && (
        <Link
          href={href}
          className="flex items-center gap-1 text-sm text-primary-500 hover:text-primary-700 font-medium transition-colors shrink-0 ml-4"
        >
          Ver más
          <ArrowRight className="w-4 h-4" />
        </Link>
      )}
    </div>
  )
}

interface EventCarouselProps {
  events: EventSummary[]
  loading: boolean
}

function EventCarousel({ events, loading }: EventCarouselProps) {
  const scrollRef = useRef<HTMLDivElement>(null)

  const scroll = (dir: 'left' | 'right') => {
    scrollRef.current?.scrollBy({ left: dir === 'right' ? 296 : -296, behavior: 'smooth' })
  }

  if (loading) {
    return (
      <div className="flex gap-4 overflow-hidden">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="w-72 shrink-0">
            <SkeletonCard />
          </div>
        ))}
      </div>
    )
  }

  if (!events.length) return null

  return (
    <div className="relative group">
      {/* Left scroll button */}
      <button
        onClick={() => scroll('left')}
        aria-label="Anterior"
        className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-5 z-10 hidden md:flex items-center justify-center w-10 h-10 bg-white rounded-full shadow-card opacity-0 group-hover:opacity-100 hover:shadow-soft transition-all duration-200"
      >
        <ChevronLeft className="w-5 h-5 text-secondary-700" />
      </button>

      {/* Scrollable cards */}
      <div
        ref={scrollRef}
        className="flex gap-4 overflow-x-auto pb-2"
        style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
      >
        {events.map((event) => (
          <div key={event.id} className="w-72 shrink-0">
            <EventCard event={event} className="h-full" />
          </div>
        ))}
      </div>

      {/* Right scroll button */}
      <button
        onClick={() => scroll('right')}
        aria-label="Siguiente"
        className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-5 z-10 hidden md:flex items-center justify-center w-10 h-10 bg-white rounded-full shadow-card opacity-0 group-hover:opacity-100 hover:shadow-soft transition-all duration-200"
      >
        <ChevronRight className="w-5 h-5 text-secondary-700" />
      </button>
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function HomePage() {
  const [popularEvents, setPopularEvents]   = useState<EventSummary[]>([])
  const [semanaEvents,  setSemanaEvents]    = useState<EventSummary[]>([])
  const [gratisEvents,  setGratisEvents]    = useState<EventSummary[]>([])
  const [loadingPopular, setLoadingPopular] = useState(true)
  const [loadingSemana,  setLoadingSemana]  = useState(true)
  const [loadingGratis,  setLoadingGratis]  = useState(true)

  useEffect(() => {
    eventsApi.list({ size: 8 })
      .then((res) => setPopularEvents(res.items))
      .catch(() => {})
      .finally(() => setLoadingPopular(false))

    eventsApi.list({ fecha: 'semana', size: 6 })
      .then((res) => setSemanaEvents(res.items))
      .catch(() => {})
      .finally(() => setLoadingSemana(false))

    eventsApi.list({ precio: 'gratis', size: 8 })
      .then((res) => setGratisEvents(res.items))
      .catch(() => {})
      .finally(() => setLoadingGratis(false))
  }, [])

  return (
    <div>

      {/* ── 1. HERO ─────────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden bg-secondary-900 text-white py-24 md:py-36">

        {/* Background – Buenos Aires image placeholder with gradient */}
        <div
          aria-hidden
          className="absolute inset-0 bg-gradient-to-br from-secondary-950 via-secondary-800 to-primary-950"
        />
        {/* Decorative glows */}
        <div aria-hidden className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-[28rem] h-[28rem] rounded-full bg-primary-500/10 blur-3xl" />
          <div className="absolute top-1/2 left-1/4 w-64 h-64 rounded-full bg-primary-600/5 blur-2xl" />
          <div className="absolute -bottom-40 -left-40 w-[28rem] h-[28rem] rounded-full bg-secondary-400/10 blur-3xl" />
        </div>

        <div className="relative container-custom text-center">
          <p className="text-primary-300 text-xs font-bold uppercase tracking-[0.2em] mb-5">
            Buenos Aires · Agenda cultural
          </p>

          <h1 className="font-display text-5xl sm:text-6xl md:text-7xl font-bold mb-5 leading-tight">
            Descubrí Buenos Aires
            <br />
            <span className="text-primary-400">Hoy</span>
          </h1>

          <p className="text-secondary-300 text-lg sm:text-xl mb-10 max-w-lg mx-auto leading-relaxed">
            Tu guía personalizada de cultura, gastronomía y ocio
          </p>

          {/* Prominent search bar */}
          <div className="max-w-2xl mx-auto mb-8 rounded-xl overflow-hidden shadow-2xl">
            <SearchBar size="lg" placeholder="Buscar eventos, artistas, lugares..." />
          </div>

          {/* Quick-search tags */}
          <div className="flex flex-wrap justify-center gap-2">
            {['Teatro hoy', 'Música gratis', 'Exposiciones', 'Esta semana'].map((tag) => (
              <Link
                key={tag}
                href={`/buscar?q=${encodeURIComponent(tag)}`}
                className="px-4 py-2 bg-white/10 hover:bg-white/20 border border-white/10 hover:border-white/25 rounded-full text-sm text-secondary-200 transition-colors"
              >
                {tag}
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* ── 2. CATEGORÍAS RÁPIDAS ────────────────────────────────────────── */}
      <section className="py-12 container-custom">
        <SectionHeader title="¿Qué querés hacer?" href="/explorar" />

        <div className="grid grid-cols-4 lg:grid-cols-8 gap-3">
          {CATEGORIAS_RAPIDAS.map((cat) => (
            <Link
              key={cat.id}
              href={cat.href}
              className="flex flex-col items-center gap-2 p-3 sm:p-4 bg-white rounded-xl shadow-card hover:shadow-soft hover:-translate-y-1 transition-all duration-200 group"
            >
              <span className="text-2xl sm:text-3xl">{cat.emoji}</span>
              <span className="text-[11px] sm:text-xs font-semibold text-secondary-700 group-hover:text-primary-600 transition-colors text-center leading-tight">
                {cat.label}
              </span>
            </Link>
          ))}
        </div>
      </section>

      {/* ── 3. PARA TI HOY ──────────────────────────────────────────────── */}
      <section className="py-12 bg-white">
        <div className="container-custom">
          <SectionHeader title="Para vos hoy" href="/explorar" />
          <p className="text-sm text-gray-500 -mt-4 mb-6">
            Eventos populares en Buenos Aires
          </p>
          <EventCarousel events={popularEvents} loading={loadingPopular} />
        </div>
      </section>

      {/* ── 4. ESTA SEMANA ──────────────────────────────────────────────── */}
      <section className="py-12 container-custom">
        <SectionHeader title="Esta semana en BA" href="/explorar?fecha=semana" />

        {loadingSemana ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)}
          </div>
        ) : semanaEvents.length === 0 ? (
          <div className="flex flex-col items-center py-16 text-center">
            <span className="text-4xl mb-3">📅</span>
            <p className="text-gray-500 text-sm">No hay eventos cargados para esta semana todavía.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {semanaEvents.map((event) => (
              <EventCard key={event.id} event={event} />
            ))}
          </div>
        )}
      </section>

      {/* ── 5. GRATIS EN BA ─────────────────────────────────────────────── */}
      <section className="py-12 bg-emerald-50">
        <div className="container-custom">
          <SectionHeader title="🎁 Gratis en BA" href="/explorar?precio=gratis" />
          <p className="text-sm text-gray-500 -mt-4 mb-6">
            Los mejores eventos gratuitos de la ciudad
          </p>
          <EventCarousel events={gratisEvents} loading={loadingGratis} />
        </div>
      </section>

      {/* ── 6. CERCA DE VOS (futuro) ─────────────────────────────────────── */}
      <section className="py-12 container-custom">
        <SectionHeader title="Cerca de vos" />

        <div className="rounded-2xl border-2 border-dashed border-secondary-200 bg-white p-10 sm:p-16 text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-secondary-100 mb-5">
            <MapPin className="w-7 h-7 text-secondary-400" />
          </div>
          <h3 className="font-display text-xl font-semibold text-secondary-700 mb-3">
            Eventos cerca de tu barrio
          </h3>
          <p className="text-sm text-gray-500 mb-6 max-w-sm mx-auto">
            Activá tu ubicación para descubrir eventos que están pasando cerca tuyo ahora mismo.
          </p>
          <button
            className="btn-outline inline-flex items-center gap-2 text-sm"
            onClick={() => {/* geolocation – próximamente */}}
          >
            <MapPin className="w-4 h-4" />
            Activar ubicación
          </button>
          <p className="text-xs text-gray-400 mt-3">Próximamente disponible</p>
        </div>
      </section>

    </div>
  )
}
