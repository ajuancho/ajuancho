import EventCard from './EventCard'
import { SkeletonCard } from '@/components/ui/Loading'
import type { EventSummary } from '@/lib/api'

interface EventGridProps {
  events: EventSummary[]
  loading?: boolean
  emptyMessage?: string
}

export default function EventGrid({
  events,
  loading = false,
  emptyMessage = 'No se encontraron eventos.',
}: EventGridProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {Array.from({ length: 8 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    )
  }

  if (events.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <div className="text-5xl mb-4">🎭</div>
        <p className="font-display text-xl font-semibold text-secondary-700 mb-2">Sin resultados</p>
        <p className="text-gray-500 text-sm max-w-xs">{emptyMessage}</p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {events.map((event) => (
        <EventCard key={event.id} event={event} />
      ))}
    </div>
  )
}
