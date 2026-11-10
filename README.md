# GeneradorUML

Herramienta CASE para editar diagramas de clases, colaborar, intercambiar modelos y generar aplicaciones CRUD Spring Boot y Flutter a partir del mismo diagrama.

**Web pública:** [generador-uml.onrender.com](https://generador-uml.onrender.com) · **Revisión:** 10 de noviembre de 2026.

El primer ciclo académico establece el editor y la transformación del modelo. El segundo amplía la generación de APK, seguimiento móvil, interoperabilidad y recuperación. Son ciclos incrementales del Proceso Unificado; no sustituyen sus fases de Inicio, Elaboración, Construcción y Transición.

## Capacidades

- Modelado de clases, atributos, operaciones, relaciones, extremos y multiplicidades; deshacer y validación estructural.
- Fotografías con lectura local o Gemini en línea, revisión del borrador y confirmación de conexiones.
- **Clase de asociación**: Venta y Producto muchos a muchos, con Detalle unido a la asociación mediante línea discontinua.
- Colaboración por WebSockets, permisos, revisiones, resolución de conflictos, conversación y acuerdos del equipo.
- Asistencia por texto/voz e IA; las propuestas del equipo requieren aplicación explícita. Gemini necesita conexión y configuración.
- Intercambio JSON, XMI 2.1 y MDJ; exportación SVG, PNG, PlantUML y Mermaid, dentro del alcance de cada formato.
- Generación de backend REST Spring Boot/JPA, cliente Flutter y colección Postman.
- **Compilación local de APK**, con seis etapas, errores visibles y descargas reales.
- **Guardar en Google Drive** una copia JSON editable y restaurarla mediante descarga e importación.

No se implementa toda UML ni se deduce la lógica comercial completa de nombres de métodos. La validación estructural no es una certificación UML.

## Dos aplicaciones Android diferentes

| Aplicación | Finalidad | Tecnología |
|---|---|---|
| Graficador UML / seguimiento | Consultar diagrama, actividad y conversación; recibir notificaciones | Contenedor Android con contenido web y capacidades nativas |
| APK generada del diagrama | Crear, consultar, editar y eliminar registros del dominio, con referencias al backend generado | Flutter + API Spring Boot |

La APK del dominio ofrece inicio, secciones, registros y ajustes, con modos claro y oscuro. Los formularios dependen del modelo; no se agrega un asistente de voz ajeno al dominio. La aplicación informativa no sustituye al CRUD generado.

## Inicio local en Windows

```powershell
git clone https://github.com/alecaballero17/generador-uml.git
cd generador-uml
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
powershell -NoProfile -File scripts/Start-Local.ps1
```

Abrir [http://127.0.0.1:8765](http://127.0.0.1:8765) y mantener la terminal abierta. Para lectura local de imágenes se necesita Tesseract y sus idiomas. Para compilar se requieren Java, Maven, Flutter y Android SDK; la primera ejecución puede descargar dependencias.

Importar un diagrama, validarlo y abrir **Generar Código → Generar y compilar APK (local)**. El panel muestra generación, prueba del backend, preparación de Flutter, prueba móvil, compilación Android y preparación de descarga. **APK lista** significa que existe el archivo compilado: todavía hay que descargarlo e instalarlo. Apagar la computadora interrumpe la construcción; revisar el estado e iniciar otro trabajo si quedó interrumpida.

Los backends generados son aplicaciones independientes. Consultar las instrucciones del paquete y los scripts:

```powershell
powershell -NoProfile -File scripts/Start-Generated.ps1 -BuildId <identificador>
powershell -NoProfile -File scripts/Install-GeneratedApk.ps1 -BuildId <identificador>
```

Configurar en Ajustes una URL del backend accesible desde el teléfono. `localhost` en Android identifica al propio teléfono: se necesita el túnel ADB correspondiente o una dirección accesible por red. Ver [guía local y APK](docs/primera-parte.md).

## Render y almacenamiento

Render sirve frontend y API en un servicio Docker, escuchando en `0.0.0.0:$PORT`; control de salud: `/api/health`.

| Entorno público | Computadora local |
|---|---|
| Editor, colaboración y seguimiento web | Editor con herramientas de desarrollo |
| IA en línea configurada y generación de código | Lectura local y generación de código |
| Respaldo en Drive configurado | Compilación, prueba e instalación de APK |

**Render no compila APKs.** Mantener `UML_LOCAL_BUILD` desactivado en el servicio público. Publicar el editor tampoco publica cada backend Spring Boot generado.

Se utiliza el plan gratuito elegido para la demostración. **El almacenamiento del servidor es temporal**: reinicios y despliegues pueden eliminar salas, historial y suscripciones. El borrador del navegador y JSON/Drive permiten recuperar el diagrama, pero no conservan su historial ni el mismo enlace compartido.

Sin enlace, **Proyectos** permite crear un proyecto o retomar el guardado en ese navegador. Si un enlace pierde acceso, descargar el respaldo y elegir **Recuperar como proyecto compartido** crea una sala y un enlace nuevos. Chrome normal e incógnito tienen almacenamientos separados; pueden mostrar proyectos distintos con la misma versión de la aplicación.

Ver [despliegue en Render](docs/despliegue-render.md).

## Google Drive

Usar **Acciones → Guardar en Drive**, autorizar la cuenta y comprobar el archivo. Para recuperarlo, descargar el JSON e importarlo en el editor.

- Permiso limitado `drive.file`, para los archivos usados con esta aplicación.
- Carga directa del navegador a Drive; token de acceso únicamente en memoria, sin enviarlo al backend.
- Cada respaldo crea un archivo nuevo con el diagrama y sus posiciones. No incluye APK, código generado, historial, enlaces de acceso ni credenciales.
- OAuth está en prueba: agregar las cuentas autorizadas como usuarios de prueba. La aplicación no se presenta como verificada por Google.
- La autorización puede cerrarse o reintentarse tras el tiempo de espera. Si una carga se interrumpe después del envío, revisar Drive antes de repetirla.

El recorrido público de guardar, visualizar en Drive, descargar y reimportar un modelo de una clase se completó el 10 de noviembre de 2026. Ver [configuración de Drive](docs/google-drive.md).

## Configuración

| Variable | Uso |
|---|---|
| `GEMINI_API_KEY` | Secreto del servidor para IA en línea |
| `GEMINI_ASSISTANT_MODEL` | Selección del modelo del asistente |
| `GOOGLE_DRIVE_CLIENT_ID` | Identificador público del cliente OAuth web; no necesita client secret |
| `APP_DATA_DIR` | Directorio de datos del editor y colaboración |
| `UML_LOCAL_BUILD` | `1` únicamente en entorno local autorizado para compilar |
| `FIREBASE_SERVICE_ACCOUNT_JSON` o `FIREBASE_SERVICE_ACCOUNT` | Credencial de servidor para push nativo, como JSON o ruta de archivo secreto |

Usar variables de entorno o archivos excluidos de Git. Nunca publicar claves, tokens, secretos OAuth ni cuentas de servicio. Habilitar Drive API y registrar el origen autorizado antes de usar la integración.

## Interoperabilidad

Se comprobó **web → XMI → Enterprise Architect → XMI → web**, incluyendo clase de asociación e importación con `Strip GUIDs`. El generador convierte esa clase en referencias hacia ambos extremos sin cambiar el lienzo: Detalle referencia Venta y Producto y conserva sus propios atributos.

MDJ funciona para el alcance admitido, pero **se rechaza exportar clases de asociación** con mensaje explícito para evitar pérdida silenciosa. No se garantiza equivalencia entre todos los dialectos UML.

## Evidencia y pendientes

| Recorrido | Estado al 10 de noviembre de 2026 |
|---|---|
| Regresión | Ejecución registrada de 140 pruebas Python y 21 suites JavaScript; después se ejecutaron pruebas específicas de recuperación y Drive. Son ejecuciones diferentes, no un total acumulado de casos únicos. |
| Backend PostgreSQL | Newman: 31 peticiones y 57 comprobaciones sin fallos; referencias, errores y persistencia tras reinicio verificados localmente. No requiere Postman de escritorio. |
| APK Flutter física | Instalación y CRUD de Producto; creación de Vendedor, Cliente, Venta y Detalle con referencias válidas. |
| APK informativa | Notificación real en segundo plano con sonido y vibración; apertura del proyecto en pruebas locales. |
| Enterprise Architect | Recorrido manual de ida y vuelta con clase de asociación aprobado. |
| Foto manuscrita | Lectura local sin clases en la foto probada; Gemini recuperó cinco clases y un borrador revisable. No hay tasa general de precisión medida. |
| Despliegue público | Servicio Live, HTTPS y respaldo/restauración Drive comprobados. |
| Aceptación pública restante | Colaboración completa entre dos sesiones, seguimiento/push Android del proyecto público y repetición del flujo de generación publicado pendientes. El backend de negocio no está desplegado como servicio público independiente. |

Las pruebas locales no sustituyen la aceptación en Render. No se presentan pruebas pendientes como aprobadas.

## Estructura y documentación

El frontend usa HTML, CSS y JavaScript. FastAPI/SQLite pertenecen al editor; Spring Boot/JPA y Flutter pertenecen a las aplicaciones generadas.

```text
backend/app/models/       Metamodelo y validación
backend/app/services/     Colaboración, OCR/IA, adaptadores y generadores
frontend/js/              Lienzo, sesiones, colaboración y Drive
mobile-android/           Aplicación Android de seguimiento
scripts/                  Arranque, compilación e instalación local
tests/                    Regresión Python y JavaScript
examples/                 Modelos de prueba
docs/                     Arquitectura, manuales e informes académicos
```

- [Proceso Unificado y trazabilidad](docs/proceso_unificado_pud.md)
- [Arquitectura](docs/arquitectura.md)
- [Manual de usuario](docs/manual_usuario.md)
- [Guía local y APK](docs/primera-parte.md)
- [Render](docs/despliegue-render.md)
- [Google Drive](docs/google-drive.md)
- [Documentación académica del primer ciclo](docs/entrega/)

Los informes anteriores conservan el estado de su fecha. Para la revisión vigente, consultar este README y distinguir entorno, versión y resultado observado.
