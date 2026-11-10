# Respaldo del diagrama en Google Drive

El botón **Guardar en Drive**, en Acciones, crea una copia JSON del diagrama actual:
clases, atributos, relaciones, clases de asociación y posiciones. No incluye el
historial compartido, permisos de colaboración, APK, backend generado ni credenciales.
Cada respaldo crea un archivo nuevo; no sobrescribe otros archivos del usuario.
Para restaurarlo, descargar el JSON desde Drive y usar **Importar** en el editor.

## Configuración del administrador

1. Elegir el proyecto de Google Cloud y habilitar **Google Drive API**.
2. En **Google Auth Platform**, configurar Branding, Audience y Data Access.
   Solicitar únicamente `https://www.googleapis.com/auth/drive.file`.
3. Crear un cliente OAuth **Web application**. Registrar como origen JavaScript
   autorizado `https://generador-uml.onrender.com` (sin ruta ni barra final).
   Para desarrollo agregar `http://127.0.0.1:8765` o el origen local utilizado.
4. Si la aplicación está en Testing, agregar las cuentas de la defensa como
   usuarios de prueba. Para otros usuarios revisar las condiciones de publicación
   que indique Google en la consola.
5. En Render > Environment, agregar `GOOGLE_DRIVE_CLIENT_ID` con el identificador
   terminado en `.apps.googleusercontent.com` y desplegar. No cargar un client secret.
6. Abrir el editor, pulsar Guardar en Drive, autorizar con una cuenta de prueba y
   comprobar el archivo real en Drive. Descargarlo e importarlo para verificar su contenido.

## Autorización

Se utiliza Google Identity Services, con autorización interactiva en una ventana
de Google. La carga va directamente del navegador a Drive. El token de acceso
solo se usa en memoria; no se guarda en localStorage ni se envía al backend.
La falta de configuración o permisos se muestra como error, nunca como guardado.
Una interrupción después de enviar puede haber creado el archivo: revisar Drive
antes de reintentar para evitar respaldos duplicados.

Fuentes:
- https://developers.google.com/identity/oauth2/web/guides/use-token-model
- https://developers.google.com/workspace/drive/api/guides/api-specific-auth
- https://developers.google.com/workspace/drive/api/guides/manage-uploads
