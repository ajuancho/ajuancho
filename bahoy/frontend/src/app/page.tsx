import Link from 'next/link'
import { ArrowRight, Ticket, MapPin, Sparkles } from 'lucide-react'
import SearchBar from '@/components/search/SearchBar'
import Button from '@/components/ui/Button'

const CATEGORIAS_DESTACADAS = [
  { id: 'teatro',      label: 'Teatro',     emoji: '🎭', href: '/explorar?categoria=teatro' },
  { id: 'musica',      label: 'Música',      emoji: '🎵', href: '/explorar?categoria=musica' },
  { id: 'arte',        label: 'Arte',        emoji: '🎨', href: '/explorar?categoria=arte' },
  { id: 'gastronomia', label: 'Gastronomía', emoji: '🍽️', href: '/explorar?categoria=gastronomia' },
  { id: 'danza',       label: 'Danza',       emoji: '💃', href: '/explorar?categoria=danza' },
  { id: 'cine',        label: 'Cine',        emoji: '🎬', href: '/explorar?categoria=cine' },
  { id: 'stand-up',    label: 'Stand-up',    emoji: '🎤', href: '/explorar?categoria=stand-up' },
  { id: 'deportes',    label: 'Deportes',    emoji: '⚽', href: '/explorar?categoria=deportes' },
]

const BARRIOS = [
  'Palermo', 'San Telmo', 'Recoleta', 'Belgrano',
  'Villa Crespo', 'Almagro', 'Boedo', 'Núñez',
]

export default function HomePage() {
  return (
    <div>
      {/* Hero */}
      <section className="bg-secondary-800 text-white py-20 md:py-28">
        <div className="container-custom text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary-500/20 text-primary-300 text-sm font-medium mb-6">
            <Sparkles className="w-4 h-4" />
            La agenda cultural de Buenos Aires
          </div>

          <h1 className="font-display text-4xl sm:text-5xl md:text-6xl font-bold mb-6 leading-tight">
            Descubrí lo mejor
            <br />
            <span className="text-primary-400">de Buenos Aires</span>
          </h1>

          <p className="text-secondary-300 text-lg sm:text-xl mb-10 max-w-xl mx-auto">
            Teatro, música, arte, gastronomía y más. Tu guía completa de eventos en la ciudad.
          </p>

          <div className="max-w-2xl mx-auto mb-6">
            <SearchBar size="lg" placeholder="Buscar eventos, artistas, venues..." />
          </div>

          <div className="flex flex-wrap justify-center gap-2">
            {['Teatro', 'Música gratis', 'Esta semana', 'Palermo'].map((tag) => (
              <Link
                key={tag}
                href={`/buscar?q=${encodeURIComponent(tag)}`}
                className="px-3 py-1.5 bg-white/10 hover:bg-white/20 rounded-full text-sm text-secondary-200 transition-colors"
              >
                {tag}
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Categorías */}
      <section className="py-16 container-custom">
        <div className="flex items-center justify-between mb-8">
          <h2 className="section-title">Explorar por categoría</h2>
          <Link
            href="/explorar"
            className="flex items-center gap-1 text-sm text-primary-500 hover:text-primary-700 font-medium transition-colors"
          >
            Ver todo
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
          {CATEGORIAS_DESTACADAS.map((cat) => (
            <Link
              key={cat.id}
              href={cat.href}
              className="flex flex-col items-center gap-2 p-4 bg-white rounded-xl shadow-card hover:shadow-soft hover:-translate-y-0.5 transition-all duration-200 group"
            >
              <span className="text-3xl">{cat.emoji}</span>
              <span className="text-xs font-semibold text-secondary-700 group-hover:text-primary-600 transition-colors text-center">
                {cat.label}
              </span>
            </Link>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="py-16 bg-white">
        <div className="container-custom">
          <h2 className="section-title text-center mb-12">¿Por qué Bahoy?</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                icon: <Sparkles className="w-8 h-8 text-primary-500" />,
                title: 'Recomendado para vos',
                desc: 'Nuestro sistema aprende tus gustos y te sugiere eventos que te van a gustar.',
              },
              {
                icon: <Ticket className="w-8 h-8 text-primary-500" />,
                title: 'Gratis y con costo',
                desc: 'Encontrá desde entradas gratuitas hasta los mejores shows pagos de la ciudad.',
              },
              {
                icon: <MapPin className="w-8 h-8 text-primary-500" />,
                title: 'Por barrio',
                desc: 'Filtrá eventos cerca tuyo, en tu barrio favorito de Buenos Aires.',
              },
            ].map((f) => (
              <div key={f.title} className="text-center p-6">
                <div className="flex justify-center mb-4">{f.icon}</div>
                <h3 className="font-display text-lg font-semibold text-secondary-800 mb-3">{f.title}</h3>
                <p className="font-sans text-gray-500 text-sm leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Barrios */}
      <section className="py-16 container-custom">
        <h2 className="section-title mb-8">Por barrio</h2>
        <div className="flex flex-wrap gap-3">
          {BARRIOS.map((barrio) => (
            <Link
              key={barrio}
              href={`/explorar?barrio=${encodeURIComponent(barrio)}`}
              className="px-5 py-2.5 border-2 border-secondary-200 text-secondary-700 rounded-full text-sm font-medium hover:border-primary-400 hover:text-primary-600 transition-colors"
            >
              {barrio}
            </Link>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-primary-500">
        <div className="container-custom text-center text-white">
          <h2 className="font-display text-3xl sm:text-4xl font-bold mb-4">
            No te pierdas nada en Buenos Aires
          </h2>
          <p className="text-primary-100 text-lg mb-8 max-w-md mx-auto">
            Explorá el catálogo completo y encontrá tu próximo plan.
          </p>
          <Link href="/explorar">
            <Button
              variant="secondary"
              size="lg"
              className="bg-white text-primary-600 hover:bg-primary-50 focus:ring-white"
            >
              Explorar eventos
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
          </Link>
        </div>
      </section>
    </div>
  )
}
