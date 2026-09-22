# Requisitos de la documentación académica

Fuente: indicaciones del usuario recuperadas el 21 de septiembre de 2026. No sustituyen una plantilla institucional no suministrada.

| Requisito | Entregable | Estado |
|---|---|---|
| Fundamentación sin contenido inventado o ajeno al proyecto | Marco teórico con citas y aplicación al sistema | En preparación |
| Ingeniería de software asistida por computadora (CASE) | Fundamento y relación con modelado, validación y generación | Pendiente de desarrollo bibliográfico |
| Desarrollo basado en componentes | Inventario de componentes reutilizados y contratos | Inventario inicial disponible en código |
| Arquitectura flexible, extensible y mantenible | Arquitectura, decisiones, límites y riesgos | Documento previo requiere depuración |
| Mecanismo de aprendizaje para cualquier usuario | Manual y tutorial web/Android | Manual previo por contrastar con interfaz actual |
| Anexos y carátula | Evidencias, modelos y datos académicos | Datos de portada pendientes |
| Formato APA | Citas, referencias y maquetación | APA 7 como base provisional |
| Capítulo dedicado al diagrama de clases | Diseño explicado con UML 2.5 o superior | Modelos existentes pendientes de contraste |
| Registro fiel al Proceso Unificado | Fases, iteraciones, artefactos y trazabilidad | Borrador con nueve casos y once historias |
| Software entregado como producto completo | Matriz de aceptación y evidencias | No declarar completo mientras haya pendientes |

No inventar cronogramas, resultados, entrevistas, lecturas, mediciones ni aprobación del docente. Distinguir requisitos de resultados observados. Las cuatro fases de PUD no equivalen automáticamente a cuatro capítulos del documento.

## Inventario inicial de reutilización comprobado

- FastAPI, Pydantic y Jinja2: declarados en backend/requirements.txt.
- AndroidX WebKit: declarado en mobile-android/app/build.gradle.
- Tesseract y modelo local de transcripción: integración en frontend/js/local-ai.js y recursos offline.
- Metamodelo, adaptadores y generadores propios: backend/app/models y backend/app/services.

El uso de bibliotecas demuestra reutilización, pero no prueba por sí solo una arquitectura completamente desacoplada ni escalabilidad medida.

## Fuentes localizadas para lectura y citación

- Object Management Group. (2017). *Unified Modeling Language, version 2.5.1*. https://www.omg.org/spec/UML/2.5.1/About-UML
- IBM. (s. f.). *Project planning*. https://www.ibm.com/docs/en/rational-clearquest/10.0.9?topic=settings-project-planning
- Android Developers. (s. f.). *Build web apps in WebView*. https://developer.android.com/develop/ui/views/layout/webapps/webview
- FastAPI. (s. f.). *Dependencies*. https://fastapi.tiangolo.com/tutorial/dependencies/

Referencias preliminares: comprobar autoría y fecha visible de cada página durante la revisión bibliográfica final. La capacidad de inyección de dependencias de FastAPI no debe atribuirse al proyecto sin identificar dónde se usa.
