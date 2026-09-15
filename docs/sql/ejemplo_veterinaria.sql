-- ============================================================================
-- GeneradorUML — Script DDL PostgreSQL del Proyecto de Ejemplo 'Veterinaria'
-- (Para el código generado por Spring Boot)
-- ============================================================================

CREATE TABLE IF NOT EXISTS cliente (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(255),
    apellido VARCHAR(255),
    telefono VARCHAR(255),
    email VARCHAR(255),
    direccion VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS mascota (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(255),
    especie VARCHAR(255),
    raza VARCHAR(255),
    fecha_nacimiento DATE,
    peso DOUBLE PRECISION,
    sexo VARCHAR(255),
    cliente_id BIGINT REFERENCES cliente(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS veterinario (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(255),
    apellido VARCHAR(255),
    especialidad VARCHAR(255),
    matricula VARCHAR(255),
    telefono VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS cita (
    id BIGSERIAL PRIMARY KEY,
    fecha TIMESTAMP,
    motivo VARCHAR(255),
    diagnostico VARCHAR(255),
    estado VARCHAR(255),
    observaciones VARCHAR(255),
    mascota_id BIGINT REFERENCES mascota(id) ON DELETE SET NULL,
    veterinario_id BIGINT REFERENCES veterinario(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS tratamiento (
    id BIGSERIAL PRIMARY KEY,
    descripcion VARCHAR(255),
    medicamento VARCHAR(255),
    dosis VARCHAR(255),
    duracion_dias INTEGER,
    costo NUMERIC(12, 2),
    cita_id BIGINT REFERENCES cita(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_mascota_cliente_id ON mascota(cliente_id);
CREATE INDEX IF NOT EXISTS idx_cita_mascota_id ON cita(mascota_id);
CREATE INDEX IF NOT EXISTS idx_cita_veterinario_id ON cita(veterinario_id);
CREATE INDEX IF NOT EXISTS idx_tratamiento_cita_id ON tratamiento(cita_id);
