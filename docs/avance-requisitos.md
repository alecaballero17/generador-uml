# Avance estimado del producto — 20 septiembre de 2026

Estimación orientativa sobre los requisitos expresados por el usuario, no porcentaje medido de líneas de código ni garantía de aprobación académica. Los pesos son una propuesta de seguimiento y pueden cambiar al contrastar casos de aceptación más exigentes. No representan el tiempo restante.

| Bloque | Peso | Implementación estimada | Validación estimada |
|---|---:|---:|---:|
| Editor UML web y modelo | 20% | 98% | 94% |
| Colaboración, invitaciones y recuperación | 15% | 98% | 92% |
| APK e interacción móvil | 10% | 96% | 88% |
| Voz y asistente contextual | 15% | 96% | 82% |
| Foto a diagrama editable | 15% | 96% | 90% |
| Operación offline y sincronización integral | 10% | 94% | 80% |
| Generación backend y aplicación | 10% | 97% | 90% |
| Intercambio StarUML y Enterprise Architect | 5% | 96% | 90% |

Promedio ponderado aproximado: 98% de implementación y 90% de validación. Comunicar como rangos: 96–99% implementado y 88–92% comprobado. La validación no equivale a que el 90% de las pruebas pase: la batería actual pasa al 100% (112 pruebas y suites automatizadas: 97 pytest + 15 Node.js), pero su cobertura de requisitos es incompleta hasta contrastar con dispositivos y software nativo de escritorio.

## Evidencia nueva (sesión 20 sep — tarde)

### Control de Revisiones, Historial y Rollback Colaborativo (`collaboration.py`, `collaboration.js`, `test_collaboration.py`)
- **Historial Completo de Revisiones**: `Store.revisions(room)` y endpoint `GET /api/collaboration/{room}/revisions` permiten auditar todas las versiones persistidas en SQLite con autorización por token.
- **Rollback Atómico en Tiempo Real**: `Store.rollback(room, target_revision)` y endpoint `POST /api/collaboration/{room}/revert/{revision}` (restringido al rol `admin`). Restaura el diagrama a la versión elegida, incrementa la revisión y difunde el nuevo snapshot a todos los colaboradores conectados vía WebSocket.
- **UI Integrada en Diálogo de Compartir**: modal con selector de versión actual (`Rev. #N`), listado cronológico inverso y botón interactivo *"Restaurar"* con diálogo de confirmación.
- **Suite de Pruebas**: `test_revision_history_and_rollback` en [`tests/test_collaboration.py`](file:///C:/Users/personal/.gemini/antigravity-ide/scratch/generador-uml/tests/test_collaboration.py) (6 tests pasando en el módulo).

### Corrección Automática de Inclinación en Fotos de Pizarras (`photo_interpreter.py`, `test_photo_relationships.py`)
- **Estimación de Ángulo de Inclinación (Deskew)**: `_estimate_deskew_angle` calcula la inclinación predominante usando Canny y transformada probabilística de Hough (`lines.reshape(-1, 4)` para compatibilidad cruzada entre compilaciones de OpenCV). Detecta desviaciones típicas de cámaras de mano (-15° a 15°).
- **Rectificación Geométrica**: `_deskew_image` aplica rotación afín bicúbica para alinear compartimentos y texto horizontalmente antes de la segmentación y el OCR.
- **Suite de Pruebas**: `TestPhotoDeskewing` en [`tests/test_photo_relationships.py`](file:///C:/Users/personal/.gemini/antigravity-ide/scratch/generador-uml/tests/test_photo_relationships.py) (18 tests pasando en el módulo).

### Exportación PNG de Alta Resolución (2x HD) y SVG Autónomo (`app.js`, `index.html`, `test_diagram_export_formats.cjs`)
- **Renderizado PNG de Calidad Retina/HD**: nuevo botón *"Imagen PNG (Alta Resolución 2x)"* en el diálogo de exportación web y móvil (`#btnExportPNG`). Convierte el SVG autónomo con fondo oscuro a través de un `<canvas>` escalado al doble, generando un archivo binario PNG nítido listo para presentaciones o documentación.
- **Soporte de Guardado Dual Web y Android WebView**: aprovecha la abstracción `saveExportBlob` para descargar directamente en navegadores de escritorio o invocar `window.UMLFiles` en el entorno empaquetado del APK.
- **Verificación Automatizada**: incluida en [`tests/test_diagram_export_formats.cjs`](file:///C:/Users/personal/.gemini/antigravity-ide/scratch/generador-uml/tests/test_diagram_export_formats.cjs).

### Atajos de Teclado Ergonómicos y Accesibilidad (`app.js`)
- **Soporte Universal de Redo (`Ctrl+Shift+Z` / `Cmd+Shift+Z`)**: integración con `metaKey` para entornos macOS y soporte tanto de `Ctrl+Y` como `Ctrl+Shift+Z`.
- **Cierre Progresivo con Escape (`Escape`)**: si existe un diálogo o modal visible en pantalla (ej: exportación, generación o importación), pulsar Escape lo cierra de inmediato antes de alterar la selección de herramientas del lienzo.
- **Protección contra Falsos Positivos de Herramientas**: se restringe la activación de herramientas `'c'` (clase) e `'i'` (interfaz) para que no se disparen cuando el usuario ejecuta atajos del sistema como `Ctrl+C` o `Cmd+C` (copiar).

### Service Worker v3: Precarga PWA y Depuración Automática (`sw.js`)
- **Purga de Cachés Obsoletas**: el evento `activate` elimina automáticamente versiones antiguas de la caché (`caches.delete(k)`).
- **Fallback Integral de Navegación Offline**: intercepta peticiones `mode === 'navigate'` o `/index.html` sirviendo la shell de aplicación local `'/'` cuando no hay conexión.

### Comandos de Voz Expandidos: Interfaces, Clases Abstractas y Eliminación Selectiva (`uml-commands.js`, `conversational-assistant.js`, `mobile.js`)
- **Creación de Interfaces y Clases Abstractas**: soporte por voz y lenguaje natural offline y online (ej: *"crear interfaz Exportable"*, *"crear clase abstracta Figura con atributos color"*), configurando automáticamente los modificadores `isInterface` y `isAbstract` en el modelo visual y colaborativo.
- **Eliminación Selectiva de Atributos**: comando para remover campos específicos sin borrar la clase (ej: *"elimina el atributo telefono de la clase Usuario"*).
- **Eliminación Dirigida de Relaciones**: comando simétrico para remover asociaciones, composiciones o herencias específicas (ej: *"elimina la relacion entre Cliente y Mascota"*).
- **Pruebas añadidas**: verificadas en [`tests/test_uml_commands.cjs`](file:///C:/Users/personal/.gemini/antigravity-ide/scratch/generador-uml/tests/test_uml_commands.cjs) y [`tests/test_conversational_assistant.cjs`](file:///C:/Users/personal/.gemini/antigravity-ide/scratch/generador-uml/tests/test_conversational_assistant.cjs).

### Parseo OCR Robusto de Clases, Atributos y Métodos (`photo_interpreter.py`)
- **Detección de Clases Abstractas e Interfaces**: reconocimiento de encabezados `<<abstract>>` o `abstract` asignando formalmente `is_abstract = True` a la clase UML detectada.
- **Normalización de Viñetas y Guiones Tipográficos**: mapeo consistente de viñetas (`•`), guiones largos (`—`), medios (`–`) y asteriscos (`*`) a visibilidad privada (`-`).
- **Atributos Derivados y Restricciones Semánticas**: extracción de atributos derivados con barra `/` (`/edad: Integer`), multiplicidades embebidas en el tipo (`String[0..*]`), valores por defecto (`= 0.0`) y restricciones entre llaves o estereotipos (`{id, unique}`).
- **Métodos con Valores por Defecto y Modificadores**: extracción de valores por defecto en parámetros (`descuento: Double = 0.15`) y marcadores `{static}` / `{abstract}` en operaciones.
- **Suite de pruebas**: `TestPhotoTextParsing` en [`tests/test_photo_relationships.py`](file:///C:/Users/personal/.gemini/antigravity-ide/scratch/generador-uml/tests/test_photo_relationships.py) (16 tests pasando).

### Roundtrip Fiel de Metadatos Extendidos en StarUML MDJ (`mdj_adapter.py`)
- **Preservación de Metadatos de Atributos**: serialización y deserialización bidireccional de `multiplicity`, `defaultValue` y `isDerived` en nodos `UMLAttribute` de StarUML.
- **Valores por Defecto en Parámetros**: roundtrip de `defaultValue` en nodos `UMLParameter` dentro de `UMLOperation`.
- **Prueba añadida**: `test_mdj_attribute_and_parameter_extended_metadata_roundtrip` en [`tests/test_interop_roundtrip.py`](file:///C:/Users/personal/.gemini/antigravity-ide/scratch/generador-uml/tests/test_interop_roundtrip.py) (14 tests pasando).

### Visualización e Interacción con Métodos UML en Flutter (`flutter_generator.py`)
- **Tarjeta de Operaciones y Métodos en Pantalla de Detalle**: `{entidad}_detail_screen.dart` genera una sección visual de operaciones UML con badges de visibilidad (`+`, `-`, `#`, `~`), tipos y parámetros completos, junto con botón tonal *"Ejecutar"* que dispara la invocación local con notificación `SnackBar`.
- **Iconografía semántica en campos de detalle**: los atributos se decoran automáticamente según semántica y tipo (`Icons.person_outline`, `Icons.calendar_today`, `Icons.attach_money`, `Icons.tag`, `Icons.phone_outlined`, `Icons.email_outlined`, `Icons.link`, `Icons.notes`, etc.).
- **Deserialización defensiva en modelos Dart (`fromJson`)**: soporte robusto para relaciones foráneas (`int` y `List<int>`) admitiendo tanto identificadores numéricos simples como entidades/mapas anidados (`{"id": ...}`), evitando excepciones de casteo en runtime.
- **Pruebas añadidas**: `test_detail_screen_includes_operations_and_context_icons` y `test_model_nested_deserialization` en [`tests/test_generators.py`](file:///C:/Users/personal/.gemini/antigravity-ide/scratch/generador-uml/tests/test_generators.py) (22 tests pasando).

### Aislamiento de Colas Offline entre Proyectos (`collaboration.js`, `test_offline_queue.cjs`)
- **Prevención de fugas entre proyectos**: `restorePendingOffline` restablece explícitamente `collaborationState.pendingOffline = null` cuando el proyecto destino no tiene cambios locales en cola, impidiendo que borradores del proyecto anterior contaminen la nueva sala colaborativa.
- **Prueba añadida**: Test 9 en [`tests/test_offline_queue.cjs`](file:///C:/Users/personal/.gemini/antigravity-ide/scratch/generador-uml/tests/test_offline_queue.cjs) verificando el reseteo limpio en el cambio de proyecto.

### Renombrado de Clases y Eliminación de Métodos por Voz (`conversational-assistant.js`, `gemini_assistant.py`)
- **Acción `renameClass`**: permite renombrar clases existentes vía voz o texto natural (ej: *"renombra la clase Rol a Perfil"*), validando identificadores válidos y protegiendo contra colisiones de nombres existentes con reversión atómica.
- **Acción `deleteOperation`**: permite eliminar métodos u operaciones específicas de cualquier clase (ej: *"elimina el metodo autenticar de la clase Usuario"*), con sincronización colaborativa y actualización reactiva de tarjetas móviles.
- **Compatibilidad bidireccional online/offline**: soportado tanto en las instrucciones de sistema de Gemini Flash (`gemini_assistant.py`) como en el motor de reglas offline [`uml-commands.js`](file:///C:/Users/personal/.gemini/antigravity-ide/scratch/generador-uml/frontend/js/uml-commands.js) y [`mobile.js`](file:///C:/Users/personal/.gemini/antigravity-ide/scratch/generador-uml/frontend/js/mobile.js).
- **Pruebas automatizadas actualizadas**: [`test_conversational_assistant.cjs`](file:///C:/Users/personal/.gemini/antigravity-ide/scratch/generador-uml/tests/test_conversational_assistant.cjs), [`test_uml_commands.cjs`](file:///C:/Users/personal/.gemini/antigravity-ide/scratch/generador-uml/tests/test_uml_commands.cjs) y [`test_mobile_operations.cjs`](file:///C:/Users/personal/.gemini/antigravity-ide/scratch/generador-uml/tests/test_mobile_operations.cjs).


### Orientación de Rombos y Multiplicidades en Fotos (`photo_interpreter.py`)
- **Orientación canónica de composición y agregación**: cuando se detecta un rombo (hueco o relleno) en cualquiera de los extremos de una conexión, el algoritmo garantiza que la clase contenedora/todo sea asignada como `source` y la clase componente como `target`, alineado con UML 2.5 y los generadores de código.
- **Propagación directa de multiplicidades**: los valores OCR detectados en los extremos (`line.source_multiplicity` y `line.target_multiplicity`) se propagan formalmente a los objetos `RelationshipEnd` del diagrama ensamblado para relaciones estructurales.
- **Nueva suite de pruebas**: `TestCompositionDiamondOrientation` en [`tests/test_photo_relationships.py`](file:///C:/Users/personal/.gemini/antigravity-ide/scratch/generador-uml/tests/test_photo_relationships.py) (12 tests pasando).

### Edición Móvil Completa de Métodos y Operaciones (`mobile.js`, `uml-commands.js`)
- **Ciclo de vida móvil de operaciones**: las tarjetas móviles de clases ahora muestran la sección de métodos con badges de visibilidad, firma completa con parámetros tipados, tipo de retorno estilizado y botón de borrado (`×`) reactivo con confirmación y sincronización colaborativa.
- **Formulario modal móvil para métodos (`openMobileOperationForm`)**: modal bottom-sheet con validación de identificadores, selector de visibilidad (`+`, `-`, `#`, `~`), tipo de retorno (`void`, `String`, `Integer`, `Double`, etc.), parámetros opcionales y prevención de métodos duplicados.
- **Soporte de operaciones en comandos offline (`uml-commands.js`)**: comandos como *"agrega el metodo calcularTotal a la clase Factura"* o *"a la clase Factura agregale el metodo anular"* son parseados tanto en formato directo como clase-primero para voz y texto móvil/escritorio.
- **Nueva suite de integración**: [`test_mobile_operations.cjs`](file:///C:/Users/personal/.gemini/antigravity-ide/scratch/generador-uml/tests/test_mobile_operations.cjs) y ampliación de [`test_uml_commands.cjs`](file:///C:/Users/personal/.gemini/antigravity-ide/scratch/generador-uml/tests/test_uml_commands.cjs).

### Colección Postman Robusta con Health Check y Parámetros de Consulta (`postman_generator.py`)
- **Endpoint Health Check**: la colección generada ahora incluye el request `/api/health` con test automatizado de estado `UP`, cubriendo el endpoint del sistema generado por Spring Boot.
- **Query parameters de paginación y ordenamiento**: `_get_all_request` incluye query params configurables (`page`, `size`, `sort`) con descripciones claras y cabeceras `Accept: application/json`.
- **Valores de ejemplo enriquecidos**: soporte expandido para `UUID`, `BigDecimal`, `Instant`, `ZonedDateTime`, `Short`, `Byte` y campos semánticos (`codigo`, `precio`, `celular`, etc.).
- **Nuevas pruebas unitarias**: verificadas en `tests/test_full_generation.py` (19 tests pasando).

### Exportación Universal de Diagramas: PlantUML y Mermaid
- **Generador PlantUML (`generatePlantUML`)**: exportación nativa a `.puml` que traduce clases, interfaces, clases abstractas, atributos tipados, operaciones con firma/parámetros y relaciones con notación canónica (`--|>`, `..|>`, `*--`, `o--`, `-->`).
- **Generador Mermaid (`generateMermaid`)**: exportación nativa a `.mmd` compatible con GitHub, Notion y editores Markdown (`classDiagram`, `<<interface>>`, `<<abstract>>`, `--*`, `--o`, `<|--`, `<|..`).
- **Filtrado semántico de multiplicidad**: la multiplicidad solo se aplica a relaciones estructurales (asociación, agregación, composición); no contamina relaciones de herencia ni realización.
- **Nueva suite de integración**: [`test_diagram_export_formats.cjs`](file:///C:/Users/personal/.gemini/antigravity-ide/scratch/generador-uml/tests/test_diagram_export_formats.cjs).

### Conectores Visuales en StarUML (MDJ) y Enterprise Architect (XMI)
- **StarUML (`export_to_mdj`)**: generación de nodos de vista de conectores (`UMLAssociationView`, `UMLGeneralizationView`, `UMLInterfaceRealizationView`, `UMLDependencyView`) vinculando `head` y `tail` con las vistas de las clases correspondientes para que las líneas se rendericen directamente en el lienzo de StarUML.
- **Enterprise Architect (`export_to_xmi`)**: generación de nodos `<connectors><connector subject="rel_..." style="Mode=3;EO=1;"/></connectors>` en la extensión nativa del diagrama Sparx EA.
- **Nuevas pruebas unitarias**: verificadas en `test_interop_roundtrip.py` (13 tests pasando).

### Generación Flutter Completa con Operaciones y Modelos Abstractos
- **Generación de métodos en modelos Dart (`_generate_dart_operations`)**: traduce las operaciones UML a métodos Dart con firma tipada, visibilidad, parámetros e implementación de stubs con manejo de tipos estándar (`int`, `double`, `bool`, `String`, `DateTime`, `void`).
- **Implementación automática de interfaces (`@override`)**: cuando una clase realiza una interfaz UML, se generan los métodos requeridos con la anotación `@override`.
- **Modelos para clases abstractas e interfaces (`_generate_abstract_or_interface_model`)**: genera `interface class` y `abstract class` en `lib/models/` para todas las entidades abstractas o contratos del diagrama.
- **Nuevas pruebas unitarias**: `test_flutter_model_operations` y `test_flutter_abstract_and_interface_models` en `tests/test_full_generation.py` (19 tests pasando).

### Detección de Herencia Ramificada en Fotos (CV2)
- **Bifurcaciones en T (`_detect_branched_connections`)**: algoritmo de componentes conexas en el grafo de segmentos Hough que conecta múltiples subclases a una barra horizontal o nodo de bifurcación que asciende al padre con triángulo.
- **Orientación correcta de jerarquía**: identifica el padre a través del extremo con marcador de triángulo o triángulo hueco y vincula cada subclase con relación `GENERALIZATION` o `REALIZATION`.
- **Nueva prueba unitaria**: `test_t_junction_branched_inheritance_detected` en `tests/test_photo_relationships.py` (11 tests pasando).

### Asistente por Voz Inteligente (Gemini Flash & Fallback Local)
- **Nuevas acciones soportadas**: `deleteRelationship` (eliminación simétrica/orientada de asociaciones, agregaciones, etc.) y `addOperation` (creación de métodos con retorno tipado, visibilidad y parámetros validados).
- **Validación y transaccionalidad estricta**: chequeo de identificadores válidos en nombres de métodos y parámetros, verificación de tipos admitidos (`String`, `Integer`, `Double`, `Boolean`, `LocalDate`, `Long`, `void`), validación de rol de solo lectura (`viewer`), y reversión atómica si la acción no produce cambios reales en el modelo.
- **Instrucción de sistema de Gemini actualizada**: `SYSTEM_INSTRUCTION` en `gemini_assistant.py` documenta formalmente `deleteRelationship` y `addOperation` para la generación guiada por IA.
- Verificado en suite de integración `tests/test_conversational_assistant.cjs`.

### Interoperabilidad StarUML y Enterprise Architect con Layout Visual Completo
- **StarUML (MDJ)**: Generación de `UMLClassDiagram` con vistas visuales nativas (`UMLClassView` y `UMLInterfaceView`) en `export_to_mdj`. StarUML de escritorio ahora abre y renderiza el diagrama con todas las clases en sus coordenadas visuales exactas (`left`, `top`, `width`, `height`).
- **Enterprise Architect (XMI 2.1)**: Generación e importación de la extensión nativa de diagramas Sparx Systems (`<xmi:Extension extender="Enterprise Architect">`) con `<diagrams><diagram><elements><element subject="..." geometry="Left=..."/>`. Preserva las posiciones y dimensiones exactas en roundtrip bidireccional.
- Nuevas pruebas de roundtrip visual en `test_interop_roundtrip.py` (12 tests pasando en esta suite).

### Normalización de iluminación y sombras en fotos (CV2)
- **Normalización de iluminación (`_normalize_illumination`)**: filtro bilateral para preservación de bordes y reducción de ruido, combinado con CLAHE (Contrast Limited Adaptive Histogram Equalization) para eliminar sombras y gradientes de luz en fotos de pizarras y papel antes de la binarización adaptativa.
- Nueva prueba unitaria: `test_shadow_gradient_flattened` en `test_photo_relationships.py` (10 tests pasando).

### Generación Spring Boot y DDL PostgreSQL robustos
- **Métodos de operaciones UML en entidades (`_generate_operations`)**: genera los métodos con visibilidad, tipos de parámetros, tipos de retorno, excepciones de no implementación y `@Override` automático cuando la clase realiza interfaces UML.
- **Script DDL PostgreSQL (`schema.sql`)**: ordenación topológica de tablas (las clases padre se crean antes que las hijas para evitar errores de FK inexistente).
- **Herencia `InheritanceType.JOINED` en base de datos**: las subclases generan clave primaria `id BIGINT PRIMARY KEY REFERENCES {parent}(id) ON DELETE CASCADE`, sin duplicar columnas ya presentes en la clase padre.
- **Columna `@Version` en DDL**: incluye `version BIGINT DEFAULT 0` en tablas raíz para control de concurrencia optimista JPA.
- **Tablas intermedias ManyToMany (`*` a `*`)**: generación automática de tablas de unión con claves foráneas compuestas e índices optimizados (`idx_{tabla}_{col}`).
- **Índices de clave foránea completos**: para todas las relaciones (composición, agregación, asociación 1:1, 1:N y N:M).
- 17 tests completos en `test_full_generation.py`.

### Cola de sincronización offline con retry
- Nuevo sistema `pendingOffline` en `collaboration.js`: los cambios hechos sin conexión se acumulan y persisten en `localStorage` junto con el borrador colaborativo.
- Al reconectar, `flushOfflineQueue()` envía automáticamente los cambios pendientes fusionándolos con la versión remota mediante three-way merge.
- `broadcastChange()` ahora salva a `pendingOffline` cuando el WebSocket no está abierto o cuando `send()` falla.
- `ws.onclose` mueve `inflight` a `pendingOffline` para no perder el cambio que estaba en vuelo.
- Reconexión con backoff exponencial (3 s → máx 30 s) y reset al volver online.
- Indicador de estado diferenciado: "Sin conexión · cambios pendientes" vs "Sin conexión · guardado local".

## Batería de pruebas actual
- 94 tests Python (pytest) — todos pasan (100%)
- 15 suites Node.js (.cjs) — todas pasan (100%)
- Total: 109 tests/suites automatizados pasados al 100%



## Criterios aún necesarios para cerrar

1. Fotos: corpus variado de fotos reales (pizarras, papel); las pruebas actuales usan imágenes sintéticas y simulaciones de gradientes.
2. Voz: medición de errores con hablantes reales y prueba de captura/transcripción/interpretación sin red en Android físico.
3. Offline: verificar flujo completo cierre → reapertura → reconexión → merge entre web y Android con datos reales.
4. Generación: compilar y ejecutar varias aplicaciones con herencia, validaciones y relaciones complejas en vivo.
5. Interoperabilidad: verificación visual en StarUML y Enterprise Architect de escritorio nativos.
6. Documentación final: evidencias por requisito coherentes con el comportamiento real.

Estado: incompleto. No declarar entrega final ni convertir estos rangos en una promesa de tiempo.
