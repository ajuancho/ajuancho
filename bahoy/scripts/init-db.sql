-- ========================================
-- BAHOY - Script de Inicialización de Base de Datos
-- ========================================
-- Este script se ejecuta automáticamente cuando se crea el contenedor de PostgreSQL
-- por primera vez. Se monta en /docker-entrypoint-initdb.d/

-- Habilitar la extensión pgvector para búsqueda semántica de eventos
-- Permite almacenar y comparar embeddings (vectores de alta dimensión)
CREATE EXTENSION IF NOT EXISTS vector;

-- Habilitar extensión para generación de UUIDs (identificadores únicos)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Habilitar extensión unaccent para búsquedas en español sin importar acentos
-- Ejemplo: buscar "musica" también encuentra "música"
CREATE EXTENSION IF NOT EXISTS unaccent;

-- Habilitar extensión pg_trgm para búsquedas difusas por similitud de texto
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Verificar que las extensiones se instalaron correctamente
DO $$
DECLARE
    ext RECORD;
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Bahoy - Inicialización de base de datos';
    RAISE NOTICE '========================================';
    FOR ext IN SELECT extname, extversion FROM pg_extension WHERE extname IN ('vector', 'uuid-ossp', 'unaccent', 'pg_trgm')
    LOOP
        RAISE NOTICE 'Extensión habilitada: % (v%)', ext.extname, ext.extversion;
    END LOOP;
    RAISE NOTICE 'Base de datos lista para usar.';
END $$;
