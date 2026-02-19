'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'

interface NavItem {
  label: string
  href: string
}

const navItems: NavItem[] = [
  { label: 'Inicio',   href: '/' },
  { label: 'Explorar', href: '/explorar' },
  { label: 'Buscar',   href: '/buscar' },
]

interface NavigationProps {
  mobile?: boolean
  onLinkClick?: () => void
}

export default function Navigation({ mobile = false, onLinkClick }: NavigationProps) {
  const pathname = usePathname()

  if (mobile) {
    return (
      <nav className="flex flex-col gap-1 py-2">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            onClick={onLinkClick}
            className={cn(
              'px-4 py-3 rounded-lg font-medium transition-colors duration-200',
              pathname === item.href
                ? 'bg-primary-50 text-primary-600 font-semibold'
                : 'text-secondary-800 hover:bg-gray-100',
            )}
          >
            {item.label}
          </Link>
        ))}
      </nav>
    )
  }

  return (
    <nav className="hidden md:flex items-center gap-1">
      {navItems.map((item) => (
        <Link
          key={item.href}
          href={item.href}
          className={cn(
            'px-4 py-2 rounded-lg font-medium text-sm transition-colors duration-200',
            pathname === item.href
              ? 'text-primary-600 font-semibold'
              : 'text-secondary-700 hover:text-primary-500 hover:bg-primary-50',
          )}
        >
          {item.label}
        </Link>
      ))}
    </nav>
  )
}
