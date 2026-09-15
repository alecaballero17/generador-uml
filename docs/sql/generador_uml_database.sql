-- ============================================================================
-- GeneradorUML CASE Tool — Script de Base de Datos Relacional (PostgreSQL)
-- Modelo de Persistencia del Software "GeneradorUML"
-- ============================================================================
-- Este script define la base de datos central que almacena proyectos UML,
-- clases, atributos, operaciones, relaciones, colaboración multiusuario,
-- control de versiones y el registro de generación de código fuente.
-- ============================================================================

-- 1. Crear base de datos y extensiones (ejecutar como superusuario si es necesario)
-- CREATE DATABASE generador_uml_db WITH ENCODING 'UTF8';
-- \c generador_uml_db;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- TABLA: users (Usuarios y Diseñadores del Software)
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    avatar_url VARCHAR(255),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- TABLA: projects (Proyectos y Diagramas UML creados en la herramienta)
-- ============================================================================
CREATE TABLE IF NOT EXISTS projects (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    owner_id UUID REFERENCES users(id) ON DELETE SET NULL,
    version VARCHAR(20) NOT NULL DEFAULT '1.0.0',
    uml_version VARCHAR(20) NOT NULL DEFAULT '2.5.1',
    is_public BOOLEAN NOT NULL DEFAULT FALSE,
    canvas_settings JSONB DEFAULT '{"gridSize": 20, "snapToGrid": true, "theme": "dark"}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- TABLA: project_collaborators (Colaboración en tiempo real por WebSockets)
-- ============================================================================
CREATE TABLE IF NOT EXISTS project_collaborators (
    project_id VARCHAR(100) NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'editor', 'viewer')),
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (project_id, user_id)
);

-- ============================================================================
-- TABLA: uml_classes (Clases modeladas en el lienzo UML)
-- ============================================================================
CREATE TABLE IF NOT EXISTS uml_classes (
    id VARCHAR(100) PRIMARY KEY,
    project_id VARCHAR(100) NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    visibility VARCHAR(5) NOT NULL DEFAULT '+' CHECK (visibility IN ('+', '-', '#', '~')),
    is_abstract BOOLEAN NOT NULL DEFAULT FALSE,
    is_interface BOOLEAN NOT NULL DEFAULT FALSE,
    stereotypes VARCHAR(100), -- ej. <<entity>>, <<service>>, <<interface>>
    pos_x DOUBLE PRECISION NOT NULL DEFAULT 50.0,
    pos_y DOUBLE PRECISION NOT NULL DEFAULT 50.0,
    width DOUBLE PRECISION NOT NULL DEFAULT 220.0,
    height DOUBLE PRECISION NOT NULL DEFAULT 180.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_project_class_name UNIQUE (project_id, name)
);

-- ============================================================================
-- TABLA: uml_attributes (Atributos de cada Clase UML)
-- ============================================================================
CREATE TABLE IF NOT EXISTS uml_attributes (
    id VARCHAR(100) PRIMARY KEY,
    class_id VARCHAR(100) NOT NULL REFERENCES uml_classes(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    data_type VARCHAR(100) NOT NULL DEFAULT 'String',
    visibility VARCHAR(5) NOT NULL DEFAULT '-' CHECK (visibility IN ('+', '-', '#', '~')),
    default_value TEXT,
    is_static BOOLEAN NOT NULL DEFAULT FALSE,
    order_index INTEGER NOT NULL DEFAULT 0,
    CONSTRAINT uq_class_attribute_name UNIQUE (class_id, name)
);

-- ============================================================================
-- TABLA: uml_operations (Métodos y Operaciones de cada Clase UML)
-- ============================================================================
CREATE TABLE IF NOT EXISTS uml_operations (
    id VARCHAR(100) PRIMARY KEY,
    class_id VARCHAR(100) NOT NULL REFERENCES uml_classes(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    return_type VARCHAR(100) NOT NULL DEFAULT 'void',
    visibility VARCHAR(5) NOT NULL DEFAULT '+' CHECK (visibility IN ('+', '-', '#', '~')),
    is_abstract BOOLEAN NOT NULL DEFAULT FALSE,
    is_static BOOLEAN NOT NULL DEFAULT FALSE,
    order_index INTEGER NOT NULL DEFAULT 0
);

-- ============================================================================
-- TABLA: uml_parameters (Parámetros de las Operaciones)
-- ============================================================================
CREATE TABLE IF NOT EXISTS uml_parameters (
    id VARCHAR(100) PRIMARY KEY,
    operation_id VARCHAR(100) NOT NULL REFERENCES uml_operations(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    data_type VARCHAR(100) NOT NULL DEFAULT 'String',
    default_value TEXT,
    order_index INTEGER NOT NULL DEFAULT 0
);

-- ============================================================================
-- TABLA: uml_relationships (Relaciones entre Clases UML)
-- ============================================================================
CREATE TABLE IF NOT EXISTS uml_relationships (
    id VARCHAR(100) PRIMARY KEY,
    project_id VARCHAR(100) NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(100),
    relationship_type VARCHAR(30) NOT NULL CHECK (
        relationship_type IN ('association', 'aggregation', 'composition', 'generalization', 'realization', 'dependency')
    ),
    -- Extremo Origen (Source End)
    source_class_id VARCHAR(100) NOT NULL REFERENCES uml_classes(id) ON DELETE CASCADE,
    source_role VARCHAR(50),
    source_multiplicity VARCHAR(20) DEFAULT '1',
    source_navigable BOOLEAN NOT NULL DEFAULT TRUE,
    -- Extremo Destino (Target End)
    target_class_id VARCHAR(100) NOT NULL REFERENCES uml_classes(id) ON DELETE CASCADE,
    target_role VARCHAR(50),
    target_multiplicity VARCHAR(20) DEFAULT '0..*',
    target_navigable BOOLEAN NOT NULL DEFAULT TRUE,
    -- Puntos de anclaje visuales / enrutamiento ortogonal
    routing_points JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- TABLA: generation_jobs (Historial de Generación de Código y Descargas)
-- ============================================================================
CREATE TABLE IF NOT EXISTS generation_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id VARCHAR(100) NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    target_technologies VARCHAR(100) NOT NULL, -- ej: "springboot,flutter,postman"
    base_package VARCHAR(150) NOT NULL DEFAULT 'com.generated.app',
    database_type VARCHAR(30) NOT NULL DEFAULT 'PostgreSQL',
    output_directory VARCHAR(255) NOT NULL,
    zip_archive_path VARCHAR(255),
    total_files_generated INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(30) NOT NULL CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    error_message TEXT,
    execution_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- TABLA: diagram_change_logs (Historial de Cambios y Versionamiento WebSocket)
-- ============================================================================
CREATE TABLE IF NOT EXISTS diagram_change_logs (
    id BIGSERIAL PRIMARY KEY,
    project_id VARCHAR(100) NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    version_number INTEGER NOT NULL,
    action_type VARCHAR(50) NOT NULL, -- ej: "add_class", "move_class", "add_relationship", "delete"
    action_payload JSONB NOT NULL,
    client_timestamp TIMESTAMP WITH TIME ZONE,
    server_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ÍNDICES DE RENDIMIENTO Y OPTIMIZACIÓN
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_projects_owner ON projects(owner_id);
CREATE INDEX IF NOT EXISTS idx_classes_project ON uml_classes(project_id);
CREATE INDEX IF NOT EXISTS idx_attributes_class ON uml_attributes(class_id);
CREATE INDEX IF NOT EXISTS idx_operations_class ON uml_operations(class_id);
CREATE INDEX IF NOT EXISTS idx_parameters_operation ON uml_parameters(operation_id);
CREATE INDEX IF NOT EXISTS idx_relationships_project ON uml_relationships(project_id);
CREATE INDEX IF NOT EXISTS idx_relationships_source ON uml_relationships(source_class_id);
CREATE INDEX IF NOT EXISTS idx_relationships_target ON uml_relationships(target_class_id);
CREATE INDEX IF NOT EXISTS idx_generation_project ON generation_jobs(project_id);
CREATE INDEX IF NOT EXISTS idx_changelog_project_version ON diagram_change_logs(project_id, version_number);

-- ============================================================================
-- DATOS SEMILLA DE INICIALIZACIÓN (Seed Data de prueba de la herramienta)
-- ============================================================================
INSERT INTO users (id, username, email, password_hash, full_name)
VALUES (
    'a0000000-0000-0000-0000-000000000001',
    'admin',
    'admin@generadoruml.io',
    '$2b$12$e8Kz6WzB9p...hash_seguro...',
    'Administrador GeneradorUML'
) ON CONFLICT (username) DO NOTHING;

INSERT INTO projects (id, name, description, owner_id, version, uml_version)
VALUES (
    'proj-generador-uml-core',
    'GeneradorUML Metamodel Project',
    'Proyecto raíz de la herramienta CASE para diseño UML y generación de software de producción.',
    'a0000000-0000-0000-0000-000000000001',
    '1.0.0',
    '2.5.1'
) ON CONFLICT (id) DO NOTHING;
