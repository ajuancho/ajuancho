import type { Metadata } from 'next'
import { Inter, Playfair_Display } from 'next/font/google'
import './globals.css'
import Header from '@/components/layout/Header'
import Footer from '@/components/layout/Footer'

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
})

const playfair = Playfair_Display({
  subsets: ['latin'],
  variable: '--font-playfair',
  display: 'swap',
})

export const metadata: Metadata = {
  title: {
    default: 'Bahoy - Eventos en Buenos Aires',
    template: '%s | Bahoy',
  },
  description: 'Descubrí los mejores eventos culturales, musicales y de entretenimiento en Buenos Aires.',
  keywords: ['eventos', 'buenos aires', 'teatro', 'música', 'cultura', 'entretenimiento', 'agenda'],
  authors: [{ name: 'Equipo Bahoy' }],
  creator: 'Bahoy',
  openGraph: {
    type: 'website',
    locale: 'es_AR',
    url: 'https://bahoy.com.ar',
    title: 'Bahoy - Eventos en Buenos Aires',
    description: 'Descubrí los mejores eventos culturales, musicales y de entretenimiento en Buenos Aires.',
    siteName: 'Bahoy',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Bahoy - Eventos en Buenos Aires',
    description: 'Descubrí los mejores eventos culturales, musicales y de entretenimiento en Buenos Aires.',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="es-AR" className={`${inter.variable} ${playfair.variable}`}>
      <body className="font-sans antialiased bg-accent flex flex-col min-h-screen">
        <Header />
        <main className="flex-1">
          {children}
        </main>
        <Footer />
      </body>
    </html>
  )
}
