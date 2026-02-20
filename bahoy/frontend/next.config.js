/** @type {import('next').NextConfig} */

/**
 * Bahoy - Configuración de Next.js
 * Este archivo configura el comportamiento de Next.js para la aplicación.
 */

const nextConfig = {
  // Habilitar React Strict Mode para detectar problemas potenciales
  reactStrictMode: true,
  // Requerido por el Dockerfile para el runner standalone
  output: 'standalone',

  // Configuración de imágenes
  images: {
    // Dominios permitidos para cargar imágenes externas
    // Agregar aquí los dominios de donde se cargarán imágenes de propiedades
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**.example.com', // Cambiar por dominios reales
      },
    ],
    // Tamaños de imágenes optimizadas
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },

  // Variables de entorno públicas (accesibles desde el cliente)
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    NEXT_PUBLIC_APP_NAME: 'Bahoy',
  },

  // Configuración de compilación
  compiler: {
    // Remover console.log en producción (opcional)
    // removeConsole: process.env.NODE_ENV === 'production',
  },

  // Headers de seguridad
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on'
          },
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN'
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          {
            key: 'Referrer-Policy',
            value: 'origin-when-cross-origin'
          },
        ],
      },
    ]
  },

  // Redirects (ejemplo)
  // async redirects() {
  //   return [
  //     {
  //       source: '/old-path',
  //       destination: '/new-path',
  //       permanent: true,
  //     },
  //   ]
  // },

  // Rewrites para proxy de API (opcional)
  // async rewrites() {
  //   return [
  //     {
  //       source: '/api/:path*',
  //       destination: 'http://localhost:8000/api/:path*',
  //     },
  //   ]
  // },
}

module.exports = nextConfig
