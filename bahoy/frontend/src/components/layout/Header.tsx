'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Menu, X, User, MapPin } from 'lucide-react'
import Navigation from './Navigation'
import Button from '@/components/ui/Button'

export default function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <header className="bg-secondary-800 text-white shadow-md sticky top-0 z-50">
      <div className="container-custom">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 group">
            <span className="flex items-center justify-center w-8 h-8 bg-primary-500 rounded-lg text-white font-display font-bold text-lg leading-none">
              B
            </span>
            <span className="font-display font-bold text-xl text-white group-hover:text-primary-300 transition-colors">
              Bahoy
            </span>
            <span className="hidden sm:flex items-center gap-1 text-xs text-secondary-300 ml-1">
              <MapPin className="w-3 h-3" />
              Buenos Aires
            </span>
          </Link>

          {/* Desktop nav */}
          <Navigation />

          {/* Desktop actions */}
          <div className="hidden md:flex items-center gap-3">
            <Link href="/buscar">
              <Button variant="outline" size="sm" className="border-white/30 text-white hover:bg-white/10 hover:text-white focus:ring-white/30">
                Buscar
              </Button>
            </Link>
            <Link href="/perfil">
              <button className="flex items-center gap-1.5 text-sm text-secondary-200 hover:text-white transition-colors px-3 py-2 rounded-lg hover:bg-white/10">
                <User className="w-4 h-4" />
                Mi perfil
              </button>
            </Link>
          </div>

          {/* Mobile menu toggle */}
          <button
            className="md:hidden p-2 rounded-lg text-secondary-200 hover:text-white hover:bg-white/10 transition-colors"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Abrir menú"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-secondary-900 border-t border-secondary-700 px-4 pb-4 animate-slide-down">
          <Navigation mobile onLinkClick={() => setMobileMenuOpen(false)} />
          <div className="mt-3 pt-3 border-t border-secondary-700 flex flex-col gap-2">
            <Link href="/buscar" onClick={() => setMobileMenuOpen(false)}>
              <Button variant="outline" size="sm" className="w-full border-white/30 text-white hover:bg-white/10 hover:text-white focus:ring-white/30">
                Buscar eventos
              </Button>
            </Link>
            <Link href="/perfil" onClick={() => setMobileMenuOpen(false)}>
              <button className="w-full flex items-center justify-center gap-2 text-sm text-secondary-200 hover:text-white transition-colors px-3 py-2 rounded-lg hover:bg-white/10">
                <User className="w-4 h-4" />
                Mi perfil
              </button>
            </Link>
          </div>
        </div>
      )}
    </header>
  )
}
