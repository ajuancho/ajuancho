import Link from 'next/link'
import { Calendar, MapPin, Tag } from 'lucide-react'
import { cn, formatEventDate, formatPrice } from '@/lib/utils'
import type { EventSummary } from '@/lib/api'

interface EventListProps {
  events: EventSummary[]
  loading?: boolean
  emptyMessage?: string
}

export default function EventList({
  events,
  loading = false,
  emptyMessage = 'No se encontraron eventos.',
}: EventListProps) {
  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <div
            key={i}
            className="bg-white rounded-xl shadow-card p-4 flex gap-4 animate-pulse"
          >
            <div className="w-36 sm:w-48 h-28 bg-gray-200 rounded-lg shrink-0" />
            <div className="flex-1 space-y-2 py-1">
              <div className="h-5 bg-gray-200 rounded w-3/4" />
              <div className="h-4 bg-gray-200 rounded w-full" />
              <div className="h-4 bg-gray-200 rounded w-2/3" />
              <div className="h-3 bg-gray-200 rounded w-1/2 mt-4" />
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (events.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <div className="text-5xl mb-4">🎭</div>
        <p className="font-display text-xl font-semibold text-secondary-700 mb-2">
          Sin resultados
        </p>
        <p className="text-gray-500 text-sm max-w-xs">{emptyMessage}</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {events.map((event) => {
        const categoria = event.categorias?.[0]?.nombre
        const precioLabel = event.es_gratuito
          ? 'Gratis'
          : event.precio_min != null
            ? formatPrice(event.precio_min)
            : null

        return (
          <Link key={event.id} href={`/evento/${event.id}`} className="group block">
            <article className="bg-white rounded-xl shadow-card overflow-hidden flex hover:shadow-soft transition-shadow duration-200">
              {/* Image */}
              <div className="relative w-36 sm:w-48 shrink-0 bg-secondary-100 overflow-hidden min-h-[7rem]">
                {event.imagen_url ? (
                  <img
                    src={event.imagen_url}
                    alt={event.titulo}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  />
                ) : (
                  <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-secondary-700 to-secondary-900">
                    <span className="font-display text-3xl font-bold text-white/20 select-none">
                      {event.titulo.charAt(0)}
                    </span>
                  </div>
                )}
              </div>

              {/* Content */}
              <div className="flex flex-col flex-1 p-4 gap-2 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <h3 className="font-display font-semibold text-secondary-800 text-base leading-snug line-clamp-2 group-hover:text-primary-600 transition-colors">
                    {event.titulo}
                  </h3>
                  {precioLabel && (
                    <span
                      className={cn(
                        'shrink-0 px-2.5 py-1 text-xs font-bold rounded-full',
                        event.es_gratuito
                          ? 'bg-green-100 text-green-700'
                          : 'bg-gray-100 text-gray-700',
                      )}
                    >
                      {precioLabel}
                    </span>
                  )}
                </div>

                <p className="font-sans text-sm text-gray-500 line-clamp-2 flex-1">
                  {event.descripcion}
                </p>

                <div className="flex flex-wrap items-center gap-3 mt-auto">
                  {categoria && (
                    <span className="inline-flex items-center gap-1 text-xs text-primary-600 font-medium">
                      <Tag className="w-3 h-3" />
                      {categoria}
                    </span>
                  )}
                  <span className="flex items-center gap-1 text-xs text-gray-500">
                    <Calendar className="w-3.5 h-3.5 text-primary-400 shrink-0" />
                    {formatEventDate(event.fecha_inicio)}
                  </span>
                  {event.venue && (
                    <span className="flex items-center gap-1 text-xs text-gray-500 min-w-0">
                      <MapPin className="w-3.5 h-3.5 text-primary-400 shrink-0" />
                      <span className="truncate">
                        {event.venue.nombre}
                        {event.venue.barrio && `, ${event.venue.barrio}`}
                      </span>
                    </span>
                  )}
                </div>
              </div>
            </article>
          </Link>
        )
      })}
    </div>
  )
}
