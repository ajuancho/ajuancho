-- ========================================
-- BAHOY - Script de Inicialización de Base de Datos
-- ========================================
-- Este script se ejecuta automáticamente cuando se crea el contenedor de PostgreSQL

-- Habilitar la extensión pgvector para búsqueda semántica
CREATE EXTENSION IF NOT EXISTS vector;

-- Habilitar extensión para generación de UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Mensaje de confirmación
DO $$
BEGIN
    RAISE NOTICE 'Base de datos Bahoy inicializada correctamente';
    RAISE NOTICE 'Extensiones habilitadas: pgvector, uuid-ossp';
END $$;

-- TODO: Agregar aquí tablas iniciales o datos de prueba si es necesario
-- Ejemplo:
-- CREATE TABLE IF NOT EXISTS propiedades (
--     id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
--     titulo VARCHAR(255) NOT NULL,
--     descripcion TEXT,
--     precio DECIMAL(15, 2),
--     embedding vector(768),
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );
