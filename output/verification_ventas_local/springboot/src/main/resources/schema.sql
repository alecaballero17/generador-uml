-- ============================================================================
-- GeneradorUML — Script DDL PostgreSQL para 'Sistema Ventas'
-- Generado automáticamente
-- ============================================================================

-- Descomentar si se ejecuta como superusuario:
-- CREATE DATABASE sistema__ventas;
-- \c sistema__ventas;

-- Tabla: vendedor
CREATE TABLE IF NOT EXISTS vendedor (
    id BIGSERIAL PRIMARY KEY,
    version BIGINT DEFAULT 0,
    nombre VARCHAR(255),
    comision DOUBLE PRECISION
);

-- Tabla: venta
CREATE TABLE IF NOT EXISTS venta (
    id BIGSERIAL PRIMARY KEY,
    version BIGINT DEFAULT 0,
    fecha DATE,
    vendedor_id BIGINT REFERENCES vendedor(id) ON DELETE SET NULL,
    cliente_id BIGINT REFERENCES cliente(id) ON DELETE SET NULL
);

-- Tabla: producto
CREATE TABLE IF NOT EXISTS producto (
    id BIGSERIAL PRIMARY KEY,
    version BIGINT DEFAULT 0,
    nombre VARCHAR(255),
    precio DOUBLE PRECISION,
    stock INTEGER
);

-- Tabla: detalle
CREATE TABLE IF NOT EXISTS detalle (
    id BIGSERIAL PRIMARY KEY,
    version BIGINT DEFAULT 0,
    cantidad INTEGER,
    precio_unitario DOUBLE PRECISION,
    venta_id BIGINT REFERENCES venta(id) ON DELETE SET NULL,
    producto_id BIGINT REFERENCES producto(id) ON DELETE SET NULL
);

-- Tabla: cliente
CREATE TABLE IF NOT EXISTS cliente (
    id BIGSERIAL PRIMARY KEY,
    version BIGINT DEFAULT 0,
    nombre VARCHAR(255),
    email VARCHAR(255)
);

-- Tablas intermedias para relaciones Muchos a Muchos
-- Índices de optimización para Claves Foráneas
CREATE INDEX IF NOT EXISTS idx_venta_vendedor_id ON venta(vendedor_id);
CREATE INDEX IF NOT EXISTS idx_venta_cliente_id ON venta(cliente_id);
CREATE INDEX IF NOT EXISTS idx_detalle_venta_id ON detalle(venta_id);
CREATE INDEX IF NOT EXISTS idx_detalle_producto_id ON detalle(producto_id);
