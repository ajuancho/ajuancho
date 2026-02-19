import Link from 'next/link'
import { MapPin, Mail, Instagram, Twitter } from 'lucide-react'

const links = {
  explorar: [
    { label: 'Teatro',    href: '/explorar?categoria=teatro' },
    { label: 'Música',    href: '/explorar?categoria=musica' },
    { label: 'Arte',      href: '/explorar?categoria=arte' },
    { label: 'Gastronomía', href: '/explorar?categoria=gastronomia' },
    { label: 'Deportes',  href: '/explorar?categoria=deportes' },
  ],
  plataforma: [
    { label: 'Inicio',   href: '/' },
    { label: 'Explorar', href: '/explorar' },
    { label: 'Buscar',   href: '/buscar' },
    { label: 'Mi perfil', href: '/perfil' },
  ],
}

export default function Footer() {
  return (
    <footer className="bg-secondary-800 text-secondary-200 mt-auto">
      <div className="container-custom py-12">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="lg:col-span-2">
            <div className="flex items-center gap-2 mb-3">
              <span className="flex items-center justify-center w-8 h-8 bg-primary-500 rounded-lg text-white font-display font-bold text-lg">
                B
              </span>
              <span className="font-display font-bold text-xl text-white">Bahoy</span>
            </div>
            <p className="text-sm text-secondary-300 mb-4 max-w-xs">
              Tu guía de eventos en Buenos Aires. Descubrí teatro, música, arte, gastronomía y mucho más en la ciudad.
            </p>
            <div className="flex items-center gap-1.5 text-sm text-secondary-400">
              <MapPin className="w-4 h-4 text-primary-400" />
              Ciudad Autónoma de Buenos Aires, Argentina
            </div>
            <div className="flex gap-3 mt-4">
              <a
                href="#"
                className="text-secondary-400 hover:text-primary-400 transition-colors"
                aria-label="Instagram"
              >
                <Instagram className="w-5 h-5" />
              </a>
              <a
                href="#"
                className="text-secondary-400 hover:text-primary-400 transition-colors"
                aria-label="Twitter / X"
              >
                <Twitter className="w-5 h-5" />
              </a>
              <a
                href="mailto:hola@bahoy.com.ar"
                className="text-secondary-400 hover:text-primary-400 transition-colors"
                aria-label="Email"
              >
                <Mail className="w-5 h-5" />
              </a>
            </div>
          </div>

          {/* Explorar */}
          <div>
            <h3 className="font-semibold text-white mb-4 text-sm uppercase tracking-wider">Categorías</h3>
            <ul className="space-y-2">
              {links.explorar.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-sm text-secondary-300 hover:text-primary-300 transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Plataforma */}
          <div>
            <h3 className="font-semibold text-white mb-4 text-sm uppercase tracking-wider">Plataforma</h3>
            <ul className="space-y-2">
              {links.plataforma.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-sm text-secondary-300 hover:text-primary-300 transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="border-t border-secondary-700 mt-10 pt-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-secondary-500">
          <p>&copy; {new Date().getFullYear()} Bahoy. Todos los derechos reservados.</p>
          <p>Hecho con amor en Buenos Aires</p>
        </div>
      </div>
    </footer>
  )
}
