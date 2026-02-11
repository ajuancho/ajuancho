/**
 * Bahoy - Funciones de utilidad
 * Este archivo contiene funciones auxiliares reutilizables en toda la aplicación.
 */

import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

/**
 * Combina clases de Tailwind CSS de manera inteligente.
 * Usa clsx para concatenar y twMerge para resolver conflictos.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Formatea un número como precio en pesos colombianos.
 * Ejemplo: formatPrice(1000000) => "$1.000.000"
 */
export function formatPrice(price: number): string {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(price)
}

/**
 * Formatea un área en metros cuadrados.
 * Ejemplo: formatArea(120) => "120 m²"
 */
export function formatArea(area: number): string {
  return `${area.toLocaleString('es-CO')} m²`
}

/**
 * Trunca un texto a una longitud específica.
 * Ejemplo: truncate("Texto largo", 10) => "Texto la..."
 */
export function truncate(text: string, length: number): string {
  if (text.length <= length) return text
  return text.slice(0, length) + '...'
}
