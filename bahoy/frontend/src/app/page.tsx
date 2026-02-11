/**
 * Bahoy - Página principal
 * Esta es la página de inicio de la aplicación.
 */

export default function HomePage() {
  return (
    <div className="container mx-auto px-4 py-16">
      {/* Hero Section */}
      <section className="text-center mb-16">
        <h1 className="text-5xl md:text-6xl font-heading font-bold text-gray-900 mb-6">
          Encuentra tu <span className="text-primary-500">hogar ideal</span>
        </h1>
        <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
          Busca propiedades de manera inteligente con nuestra plataforma potenciada por IA
        </p>

        {/* Barra de búsqueda - Placeholder */}
        <div className="max-w-3xl mx-auto">
          <div className="bg-white rounded-2xl shadow-card p-6">
            <input
              type="text"
              placeholder="¿Qué tipo de propiedad buscas?"
              className="w-full px-6 py-4 text-lg border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
            <button className="mt-4 w-full md:w-auto bg-primary-500 hover:bg-primary-600 text-white font-semibold px-8 py-4 rounded-xl transition-colors duration-200">
              Buscar propiedades
            </button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="grid md:grid-cols-3 gap-8 mb-16">
        <FeatureCard
          title="Búsqueda Inteligente"
          description="Usa lenguaje natural para encontrar exactamente lo que buscas"
          icon="🔍"
        />
        <FeatureCard
          title="Resultados Precisos"
          description="Algoritmos de IA que entienden tus preferencias"
          icon="🎯"
        />
        <FeatureCard
          title="Actualización Constante"
          description="Base de datos actualizada con las últimas propiedades"
          icon="⚡"
        />
      </section>

      {/* CTA Section */}
      <section className="text-center bg-primary-500 rounded-3xl p-12 text-white">
        <h2 className="text-3xl font-heading font-bold mb-4">
          ¿Listo para encontrar tu nuevo hogar?
        </h2>
        <p className="text-lg mb-6 opacity-90">
          Únete a miles de personas que ya encontraron su lugar ideal
        </p>
        <button className="bg-white text-primary-500 hover:bg-gray-100 font-semibold px-8 py-4 rounded-xl transition-colors duration-200">
          Comenzar ahora
        </button>
      </section>
    </div>
  )
}

// Componente auxiliar para las tarjetas de características
function FeatureCard({
  title,
  description,
  icon
}: {
  title: string
  description: string
  icon: string
}) {
  return (
    <div className="bg-white rounded-2xl shadow-soft p-8 hover:shadow-card transition-shadow duration-200">
      <div className="text-4xl mb-4">{icon}</div>
      <h3 className="text-xl font-heading font-semibold text-gray-900 mb-3">
        {title}
      </h3>
      <p className="text-gray-600">
        {description}
      </p>
    </div>
  )
}
