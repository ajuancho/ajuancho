import { Calendar, MapPin, Tag, ExternalLink, Clock } from 'lucide-react'
import { formatEventDate, formatPrice } from '@/lib/utils'
import Button from '@/components/ui/Button'
import type { Event } from './EventCard'

interface EventDetailProps {
  event: Event & {
    descripcion_larga?: string
    url_entradas?: string
    url_fuente?: string
    fecha_fin?: string
    venue?: {
      nombre: string
      direccion?: string
      barrio?: string
      ciudad?: string
    }
  }
}

export default function EventDetail({ event }: EventDetailProps) {
  const precioLabel = event.es_gratuito
    ? 'Entrada gratuita'
    : event.precio_min != null && event.precio_max != null
      ? `${formatPrice(event.precio_min)} – ${formatPrice(event.precio_max)}`
      : event.precio_min != null
        ? `Desde ${formatPrice(event.precio_min)}`
        : 'Consultar precio'

  return (
    <article className="max-w-4xl mx-auto">
      {/* Hero image */}
      <div className="relative h-64 sm:h-80 md:h-96 bg-secondary-800 rounded-2xl overflow-hidden mb-8">
        {event.imagen_url ? (
          <img
            src={event.imagen_url}
            alt={event.titulo}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-secondary-700 to-secondary-900">
            <span className="font-display text-8xl font-bold text-white/20 select-none">
              {event.titulo.charAt(0)}
            </span>
          </div>
        )}

        {/* Categorías overlay */}
        {event.categorias && event.categorias.length > 0 && (
          <div className="absolute bottom-4 left-4 flex flex-wrap gap-2">
            {event.categorias.map((cat) => (
              <span
                key={cat.nombre}
                className="inline-flex items-center gap-1 px-3 py-1 bg-primary-500 text-white text-xs font-semibold rounded-full"
              >
                <Tag className="w-3 h-3" />
                {cat.nombre}
              </span>
            ))}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main content */}
        <div className="lg:col-span-2 space-y-6">
          <div>
            <h1 className="font-display text-3xl sm:text-4xl font-bold text-secondary-800 leading-tight mb-3">
              {event.titulo}
            </h1>
            <p className="font-sans text-gray-600 text-lg leading-relaxed">
              {event.descripcion}
            </p>
          </div>

          {event.descripcion_larga && (
            <div>
              <h2 className="font-display text-xl font-semibold text-secondary-700 mb-3">Sobre el evento</h2>
              <div className="prose prose-gray max-w-none font-sans text-gray-600 leading-relaxed whitespace-pre-line">
                {event.descripcion_larga}
              </div>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <aside className="space-y-4">
          <div className="bg-white rounded-xl shadow-card p-6 space-y-4">
            {/* Fecha */}
            <div className="flex gap-3">
              <Calendar className="w-5 h-5 text-primary-500 shrink-0 mt-0.5" />
              <div>
                <p className="font-sans font-semibold text-secondary-800 text-sm">Fecha</p>
                <p className="font-sans text-gray-600 text-sm">{formatEventDate(event.fecha_inicio)}</p>
                {event.fecha_fin && (
                  <p className="font-sans text-gray-500 text-xs mt-0.5">
                    hasta {formatEventDate(event.fecha_fin)}
                  </p>
                )}
              </div>
            </div>

            {/* Horario */}
            <div className="flex gap-3">
              <Clock className="w-5 h-5 text-primary-500 shrink-0 mt-0.5" />
              <div>
                <p className="font-sans font-semibold text-secondary-800 text-sm">Horario</p>
                <p className="font-sans text-gray-600 text-sm">
                  {new Date(event.fecha_inicio).toLocaleTimeString('es-AR', {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </p>
              </div>
            </div>

            {/* Lugar */}
            {event.venue && (
              <div className="flex gap-3">
                <MapPin className="w-5 h-5 text-primary-500 shrink-0 mt-0.5" />
                <div>
                  <p className="font-sans font-semibold text-secondary-800 text-sm">{event.venue.nombre}</p>
                  {event.venue.direccion && (
                    <p className="font-sans text-gray-500 text-xs">{event.venue.direccion}</p>
                  )}
                  {event.venue.barrio && (
                    <p className="font-sans text-gray-500 text-xs">{event.venue.barrio}</p>
                  )}
                </div>
              </div>
            )}

            {/* Precio */}
            <div className="border-t border-gray-100 pt-4">
              <p className="font-sans text-xs text-gray-500 uppercase tracking-wide mb-1">Precio</p>
              <p
                className={
                  event.es_gratuito
                    ? 'font-display font-bold text-green-600 text-lg'
                    : 'font-display font-bold text-secondary-800 text-lg'
                }
              >
                {precioLabel}
              </p>
            </div>

            {/* CTAs */}
            <div className="space-y-2 pt-2">
              {event.url_entradas && (
                <a href={event.url_entradas} target="_blank" rel="noopener noreferrer" className="block">
                  <Button variant="primary" className="w-full">
                    <ExternalLink className="w-4 h-4 mr-2" />
                    Comprar entradas
                  </Button>
                </a>
              )}
              {event.url_fuente && (
                <a href={event.url_fuente} target="_blank" rel="noopener noreferrer" className="block">
                  <Button variant="outline" size="sm" className="w-full">
                    Ver fuente original
                  </Button>
                </a>
              )}
            </div>
          </div>
        </aside>
      </div>
    </article>
  )
}
