# Manual de Usuario — GeneradorUML

**Versión:** 1.0.0  
**Fecha:** Septiembre 2026  
**Proyecto:** GeneradorUML — Herramienta CASE de Ingeniería de Software Asistida por Computadora  

---

## Índice

1. [Introducción y Requisitos del Sistema](#1-introducción-y-requisitos-del-sistema)
2. [Puesta en Marcha Rápida](#2-puesta-en-marcha-rápida)
3. [Interfaz del Editor Web](#3-interfaz-del-editor-web)
4. [Modelado de Clases y Elementos](#4-modelado-de-clases-y-elementos)
5. [Definición de Relaciones entre Clases](#5-definición-de-relaciones-entre-clases)
6. [Validación Semántica UML 2.5+](#6-validación-semántica-uml-25)
7. [Entrada y Dictado por Voz](#7-entrada-y-dictado-por-voz)
8. [Interpretación de Fotografías de Pizarra o Papel](#8-interpretación-de-fotografías-de-pizarra-o-papel)
9. [Interoperabilidad: XMI 2.1 y StarUML](#9-interoperabilidad-xmi-21-y-staruml)
10. [Generación de Aplicaciones Completas](#10-generación-de-aplicaciones-completas)
11. [Guía de Ejecución del Código Generado](#11-guía-de-ejecución-del-código-generado)
12. [Colaboración en Tiempo Real y Modo Offline](#12-colaboración-en-tiempo-real-y-modo-offline)
13. [Atajos de Teclado y Productividad](#13-atajos-de-teclado-y-productividad)

---

## 1. Introducción y Requisitos del Sistema

**GeneradorUML** es una herramienta CASE (Computer-Aided Software Engineering) moderna diseñada para asistir en el ciclo de vida de desarrollo de software: permite modelar visualmente diagramas de clases UML 2.5+, validar su corrección semántica, dictar componentes por voz, interpretar diagramas dibujados a mano en fotos de pizarras o papel, importar/exportar proyectos en estándares internacionales (XMI 2.1 y StarUML MDJ), y finalmente generar aplicaciones de producción funcionales de extremo a extremo:
- **Backend:** Spring Boot 3.x con Java 17, Spring Data JPA / Hibernate, controladores REST y PostgreSQL.
- **Frontend Móvil:** Aplicación completa Flutter 3.x con Material 3, pantallas CRUD con formularios reactivos, validación, búsqueda, caché offline y pantalla de Asistente IA/Voz.
- **Pruebas de API:** Colección Postman v2.1.0 completa con scripts de pruebas automatizadas y variables de entorno.

### Requisitos Mínimos:
- **Sistema Operativo:** Windows 10/11, Linux (Ubuntu 20.04+) o macOS.
- **Python:** 3.10 o superior (con `pip`).
- **Navegador Web:** Chrome, Edge, Brave o Firefox (se recomienda Chromium para Web Speech API).
- **Para ejecutar backend generado:** Java JDK 17+ y Apache Maven 3.8+.
- **Para ejecutar app móvil generada:** Flutter SDK 3.10+ y Android Studio o emulador.
- **Base de Datos:** PostgreSQL 14+ (o contenedor Docker con postgres:15).

---

## 2. Puesta en Marcha Rápida

1. **Abrir la terminal en la raíz del proyecto:**
   ```bash
   cd generador-uml/backend
   ```

2. **Instalar dependencias Python:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Iniciar el servidor backend:**
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

4. **Acceder a la aplicación:**
   Abre tu navegador en: [http://localhost:8000](http://localhost:8000)

---

## 3. Interfaz del Editor Web

La interfaz ha sido diseñada con un sistema visual oscuro y moderno (estilo glassmorphism) optimizado para sesiones de diseño prolongadas:

- **Barra Superior (Topbar):**
  - **Identificador de Proyecto:** Edita el nombre del diagrama con un clic.
  - **Insignia de Colaboración:** Muestra el estado del WebSocket (`🟢 Conectado` o `🟡 Modo Local`).
  - **Pestañas Editor / Generar:** Alterna entre el lienzo de modelado y el panel de generación de código.
  - **Acceso Directo a Funciones:** Entrada por voz (`🎤`), Cargar fotografía (`📷`), Importar archivo (`📥`), Exportar (`📤`), Guardar proyecto (`💾` o `Ctrl+S`), y botón principal **Generar Código**.
- **Barra Lateral Izquierda (Herramientas):**
  - **Elementos:** Clase, Interfaz, Clase Abstracta.
  - **Relaciones:** Asociación, Agregación, Composición, Herencia (Generalización), Realización, Dependencia.
  - **Historial:** Deshacer (`Ctrl+Z`) y Rehacer (`Ctrl+Y`).
  - **Control de Zoom y Centrado:** Acercar, alejar y centrar lienzo.
- **Lienzo Central (Canvas SVG Interactivo):**
  - Cuadrícula milimétrica con soporte para arrastrar (`Pan`) manteniendo clic derecho o barra espaciadora.
  - Zoom con rueda del ratón (`Mouse Wheel`).
  - Arrastre fluido de nodos con recálculo dinámico de conectores y ángulos de flechas en tiempo real.
- **Barra Lateral Derecha (Panel de Propiedades):**
  - Al seleccionar cualquier clase o relación, despliega un editor detallado donde se configuran visibilidad, estereotipos, atributos (nombre, tipo, visibilidad, valor por defecto), operaciones (parámetros y tipo de retorno) o multiplicidades y roles.

---

## 4. Modelado de Clases y Elementos

### 4.1 Creación de Clases
1. Haz clic en el botón **Clase** en la barra lateral izquierda (o presiona la tecla `C`).
2. Haz clic en cualquier parte del lienzo para colocar la nueva clase.
3. Selecciona la clase para que se resalte con borde azul violeta y se abra el panel de propiedades.
4. En el panel de propiedades puedes:
   - Modificar el nombre de la clase (e.g., `Mascota`, `Cliente`, `Veterinario`).
   - Marcar si es una **Interfaz** o **Clase Abstracta**.
   - Definir un **Estereotipo** (e.g., `<<entity>>`, `<<service>>`, `<<repository>>`).

### 4.2 Gestión de Atributos
- Haz clic en el botón `+` en la sección de atributos del panel de propiedades.
- Configura:
  - **Visibilidad:** `-` (Privado), `+` (Público), `#` (Protegido), `~` (Paquete).
  - **Nombre:** Identificador camelCase (e.g., `fechaNacimiento`, `telefono`).
  - **Tipo:** `String`, `Integer`, `Long`, `Double`, `Boolean`, `LocalDate`, `LocalDateTime`, `BigDecimal`, etc.

### 4.3 Gestión de Operaciones (Métodos)
- Haz clic en el botón `+` en la sección de operaciones.
- Configura:
  - **Visibilidad y Nombre:** (e.g., `+ calcularEdad`).
  - **Tipo de retorno:** (e.g., `Integer`, `void`, `Boolean`).
  - **Parámetros:** Lista de parámetros formales con nombre y tipo.

---

## 5. Definición de Relaciones entre Clases

GeneradorUML soporta los 6 tipos estándar de relación UML 2.5:

| Tipo de Relación | Representación Visual | Significado en Spring Boot / JPA |
| :--- | :--- | :--- |
| **Asociación** | Línea con flecha abierta | `@ManyToOne` / `@OneToMany` estándar |
| **Agregación** | Rombo blanco en origen | Relación todo-parte débil |
| **Composición** | Rombo negro relleno en origen | `@OneToMany(cascade = ALL, orphanRemoval = true)` |
| **Herencia** | Triángulo blanco hueco | `@Inheritance(strategy = JOINED)` con `@SuperBuilder` |
| **Realización** | Línea discontinua con triángulo | Implementación de `interface` Java |
| **Dependencia** | Línea discontinua con flecha | Inyección de servicio o dependencia de uso |

### Cómo conectar dos clases:
1. Haz clic en la herramienta de relación deseada en la barra izquierda (ej. **Composición**).
2. Haz clic en la clase origen (por ejemplo, `Cliente`).
3. Verás una línea elástica discontinua guiando el cursor.
4. Haz clic en la clase destino (por ejemplo, `Mascota`).
5. La relación se creará instantáneamente con sus terminadores gráficos oficiales y multiplicidades por defecto (`1` a `0..*`).
6. Al hacer clic en la línea de la relación, puedes cambiar las multiplicidades en el panel derecho (`1`, `0..1`, `*`, `1..*`, `n..m`) y asignar nombres de rol.

---

## 6. Validación Semántica UML 2.5+

GeneradorUML incorpora un validador semántico en tiempo de edición que previene inconsistencias arquitectónicas antes de generar código:

- **Herencia Circular:** Detecta ciclos inválidos como `A -> B -> C -> A`.
- **Atributos y Métodos Duplicados:** Alerta si una clase contiene dos atributos con el mismo identificador.
- **Relaciones Huérfanas:** Detecta conexiones cuyos extremos apuntan a clases inexistentes.
- **Consistencia de Clases Abstractas e Interfaces:** Verifica que las interfaces no declaren atributos mutables no estáticos.

Para ejecutar la validación manual, haz clic en el botón de validación o abre el panel de generación de código; el sistema listará advertencias y errores en color ámbar y rojo respectivamente.

---

## 7. Entrada y Dictado por Voz

Para acelerar el modelado o permitir accesibilidad total, el sistema cuenta con integración de dictado en lenguaje natural en español:

1. Haz clic en el icono de micrófono (`🎤`) en la barra superior.
2. Haz clic en **Comenzar** y pronuncia tu instrucción con claridad.
3. Ejemplos de comandos admitidos:
   - *"Crear clase Veterinario"*
   - *"Agregar atributo especialidad tipo String a Veterinario"*
   - *"Agregar atributo telefono tipo String a Cliente"*
   - *"Crear relación de composición de Cliente a Mascota"*
   - *"Agregar operación vacunar a Mascota que retorna void"*
4. La transcripción se mostrará en pantalla.
5. Haz clic en **Aplicar** (o se procesará automáticamente al finalizar la frase) y el elemento se insertará directamente en el lienzo.

---

## 8. Interpretación de Fotografías de Pizarra o Papel

¿Tienes un diagrama bosquejado a mano en una pizarra o en una hoja de cuaderno? GeneradorUML cuenta con un pipeline de Computer Vision y OCR:

### Pasos para interpretar:
1. Haz clic en el botón de fotografía (`📷`) en la barra superior.
2. Arrastra una imagen fotográfica (JPG, PNG) o haz clic para seleccionarla.
3. Haz clic en **Interpretar Diagrama**.
4. El servidor procesará la imagen:
   - Binarización adaptativa de bordes.
   - Detección de cajas de clases y compartimentos de atributos/métodos.
   - Extracción de texto mediante OCR de alta resolución.
   - Detección de líneas de conexión entre cajas mediante transformada de Hough.
5. **Revisión Humana (Human-in-the-Loop):**
   - El sistema presentará un panel con el nivel de confianza (e.g., `Confianza: 85%`), número de clases y relaciones detectadas, y observaciones.
   - Haz clic en **✓ Aceptar e Importar al Lienzo** para plasmar el diagrama editable en el lienzo SVG.

### Recomendaciones para mejores resultados:
- Tomar la fotografía de frente, evitando ángulos muy inclinados.
- Asegurar buena iluminación sin sombras densas sobre el texto.
- Usar trazos definidos con marcadores negros o azules sobre fondo blanco.

---

## 9. Interoperabilidad: XMI 2.1 y StarUML

GeneradorUML garantiza portabilidad total con las herramientas CASE de la industria:

### Exportar:
1. Haz clic en el botón **Exportar** (`📤`).
2. Elige el formato deseado:
   - **GeneradorUML JSON:** Formato nativo con coordenadas exactas del canvas.
   - **XMI 2.1 (ISO/IEC 19509):** Compatible directamente con Enterprise Architect y StarUML.
   - **StarUML (.mdj):** Archivo JSON con estructura nativa de StarUML 3.x/4.x/5.x.
   - **Imagen SVG:** Gráfico vectorial escalable con fondo oscuro para reportes y diapositivas.

### Importar:
1. Haz clic en el botón **Importar** (`📥`).
2. Selecciona un archivo `.json`, `.mdj`, `.xmi` o `.xml`.
3. El sistema reconocerá automáticamente el estándar, parseará las clases, atributos, métodos y relaciones, y renderizará el modelo en el lienzo.

---

## 10. Generación de Aplicaciones Completas

1. Diseña o carga tu diagrama (por ejemplo, el caso de prueba `examples/veterinaria.json`).
2. Haz clic en el botón violeta **Generar Código** o en la pestaña **Generar**.
3. Se abrirá el panel de generación con estadísticas en tiempo real:
   - Total de clases, relaciones, atributos y operaciones.
   - **Paquete base:** `com.generated.app` (configurable).
   - Opciones activas: Spring Boot + PostgreSQL, Flutter móvil, Colección Postman.
4. Opciones disponibles:
   - **Generar Aplicación:** Genera los archivos en el servidor bajo la carpeta `output/project_YYYYMMDD_HHMMSS/`.
   - **Descargar ZIP:** Empaqueta todo el proyecto (Spring Boot + Flutter + Postman) en un archivo comprimido descargable con un solo clic.

---

## 11. Guía de Ejecución del Código Generado

### 11.1 Ejecución del Backend Spring Boot

1. **Revisar base de datos:**
   Asegúrate de que PostgreSQL esté corriendo con una base de datos creada:
   ```sql
   CREATE DATABASE app_db;
   ```
   *Nota:* Las credenciales por defecto se encuentran en `src/main/resources/application.properties` (`user: postgres`, `password: postgres`, `port: 5432`).

2. **Compilar y ejecutar con Maven:**
   ```bash
   cd output/project_<timestamp>/springboot
   # Si cuentas con Maven instalado:
   mvn clean compile spring-boot:run
   # O usando el wrapper en Windows:
   .\mvnw.cmd spring-boot:run
   ```
3. El backend iniciará en `http://localhost:8080`:
   - Las tablas de base de datos se crearán automáticamente gracias a `spring.jpa.hibernate.ddl-auto=update`.
   - Podrás acceder a los endpoints REST de cada entidad (ej. `GET /api/clientes`, `GET /api/mascotas`, etc.).

### 11.2 Ejecución de la App Móvil / Web Flutter

1. **Generar soporte de plataforma nativa (Web, Desktop, Móvil):**
   Dado que el generador produce el código Dart limpio (`lib/` y `pubspec.yaml`), inicializa las carpetas de plataforma correspondientes:
   ```bash
   cd output/project_<timestamp>/flutter_app
   flutter create .
   ```

2. **Instalar dependencias Dart:**
   ```bash
   flutter pub get
   ```

3. **Configurar URL del servidor:**
   En `lib/services/api_config.dart`, la URL base apunta por defecto a:
   - `http://10.0.2.2:8080/api` para emuladores Android.
   - `http://localhost:8080/api` para Flutter Web o Desktop.

4. **Lanzar la aplicación:**
   ```bash
   # Para probar en navegador Chrome:
   flutter run -d chrome
   # O en emulador/dispositivo conectado:
   flutter run
   ```

### 11.3 Ejecución de la Colección Postman

1. Abre **Postman**.
2. Haz clic en **Import** y selecciona el archivo `postman_collection.json`.
3. Verás una colección estructurada con carpetas para cada clase del diagrama:
   - `Crear <Clase>` (POST con JSON de ejemplo precargado).
   - `Listar <Clase>` (GET).
   - `Buscar <Clase> por ID` (GET).
   - `Actualizar <Clase>` (PUT).
   - `Eliminar <Clase>` (DELETE).
4. Cada petición incluye pruebas de aserción automáticas (`pm.test("Status code is 200/201")`).

---

## 12. Colaboración en Tiempo Real y Modo Offline

- **Colaboración en Vivo:**
  Al trabajar en equipo sobre el mismo proyecto, GeneradorUML se conecta automáticamente al canal WebSocket `/ws/{project_id}`. Cualquier cambio en las clases o relaciones se propaga instantáneamente a los lienzos de los demás diseñadores sin recargar la página.
- **Modo Offline Resiliente:**
  Si se pierde la conexión de red o el servidor se reinicia, el indicador de estado cambiará a `🟡 Modo Local`. Todo el trabajo se guarda de forma continua en `localStorage`. Al pulsar `Ctrl+S`, se guardará tanto localmente como en el servidor cuando regrese la conectividad.

---

## 13. Atajos de Teclado y Productividad

| Atajo | Acción |
| :--- | :--- |
| `Ctrl + S` / `Cmd + S` | Guardar proyecto actual (servidor y local) |
| `Ctrl + Z` / `Cmd + Z` | Deshacer última acción en el lienzo |
| `Ctrl + Y` / `Cmd + Shift + Z` | Rehacer acción revertida |
| `C` | Activar herramienta de nueva Clase |
| `Delete` / `Supr` | Eliminar elemento seleccionado |
| `Rueda del Ratón` | Acercar / Alejar zoom del lienzo |
| `Clic Derecho + Arrastrar` | Desplazamiento panorámico (Pan) del lienzo |
| `Escape` | Cancelar trazado de relación o deseleccionar |

---
*GeneradorUML — Desarrollado para la presentación académica de Ingeniería de Software.*
