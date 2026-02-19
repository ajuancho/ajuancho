/**
 * Bahoy - Dashboard de métricas de recomendaciones
 * Panel administrativo para visualizar la calidad del sistema de recomendaciones.
 */

'use client'

import { useEffect, useState } from 'react'

// ─── Tipos ─────────────────────────────────────────────────────────────────

interface MetricasReporte {
  periodo_dias: number
  generado_en: string
  metricas: {
    ctr: number
    tasa_guardado: number
    diversidad: number
    cobertura: number
    precision_at_10: number
  }
  totales: {
    impresiones: number
    interacciones: number
    interacciones_por_tipo: Record<string, number>
    impresiones_por_tipo_recomendacion: Record<string, number>
  }
}

// ─── Componentes auxiliares ─────────────────────────────────────────────────

function MetricCard({
  titulo,
  valor,
  descripcion,
  formato = 'porcentaje',
  color = 'blue',
}: {
  titulo: string
  valor: number
  descripcion: string
  formato?: 'porcentaje' | 'numero'
  color?: 'blue' | 'green' | 'purple' | 'orange' | 'teal'
}) {
  const colores: Record<string, string> = {
    blue:   'bg-blue-50 border-blue-200 text-blue-700',
    green:  'bg-green-50 border-green-200 text-green-700',
    purple: 'bg-purple-50 border-purple-200 text-purple-700',
    orange: 'bg-orange-50 border-orange-200 text-orange-700',
    teal:   'bg-teal-50 border-teal-200 text-teal-700',
  }

  const valorFormateado =
    formato === 'porcentaje'
      ? `${(valor * 100).toFixed(2)}%`
      : valor.toLocaleString('es-AR')

  return (
    <div className={`border rounded-xl p-6 ${colores[color]}`}>
      <p className="text-sm font-medium opacity-75 mb-1">{titulo}</p>
      <p className="text-3xl font-bold mb-2">{valorFormateado}</p>
      <p className="text-xs opacity-60">{descripcion}</p>
    </div>
  )
}

function BarChart({
  datos,
  titulo,
}: {
  datos: Record<string, number>
  titulo: string
}) {
  const total = Object.values(datos).reduce((a, b) => a + b, 0)
  if (total === 0) {
    return (
      <div className="border rounded-xl p-6 bg-white">
        <h3 className="font-semibold text-gray-700 mb-4">{titulo}</h3>
        <p className="text-gray-400 text-sm">Sin datos en este período.</p>
      </div>
    )
  }

  const coloresBarra = [
    'bg-blue-400',
    'bg-green-400',
    'bg-purple-400',
    'bg-orange-400',
    'bg-teal-400',
    'bg-pink-400',
  ]

  return (
    <div className="border rounded-xl p-6 bg-white">
      <h3 className="font-semibold text-gray-700 mb-4">{titulo}</h3>
      <div className="space-y-3">
        {Object.entries(datos)
          .sort(([, a], [, b]) => b - a)
          .map(([clave, valor], idx) => (
            <div key={clave}>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600 capitalize">{clave.replace('_', ' ')}</span>
                <span className="font-medium text-gray-800">
                  {valor} ({((valor / total) * 100).toFixed(1)}%)
                </span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${coloresBarra[idx % coloresBarra.length]}`}
                  style={{ width: `${(valor / total) * 100}%` }}
                />
              </div>
            </div>
          ))}
      </div>
      <p className="text-xs text-gray-400 mt-3">Total: {total.toLocaleString('es-AR')}</p>
    </div>
  )
}

// ─── Página principal ───────────────────────────────────────────────────────

export default function MetricsDashboard() {
  const [reporte, setReporte] = useState<MetricasReporte | null>(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [periodo, setPeriodo] = useState(30)

  const PERIODOS = [
    { label: '7 días',  valor: 7 },
    { label: '30 días', valor: 30 },
    { label: '90 días', valor: 90 },
  ]

  useEffect(() => {
    const cargarMetricas = async () => {
      setCargando(true)
      setError(null)
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'}/api/v1/admin/metrics?periodo=${periodo}`
        )
        if (!res.ok) {
          throw new Error(`Error ${res.status}: ${res.statusText}`)
        }
        const datos: MetricasReporte = await res.json()
        setReporte(datos)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error al cargar métricas')
      } finally {
        setCargando(false)
      }
    }

    cargarMetricas()
  }, [periodo])

  const fechaGeneracion = reporte
    ? new Date(reporte.generado_en).toLocaleString('es-AR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    : null

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Métricas de Recomendación
            </h1>
            <p className="text-sm text-gray-500 mt-0.5">
              Evaluación de la calidad del sistema de recomendaciones
            </p>
          </div>

          {/* Selector de período */}
          <div className="flex gap-2">
            {PERIODOS.map((p) => (
              <button
                key={p.valor}
                onClick={() => setPeriodo(p.valor)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  periodo === p.valor
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Contenido */}
      <div className="max-w-7xl mx-auto px-6 py-8">

        {/* Estado de carga */}
        {cargando && (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600" />
            <span className="ml-3 text-gray-500">Cargando métricas...</span>
          </div>
        )}

        {/* Error */}
        {error && !cargando && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
            <p className="text-red-600 font-medium">{error}</p>
            <p className="text-red-400 text-sm mt-1">
              Verifica que el backend esté disponible en{' '}
              {process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'}
            </p>
          </div>
        )}

        {/* Reporte */}
        {reporte && !cargando && (
          <>
            {/* Metadatos */}
            <div className="flex items-center justify-between mb-6">
              <p className="text-sm text-gray-500">
                Período: últimos{' '}
                <span className="font-medium text-gray-700">{reporte.periodo_dias} días</span>
              </p>
              <p className="text-sm text-gray-400">
                Generado: {fechaGeneracion}
              </p>
            </div>

            {/* Métricas principales */}
            <section className="mb-8">
              <h2 className="text-lg font-semibold text-gray-700 mb-4">
                Métricas de Calidad
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
                <MetricCard
                  titulo="CTR"
                  valor={reporte.metricas.ctr}
                  descripcion="Clics sobre recomendaciones mostradas"
                  color="blue"
                />
                <MetricCard
                  titulo="Tasa de Guardado"
                  valor={reporte.metricas.tasa_guardado}
                  descripcion="Recomendaciones guardadas por el usuario"
                  color="green"
                />
                <MetricCard
                  titulo="Diversidad"
                  valor={reporte.metricas.diversidad}
                  descripcion="Variedad de categorías en cada sesión"
                  color="purple"
                />
                <MetricCard
                  titulo="Cobertura"
                  valor={reporte.metricas.cobertura}
                  descripcion="Porcentaje del catálogo recomendado"
                  color="orange"
                />
                <MetricCard
                  titulo="Precision@10"
                  valor={reporte.metricas.precision_at_10}
                  descripcion="Precisión en las 10 primeras recomendaciones"
                  color="teal"
                />
              </div>
            </section>

            {/* Totales */}
            <section className="mb-8">
              <h2 className="text-lg font-semibold text-gray-700 mb-4">
                Totales del Período
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <MetricCard
                  titulo="Impresiones"
                  valor={reporte.totales.impresiones}
                  descripcion="Sesiones de recomendación mostradas"
                  formato="numero"
                  color="blue"
                />
                <MetricCard
                  titulo="Interacciones"
                  valor={reporte.totales.interacciones}
                  descripcion="Total de interacciones usuario-evento"
                  formato="numero"
                  color="green"
                />
              </div>
            </section>

            {/* Gráficos de distribución */}
            <section>
              <h2 className="text-lg font-semibold text-gray-700 mb-4">
                Distribución
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <BarChart
                  datos={reporte.totales.interacciones_por_tipo}
                  titulo="Interacciones por tipo"
                />
                <BarChart
                  datos={reporte.totales.impresiones_por_tipo_recomendacion}
                  titulo="Impresiones por tipo de recomendación"
                />
              </div>
            </section>

            {/* Guía de métricas */}
            <section className="mt-8 bg-white border rounded-xl p-6">
              <h2 className="text-base font-semibold text-gray-700 mb-3">
                Referencia de métricas
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 text-sm">
                {[
                  {
                    nombre: 'CTR',
                    formula: 'clics / impresiones',
                    bueno: '> 5%',
                  },
                  {
                    nombre: 'Tasa de guardado',
                    formula: 'guardados / impresiones',
                    bueno: '> 2%',
                  },
                  {
                    nombre: 'Diversidad',
                    formula: 'categorías distintas / total eventos',
                    bueno: '> 0.5',
                  },
                  {
                    nombre: 'Cobertura',
                    formula: 'eventos recomendados / total catálogo',
                    bueno: '> 20%',
                  },
                  {
                    nombre: 'Precision@10',
                    formula: 'interacciones positivas / 10',
                    bueno: '> 30%',
                  },
                ].map((m) => (
                  <div key={m.nombre} className="bg-gray-50 rounded-lg p-3">
                    <p className="font-medium text-gray-800">{m.nombre}</p>
                    <p className="text-gray-500 font-mono text-xs mt-0.5">{m.formula}</p>
                    <p className="text-green-600 text-xs mt-1">Objetivo: {m.bueno}</p>
                  </div>
                ))}
              </div>
            </section>
          </>
        )}
      </div>
    </div>
  )
}
