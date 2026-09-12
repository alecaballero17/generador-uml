# Documento de Arquitectura y Decisiones de Diseño — GeneradorUML

**Versión:** 1.0.0  
**Fecha:** Septiembre 2026  
**Proyecto:** GeneradorUML — Herramienta CASE de Ingeniería de Software Asistida por Computadora  

---

## 1. Visión General de la Arquitectura

GeneradorUML está construido siguiendo los principios de **Clean Architecture**, alta cohesión y bajo acoplamiento. El sistema se compone de dos subsistemas principales:

1. **Frontend (SPA en HTML5 + SVG + Vanilla CSS/JS):**
   - Lienzo vectorial basado en estándares W3C SVG.
   - Sin dependencias de frameworks pesados para garantizar máxima reactividad a 60 FPS.
   - Sistema de diseño de modo oscuro con glassmorphism, tipografía Inter/JetBrains Mono y microanimaciones fluidas.
   - Capa de comunicación asíncrona dual: REST API para operaciones transaccionales y WebSockets para sincronización colaborativa en tiempo real.
   - Almacenamiento local `localStorage` como fallback offline de alta disponibilidad.

2. **Backend (Python 3.11+ con FastAPI):**
   - Núcleo de metamodelo orientado a objetos desacoplado de la infraestructura.
   - Motores de generación especializados para Spring Boot 3.x, Flutter 3.x y Postman.
   - Adaptadores de interoperabilidad para XMI 2.1 (ISO/IEC 19509) y StarUML `.mdj`.
   - Pipeline de Visión por Computadora y OCR (OpenCV + Tesseract) con enfoque *Human-in-the-Loop*.

```
+---------------------------------------------------------------------------------+
|                                 NAVEGADOR WEB                                   |
|  +---------------------------+   +-------------------+   +--------------------+  |
|  |   Lienzo SVG Interactivo  |   | Reconocimiento    |   |  Gestión de Estado |  |
|  |  (Clases, Conectores, Pan)|   | Voz (Web Speech)  |   |  (Undo, Redo, Cache|  |
|  +-------------+-------------+   +---------+---------+   +----------+---------+  |
+----------------|---------------------------|------------------------|-----------+
                 | REST API (HTTP/JSON)      |                        | WebSocket
                 v                           v                        v
+---------------------------------------------------------------------------------+
|                             FASTAPI BACKEND (Python)                            |
|                                                                                 |
|   +-------------------------------------------------------------------------+   |
|   |                       METAMODELO UML 2.5+ INTERNO                       |   |
|   |   (UMLDiagram, UMLClass, UMLAttribute, UMLOperation, UMLRelationship)   |   |
|   +------------------------------------+------------------------------------+   |
|                                        |                                        |
|         +------------------------------+------------------------------+         |
|         |                              |                              |         |
|         v                              v                              v         |
|  +--------------+               +--------------+              +---------------+ |
|  | Spring Boot  |               | Flutter 3.x  |              | XMI 2.1 &     | |
|  | Generator    |               | Generator    |              | StarUML MDJ   | |
|  +-------+------+               +-------+------+              +-------+-------+ |
|          |                              |                             |         |
|          v                              v                             v         |
|  [Java 17, JPA,                 [Dart, M3 CRUD,               [Enterprise       |
|   PostgreSQL, REST]              Offline Cache, Voice]         Architect, MDJ]  |
+---------------------------------------------------------------------------------+
```

---

## 2. Metamodelo UML Interno y Validador Semántico

El núcleo de GeneradorUML no manipula representaciones crudas de bases de datos ni árboles sintácticos de un lenguaje específico, sino un **metamodelo formal UML 2.5.1**:

- `UMLDiagram`: Raíz del grafo de modelado. Agrupa clases, relaciones y metadatos de versión.
- `UMLClass`: Representa clasificadores (clases estándar, abstractas o interfaces) con su identificador UUID inmutable, visibilidad y estereotipo.
- `UMLAttribute`: Atributo tipado con visibilidad, multiplicidad opcional, valor inicial y banderas de modificador (`is_static`, `is_final`, `is_derived`).
- `UMLOperation`: Métodos con lista de `UMLParameter` tipados y tipo de retorno.
- `UMLRelationship`: Representa arcos dirigidos o no dirigidos con extremos `RelationshipEnd` que definen multiplicidad (`1`, `0..1`, `*`, `1..*`), navegabilidad y rol semántico.

### Validador Semántico (`UMLValidator`)
El validador inspecciona el diagrama previo a la persistencia o generación:
1. **Detección de Herencia Circular:** Construye un grafo dirigido de generalizaciones y ejecuta un análisis de ciclos mediante DFS (Depth-First Search). Si encuentra un ciclo, emite un error bloqueante con la traza de clases implicadas.
2. **Atributos y Operaciones Duplicados:** Valida colisiones de nombres dentro de la misma clase.
3. **Integridad Referencial de Relaciones:** Verifica que los extremos `source` y `target` correspondan a clases existentes en el diagrama.

---

## 3. Estrategia de Mapeo Relacional Objeto (JPA / Hibernate)

El generador Spring Boot (`SpringBootGenerator`) traduce la semántica UML a anotaciones de la especificación JPA 3.x de manera estricta:

### 3.1 Composición vs. Agregación y Asociación
- **Composición UML (Rombo relleno):** Implica ciclo de vida dependiente estricto (todo-parte fuerte). Si la clase contenedora se elimina, las partes se destruyen.
  ```java
  @OneToMany(mappedBy = "cliente", cascade = CascadeType.ALL, orphanRemoval = true)
  private List<Mascota> mascotas = new ArrayList<>();
  ```
- **Asociación y Agregación UML (Rombo hueco o flecha abierta):** Relación débil con ciclo de vida independiente:
  ```java
  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "veterinario_id")
  private Veterinario veterinario;
  ```

### 3.2 Estrategia de Herencia
Para clases que heredan de otra clase abstracta o concreta, se genera:
```java
@Entity
@Inheritance(strategy = InheritanceType.JOINED)
public abstract class Persona { ... }

@Entity
public class Cliente extends Persona { ... }
```
`InheritanceType.JOINED` se seleccionó como la estrategia óptima porque normaliza la base de datos relacional, evitando columnas nulas redundantes (típicas de `SINGLE_TABLE`) y facilitando la integridad referencial y auditorías.

### 3.3 Mapeo de Tipos de Datos
| Tipo UML | Tipo Java (JPA) | Tipo Dart (Flutter) | Tipo PostgreSQL |
| :--- | :--- | :--- | :--- |
| `String` | `String` | `String` | `VARCHAR(255)` / `TEXT` |
| `Integer`, `int` | `Integer` | `int` | `INTEGER` |
| `Long` | `Long` | `int` | `BIGINT` |
| `Double`, `Float` | `Double` | `double` | `DOUBLE PRECISION` |
| `Boolean` | `Boolean` | `bool` | `BOOLEAN` |
| `LocalDate`, `Date` | `java.time.LocalDate` | `DateTime` | `DATE` |
| `LocalDateTime` | `java.time.LocalDateTime` | `DateTime` | `TIMESTAMP` |
| `BigDecimal` | `java.math.BigDecimal` | `double` | `NUMERIC(19, 2)` |

---

## 4. Arquitectura de la Aplicación Flutter Generada

La aplicación móvil generada en `flutter_app/` adopta un diseño moderno y resiliente:

1. **Patrón de Presentación (Material 3):**
   - Soporte para tema claro y oscuro con colores armoniosos.
   - Navegación clara mediante `NavigationRail` / `BottomNavigationBar`.
   - Pantalla de Dashboard con tarjetas de resumen de entidades y accesos directos.
2. **Capa de Modelo Inmutable:**
   - Cada clase del diagrama genera un modelo Dart con serializadores seguros `fromJson` y `toJson`, y método `copyWith` para actualizaciones inmutables.
3. **Capa de Servicio HTTP Desacoplada:**
   - Servicios REST dedicados para cada entidad (`ClienteService`, `MascotaService`, etc.).
   - Parámetros de URL dinámicos centralizados en `ApiConfig.baseUrl`.
4. **Caché Offline y Fallback Transparente (`OfflineCacheService`):**
   - Cuando el dispositivo no tiene acceso a internet o el backend está caído, las pantallas leen automáticamente de la caché local `SharedPreferences`.
   - Las operaciones de escritura en modo offline se encolan con una bandera para sincronizarse al restablecer la conexión.
5. **Asistente de Voz / IA Integrado (`AssistantScreen`):**
   - Pantalla interactiva en Flutter que permite consultar datos del sistema o ejecutar acciones en lenguaje natural.

---

## 5. Pipeline de Computer Vision y OCR (Fotos de Pizarra)

El módulo `PhotoInterpreter` procesa fotografías reales de pizarras o papel:

1. **Preprocesamiento:**
   - Conversión a escala de grises.
   - Suavizado Gaussiano `(5, 5)` para atenuar ruido de compresión de imagen.
   - Binarización adaptativa (`cv2.adaptiveThreshold` con `GAUSSIAN_C`), indispensable para compensar iluminaciones desiguales en pizarras.
2. **Segmentación y Detección de Cajas:**
   - Dilatación morfológica para conectar líneas discontinuas dibujadas con marcador.
   - Extracción de contornos (`cv2.findContours`) con filtrado por relación de aspecto (0.4 a 3.5) y área relativa (0.5% a 40% del total de la imagen).
   - Detección secundaria mediante kernels morfológicos rectangulares horizontales y verticales cruzados para pizarras con líneas finas.
3. **OCR y Parsing Semántico:**
   - Para cada ROI (Region of Interest) detectada, se aplica reescalado cúbico 1.8x y denoising antes de alimentar el motor Tesseract.
   - Las líneas de texto se analizan sintácticamente mediante expresiones regulares:
     - Identificación del estereotipo `<<interface>>`.
     - Atributos con formato `[+-#~] nombre: Tipo [= valor]`.
     - Operaciones con formato `[+-#~] nombre(p1: T1): TipoRetorno`.
4. **Detección de Conexiones:**
   - Transformada probabilística de Hough (`cv2.HoughLinesP`) para encontrar segmentos rectilíneos.
   - Asociación geométrica de los extremos de la línea con las cajas de clases más cercanas (distancia euclidiana mínima).
5. **Human-in-the-Loop:**
   - La visión artificial no debe sobreescribir ciegamente un proyecto sin confirmación. El servicio calcula un índice de confianza y genera un informe estructurado que el diseñador revisa en el navegador antes de aceptar la importación.

---

## 6. Interoperabilidad: XMI 2.1 y StarUML

### 6.1 XMI 2.1 (ISO/IEC 19509)
- Genera XML conforme al esquema estándar OMG UML 2.1 / 2.5:
  - Espacio de nombres: `http://schema.omg.org/spec/XMI/2.1` y `http://www.omg.org/spec/UML/20131001`.
  - Estructura `xmi:XMI -> uml:Model -> packagedElement`.
  - Propiedades tipadas con primitivas OMG (`PrimitiveTypes.xmi#String`, `#Integer`, `#Boolean`).
  - Compatible en importación y exportación con **Enterprise Architect** (Sparx Systems) y **StarUML**.

### 6.2 StarUML (.mdj)
- Archivo JSON estructurado en jerarquía nativa:
  - `Project` -> `UMLModel` -> `UMLClassDiagram`.
  - Preserva vistas visuales (`UMLClassView`, `UMLAttributeCompartmentView`, `UMLOperationCompartmentView`) y nodos lógicos (`UMLClass`, `UMLAttribute`, `UMLOperation`, `UMLAssociation`).
  - Importación y exportación probada con 100% de preservación de clases y relaciones.

---

## 7. Sincronización en Tiempo Real y Persistencia Local

### WebSocket Manager
El servidor FastAPI implementa un `ConnectionManager` que agrupa conexiones por `project_id`:
- Cuando un cliente realiza una modificación en el lienzo (mover clase, cambiar atributo, añadir relación), emite un evento `diagram_update` debounced a 250ms.
- El servidor difunde el mensaje a los demás clientes conectados al mismo proyecto (`exclude=websocket_emisor`).
- Los clientes remotos actualizan su lienzo sin redisparar el broadcast (`isRemoteUpdate = true`), evitando bucles de mensajes.

### Persistencia Híbrida
- En el servidor: Los proyectos se guardan en `output/projects/{project_id}.json`.
- En el cliente: Cada cambio se serializa inmediatamente en `localStorage.getItem('generador_uml_current')`. Si el usuario cierra el navegador o se desconecta el servidor, al recargar la página su diagrama se restaura íntegramente.

---
*GeneradorUML — Documento de Arquitectura de Software.*
