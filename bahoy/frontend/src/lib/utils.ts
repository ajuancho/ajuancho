import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

/**
 * Combina clases de Tailwind CSS de manera inteligente.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Formatea un precio en pesos argentinos.
 * Ejemplo: formatPrice(5000) => "$5.000"
 */
export function formatPrice(price: number): string {
  return new Intl.NumberFormat('es-AR', {
    style: 'currency',
    currency: 'ARS',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(price)
}

/**
 * Formatea una fecha ISO para mostrar en eventos.
 * Ejemplo: "2024-03-15T20:00:00" => "vie 15 mar · 20:00"
 */
export function formatEventDate(isoDate: string): string {
  const date = new Date(isoDate)
  return (
    date.toLocaleDateString('es-AR', {
      weekday: 'short',
      day: 'numeric',
      month: 'short',
    }) +
    ' · ' +
    date.toLocaleTimeString('es-AR', {
      hour: '2-digit',
      minute: '2-digit',
    })
  )
}

/**
 * Formatea una fecha corta.
 * Ejemplo: "2024-03-15T20:00:00" => "15 mar 2024"
 */
export function formatShortDate(isoDate: string): string {
  return new Date(isoDate).toLocaleDateString('es-AR', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

/**
 * Trunca un texto a una longitud específica.
 */
export function truncate(text: string, length: number): string {
  if (text.length <= length) return text
  return text.slice(0, length) + '...'
}

/**
 * Normaliza una cadena para búsqueda (minúsculas, sin tildes).
 */
export function normalizeForSearch(text: string): string {
  return text
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
}

/**
 * Devuelve true si la fecha es hoy o en el futuro.
 */
export function isUpcoming(isoDate: string): boolean {
  const date = new Date(isoDate)
  const now = new Date()
  now.setHours(0, 0, 0, 0)
  return date >= now
}
