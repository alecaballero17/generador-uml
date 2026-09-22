# GeneradorUML
## Resumen
GeneradorUML es una herramienta de ingeniería de software asistida por computadora orientada a construir diagramas de clases, revisarlos y transformarlos en proyectos de software. Integra un editor web colaborativo y un complemento Android del mismo editor. Permite introducir información mediante controles visuales, formularios, voz e imágenes. Los proyectos Spring Boot y Flutter generados constituyen una salida del sistema, distinta de la APK Graficador UML.
Este informe describe el problema, la fundamentación utilizada, los requisitos, el diseño mediante diagramas UML, la reconstrucción del proceso iterativo e incremental y los procedimientos de uso. El contenido se apoya en documentación técnica consultada, código del repositorio y pruebas registradas. Se identifican expresamente los límites de reconocimiento de voz e imágenes y las verificaciones pendientes de dispositivos y herramientas externas. La documentación está completa como versión de revisión académica; no acredita una aceptación del producto que todavía no se ha realizado.
Palabras clave: CASE, UML, Proceso Unificado, componentes, colaboración, generación de código.
## 1 Introducción y definición del proyecto
### 1.1 Problema y contexto
La elaboración de diagramas puede comenzar en una pizarra, continuar en un teléfono y refinarse en una computadora. Transcribir manualmente esos elementos, mantener versiones diferentes y trasladar la estructura al código introduce trabajo repetido y oportunidades de error. El proyecto busca mantener un modelo común entre esas actividades, con mecanismos de revisión que permitan corregir interpretaciones incorrectas.
El contexto académico exige una herramienta demostrable y una explicación verificable de su construcción. Por ello, el informe diferencia requisitos, decisiones de diseño, funciones implementadas y resultados de pruebas. No se considera que la existencia de un botón o de una clase en el código sea suficiente para demostrar el cumplimiento de un requisito.
### 1.2 Objetivo general
Desarrollar y documentar una herramienta CASE para crear y editar diagramas de clases desde web y Android, colaborar sobre un modelo compartido e intercambiar y transformar ese modelo en código fuente.
### 1.3 Objetivos específicos
- Mantener una representación de clases, atributos, operaciones y relaciones utilizable por el editor y los generadores.
- Facilitar la entrada móvil mediante formularios, transcripción de voz y lectura de imágenes con revisión.
- Conservar cambios locales y reconciliarlos con el proyecto compartido al recuperar la conexión.
- Ofrecer adaptadores de archivos y generación de proyectos con controles de coherencia.
- Registrar requisitos, decisiones, pruebas y limitaciones mediante un proceso iterativo e incremental.
### 1.4 Alcance y límites
El alcance funcional se concentra en diagramas de clases. Los demás diagramas incluidos en este informe explican el diseño del software; no significan que el editor permita crear todos esos tipos de diagramas. Tampoco se afirma implementación de toda la especificación UML 2.5.1 ni certificación formal de conformidad.
La transcripción local y el intérprete de comandos no equivalen a una conversación general sin conexión. Gemini es un servicio en línea. La generación de firmas de métodos no permite deducir automáticamente toda la lógica de negocio. La interoperabilidad debe verificarse también dentro de las herramientas externas, además de las pruebas internas de archivos.
## 2 Fundamentación teórica aplicada
### 2.1 Ingeniería de software asistida por computadora
Las herramientas CASE apoyan y automatizan parcialmente actividades de la ingeniería de software, como especificación, diseño, implementación y pruebas (IEEE, s. f.). La palabra parcialmente es relevante: la herramienta facilita tareas, pero no sustituye la decisión del modelador sobre el significado del dominio.
En GeneradorUML, la aplicación de este enfoque se observa en el editor, el validador, los adaptadores y los generadores. El modelo estructurado es el elemento que permite pasar de la representación gráfica a archivos de intercambio y fuentes. Esta clasificación describe el propósito del proyecto; no lo equipara a una plataforma industrial certificada ni implica que cubra todo el ciclo de vida.
### 2.2 Desarrollo basado en componentes y reutilización
Clements (1995) presenta el desarrollo basado en componentes como evolución de la reutilización de software. Para este proyecto, reutilizar significa integrar capacidades existentes mediante contratos definidos y conservar código propio para la coordinación y las reglas específicas del modelado.
El servidor utiliza FastAPI y bibliotecas de tratamiento de datos; Android utiliza WebView; el lector utiliza Tesseract y la transcripción utiliza un modelo ejecutado con Transformers.js. Estos elementos no se desarrollaron desde cero. Su integración exige revisar entradas, salidas, versiones, disponibilidad y errores. La presencia de bibliotecas no demuestra por sí sola una arquitectura desacoplada: esa calidad debe analizarse en las dependencias concretas.
### 2.3 Arquitectura y capacidad de cambio
La arquitectura expresa decisiones sobre estructura y comportamiento que permiten razonar sobre cualidades del sistema, entre ellas modificabilidad, disponibilidad y seguridad (Software Engineering Institute, s. f.). En este proyecto, separar modelo, validación, adaptadores y generadores busca reducir el impacto de añadir un formato o corregir una transformación.
La reutilización del lector entre web y Android evita implementar reglas diferentes para la misma fotografía. Sin embargo, existen dependencias entre módulos JavaScript y estado compartido que limitan el aislamiento. La escalabilidad es un objetivo de evolución, no un resultado medido: no se dispone de evidencia suficiente para afirmar un número de usuarios simultáneos ni rendimiento constante.
### 2.4 UML como lenguaje de modelado
La especificación de referencia es UML 2.5.1, publicada por Object Management Group en 2017. Se utiliza para describir estructura e interacción mediante vistas complementarias (Object Management Group [OMG], 2017). El informe emplea clases, casos de uso, componentes, despliegue, secuencias, actividades y estados según el propósito de cada figura.
La estructura implementada por GeneradorUML representa un subconjunto de conceptos del lenguaje. Una propiedad de configuración que indique la versión UML no prueba conformidad. Los diagramas de este informe son elaboraciones del proyecto; PlantUML se utiliza como herramienta de representación y no como certificado de corrección semántica.
### 2.5 Proceso Unificado iterativo e incremental
El Proceso Unificado organiza el desarrollo mediante las fases Inicio, Elaboración, Construcción y Transición, divididas en iteraciones (IBM, s. f.). En este informe, los casos de uso ayudan a expresar objetivos de los actores y las iteraciones agrupan incrementos verificables. Las historias de usuario se incluyen como apoyo para priorizar y formular criterios de aceptación.
El registro disponible permite reconstruir entregas y correcciones, pero no demostrar que todas las actividades metodológicas se realizaron en una fecha específica. Por ello, no se inventa un cronograma histórico. La fase de Transición permanece abierta mientras falten aceptación y empaquetado de los cambios recientes.
### 2.6 Reconocimiento de texto y transcripción local
Tesseract es un motor de reconocimiento óptico que extrae texto de imágenes y requiere recursos de idioma (Tesseract OCR, s. f.). En el editor, extraer caracteres es solo una parte del problema: después deben distinguirse clases, atributos, métodos y conexiones. Una lectura textual correcta no acredita interpretación completa de las relaciones UML.
Transformers.js permite configurar rutas de modelos locales y deshabilitar su carga remota (Hugging Face, s. f.). El trabajador de voz del proyecto utiliza estas opciones y ejecuta la transcripción mediante WASM. El texto obtenido pasa a otra etapa de interpretación. Separar ambas etapas permite identificar si el fallo proviene del audio reconocido o de la orden interpretada.
### 2.7 Interfaz móvil reutilizada
WebView permite incorporar contenido web dentro de una aplicación Android y vincularlo con capacidades de la aplicación anfitriona (Android Developers, s. f.). GeneradorUML utiliza este enfoque para distribuir el editor en una APK y reutilizar su lógica web. No corresponde describir esta APK como una aplicación Flutter nativa.
La decisión reduce duplicación, pero exige comprobar permisos, acceso a archivos, micrófono, cámara y comportamiento sin conexión en el dispositivo. Que una función opere en el navegador de escritorio no demuestra automáticamente su funcionamiento en WebView.
## 3 Requisitos y análisis
La fuente primaria de requisitos es la descripción proporcionada por el usuario durante el desarrollo y la revisión documental del 21 de septiembre de 2026. No se han inventado encuestas ni entrevistas. Los requisitos documentales incluyen fundamentación aplicada, componentes reutilizados, arquitectura, capítulo de clases UML 2.5 o superior, registro PUD, manual, tutorial, anexos y presentación APA.
### 3.1 Requisitos funcionales
- RF01 Gestionar clases, atributos y operaciones desde las interfaces del editor.
- RF02 Definir relaciones con extremos, tipo y multiplicidad cuando corresponda.
- RF03 Compartir proyectos con roles y colaboración simultánea.
- RF04 Capturar voz, interpretar órdenes y permitir corregir resultados.
- RF05 Leer imágenes y revisar el modelo antes de importarlo.
- RF06 Persistir cambios sin conexión y resolver diferencias al reconectar.
- RF07 Importar y exportar modelos para intercambio.
- RF08 Generar fuentes Spring Boot, Flutter y artefactos asociados.
- RF09 Consultar historial y restaurar revisiones con autorización.
### 3.2 Requisitos de calidad
- RQ01 Comprensibilidad: mostrar estados de escucha, procesamiento, guardado y error con acciones claras.
- RQ02 Integridad: no reemplazar silenciosamente el diagrama ni omitir elementos inválidos sin advertencia.
- RQ03 Autorización: verificar permisos en el servidor; deshabilitar un botón no basta.
- RQ04 Modificabilidad: mantener responsabilidades reconocibles y pruebas de regresión para cambios.
- RQ05 Funcionamiento local: conservar recursos y borradores necesarios; declarar qué funciones requieren red.
- RQ06 Interoperabilidad: verificar estructura y significado, no solo que el archivo se pueda abrir.
### 3.3 Prioridad y criterio de aceptación
Modelado, colaboración, voz, foto, funcionamiento local e intercambio son requisitos centrales, no extras que sustituyan unos a otros. La aceptación requiere un recorrido completo con resultados observables. Los casos negativos son parte de la aceptación: una imagen ilegible, un enlace sin permiso o un conflicto no deben producir un mensaje falso de éxito.
## 4 Arquitectura y componentes reutilizados
### 4.1 Distribución de responsabilidades
El frontend JavaScript presenta el lienzo SVG y los formularios. El modelo del editor se serializa para almacenamiento, intercambio y envío al servidor. FastAPI expone operaciones de colaboración y generación. SQLite almacena proyectos, tokens y revisiones del servicio colaborativo. Los modelos y borradores locales pertenecen al cliente.
La aplicación generada sigue otra arquitectura: backend Spring Boot y cliente Flutter. PostgreSQL corresponde a proyectos generados según su configuración; no debe presentarse como la base de datos colaborativa del editor, que utiliza SQLite.
### 4.2 Inventario de reutilización
| Componente | Uso verificado | Límite o responsabilidad de integración |
| FastAPI | API del backend | Validar solicitudes y gestionar errores del proyecto |
| Pydantic | Datos de entrada de API | No sustituye todas las reglas semánticas UML |
| AndroidX WebKit | Contenedor Android del editor | Permisos y guardado requieren prueba física |
| Tesseract | OCR local y recursos asociados | Reconoce texto; estructura UML se interpreta aparte |
| Transformers.js y Whisper | Transcripción local | No garantiza transcripción exacta ni comprensión general |
| SQLite | Persistencia colaborativa | Capacidad de carga no medida en este informe |
| Adaptadores propios XMI y MDJ | Transformación de archivos | Validación externa sigue necesaria |
### 4.3 Decisiones y consecuencias
La representación común del diagrama permite que un cambio de interfaz no obligue a modificar cada generador. La serialización con identificadores facilita seguir elementos entre revisiones. Los adaptadores aíslan diferencias de formato, mientras las pruebas de ida y vuelta ayudan a detectar pérdidas.
El almacenamiento local y la cola de cambios permiten continuar ante interrupciones. Su costo es una reconciliación más compleja y la necesidad de distinguir guardado local de sincronización remota. La asistencia remota aumenta la flexibilidad de interpretación, pero agrega dependencia de conexión y de un servicio externo.
No se documenta una implantación completa de Clean Architecture, microservicios o balanceo horizontal porque el código y las pruebas revisadas no lo acreditan. La extensión futura debe conservar contratos del modelo, pruebas de compatibilidad y migración de datos.
## 5 Diagrama de clases y diseño estructural
### 5.1 Lectura de la notación
Cada clase se presenta con nombre y, cuando aporta información, compartimentos de atributos y operaciones. Los signos +, −, # y ~ representan visibilidad pública, privada, protegida y de paquete. Una operación indica nombre, parámetros y retorno. Los tipos Python de las figuras internas describen el código implementado; los tipos del ejemplo de negocio describen el modelo que un usuario podría crear.
Las multiplicidades expresan cuántas instancias pueden participar en un extremo. En el ejemplo de negocio, un Cliente se asocia con cero o más pedidos; cada Pedido tiene un cliente. El rombo lleno se ubica en Pedido para expresar composición con sus líneas. En el modelo interno se muestran asociaciones de referencia, sin afirmar propiedad exclusiva que el código no impone.
### 5.2 Núcleo del modelo implementado
UMLDiagram contiene listas de UMLClass y UMLRelationship. UMLClass describe atributos y operaciones; UMLOperation describe parámetros. La separación permite serializar cada elemento y conservar los identificadores usados por edición e intercambio. Los atributos mostrados son una selección legible del código, no una transcripción de todos sus campos.
### 5.3 Relaciones y extremos
UMLRelationship conserva tipo, origen y destino mediante RelationshipEnd. El extremo referencia una clase por class_id; no incorpora otra copia de la clase. Esto hace necesaria la validación de referencias. RelationshipType enumera los seis tipos disponibles. Los campos de presentación, como posición, tamaño y vértices, se omiten de esta vista para concentrarse en la estructura.
### 5.4 Servicios que consumen el modelo
UMLValidator analiza el diagrama; SpringBootGenerator y FlutterGenerator lo transforman; XMIAdapter y MDJAdapter convierten archivos. El esquema no inventa una clase base común para esos generadores. Los nombres se contrastaron con backend/app/models y backend/app/services.
### 5.5 Ejemplo de negocio y reglas
Se propone el ejemplo Cliente, Pedido y LineaPedido para explicar asociaciones, composición y operaciones. Es un ejemplo didáctico, no una captura de una prueba ni el metamodelo del editor. Una regla de negocio posible es que el total del pedido sea la suma de sus líneas; esa regla tendría que implementarse y probarse expresamente. El nombre calcularTotal no basta para generarla con garantía.
### 5.6 Reglas y trazabilidad estructural
Eliminar una clase debe tratar sus relaciones asociadas; importar una referencia inexistente exige validación. Los ciclos de generalización se rechazan en las rutas verificadas. Las conversiones deben preservar nombres, tipos, visibilidad y extremos según el alcance soportado. Las figuras se vinculan con CU01, CU02, CU07 y CU08.
## 6 Diseño dinámico y despliegue
Las secuencias explican el intercambio de mensajes de dos recorridos críticos: importar una foto y reconectar cambios. Las actividades describen el recorrido de generación, incluyendo la validación adicional del proyecto producido. El diagrama de estados resume situaciones de sincronización; no representa clases adicionales del código.
El despliegue distingue computadora, teléfono y servidor. El editor puede conservar operaciones locales sin servidor, pero compartir, consultar Gemini y utilizar la generación del backend requiere conectividad. Las líneas del diagrama representan comunicación lógica; no constituyen una topología de producción ya desplegada.
## 7 Registro del Proceso Unificado
### 7.1 Criterio del registro
El registro es una reconstrucción basada en el repositorio, los documentos y las pruebas observadas. No se asignan fechas históricas a actividades sin evidencia. Inicio delimita el producto; Elaboración trata arquitectura y riesgos; Construcción produce incrementos; Transición verifica aceptación y prepara la entrega.
### 7.2 Artefactos por disciplina
| Disciplina | Artefactos en este informe o repositorio |
| Requisitos | RF01 a RF09, historias, actores y casos de uso |
| Análisis y diseño | Modelo de clases, componentes, secuencias y despliegue |
| Implementación | Frontend, backend, adaptadores y contenedor Android |
| Pruebas | Suites Python y JavaScript, registros manuales previos |
| Configuración | Historial Git y cambios locales por integrar |
| Despliegue | APK previa y empaquetado posterior pendiente |
### 7.3 Registro de correcciones como incrementos
Se registraron fallos de transcripción, importación incorrecta de nombres, atributos añadidos a clases equivocadas, indicadores de sincronización engañosos y borrado de cachés de modelos. Las correcciones incorporaron validación previa, revisión del borrador, pruebas de reconexión y conservación de recursos offline. Cada corrección vincula un defecto observado con una prueba; no prueba por sí sola aceptación global.
Las últimas modificaciones incluyen el tratamiento de métodos sin retorno en Flutter, corrección local de inclinación, correcciones de atributos del borrador por voz y ajustes del service worker. No se ha instalado una APK que contenga todas estas modificaciones.
## 8 Manual de usuario y tutorial
### 8.1 Antes de comenzar
Abra el editor web en la dirección proporcionada por el responsable de instalación o la APK Graficador UML. No confunda esta aplicación con una aplicación de registros generada. Para colaborar, el servidor debe ser accesible desde ambos dispositivos. Para voz, acepte el permiso de micrófono cuando aparezca. Si usa el navegador, las restricciones de seguridad del micrófono dependen del origen y entorno.
Prepare los recursos sin conexión mientras tenga conectividad. El mensaje de preparación no certifica por sí solo la prueba de cierre y reapertura: realice el recorrido del apartado correspondiente. La interfaz de la APK instalada puede diferir del código más reciente hasta que se actualice.
### 8.2 Tutorial de creación móvil
1. Abra Crear clase y escriba Persona.
2. Guarde y compruebe que Persona aparece en Clases del Diagrama.
3. Pulse Agregar atributo en esa clase; escriba nombre y elija Texto.
4. Guarde y compruebe el atributo tanto en la tarjeta como en el diagrama.
5. Agregue un método mediante el formulario de operaciones disponible en la versión actual; indique nombre y retorno.
6. Cree otra clase y utilice Conectar clases para elegir extremos y tipo. Revise la dirección antes de guardar.
Resultado esperado: dos clases y una relación visibles. Si un formulario muestra error, corrija los datos; no dé por guardado el cambio únicamente por haber pulsado el botón.
### 8.3 Tutorial web
1. Seleccione Clase en las herramientas y colóquela en el lienzo.
2. Seleccione la clase y edite su nombre y propiedades.
3. Añada atributos y métodos con nombre y tipo.
4. Cree otra clase y una relación; revise tipo, extremos y multiplicidad.
5. Utilice deshacer si necesita revertir una edición y exporte una copia del modelo.
Resultado esperado: el modelo conserva los elementos introducidos. Antes de reemplazar un diagrama mediante importación, revise la opción elegida y conserve una copia si la necesita.
### 8.4 Tutorial de voz
1. Abra Usar voz y espere a que la interfaz indique escucha.
2. Diga una orden concreta, por ejemplo crear una clase Usuario con atributos nombre y teléfono.
3. Detenga la captura y revise la transcripción.
4. Compruebe la propuesta o confirmación del asistente y el resultado visible.
5. Si el texto no coincide con lo dicho, corríjalo antes de aplicar una propuesta local.
No repita envíos mientras el asistente procesa. Sin conexión, use órdenes admitidas por el intérprete local; no suponga que conserva todas las capacidades de Gemini. Para aislar un fallo, pruebe el mismo texto escrito y compare.
### 8.5 Tutorial de fotografía y corrección
1. Abra Foto u OCR y seleccione una imagen legible con el diagrama completo.
2. Espere el reconocimiento y revise los nombres, atributos y métodos del borrador.
3. Corrija manualmente o dicte: En la clase Usuario cambia el atributo coreo por correo.
4. Compruebe que la modificación ocurrió en la clase adecuada.
5. Revise conexiones candidatas y complete tipo, dirección y multiplicidad cuando sea necesario.
6. Importe después de revisar; si existen nombres duplicados, resuélvalos primero.
El lector intenta corregir inclinación moderada, pero no garantiza recuperación de fotografías con perspectiva, sombras o escritura ambigua. Los tipos ausentes pueden recibir valores predeterminados; no deben interpretarse como datos detectados.
### 8.6 Tutorial de colaboración y reconexión
1. El administrador abre Compartir y elige acceso de edición o lectura.
2. El participante abre el enlace completo en un dispositivo con acceso al servidor.
3. Ambos realizan cambios distintos y comprueban que aparecen en el proyecto compartido.
4. Para evaluar offline, prepare recursos, conserve una copia y quite la conexión de red.
5. Realice una edición, cierre y reabra; compruebe que persiste.
6. Recupere conexión; si aparece conflicto, compare versiones y elija conscientemente.
7. Compruebe el modelo final en ambos dispositivos.
Este recorrido es también un protocolo de aceptación pendiente de ejecución completa en el teléfono. No se presenta como evidencia ya obtenida. Si aparece una advertencia de almacenamiento, no cierre la aplicación antes de conservar una copia.
### 8.7 Exportar y generar
Para guardar el diagrama, abra Exportar y seleccione el formato según el destino. JSON conserva la estructura nativa; XMI y MDJ se destinan al intercambio; los formatos visuales sirven para documentación. Un PNG no sustituye al modelo editable. En Android, seleccione la ubicación de guardado cuando aparezca el selector.
Para producir código, abra el panel de generación, configure las opciones y descargue los archivos. Después revise las instrucciones del proyecto generado y complete su configuración de entorno. Una descarga exitosa no prueba compilación ni funcionamiento completo. Los métodos de dominio pueden contener implementaciones pendientes.
### 8.8 Resolución de problemas
| Síntoma | Acción del usuario |
| Voz incorrecta | Revisar transcripción y probar la orden escrita |
| Consulta sin red | Utilizar el intérprete local admitido o recuperar conectividad |
| Foto con texto incompleto | Mejorar iluminación o corregir el borrador antes de importar |
| Clase duplicada | Revisar nombres y evitar importar dos veces el mismo lote |
| Cambios pendientes | Esperar conexión y comprobar permisos antes de repetir |
| Conflicto | Comparar ambas versiones y conservar la información necesaria |
| No se pudo guardar | Mantener abierta la app y exportar una copia si es posible |
| Modelos no disponibles | Preparar nuevamente recursos con conexión |
## 9 Verificación y aceptación del producto
Las pruebas automáticas verifican contratos y casos definidos; no miden por sí solas facilidad de uso, precisión general de voz o desempeño en cualquier dispositivo. Se distingue entre pruebas de componentes, recorridos internos y aceptación con usuarios y herramientas externas.
La última ejecución completa observada antes de las correcciones posteriores registró 97 pruebas Python y 15 suites JavaScript aprobadas. Después se verificaron 42 pruebas de generación y nuevas pruebas puntuales de foto, corrección y caché. Estos conteos pertenecen a ejecuciones diferentes y no deben sumarse como casos únicos.
### 9.1 Protocolo final de aceptación
| Prueba | Resultado observable | Estado documental |
| PA01 Modelado | Crear y conservar clases, atributos, métodos y relaciones | Evidencia parcial y pruebas automáticas |
| PA02 Colaboración | Dos usuarios editan; lector no modifica; conflicto explícito | Servidor y cliente probados; recorrido físico pendiente |
| PA03 Voz | Captura, transcripción y acción coherentes | Casos previos con errores; validación amplia pendiente |
| PA04 Foto | Recuperar elementos y revisar relaciones | Ejemplo bancario y sintéticos; corpus pendiente |
| PA05 Offline | Preparar, cerrar, reabrir y sincronizar sin pérdida | Componentes probados; Android integral pendiente |
| PA06 Generación | Compilar y ejecutar casos representativos | Generación probada; validación ampliada pendiente |
| PA07 Intercambio | Abrir y reexportar en herramientas destino | Recorridos internos probados; prueba externa pendiente |
### 9.2 Criterio de cierre
El producto se considera aceptado cuando se ejecutan los recorridos acordados en la versión que se entrega y se registran resultado, entorno, versión y evidencia. La documentación completa no convierte una prueba pendiente en aprobada. El estado de Transición y los límites de la entrega deben ser visibles en la presentación.
## 10 Conclusiones y continuidad
El proyecto integra modelado, reutilización de componentes y transformación de código alrededor de una representación común del diagrama. La arquitectura permite compartir funciones entre web y Android y separar los adaptadores y generadores del ingreso de datos. Las pruebas han permitido detectar fallos concretos y convertirlos en controles de regresión.
El resultado debe presentarse con sus evidencias y límites: las últimas mejoras del código aún requieren empaquetado y validación física, y el reconocimiento general de diagramas y la interoperabilidad externa necesitan recorridos adicionales. Estas limitaciones constituyen trabajo de aceptación identificado, no resultados que deban ocultarse en la documentación.
## Referencias
Android Developers. (s. f.). Build web apps in WebView. https://developer.android.com/develop/ui/views/layout/webapps/webview
Clements, P. C. (1995, 1 de noviembre). From subroutines to subsystems: Component-based software development. Software Engineering Institute. https://www.sei.cmu.edu/library/from-subroutines-to-subsystems-component-based-software-development/
Hugging Face. (s. f.). Use custom models. https://huggingface.co/docs/transformers.js/custom_usage
IBM. (s. f.). Project planning. https://www.ibm.com/docs/en/rational-clearquest/10.0.9?topic=settings-project-planning
IEEE. (s. f.). Computer aided software engineering (CASE). IEEE Technology Navigator. https://technav.ieee.org/topic/computer-aided-software-engineering-case/
Object Management Group. (2017). Unified Modeling Language (Version 2.5.1). https://www.omg.org/spec/UML/2.5.1/
Software Engineering Institute. (s. f.). Software architecture. https://www.sei.cmu.edu/software-architecture/
Tesseract OCR. (s. f.). Introduction. https://tesseract-ocr.github.io/tessdoc/Installation.html
## Anexo A Inventario de evidencias
El repositorio constituye la fuente de evidencia de implementación. Los archivos de referencia son backend/app/models/uml_model.py, backend/app/models/uml_validator.py, backend/app/services/collaboration.py, los generadores y adaptadores de backend/app/services, frontend/js/local-ai.js, frontend/js/collaboration.js y mobile-android/app/build.gradle.
Las suites relevantes incluyen test_collaboration.py, test_generators.py, test_full_generation.py, test_interop_roundtrip.py, test_client_reconnect.cjs, test_offline_queue.cjs, test_photo_visibility.cjs, test_photo_skew.cjs, test_photo_voice.cjs y test_service_worker_cache.cjs. El registro de continuidad contiene los resultados observados. No se adjuntan claves, tokens ni enlaces privados de colaboración.
## Anexo B Guion de demostración
1. Mostrar el alcance y distinguir editor móvil de aplicaciones generadas.
2. Crear una clase y explicar nombre, atributos, métodos y visibilidad.
3. Conectar dos clases y explicar el sentido de la relación.
4. Mostrar voz y foto con revisión antes de aceptar resultados dudosos.
5. Mostrar colaboración con un editor y un visualizador.
6. Ejecutar el recorrido offline solo si la versión instalada ya fue verificada.
7. Exportar el modelo y mostrar fuentes generadas.
8. Presentar la matriz de aceptación con pendientes identificados.
## Anexo C Ficha de registro de pruebas
Para cada nueva ejecución registrar: identificador de prueba, fecha, versión o commit, plataforma, precondiciones, pasos, resultado esperado, resultado obtenido, evidencia y decisión. No completar una ficha con resultados que no se hayan observado. Esta ficha permite cerrar los pendientes sin modificar retrospectivamente las pruebas anteriores.
## Anexo D Glosario
CASE: herramientas que apoyan actividades de ingeniería de software. Modelo: representación estructurada de elementos y relaciones. Metamodelo: estructura utilizada para describir los modelos admitidos. OCR: reconocimiento óptico de caracteres. Transcripción: conversión de audio a texto. Conflicto: diferencia que no puede resolverse combinando cambios independientes. APK: paquete de aplicación Android. XMI y MDJ: formatos utilizados por los adaptadores de intercambio del proyecto.
