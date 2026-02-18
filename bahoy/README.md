# 🏠 Bahoy

Plataforma inteligente de búsqueda de propiedades potenciada por IA. Bahoy utiliza procesamiento de lenguaje natural y búsqueda semántica para ayudar a las personas a encontrar su hogar ideal.

## 🚀 Características

- 🔍 **Búsqueda Semántica**: Busca propiedades usando lenguaje natural
- 🤖 **IA Integrada**: Procesamiento de lenguaje natural para entender tus preferencias
- 📊 **Web Scraping**: Recopilación automática de propiedades de múltiples sitios
- ⚡ **Alto Rendimiento**: Cache con Redis y base de datos vectorial con pgvector
- 🎨 **Interfaz Moderna**: Frontend construido con Next.js 14 y Tailwind CSS
- 🐳 **Containerizado**: Despliega fácilmente con Docker

## 🛠️ Tecnologías

### Backend
- **Python 3.11** - Lenguaje de programación
- **FastAPI** - Framework web moderno y rápido
- **PostgreSQL + pgvector** - Base de datos con soporte para vectores
- **Redis** - Cache y mensajería
- **SQLAlchemy** - ORM para base de datos
- **Transformers** - Modelos de NLP
- **BeautifulSoup / Playwright** - Web scraping

### Frontend
- **Next.js 14** - Framework de React con App Router
- **TypeScript** - JavaScript con tipado estático
- **Tailwind CSS** - Framework de estilos utility-first
- **React Query** - Gestión de estado del servidor
- **Zustand** - Gestión de estado del cliente

## 📁 Estructura del Proyecto

```
bahoy/
├── backend/                    # Servidor Backend
│   ├── app/
│   │   ├── main.py            # Punto de entrada de la API
│   │   ├── config.py          # Configuraciones
│   │   ├── models/            # Modelos de SQLAlchemy
│   │   ├── routes/            # Endpoints de la API
│   │   ├── services/          # Lógica de negocio
│   │   ├── scrapers/          # Web scrapers
│   │   └── nlp/               # Procesamiento de texto
│   ├── requirements.txt       # Dependencias Python
│   └── Dockerfile            # Imagen Docker del backend
├── frontend/                   # Aplicación Frontend
│   ├── src/
│   │   ├── app/               # Páginas (App Router)
│   │   ├── components/        # Componentes reutilizables
│   │   └── lib/               # Utilidades
│   ├── package.json          # Dependencias Node.js
│   └── Dockerfile            # Imagen Docker del frontend
├── docker-compose.yml         # Orquestación de servicios
├── .env.example              # Variables de entorno ejemplo
└── README.md                 # Este archivo
```

## 🚀 Inicio Rápido

### Prerrequisitos

- Docker y Docker Compose instalados
- (Opcional) Node.js 18+ y Python 3.11+ para desarrollo local

### Instalación con Docker

1. **Clonar el repositorio**
   ```bash
   git clone <url-del-repositorio>
   cd bahoy
   ```

2. **Configurar variables de entorno**
   ```bash
   cp .env.example .env
   # Edita .env con tus configuraciones
   ```

3. **Iniciar todos los servicios**
   ```bash
   docker-compose up -d
   ```

4. **Verificar que todo está funcionando**
   ```bash
   curl http://localhost:8000/health
   ```
   Respuesta esperada cuando todo está OK:
   ```json
   {
     "status": "ok",
     "database": "connected",
     "pgvector": "installed",
     "redis": "connected",
     "version": "0.1.0"
   }
   ```
   - Backend API: http://localhost:8000
   - Documentación API: http://localhost:8000/docs
   - Frontend: http://localhost:3000
   - pgAdmin (opcional): http://localhost:5050

### Desarrollo Local

#### Backend

1. **Crear entorno virtual**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

2. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

3. **Ejecutar servidor de desarrollo**
   ```bash
   uvicorn app.main:app --reload
   ```

#### Frontend

1. **Instalar dependencias**
   ```bash
   cd frontend
   npm install
   ```

2. **Ejecutar servidor de desarrollo**
   ```bash
   npm run dev
   ```

## 📚 Documentación de la API

Una vez que el backend esté corriendo, accede a la documentación interactiva:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🗄️ Base de Datos

### Migraciones

Para crear y aplicar migraciones de base de datos:

```bash
# Crear una nueva migración
alembic revision --autogenerate -m "Descripción del cambio"

# Aplicar migraciones
alembic upgrade head

# Revertir última migración
alembic downgrade -1
```

### pgVector

El proyecto usa pgvector para búsqueda semántica. Los embeddings de propiedades se almacenan como vectores de 768 dimensiones.

## 🧪 Testing

### Backend
```bash
cd backend
pytest
pytest --cov=app  # Con cobertura
```

### Frontend
```bash
cd frontend
npm test
npm run test:coverage
```

## 🐳 Docker

### Comandos útiles

```bash
# Iniciar servicios
docker-compose up -d

# Ver logs
docker-compose logs -f [servicio]

# Detener servicios
docker-compose down

# Reconstruir imágenes
docker-compose build

# Limpiar volúmenes (¡cuidado!)
docker-compose down -v
```

### Iniciar con pgAdmin

```bash
docker-compose --profile tools up -d
```

## 🔧 Configuración

Todas las configuraciones se manejan a través de variables de entorno. Ver `.env.example` para la lista completa de opciones disponibles.

### Variables Importantes

- `SECRET_KEY`: Clave secreta para JWT (cambiar en producción)
- `POSTGRES_*`: Configuración de PostgreSQL
- `REDIS_*`: Configuración de Redis
- `NEXT_PUBLIC_API_URL`: URL de la API para el frontend

## 📝 Scripts Disponibles

### Backend
- Desarrollo local con hot-reload
- Tests con pytest
- Linting con flake8
- Formateo con black

### Frontend
- `npm run dev`: Servidor de desarrollo
- `npm run build`: Build de producción
- `npm run start`: Servidor de producción
- `npm run lint`: Linter
- `npm run format`: Formatear código

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo licencia MIT. Ver archivo `LICENSE` para más detalles.

## 👥 Equipo

Desarrollado con ❤️ por el equipo de Bahoy

## 📞 Contacto

- Website: https://bahoy.com
- Email: contacto@bahoy.com
- Twitter: @bahoy

---

**Nota**: Este proyecto está en desarrollo activo. Algunas características pueden estar incompletas.
