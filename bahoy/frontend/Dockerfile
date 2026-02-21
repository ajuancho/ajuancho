# ========== Dockerfile para Frontend de Bahoy ==========
# Multi-stage build para optimizar el tamaño de la imagen

# ========== Stage 1: Builder ==========
# Instala dependencias y compila en un único stage para evitar
# problemas de cache cross-stage en Railway.
FROM node:18-alpine AS builder
WORKDIR /app

# Copiar lockfile primero — el cache de este layer se invalida
# automáticamente cuando package.json o package-lock.json cambian.
COPY package.json package-lock.json ./
RUN npm ci

# Copiar el resto del código fuente
COPY . .

# Variables de entorno para el build
ENV NEXT_TELEMETRY_DISABLED=1

# Build de la aplicación
RUN npm run build

# ========== Stage 2: Runner ==========
FROM node:18-alpine AS runner
WORKDIR /app

# Variables de entorno
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Crear usuario no-root
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copiar archivos necesarios
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./package.json

# Copiar build
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Cambiar a usuario no-root
USER nextjs

# Exponer puerto
EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Comando para ejecutar la aplicación
CMD ["node", "server.js"]
