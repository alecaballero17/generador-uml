-- ============================================================================
-- GeneradorUML — Script DDL PostgreSQL para 'CursosDemo'
-- Generado automáticamente
-- ============================================================================

-- Descomentar si se ejecuta como superusuario:
-- CREATE DATABASE cursos_demo;
-- \c cursos_demo;

-- Tabla: instructor
CREATE TABLE IF NOT EXISTS instructor (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(255)
);

-- Tabla: curso_programado
CREATE TABLE IF NOT EXISTS curso_programado (
    id BIGSERIAL PRIMARY KEY,
    titulo VARCHAR(255),
    fecha_inicio DATE,
    activo BOOLEAN,
    instructor_id BIGINT REFERENCES instructor(id) ON DELETE SET NULL
);

-- Índices de optimización para Claves Foráneas
CREATE INDEX IF NOT EXISTS idx_curso_programado_instructor_id ON curso_programado(instructor_id);
