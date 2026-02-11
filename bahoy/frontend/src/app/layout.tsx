/**
 * Bahoy - Layout principal de la aplicación
 * Este componente envuelve todas las páginas de la aplicación.
 */

import type { Metadata } from 'next'
import { Inter, Poppins } from 'next/font/google'
import './globals.css'

// Configurar fuentes de Google
const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
})

const poppins = Poppins({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-poppins',
  display: 'swap',
})

// Metadata de la aplicación para SEO
export const metadata: Metadata = {
  title: 'Bahoy - Encuentra tu hogar ideal',
  description: 'Plataforma inteligente de búsqueda de propiedades con IA',
  keywords: ['propiedades', 'casas', 'apartamentos', 'arriendo', 'venta', 'inmobiliaria'],
  authors: [{ name: 'Equipo Bahoy' }],
  creator: 'Bahoy',
  openGraph: {
    type: 'website',
    locale: 'es_ES',
    url: 'https://bahoy.com',
    title: 'Bahoy - Encuentra tu hogar ideal',
    description: 'Plataforma inteligente de búsqueda de propiedades con IA',
    siteName: 'Bahoy',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Bahoy - Encuentra tu hogar ideal',
    description: 'Plataforma inteligente de búsqueda de propiedades con IA',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="es" className={`${inter.variable} ${poppins.variable}`}>
      <body className="font-sans antialiased bg-gray-50">
        {/* Header - Agregar cuando esté disponible */}
        {/* <Header /> */}

        {/* Contenido principal */}
        <main className="min-h-screen">
          {children}
        </main>

        {/* Footer - Agregar cuando esté disponible */}
        {/* <Footer /> */}
      </body>
    </html>
  )
}
