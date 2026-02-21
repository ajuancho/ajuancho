import Link from 'next/link'
import Image from 'next/image'
import { Calendar, MapPin, Tag } from 'lucide-react'
import { cn, formatEventDate, formatPrice } from '@/lib/utils'
import type { EventSummary } from '@/lib/api'

interface EventCardProps {
  event: EventSummary
  className?: string
}

export default function EventCard({ event, className }: EventCardProps) {
  const categoria = event.categorias?.[0]?.nombre
  const precioLabel = event.es_gratuito
    ? 'Gratis'
    : event.precio_min != null
      ? formatPrice(event.precio_min)
      : null

  return (
    <Link href={`/evento/${event.id}`} className={cn('group block', className)}>
      <article className="bg-white rounded-xl shadow-card overflow-hidden h-full flex flex-col hover:shadow-soft transition-shadow duration-200">
        {/* Image */}
        <div className="relative h-48 bg-secondary-100 overflow-hidden">
          {event.imagen_url ? (
            <Image
              src={event.imagen_url}
              alt={event.titulo}
              fill
              sizes="(max-width: 640px) 100vw, 288px"
              className="object-cover group-hover:scale-105 transition-transform duration-300"
            />
          ) : (
            <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-secondary-700 to-secondary-900">
              <span className="font-display text-4xl font-bold text-white/20 select-none">
                {event.titulo.charAt(0)}
              </span>
            </div>
          )}

          {/* Categoría badge */}
          {categoria && (
            <span className="absolute top-3 left-3 inline-flex items-center gap-1 px-2.5 py-1 bg-primary-500 text-white text-xs font-semibold rounded-full">
              <Tag className="w-3 h-3" />
              {categoria}
            </span>
          )}

          {/* Precio badge */}
          {precioLabel && (
            <span
              className={cn(
                'absolute top-3 right-3 px-2.5 py-1 text-xs font-bold rounded-full',
                event.es_gratuito
                  ? 'bg-green-500 text-white'
                  : 'bg-white text-secondary-800',
              )}
            >
              {precioLabel}
            </span>
          )}
        </div>

        {/* Content */}
        <div className="flex flex-col flex-1 p-5 gap-3">
          <h3 className="font-display font-semibold text-secondary-800 text-lg leading-snug line-clamp-2 group-hover:text-primary-600 transition-colors">
            {event.titulo}
          </h3>

          <p className="font-sans text-sm text-gray-500 line-clamp-2 flex-1">
            {event.descripcion}
          </p>

          <div className="space-y-1.5 mt-auto">
            <div className="flex items-center gap-1.5 text-xs text-gray-500">
              <Calendar className="w-3.5 h-3.5 text-primary-400 shrink-0" />
              <span>{formatEventDate(event.fecha_inicio)}</span>
            </div>

            {event.venue && (
              <div className="flex items-center gap-1.5 text-xs text-gray-500">
                <MapPin className="w-3.5 h-3.5 text-primary-400 shrink-0" />
                <span className="truncate">
                  {event.venue.nombre}
                  {event.venue.barrio && `, ${event.venue.barrio}`}
                </span>
              </div>
            )}
          </div>
        </div>
      </article>
    </Link>
  )
}
