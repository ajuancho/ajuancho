import type { Metadata } from 'next'
import Link from 'next/link'
import { ChevronRight, Home, ArrowLeft } from 'lucide-react'
import { eventsApi } from '@/lib/api'
import EventDetail from '@/components/events/EventDetail'

type Props = {
  params: { id: string }
}

// ─── Dynamic SEO metadata ────────────────────────────────────────────────────

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const id = Number(params.id)
  if (isNaN(id)) return { title: 'Evento no encontrado' }

  try {
    const event = await eventsApi.getById(id)
    return {
      title: event.titulo,
      description: event.descripcion,
      openGraph: {
        title: `${event.titulo} | Bahoy`,
        description: event.descripcion,
        images: event.imagen_url
          ? [{ url: event.imagen_url, width: 1200, height: 630, alt: event.titulo }]
          : [],
        type: 'article',
        locale: 'es_AR',
        siteName: 'Bahoy',
      },
      twitter: {
        card: 'summary_large_image',
        title: event.titulo,
        description: event.descripcion,
        images: event.imagen_url ? [event.imagen_url] : [],
      },
    }
  } catch {
    return { title: 'Evento | Bahoy' }
  }
}

// ─── Page ────────────────────────────────────────────────────────────────────

export default async function EventoPage({ params }: Props) {
  const id = Number(params.id)
  if (isNaN(id)) return <EventoNoEncontrado />

  let event
  try {
    event = await eventsApi.getById(id)
  } catch {
    return <EventoNoEncontrado />
  }

  // Fetch similar events by same category (best-effort)
  let eventosSimilares = []
  try {
    const categoria = event.categorias?.[0]?.nombre
    const { items } = await eventsApi.list({
      categorias: categoria ? [categoria] : undefined,
      size: 5,
    })
    eventosSimilares = items.filter((e) => e.id !== event.id).slice(0, 4)
  } catch {
    // silently ignore — section simply won't render
  }

  const categoria = event.categorias?.[0]?.nombre

  return (
    <div className="container-custom py-8">
      {/* ── Breadcrumb ───────────────────────────────────────────── */}
      <nav aria-label="Breadcrumb" className="mb-6">
        <ol className="flex items-center gap-1.5 text-sm text-gray-500 flex-wrap">
          <li>
            <Link
              href="/"
              className="inline-flex items-center gap-1 hover:text-primary-600 transition-colors"
            >
              <Home className="w-3.5 h-3.5" />
              Inicio
            </Link>
          </li>
          <li aria-hidden>
            <ChevronRight className="w-3.5 h-3.5 text-gray-300" />
          </li>
          {categoria ? (
            <>
              <li>
                <Link
                  href={`/explorar?categoria=${encodeURIComponent(categoria)}`}
                  className="capitalize hover:text-primary-600 transition-colors"
                >
                  {categoria}
                </Link>
              </li>
              <li aria-hidden>
                <ChevronRight className="w-3.5 h-3.5 text-gray-300" />
              </li>
            </>
          ) : (
            <>
              <li>
                <Link href="/explorar" className="hover:text-primary-600 transition-colors">
                  Explorar
                </Link>
              </li>
              <li aria-hidden>
                <ChevronRight className="w-3.5 h-3.5 text-gray-300" />
              </li>
            </>
          )}
          <li
            aria-current="page"
            className="text-secondary-800 font-medium truncate max-w-[180px] sm:max-w-xs"
            title={event.titulo}
          >
            {event.titulo}
          </li>
        </ol>
      </nav>

      <EventDetail event={event} eventosSimilares={eventosSimilares} />
    </div>
  )
}

// ─── 404 / error state ───────────────────────────────────────────────────────

function EventoNoEncontrado() {
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
