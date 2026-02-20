# Guía de Contribución

Gracias por querer contribuir a Bahoy. Esta guía explica el proceso para reportar bugs, proponer features y enviar código.

---

## Índice

- [Código de conducta](#código-de-conducta)
- [Reportar bugs](#reportar-bugs)
- [Proponer features](#proponer-features)
- [Proceso de desarrollo](#proceso-de-desarrollo)
- [Estilo de código](#estilo-de-código)
- [Proceso de PR](#proceso-de-pr)
- [Setup del entorno de desarrollo](#setup-del-entorno-de-desarrollo)

---

## Código de conducta

Este proyecto adopta el [Contributor Covenant](https://www.contributor-covenant.org/). Se espera un ambiente respetuoso e inclusivo. Reportar comportamiento inapropiado a los mantenedores.

---

## Reportar bugs

Antes de abrir un issue, verificar que:
1. El bug no fue ya reportado (buscar en issues)
2. El bug es reproducible en la última versión de `main`

Al reportar, incluir:
- Descripción clara del comportamiento esperado vs. el real
- Pasos para reproducir
- Output de `GET /health` (para bugs del backend)
- Versión del sistema operativo y Docker
- Logs relevantes (sin credenciales)

---

## Proponer features

Abrir un issue antes de implementar features grandes para discutir el diseño. Para cambios pequeños (bugfixes, mejoras de documentación), se puede ir directamente con un PR.

---

## Proceso de desarrollo

### 1. Fork y setup

```bash
# Fork del repositorio en GitHub
# Clonar tu fork
git clone https://github.com/TU_USUARIO/bahoy.git
cd bahoy

# Agregar upstream
git remote add upstream https://github.com/OWNER/bahoy.git

# Setup del entorno
./scripts/setup.sh
```

### 2. Crear rama de trabajo

Nomenclatura de ramas:

| Tipo | Formato | Ejemplo |
|------|---------|---------|
| Feature | `feature/descripcion-corta` | `feature/semantic-search` |
| Bugfix | `fix/descripcion-del-bug` | `fix/health-check-timeout` |
| Refactor | `refactor/que-se-refactoriza` | `refactor/recommender-service` |
| Docs | `docs/que-se-documenta` | `docs/api-endpoints` |
| Chore | `chore/que-se-hace` | `chore/update-dependencies` |

```bash
git checkout -b feature/mi-nueva-feature
```

### 3. Desarrollar

- Hacer commits pequeños y frecuentes (ver guía de mensajes abajo)
- Asegurarse que los tests pasan antes de cada commit
- Agregar tests para el código nuevo

### 4. Sincronizar con upstream

```bash
git fetch upstream
git rebase upstream/main
```

### 5. Push y PR

```bash
git push origin feature/mi-nueva-feature
# Abrir Pull Request en GitHub
```

---

## Estilo de código

### Python (Backend)

**Formateo:** `black` (líneas de 88 caracteres)

```bash
cd backend
black app/ tests/
```

**Linting:** `flake8` con configuración en `.flake8` o `setup.cfg`

```bash
flake8 app/ tests/
```

**Imports:** `isort` (compatible con black)

```bash
isort app/ tests/
```

**Type hints:** Obligatorio en funciones públicas. Correr `mypy`:

```bash
mypy app/
```

**Reglas principales:**
- Funciones async para toda lógica que toque DB o Redis
- Usar `Depends()` de FastAPI para inyección de dependencias (DB session, config)
- Pydantic para validación de entrada y salida (nunca diccionarios crudos como contrato)
- No usar `print()`: usar `logger.info/debug/warning/error()`
- Docstrings en inglés o español, pero consistente por módulo

**Ejemplo de función bien escrita:**

```python
@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> EventResponse:
    """Retorna el detalle de un evento. 404 si no existe."""
    result = await db.execute(
        select(Event).where(Event.id == event_id)
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return EventResponse.model_validate(event)
```

### TypeScript (Frontend)

**Formateo:** `prettier` con `prettier-plugin-tailwindcss`

```bash
cd frontend
npm run format
```

**Linting:** `eslint`

```bash
npm run lint
```

**Type checking:**

```bash
npm run type-check
```

**Reglas principales:**
- Siempre tipar props de componentes con `interface` o `type`
- Preferir Server Components (RSC) cuando no se necesita interactividad
- Usar `React Query` para data fetching, no `useEffect` + `fetch`
- Tailwind para estilos: evitar CSS inline y archivos `.css` adicionales
- No usar `any`: si el tipo es desconocido, usar `unknown` y narrowing

**Ejemplo de componente bien escrito:**

```typescript
interface EventCardProps {
  event: Event;
  onSave?: (id: string) => void;
}

export function EventCard({ event, onSave }: EventCardProps) {
  return (
    <article className="rounded-lg border p-4 hover:shadow-md transition-shadow">
      <h3 className="font-semibold text-lg">{event.titulo}</h3>
      <p className="text-sm text-gray-600">{event.categoria}</p>
    </article>
  );
}
```

---

## Mensajes de commit

Formato: `tipo(scope): descripción corta`

| Tipo | Cuándo usar |
|------|------------|
| `feat` | Nueva funcionalidad |
| `fix` | Corrección de bug |
| `refactor` | Refactor sin cambio de comportamiento |
| `test` | Agregar o corregir tests |
| `docs` | Documentación |
| `chore` | Dependencias, config, CI |
| `perf` | Mejora de performance |
| `style` | Formateo, sin cambio de lógica |

**Ejemplos correctos:**
```
feat(recommendations): agregar tipo hibrido con diversificacion
fix(health): timeout de 5s en conexion a postgres
test(scrapers): agregar tests para agenda_ba spider
docs(api): documentar endpoint de recomendaciones contextuales
chore(deps): actualizar fastapi a 0.110.0
```

**Ejemplos incorrectos:**
```
fix bug
Update stuff
WIP
arregle cosas
```

El cuerpo del commit (opcional) debe explicar el **por qué** del cambio, no el qué (eso ya lo dice el código).

---

## Proceso de PR

### Checklist antes de abrir un PR

- [ ] Los tests pasan: `make test`
- [ ] Sin errores de linting: `flake8 app/` y `npm run lint`
- [ ] Sin errores de tipos: `mypy app/` y `npm run type-check`
- [ ] Tests nuevos para funcionalidad nueva
- [ ] Documentación actualizada si cambia la API (docs/API.md)
- [ ] `.env.example` actualizado si hay nuevas variables de entorno
- [ ] El PR tiene una descripción clara de qué hace y por qué

### Título del PR

Seguir el mismo formato que los commits: `tipo(scope): descripción`

### Descripción del PR

Incluir:
1. **Qué hace** este PR
2. **Por qué** es necesario (link al issue si aplica)
3. **Cómo testearlo** manualmente
4. Screenshots si hay cambios visuales

### Revisión de código

- Un reviewer aprueba antes de hacer merge
- Los comentarios bloqueantes deben resolverse antes del merge
- Preferir squash merge para mantener el historial limpio
- El autor del PR hace el merge una vez aprobado

### SLAs de revisión

- PRs pequeños (< 200 líneas): máximo 2 días hábiles
- PRs grandes: acordar con el equipo antes de abrir

---

## Setup del entorno de desarrollo

### Pre-commit hooks

```bash
cd backend
pre-commit install
pre-commit run --all-files  # Para verificar el estado inicial
```

Los hooks corren automáticamente en `git commit`:
- `black`: formateo Python
- `isort`: ordenamiento de imports
- `flake8`: linting
- `trailing-whitespace`, `end-of-file-fixer`

### Correr tests localmente

```bash
# Backend: todos los tests
cd backend && pytest

# Solo tests unitarios (sin DB)
pytest -m unit

# Solo tests de integración (requiere DB y Redis corriendo)
pytest -m integration

# Con cobertura
pytest --cov=app --cov-report=html
# Abrir htmlcov/index.html para ver el reporte

# Frontend
cd frontend && npm run lint && npm run type-check
```

### Estructura de tests del backend

```
backend/tests/
├── conftest.py          # Fixtures compartidos (DB session, cliente HTTP)
├── test_api.py          # Tests de endpoints (integración)
├── test_models.py       # Tests de modelos SQLAlchemy (unitarios)
├── test_scrapers.py     # Tests de scrapers (con mocks de HTTP)
├── test_nlp.py          # Tests del módulo NLP
├── test_classifier.py   # Tests del clasificador de texto
└── test_recommender.py  # Tests del motor de recomendaciones
```

Para agregar un nuevo test de endpoint:

```python
# tests/test_api.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_event_not_found(client: AsyncClient):
    response = await client.get("/api/events/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert response.json()["detail"] == "Evento no encontrado"
```

---

## Preguntas frecuentes

**¿Puedo contribuir sin saber Python?**
Sí. El frontend (TypeScript/Next.js), la documentación y los tests son áreas donde podés contribuir sin tocar el backend.

**¿Cómo agrego una nueva fuente de scraping?**
Ver `backend/app/scrapers/README.md` para la guía de cómo implementar un nuevo spider Scrapy y registrarlo en Celery.

**¿Cómo agrego un nuevo endpoint a la API?**
1. Crear o editar el router en `backend/app/routes/`
2. Registrar el router en `main.py` si es nuevo
3. Agregar tests en `backend/tests/test_api.py`
4. Documentar en `docs/API.md`
