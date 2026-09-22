# GeneradorUML: documentación de desarrollo

**Fecha de revisión:** 21 de septiembre de 2026  
**Estado:** borrador para revisión académica; no constituye certificación de producto terminado.  
**Metodología:** Proceso Unificado de Desarrollo (PUD/UP), iterativo e incremental.  
**Referencia de modelado:** UML 2.5.1.  
**Datos de portada por completar:** autor(es), institución, asignatura y docente.

## 1. Problema, objetivo y alcance

El proyecto aborda la creación de diagramas de clases desde distintas entradas y dispositivos. En una computadora resulta apropiado un lienzo visual; en un teléfono se requieren formularios breves, voz y captura de imágenes. La colaboración debe mantener un mismo modelo compartido y permitir recuperar cambios realizados sin conectividad.

El objetivo es desarrollar una herramienta CASE que permita modelar, revisar, intercambiar y transformar diagramas de clases en código. La web y la APK Graficador UML son interfaces del editor. Los proyectos Spring Boot y Flutter generados son resultados del editor, no sustituyen a su complemento móvil.

El alcance incluye clases, atributos, operaciones, relaciones, colaboración mediante enlaces, asistencia por voz, entrada por imágenes, persistencia local, sincronización y generación. No se afirma soporte de todos los diagramas ni de toda la especificación UML. La lógica de negocio de operaciones arbitrarias no puede deducirse únicamente de sus nombres y firmas.

## 2. Enfoque metodológico

El Proceso Unificado organiza el trabajo en Inicio, Elaboración, Construcción y Transición. Cada iteración integra requisitos, análisis, diseño, implementación y pruebas según el riesgo del incremento. Esta organización toma como referencia la descripción de fases de [IBM](https://www.ibm.com/docs/en/rational-clearquest/10.0.9?topic=settings-project-planning).

La tabla siguiente reconstruye incrementos a partir de los artefactos disponibles; no inventa fechas de ejecución ni acredita ceremonias que no se hayan registrado.

| Iteración | Fase | Objetivo e incremento | Criterio de salida | Situación documentada |
|---|---|---|---|---|
| I1 | Inicio | Delimitar web, móvil y generación; actores y requisitos | Alcance y riesgos identificados | Requisitos recuperados de la conversación y documentos |
| E1 | Elaboración | Modelo UML común y arquitectura cliente/servidor | Representar y validar clases y relaciones | Código del modelo y validador disponible |
| E2 | Elaboración | Persistencia, permisos y protocolo colaborativo | Dos clientes comparten cambios y detectan conflicto | Pruebas automatizadas existentes |
| C1 | Construcción | Editor, formularios e intercambio | Modelar y realizar recorridos de importación/exportación | Implementación y pruebas internas |
| C2 | Construcción | Generadores Spring Boot y Flutter | Generar proyectos coherentes | Pruebas de generación; ejecución amplia pendiente |
| C3 | Construcción | APK, voz, fotos y edición local | Crear y revisar modelos desde móvil | Casos manuales parciales y pruebas automatizadas |
| C4 | Construcción | Correcciones de OCR, voz y recuperación offline | No perder borradores ni aplicar datos ambiguos silenciosamente | Cambios recientes probados por componentes |
| T1 | Transición | Aceptación, instalación y documentación | Verificar criterios finales en entornos objetivo | Abierta; no declarar concluida |

## 3. Actores y límite del sistema

El límite comprende el editor web, el complemento Android y el backend GeneradorUML. El backend es un componente interno, no un actor externo.

| Actor | Responsabilidad |
|---|---|
| Modelador | Crear, revisar, importar y generar desde diagramas |
| Administrador del proyecto | Compartir acceso y gestionar restauraciones autorizadas |
| Colaborador editor | Modificar un proyecto compartido |
| Visualizador | Consultar el proyecto sin modificarlo |
| Servicio Gemini | Interpretación conversacional en línea cuando se utiliza |

Una persona puede actuar como modelador desde web o Android. StarUML y Enterprise Architect intervienen mediante archivos intercambiados; no se presupone una conexión directa con sus procesos.

## 4. Requisitos e historias de usuario

Las historias complementan los casos de uso para ordenar incrementos; no sustituyen su especificación. Los criterios son objetivos de aceptación, no afirmaciones de que todos estén aprobados.

| ID | Historia de usuario | Criterio de aceptación | Caso |
|---|---|---|---|
| HU-01 | Como modelador quiero editar clases para representar mi dominio | Crear clase con atributos y métodos; conservarla al guardar y reabrir | CU-01 |
| HU-02 | Como modelador quiero conectar clases para expresar su estructura | Elegir extremos, tipo y multiplicidad; rechazar herencia cíclica | CU-02 |
| HU-03 | Como administrador quiero compartir un enlace para trabajar con otros | Editor puede modificar; visualizador no puede hacerlo en el servidor | CU-03 |
| HU-04 | Como colaborador quiero conservar cambios simultáneos | Combinar cambios independientes y presentar conflictos del mismo dato | CU-04 |
| HU-05 | Como usuario móvil quiero dictar para reducir escritura | Transcribir, interpretar y confirmar lo que realmente se aplica | CU-05 |
| HU-06 | Como modelador quiero cargar una foto para recuperar un diagrama | Revisar clases, atributos, métodos y conexiones antes de importar | CU-06 |
| HU-07 | Como usuario móvil quiero corregir una lectura con voz | Cambiar el atributo de la clase indicada sin alterar otras clases | CU-06 |
| HU-08 | Como usuario móvil quiero trabajar sin red | Guardar, cerrar, reabrir y reconciliar al recuperar conexión | CU-04 |
| HU-09 | Como modelador quiero intercambiar archivos con otras herramientas | Comparar clases y relaciones después de exportar e importar | CU-07 |
| HU-10 | Como desarrollador quiero generar una base de aplicación | Obtener fuentes Spring Boot y Flutter con estructura y rutas coherentes | CU-08 |
| HU-11 | Como administrador quiero restaurar una revisión | Autorizar restauración, registrar nueva revisión y notificar colaboradores | CU-09 |

Requisitos transversales: procesamiento local para el flujo offline; mensajes de estado comprensibles; conservación del borrador ante errores; permisos comprobados en servidor; revisión de interpretaciones ambiguas. No se fijan cifras de latencia o precisión sin mediciones.

## 5. Especificación de casos de uso

### CU-01. Gestionar elementos del diagrama
**Actor:** modelador con permiso de edición. **Precondición:** proyecto abierto. **Disparador:** crear o editar un elemento.

1. El actor introduce nombre, atributos y operaciones mediante los controles disponibles.
2. El sistema valida los datos y actualiza la representación.
3. El sistema guarda y notifica cambios según conectividad.

**Alternativas:** dato inválido: mostrar error sin aplicar; solo lectura: rechazar modificación. **Postcondición de éxito:** modelo actualizado. **Error de almacenamiento:** informar que no se pudo guardar, sin afirmar persistencia.

### CU-02. Definir relaciones
**Actor:** modelador. **Precondición:** extremos existentes y permiso de edición.

1. Seleccionar clases, tipo de relación y multiplicidades aplicables.
2. Validar extremos, duplicados y restricciones de herencia.
3. Incorporar la relación y actualizar vistas.

**Alternativa:** ciclo o extremos inválidos: rechazar. **Postcondición:** relación válida registrada; las multiplicidades no se inventan si no se especifican.

### CU-03. Compartir acceso
**Actor:** administrador; participantes invitados. **Precondición:** servidor accesible y proyecto compartido.

1. El administrador elige permiso y genera enlace.
2. El participante abre el enlace.
3. El servidor verifica el acceso y entrega el modelo con su rol.

**Alternativa:** enlace inválido: acceso denegado; sin servidor: no generar invitación. **Postcondición:** sesión autorizada. Un enlace local no garantiza acceso desde otra red.

### CU-04. Editar offline y sincronizar
**Actor:** colaborador editor. **Precondición:** proyecto cargado y almacenamiento disponible.

1. Editar sin conexión; conservar el borrador local.
2. Reabrir y recuperar el borrador.
3. Reconectar y comparar base, versión local y remota.
4. Combinar cambios independientes y confirmar su recepción.

**Alternativas:** mismo dato cambiado: ofrecer resolución explícita; fallo de envío: mantener pendiente; almacenamiento fallido: advertir. **Postcondición:** cambios reconciliados o conflicto visible, sin declarar sincronización mientras queden cambios pendientes. La aceptación física completa está pendiente.

### CU-05. Modelar mediante voz
**Actor:** modelador. **Precondición:** permiso de micrófono y recursos de transcripción disponibles.

1. Iniciar captura y mostrar estado de escucha.
2. Detener y transcribir audio.
3. Interpretar el texto mediante el asistente disponible.
4. Aplicar acciones válidas según el flujo y comunicar el resultado real.

**Alternativas:** sin conexión: interpretación local limitada y propuesta revisable; frase ambigua: pedir corrección; error: conservar el modelo. **Postcondición:** cambio confirmado o propuesta pendiente. Gemini requiere conexión; no se atribuye su capacidad al motor offline.

### CU-06. Importar una fotografía y revisar
**Actor:** modelador. **Precondición:** imagen seleccionada y recursos OCR disponibles.

1. Leer imagen localmente, corregir inclinación cuando haya evidencia y separar recuadros.
2. Presentar texto y conexiones candidatas para revisión.
3. Corregir texto, opcionalmente con comandos de voz admitidos.
4. Validar el lote e importar mediante confirmación.

**Alternativas:** texto ilegible o duplicado: bloquear importación; conexiones ambiguas: revisar manualmente. **Postcondición:** lote incorporado; deshacer permite revertirlo. En web se agrega por defecto y reemplazar exige elección explícita. Perspectiva y pizarras variadas requieren más validación.

### CU-07. Intercambiar modelos
**Actor:** modelador. **Precondición:** archivo admitido o modelo abierto.

1. Elegir formato y archivo/destino.
2. Convertir y presentar o guardar el resultado.
3. Comparar los elementos relevantes tras la importación.

**Alternativa:** formato o datos no admitidos: informar error. **Postcondición:** archivo o modelo convertido. Las pruebas internas no certifican fidelidad completa dentro de Enterprise Architect o StarUML.

### CU-08. Generar proyectos
**Actor:** modelador/desarrollador. **Precondición:** modelo válido y backend generador disponible.

1. Seleccionar generación y opciones.
2. Validar y transformar el modelo.
3. Entregar los archivos generados.

**Alternativa:** validación fallida: mostrar problemas antes de generar. **Postcondición:** fuentes disponibles. Compilar y ejecutar es una comprobación adicional; los métodos de negocio pueden requerir implementación manual.

### CU-09. Restaurar revisión
**Actor:** administrador. **Precondición:** historial y servidor disponibles.

1. Consultar historial y elegir revisión.
2. Confirmar restauración.
3. Verificar autorización, crear revisión nueva y difundir el estado.

**Alternativa:** permiso insuficiente o revisión ausente: rechazar. **Postcondición:** revisión restaurada conservando trazabilidad histórica.

## 6. Arquitectura y notación

El cliente web utiliza JavaScript y SVG. La APK aloja el editor mediante WebView; no se describe como interfaz Flutter nativa. El backend utiliza FastAPI. El servicio colaborativo persiste revisiones y permisos en SQLite. La transcripción local y OCR son componentes distintos de la interpretación conversacional remota. Los generadores producen proyectos Spring Boot y Flutter.

Los diagramas deben representar actores fuera del límite, casos de uso dentro del sistema y dependencias con sentido explícito. En clases, `+`, `-`, `#` y `~` expresan visibilidad; la generalización apunta al padre y el rombo pertenece al extremo contenedor. Se toma como referencia [OMG UML 2.5.1](https://www.omg.org/spec/UML/2.5.1/About-UML). Usar esta notación no equivale a certificar conformidad completa de la herramienta.

Los modelos existentes se encuentran en `docs/diagramas/`. Su correspondencia con el código requiere revisión antes de presentarlos como diseño definitivo. El esquema SQL documental tampoco debe confundirse con una migración ejecutada del sistema.

## 7. Trazabilidad de verificación

Diagramas fuente de esta revisión: `diagramas/casos_uso_generador.puml` y `diagramas/secuencia_sincronizacion.puml`. Son vistas de requisitos y del flujo de reconexión; están pendientes de renderizado y revisión visual antes de incorporarlos al documento de entrega.

| Casos | Evidencia disponible | Límite de la evidencia |
|---|---|---|
| CU-01/02 | test_mobile_operations.cjs, test_mobile_relationship.cjs, test_generators.py | Pruebas de componentes, no toda interacción visual |
| CU-03/04/09 | test_collaboration.py, test_client_reconnect.cjs, test_offline_queue.cjs | Falta recorrido físico web–Android completo |
| CU-05 | test_conversational_assistant.cjs, test_assistant_send.cjs | No mide precisión con hablantes reales |
| CU-06 | test_photo_voice.cjs, test_photo_skew.cjs, test_photo_visibility.cjs | Sintéticos y ejemplo bancario; no corpus amplio |
| CU-07 | test_interop_roundtrip.py, test_diagram_export_formats.cjs | No reemplaza apertura en software externo |
| CU-08 | test_full_generation.py, test_generators.py | Comprobación de fuentes, no ejecución universal |

La última batería completa registrada antes de las correcciones posteriores tuvo 97 pruebas Python y 15 suites JavaScript aprobadas. Después se añadieron pruebas puntuales; no se presenta ese total antiguo como el conteo final actual. Las correcciones recientes no se han empaquetado en una nueva APK.

## 8. Riesgos y preparación de entrega

| Riesgo | Tratamiento | Validación pendiente |
|---|---|---|
| Transcripción incorrecta | Mostrar texto y permitir revisión | Audio real con varios hablantes |
| Foto ambigua | No inventar conexiones; revisión explícita | Pizarras, perspectiva y cruces |
| Pérdida offline | Persistencia, cola, reconciliación y advertencias | Cierre y reapertura en Android |
| Código generado incompleto | Pruebas de generación y límites explícitos | Compilar/ejecutar casos representativos |
| Diferencias entre herramientas | Adaptadores y recorridos internos | StarUML y Enterprise Architect reales |

Para la presentación: completar portada, confirmar formato solicitado, revisar diagramas y adjuntar evidencias. Presentar la Transición como abierta hasta realizar la aceptación pendiente. No incluir porcentajes de avance como sustituto de la matriz de verificación.

## 9. Referencias

- OMG. Unified Modeling Language, versión 2.5.1. https://www.omg.org/spec/UML/2.5.1/About-UML
- IBM. Project planning: fases e iteraciones de RUP. https://www.ibm.com/docs/en/rational-clearquest/10.0.9?topic=settings-project-planning
- Repositorio GeneradorUML: código, pruebas y `docs/continuidad-ocr.md` como evidencia técnica del desarrollo.
