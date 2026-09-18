# Estado verificable: 18 de septiembre de 2026

Proyecto real: esta carpeta de Antigravity. Los cambios estan guardados, sin commit.

## Arranque tras reiniciar Windows

Desde esta carpeta, ejecutar `powershell -NoProfile -File scripts/Start-Demo.ps1 -Open`.
El script reutiliza la instalacion existente de PostgreSQL 16, Maven 3.9.9,
Flutter 3.19.6 y el entorno Python .venv. No instala dependencias.
Utiliza exclusivamente el cluster de demostracion .runtime/postgres-demo,
puerto 55432 y base cursos_demo. No modifica el servicio PostgreSQL del sistema.
Los servicios tardan en compilar; consulte sus archivos de log en .runtime.

- Editor UML: http://127.0.0.1:8765/
- App Flutter generada de cursos: http://127.0.0.1:8090/
- Backend generado: http://127.0.0.1:8080/api/health

La aplicacion de cursos es una muestra REAL generada desde examples/cursos.json.
No representa todos los diagramas posibles. El editor es el producto generador.

## Evidencia obtenida

- 20 pruebas Python del generador pasaron (antes de las mejoras de asistente de hoy).
- Backend de cursos compilo y paso prueba de contexto Spring con H2.
- Backend de cursos inicio contra PostgreSQL y acepto CRUD con Instructor y CursoProgramado.
- Fecha camelCase, booleano y relacion por ID conservaron sus valores al leer.
- Actualizar una version obsoleta devolvio 409; referencia inexistente devolvio 400.
- Registros temporales de esa comprobacion eliminados al terminar.
- Flutter web compilo y mostro panel conectado al servidor en navegador integrado.
- Flutter analyze posterior al asistente nuevo: sin errores; 24 avisos/informaciones pendientes.

## Correcciones recientes

DTOs de relaciones y versiones, referencias Jackson unicas, preservacion camelCase,
interfaces Java, ID heredado, Boolean, generacion de plataformas Flutter,
fecha sin hora para LocalDate, validacion de descarga, y errores de OCR sin diagrama inventado.
Se elimino progreso simulado del editor.
El asistente ahora genera consultas reales de listado/conteo y abre formularios;
guarda historial local. Aun falta probar ese flujo en navegador tras recompilar.

## Pendientes: NO declarar el proyecto terminado

- Voz LOCAL offline y registro por voz de campos completos. speech_to_text no garantiza offline.
- Escritura sin conexion, cola persistente, conflictos e idempotencia al sincronizar.
- Formularios con selectores legibles de relaciones, opcionales y fechas obligatorias.
- Pruebas completas Android/APK; probar web NO verifica permisos/audio/nativo.
- Prueba generada veterinaria y matrices de herencia/composicion/N:M/autorelaciones.
- Colaboracion: proyectos separados, invitaciones, permisos, conflictos y reconexion.
- Import/export MDJ y Architect: fidelidad de vistas/atributos; falta producto/version de Architect.
- OCR real instalado y probado con fotos representativas.
- Documentacion y evidencias finales del Proceso Unificado.

No aplicar el antiguo changes.json del informe: Antigravity cambio los archivos posteriormente.
