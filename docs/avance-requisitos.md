# Avance estimado del producto — 20 septiembre de 2026

Estimación orientativa sobre los requisitos expresados por el usuario, no porcentaje medido de líneas de código ni garantía de aprobación académica. Los pesos son una propuesta de seguimiento y pueden cambiar al contrastar casos de aceptación más exigentes. No representan el tiempo restante.

| Bloque | Peso | Implementación estimada | Validación estimada |
|---|---:|---:|---:|
| Editor UML web y modelo | 20% | 90% | 85% |
| Colaboración, invitaciones y recuperación | 15% | 90% | 70% |
| APK e interacción móvil | 10% | 85% | 75% |
| Voz y asistente contextual | 15% | 75% | 50% |
| Foto a diagrama editable | 15% | 75% | 65% |
| Operación offline y sincronización integral | 10% | 80% | 55% |
| Generación backend y aplicación | 10% | 88% | 70% |
| Intercambio StarUML y Enterprise Architect | 5% | 75% | 55% |

Promedio ponderado aproximado: 84% de implementación y 67% de validación. Comunicar como rangos: 80–85% implementado y 65–70% comprobado. La validación no equivale a que el 67% de las pruebas pase: la batería actual pasa, pero su cobertura de requisitos es incompleta.

## Evidencia nueva (sesión 20 sep — tarde)

### Generación Spring Boot y DDL PostgreSQL robustos
- **Métodos de operaciones UML en entidades (`_generate_operations`)**: genera los métodos con visibilidad, tipos de parámetros, tipos de retorno, excepciones de no implementación y `@Override` automático cuando la clase realiza interfaces UML.
- **Script DDL PostgreSQL (`schema.sql`)**: ordenación topológica de tablas (las clases padre se crean antes que las hijas para evitar errores de FK inexistente).
- **Herencia `InheritanceType.JOINED` en base de datos**: las subclases generan clave primaria `id BIGINT PRIMARY KEY REFERENCES {parent}(id) ON DELETE CASCADE`, sin duplicar columnas ya presentes en la clase padre.
- **Columna `@Version` en DDL**: incluye `version BIGINT DEFAULT 0` en tablas raíz para control de concurrencia optimista JPA.
- **Tablas intermedias ManyToMany (`*` a `*`)**: generación automática de tablas de unión con claves foráneas compuestas e índices optimizados (`idx_{tabla}_{col}`).
- **Índices de clave foránea completos**: para todas las relaciones (composición, agregación, asociación 1:1, 1:N y N:M).
- Nuevos tests añadidos en `test_full_generation.py` (17 tests completos).

### Interoperabilidad StarUML y Enterprise Architect (XMI / MDJ)
- Verificación y round-trip de diagramas reales de arquitectura de software (`diagrama_generador_uml_software.mdj` y `diagrama_generador_uml_software.xmi`) sumados a los de veterinaria.
- `test_interop_samples.py` ampliado con validación completa y re-exportación (4 tests).

### Cola de sincronización offline con retry
- Nuevo sistema `pendingOffline` en `collaboration.js`: los cambios hechos sin conexión se acumulan y persisten en `localStorage` junto con el borrador colaborativo.
- Al reconectar, `flushOfflineQueue()` envía automáticamente los cambios pendientes fusionándolos con la versión remota mediante three-way merge.
- `broadcastChange()` ahora salva a `pendingOffline` cuando el WebSocket no está abierto o cuando `send()` falla.
- `ws.onclose` mueve `inflight` a `pendingOffline` para no perder el cambio que estaba en vuelo.
- Reconexión con backoff exponencial (3 s → máx 30 s) y reset al volver online.
- Indicador de estado diferenciado: "Sin conexión · cambios pendientes" vs "Sin conexión · guardado local".
- Test suite: `test_offline_queue.cjs` (8 tests) + `test_offline_broadcast.cjs`.

### Detección semántica de relaciones en fotos
- **Clasificación detallada de endpoints** (`_classify_endpoint_detailed`): distingue triángulo hueco (posible realización) de triángulo relleno (herencia), y rombo hueco (agregación) de rombo relleno (composición).
- **Detección de líneas discontinuas** (`_is_dashed_line`): si un triángulo hueco se combina con una línea discontinua, se interpreta como REALIZACIÓN en lugar de herencia.
- **Detección de cruces** (`_detect_line_crossings`): identifica puntos de intersección de segmentos fuera de las cajas y reduce la confianza de las relaciones afectadas, generando notas de revisión.
- **Multiplicidades mejoradas**: ROI expandida a 45 px con escalado 2× para mejor OCR; nombres de clase incluidos en las notas de revisión.
- Test suite: `test_photo_crossings.py` (6 tests).

### Mejora de revisión UI de relaciones desde fotos
- `renderPhotoConnections` rediseñado: cada marcador muestra botones separados para herencia y realización.
- Rombos huecos ofrecen botón directo de agregación.
- Cruces y ramificaciones se muestran en sección destacada con estilo de alerta (amarillo).
- Multiplicidades detectadas se muestran junto al nombre de la relación propuesta.

### Asistente de voz: soporte de relaciones ampliado
- El asistente ahora soporta `realization` y `dependency` como tipos de relación válidos, tanto en el prompt de Gemini como en la validación del frontend.

## Batería de pruebas actual
- 79 tests Python (pytest) — todos pasan
- 13 suites Node.js (.cjs) — todas pasan
- Total: 92 tests/suites automatizados

## Criterios aún necesarios para cerrar

1. Fotos: corpus variado de fotos reales (pizarras, papel); las pruebas actuales usan imágenes sintéticas.
2. Voz: medición de errores con hablantes reales y prueba de captura/transcripción/interpretación sin red en Android.
3. Offline: verificar flujo completo cierre → reapertura → reconexión → merge entre web y Android con datos reales.
4. Generación: compilar y ejecutar varias aplicaciones con herencia, validaciones y relaciones complejas.
5. Interoperabilidad: abrir y reexportar archivos dentro de StarUML y Enterprise Architect reales.
6. Documentación final: evidencias por requisito coherentes con el comportamiento real.

Estado: incompleto. No declarar entrega final ni convertir estos rangos en una promesa de tiempo.
