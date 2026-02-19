'use client'

import { useEffect, useState } from 'react'
import { useParams, notFound } from 'next/navigation'
import { ArrowLeft } from 'lucide-react'
import Link from 'next/link'
import EventDetail from '@/components/events/EventDetail'
import Loading from '@/components/ui/Loading'
import { eventsApi } from '@/lib/api'
import type { EventDetail as EventDetailType } from '@/lib/api'

export default function EventoPage() {
  const { id } = useParams<{ id: string }>()
  const [event, setEvent] = useState<EventDetailType | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    const eventId = Number(id)
    if (isNaN(eventId)) {
      setError(true)
      setLoading(false)
      return
    }

    eventsApi
      .getById(eventId)
      .then(setEvent)
      .catch(() => setError(true))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) {
    return <Loading fullPage text="Cargando evento..." />
  }

  if (error || !event) {
    return (
      <div className="container-custom py-16 text-center">
        <p className="text-5xl mb-4">😕</p>
        <h1 className="font-display text-2xl font-bold text-secondary-800 mb-2">
          Evento no encontrado
        </h1>
        <p className="font-sans text-gray-500 mb-6">
          El evento que buscás no existe o fue removido.
        </p>
        <Link href="/explorar">
          <span className="btn-primary inline-flex items-center gap-2">
            <ArrowLeft className="w-4 h-4" />
            Explorar eventos
          </span>
        </Link>
      </div>
    )
  }

  return (
    <div className="container-custom py-8">
      {/* Breadcrumb */}
      <nav className="mb-6">
        <Link
          href="/explorar"
          className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-primary-600 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Volver a explorar
        </Link>
      </nav>

      <EventDetail event={event} />
    </div>
  )
}
