'use client'

import { User, Heart, Clock, Settings } from 'lucide-react'
import Card, { CardBody, CardHeader } from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import EventGrid from '@/components/events/EventGrid'

// Placeholder – will connect to real API when auth is implemented
export default function PerfilPage() {
  return (
    <div className="container-custom py-8">
      <h1 className="font-display text-3xl font-bold text-secondary-800 mb-8">Mi perfil</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Sidebar de perfil */}
        <aside className="space-y-6">
          {/* Avatar + info */}
          <Card>
            <CardBody className="flex flex-col items-center text-center py-8">
              <div className="w-20 h-20 rounded-full bg-secondary-100 flex items-center justify-center mb-4">
                <User className="w-10 h-10 text-secondary-400" />
              </div>
              <h2 className="font-display text-xl font-semibold text-secondary-800">Mi cuenta</h2>
              <p className="font-sans text-sm text-gray-400 mt-1">usuario@ejemplo.com</p>
              <Button variant="outline" size="sm" className="mt-4">
                Editar perfil
              </Button>
            </CardBody>
          </Card>

          {/* Stats */}
          <Card>
            <CardHeader>
              <h3 className="font-display font-semibold text-secondary-800">Tu actividad</h3>
            </CardHeader>
            <CardBody className="pt-0 space-y-4">
              {[
                { icon: <Heart className="w-4 h-4 text-primary-500" />, label: 'Guardados', value: '0' },
                { icon: <Clock className="w-4 h-4 text-primary-500" />, label: 'Vistos',    value: '0' },
              ].map((stat) => (
                <div key={stat.label} className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    {stat.icon}
                    {stat.label}
                  </div>
                  <span className="font-semibold text-secondary-800">{stat.value}</span>
                </div>
              ))}
            </CardBody>
          </Card>

          {/* Configuración */}
          <Card>
            <CardBody>
              <button className="w-full flex items-center gap-2 text-sm text-gray-600 hover:text-secondary-800 transition-colors">
                <Settings className="w-4 h-4" />
                Preferencias de notificaciones
              </button>
            </CardBody>
          </Card>
        </aside>

        {/* Contenido principal */}
        <div className="lg:col-span-2 space-y-8">
          {/* Recomendaciones */}
          <section>
            <h2 className="font-display text-xl font-semibold text-secondary-800 mb-4">
              Recomendados para vos
            </h2>
            <EventGrid
              events={[]}
              loading={false}
              emptyMessage="Interactuá con eventos para recibir recomendaciones personalizadas."
            />
          </section>

          {/* Guardados */}
          <section>
            <h2 className="font-display text-xl font-semibold text-secondary-800 mb-4">
              Eventos guardados
            </h2>
            <EventGrid
              events={[]}
              loading={false}
              emptyMessage="Todavía no guardaste ningún evento. Explorá el catálogo."
            />
          </section>
        </div>
      </div>
    </div>
  )
}
