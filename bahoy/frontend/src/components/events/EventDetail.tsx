'use client'

import { useState, useEffect, useRef } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import {
  Calendar,
  MapPin,
  Tag,
  ExternalLink,
  Heart,
  Share2,
  Copy,
  Check,
  Map,
} from 'lucide-react'
import { formatEventDate, formatPrice } from '@/lib/utils'
import Button from '@/components/ui/Button'
import EventCard from './EventCard'
import type { EventDetail as EventDetailType, EventSummary } from '@/lib/api'

interface EventDetailProps {
  event: EventDetailType
  eventosSimilares?: EventSummary[]
}

export default function EventDetail({ event, eventosSimilares = [] }: EventDetailProps) {
  const [guardado, setGuardado] = useState(false)
  const [showShareMenu, setShowShareMenu] = useState(false)
  const [copiado, setCopiado] = useState(false)
  const shareMenuRef = useRef<HTMLDivElement>(null)

  // Sync saved state from localStorage
  useEffect(() => {
    const guardados: number[] = JSON.parse(localStorage.getItem('eventos_guardados') || '[]')
    setGuardado(guardados.includes(event.id))
  }, [event.id])

  // Close share menu on outside click
  useEffect(() => {
    if (!showShareMenu) return
    const handler = (e: MouseEvent) => {
      if (shareMenuRef.current && !shareMenuRef.current.contains(e.target as Node)) {
        setShowShareMenu(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [showShareMenu])

  const toggleGuardar = () => {
    const guardados: number[] = JSON.parse(localStorage.getItem('eventos_guardados') || '[]')
    if (guardado) {
      localStorage.setItem(
        'eventos_guardados',
        JSON.stringify(guardados.filter((id) => id !== event.id)),
      )
      setGuardado(false)
    } else {
      localStorage.setItem('eventos_guardados', JSON.stringify([...guardados, event.id]))
      setGuardado(true)
    }
  }

  const copiarLink = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href)
      setCopiado(true)
      setShowShareMenu(false)
      setTimeout(() => setCopiado(false), 2500)
    } catch {
      // fallback: select URL from input
    }
  }

  const compartirWhatsApp = () => {
    const text = encodeURIComponent(`${event.titulo}\n${window.location.href}`)
    window.open(`https://wa.me/?text=${text}`, '_blank', 'noopener,noreferrer')
    setShowShareMenu(false)
  }

  // Price label
  const precioLabel = event.es_gratuito
    ? 'Entrada gratuita'
    : event.precio_min != null && event.precio_max != null
      ? `${formatPrice(event.precio_min)} – ${formatPrice(event.precio_max)}`
      : event.precio_min != null
        ? `Desde ${formatPrice(event.precio_min)}`
        : 'Consultar precio'

  // Map URLs
  const direccionCompleta = [
    event.venue?.direccion,
    event.venue?.barrio,
    event.venue?.ciudad ?? (event.venue ? 'Buenos Aires' : undefined),
  ]
    .filter(Boolean)
    .join(', ')

  const mapQuery = direccionCompleta || event.venue?.nombre

  let mapEmbedUrl: string | null = null
  let mapLinkUrl: string | null = null

  if (event.venue?.lat != null && event.venue?.lng != null) {
    const { lat, lng } = event.venue
    mapEmbedUrl = `https://www.openstreetmap.org/export/embed.html?bbox=${lng - 0.005},${lat - 0.005},${lng + 0.005},${lat + 0.005}&layer=mapnik&marker=${lat},${lng}`
    mapLinkUrl = `https://www.google.com/maps/search/?api=1&query=${lat},${lng}`
  } else if (mapQuery) {
    mapEmbedUrl = `https://maps.google.com/maps?q=${encodeURIComponent(mapQuery)}&output=embed`
    mapLinkUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(mapQuery)}`
  }

  return (
    <article className="max-w-5xl mx-auto">
      {/* ── Hero image ────────────────────────────────────────────── */}
      <div className="relative h-72 sm:h-96 md:h-[28rem] bg-secondary-800 rounded-2xl overflow-hidden mb-8">
        {event.imagen_url ? (
          <Image
            src={event.imagen_url}
            alt={event.titulo}
            fill
            sizes="(max-width: 768px) 100vw, 1024px"
            className="object-cover"
            priority
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-secondary-700 to-secondary-900">
            <span className="font-display text-9xl font-bold text-white/20 select-none">
              {event.titulo.charAt(0)}
            </span>
          </div>
        )}
      </div>

      {/* ── Title, meta & actions ─────────────────────────────────── */}
      <div className="mb-8">
        <h1 className="font-display text-3xl sm:text-4xl font-bold text-secondary-800 leading-tight mb-4">
          {event.titulo}
        </h1>

        {/* Meta chips */}
        <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-sm text-gray-600 mb-5">
          {event.categorias && event.categorias.length > 0 && (
            <span className="inline-flex items-center gap-1.5 text-primary-600 font-medium">
              <Tag className="w-4 h-4" />
              {event.categorias[0].nombre}
            </span>
          )}
          {event.venue && (
            <span className="inline-flex items-center gap-1.5">
              <MapPin className="w-4 h-4 text-primary-500" />
              {event.venue.nombre}
              {event.venue.barrio ? `, ${event.venue.barrio}` : ''}
            </span>
          )}
          <span className="inline-flex items-center gap-1.5">
            <Calendar className="w-4 h-4 text-primary-500" />
            {formatEventDate(event.fecha_inicio)}
          </span>
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-3 flex-wrap">
          {/* Save button */}
          <button
            onClick={toggleGuardar}
            aria-label={guardado ? 'Quitar de guardados' : 'Guardar evento'}
            className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg border font-sans text-sm font-medium transition-all duration-200 ${
              guardado
                ? 'bg-primary-50 border-primary-300 text-primary-700'
                : 'bg-white border-gray-200 text-gray-600 hover:border-primary-300 hover:text-primary-600'
            }`}
          >
            <Heart
              className={`w-4 h-4 transition-all ${guardado ? 'fill-primary-500 text-primary-500' : ''}`}
            />
            {guardado ? 'Guardado ✓' : 'Guardar'}
          </button>

          {/* Share button with dropdown */}
          <div className="relative" ref={shareMenuRef}>
            <button
              onClick={() => setShowShareMenu((v) => !v)}
              aria-label="Compartir evento"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-200 bg-white text-gray-600 font-sans text-sm font-medium hover:border-gray-300 transition-all duration-200"
            >
              {copiado ? (
                <>
                  <Check className="w-4 h-4 text-green-500" />
                  <span className="text-green-600">¡Copiado!</span>
                </>
              ) : (
                <>
                  <Share2 className="w-4 h-4" />
                  Compartir
                </>
              )}
            </button>

            {showShareMenu && (
              <div className="absolute left-0 top-full mt-2 w-56 bg-white rounded-xl shadow-lg border border-gray-100 py-1 z-20 animate-fade-in">
                <button
                  onClick={copiarLink}
                  className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  <Copy className="w-4 h-4 text-gray-400" />
                  Copiar enlace
                </button>
                <button
                  onClick={compartirWhatsApp}
                  className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  <svg className="w-4 h-4 text-green-500 shrink-0" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.890-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z" />
                  </svg>
                  Compartir por WhatsApp
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── Main content grid ─────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-12">
        {/* Left: Information */}
        <div className="lg:col-span-2 space-y-6">
          <div>
            <h2 className="font-display text-xl font-semibold text-secondary-700 mb-3 pb-2 border-b border-gray-100">
              Información
            </h2>
            <p className="font-sans text-gray-600 text-base leading-relaxed">
              {event.descripcion}
            </p>
          </div>

          {event.descripcion_larga && (
            <div className="font-sans text-gray-600 text-base leading-relaxed whitespace-pre-line">
              {event.descripcion_larga}
            </div>
          )}
        </div>

        {/* Right: Details sidebar */}
        <aside className="space-y-5">
          <div className="bg-white rounded-xl shadow-card p-5 space-y-4">
            <h2 className="font-display text-xl font-semibold text-secondary-700 pb-2 border-b border-gray-100">
              Detalles
            </h2>

            {/* Fecha y hora */}
            <div className="flex gap-3">
              <Calendar className="w-5 h-5 text-primary-500 shrink-0 mt-0.5" />
              <div>
                <p className="font-sans font-semibold text-secondary-800 text-sm">📅 Fecha y hora</p>
                <p className="font-sans text-gray-600 text-sm mt-0.5">
                  {formatEventDate(event.fecha_inicio)}
                </p>
                {event.fecha_fin && (
                  <p className="font-sans text-gray-500 text-xs mt-0.5">
                    Hasta {formatEventDate(event.fecha_fin)}
                  </p>
                )}
              </div>
            </div>

            {/* Dirección */}
            {event.venue && (
              <div className="flex gap-3">
                <MapPin className="w-5 h-5 text-primary-500 shrink-0 mt-0.5" />
                <div>
                  <p className="font-sans font-semibold text-secondary-800 text-sm">📍 Dirección</p>
                  <p className="font-sans text-gray-700 text-sm mt-0.5">{event.venue.nombre}</p>
                  {event.venue.direccion && (
                    <p className="font-sans text-gray-500 text-xs mt-0.5">{event.venue.direccion}</p>
                  )}
                  {event.venue.barrio && (
                    <p className="font-sans text-gray-400 text-xs">{event.venue.barrio}</p>
                  )}
                </div>
              </div>
            )}

            {/* Precio */}
            <div className="flex gap-3 items-start">
              <span className="w-5 h-5 flex items-center justify-center shrink-0 mt-0.5 text-base leading-none">
                💰
              </span>
              <div>
                <p className="font-sans font-semibold text-secondary-800 text-sm">Precio</p>
                <p
                  className={`font-display font-bold text-base mt-0.5 ${
                    event.es_gratuito ? 'text-green-600' : 'text-secondary-800'
                  }`}
                >
                  {precioLabel}
                </p>
              </div>
            </div>

            {/* Tags from event.tags */}
            {event.tags && event.tags.length > 0 && (
              <div>
                <p className="font-sans font-semibold text-secondary-800 text-sm mb-2">🏷️ Tags</p>
                <div className="flex flex-wrap gap-1.5">
                  {event.tags.map((tag) => (
                    <Link
                      key={tag}
                      href={`/buscar?q=${encodeURIComponent(tag)}`}
                      className="inline-block px-2.5 py-1 bg-gray-100 hover:bg-primary-50 hover:text-primary-700 text-gray-600 text-xs rounded-full transition-colors"
                    >
                      {tag}
                    </Link>
                  ))}
                </div>
              </div>
            )}

            {/* Categorías clickeables */}
            {event.categorias && event.categorias.length > 0 && (
              <div>
                <p className="font-sans font-semibold text-secondary-800 text-sm mb-2 flex items-center gap-1.5">
                  <Tag className="w-3.5 h-3.5 text-primary-400" />
                  Categorías
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {event.categorias.map((cat) => (
                    <Link
                      key={cat.nombre}
                      href={`/explorar?categoria=${encodeURIComponent(cat.nombre)}`}
                      className="inline-block px-2.5 py-1 bg-primary-50 hover:bg-primary-100 text-primary-700 text-xs rounded-full font-medium transition-colors"
                    >
                      {cat.nombre}
                    </Link>
                  ))}
                </div>
              </div>
            )}

            {/* CTAs */}
            {(event.url_entradas || event.url_fuente) && (
              <div className="space-y-2 pt-2 border-t border-gray-100">
                {event.url_entradas && (
                  <a
                    href={event.url_entradas}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block"
                  >
                    <Button variant="primary" className="w-full">
                      <ExternalLink className="w-4 h-4 mr-2" />
                      Comprar entradas
                    </Button>
                  </a>
                )}
                {event.url_fuente && (
                  <a
                    href={event.url_fuente}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block"
                  >
                    <Button variant="outline" size="sm" className="w-full">
                      Ver fuente original
                    </Button>
                  </a>
                )}
              </div>
            )}
          </div>

          {/* Map */}
          {mapEmbedUrl && (
            <div className="bg-white rounded-xl shadow-card overflow-hidden">
              <div className="h-52">
                <iframe
                  src={mapEmbedUrl}
                  width="100%"
                  height="100%"
                  style={{ border: 0 }}
                  allowFullScreen
                  loading="lazy"
                  referrerPolicy="no-referrer-when-downgrade"
                  title={`Mapa: ${event.venue?.nombre ?? 'Lugar del evento'}`}
                />
              </div>
              {mapLinkUrl && (
                <div className="px-4 py-3 border-t border-gray-100">
                  <a
                    href={mapLinkUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 text-sm text-primary-600 hover:text-primary-700 font-medium transition-colors"
                  >
                    <Map className="w-4 h-4" />
                    Ver en Maps
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              )}
            </div>
          )}
        </aside>
      </div>

      {/* ── Eventos similares ─────────────────────────────────────── */}
      {eventosSimilares.length > 0 && (
        <section className="border-t border-gray-100 pt-8">
          <h2 className="font-display text-2xl font-bold text-secondary-800 mb-6">
            Eventos similares
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {eventosSimilares.map((e) => (
              <EventCard key={e.id} event={e} />
            ))}
          </div>
        </section>
      )}
    </article>
  )
}
