'use client'

import { useState, useEffect, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import SearchBar from '@/components/search/SearchBar'
import EventGrid from '@/components/events/EventGrid'
import { eventsApi, type EventSummary } from '@/lib/api'

function BuscarContent() {
  const searchParams = useSearchParams()
  const [query, setQuery] = useState(searchParams.get('q') ?? '')
  const [events, setEvents] = useState<EventSummary[]>([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)

  const runSearch = (q: string) => {
    setQuery(q)
    if (!q.trim()) {
      setEvents([])
      setSearched(false)
      return
    }

    setLoading(true)
    setSearched(true)
    eventsApi
      .search(q, { size: 24 })
      .then((res) => setEvents(res.items))
      .catch(() => setEvents([]))
      .finally(() => setLoading(false))
  }

  // Run initial search from URL param
  useEffect(() => {
    const q = searchParams.get('q')
    if (q) runSearch(q)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="container-custom py-8">
      <h1 className="font-display text-3xl font-bold text-secondary-800 mb-6">Buscar eventos</h1>

      <div className="max-w-2xl mb-8">
        <SearchBar
          initialQuery={query}
          placeholder="Teatro, música, stand-up, tango..."
          size="lg"
          onSearch={runSearch}
        />
      </div>

      {!searched && !loading && (
        <div className="py-12 text-center">
          <p className="text-5xl mb-4">🔍</p>
          <p className="font-display text-xl font-semibold text-secondary-700 mb-2">
            ¿Qué evento buscás?
          </p>
          <p className="font-sans text-gray-400 text-sm">
            Ingresá un término para empezar a buscar eventos en Buenos Aires.
          </p>
        </div>
      )}

      {searched && (
        <>
          {!loading && (
            <p className="font-sans text-sm text-gray-500 mb-4">
              {events.length > 0
                ? `${events.length} resultados para "${query}"`
                : `Sin resultados para "${query}"`}
            </p>
          )}
          <EventGrid
            events={events}
            loading={loading}
            emptyMessage={`No encontramos eventos para "${query}". Probá con otra búsqueda.`}
          />
        </>
      )}
    </div>
  )
}

export default function BuscarPage() {
  return (
    <Suspense>
      <BuscarContent />
    </Suspense>
  )
}
