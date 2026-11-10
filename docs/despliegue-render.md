# Despliegue en Render

El servicio publica el editor FastAPI, los archivos web y el seguimiento del equipo.
La compilación Android usa `scripts/Start-Local.ps1` en la computadora con Flutter,
Java y Android SDK. Los backends Spring Boot generados son aplicaciones independientes.

## Servicio web

- Repositorio: `alecaballero17/generador-uml`.
- Contexto Docker: raíz del repositorio; Dockerfile: `./Dockerfile`.
- Comando de inicio: el definido en Dockerfile, que escucha en `0.0.0.0:$PORT`.
- Health check: `/api/health`.
- Una sola instancia mientras se utilice SQLite y un disco local.
- Mantener `UML_LOCAL_BUILD` desactivado (ausente o `0`).

Primero revisar el servicio existente y su rama, configuración y almacenamiento.
No crear un segundo servicio ni contratar recursos sin revisar el costo.

## Datos y secretos

Para conservar proyectos, historial, suscripciones push y claves Web Push, montar
un disco persistente y establecer `APP_DATA_DIR` a su ruta, por ejemplo `/var/data`.
Render requiere un servicio pago para adjuntar discos persistentes. Sin disco,
los datos del servidor se pierden tras un reinicio o despliegue.

Configurar `GEMINI_API_KEY` como secreto si se usa IA en línea. Para push nativo,
configurar la cuenta de servicio mediante `FIREBASE_SERVICE_ACCOUNT_JSON` o un
archivo secreto y `FIREBASE_SERVICE_ACCOUNT`. Nunca incluir claves en Git ni
capturas. No hace falta copiar credenciales locales para arrancar el editor.

Los proyectos locales no se transfieren automáticamente al servicio público.
Exportar los diagramas que se quieran llevar; importar en la web pública y crear
los enlaces compartidos desde esa web. Las suscripciones del teléfono deben
corresponder al servidor y al proyecto públicos.

## Comprobación después de publicar

1. Consultar `/api/health` y abrir el editor y `/seguimiento.html` por HTTPS.
2. Crear un proyecto de prueba, comprobar colaboración entre dos sesiones y
   reconexión WebSocket.
3. Verificar generación y descarga de código e intercambio XMI.
4. Comprobar IA y push solo después de configurar sus secretos.
5. Con almacenamiento persistente, reiniciar el servicio y comprobar que el
   proyecto y su historial siguen disponibles.

Fuentes: https://render.com/docs/deploy-fastapi y https://render.com/docs/disks.
