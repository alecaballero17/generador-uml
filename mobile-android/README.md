# Graficador UML Android — prueba local

APK del editor, paquete com.generadoruml.mobile. Interfaz y modelos se empaquetan localmente en assets; no carga la web de la computadora.

Estado: el editor empaquetado usa por defecto el servicio público de GeneradorUML en Render. Puede cambiarse desde el diálogo de conexión para desarrollo local. La primera apertura del servicio gratuito puede tardar cerca de un minuto si estaba inactivo. El selector de archivos permite elegir una foto; captura directa pendiente.

Compilar: copiar frontend a app/src/main/assets, usar JDK de Android Studio y ejecutar gradlew.bat assembleDebug desde esta carpeta. No incluir assets duplicados ni local.properties en Git. No se necesita `adb reverse` cuando se utiliza el servicio público.

Fuentes: https://developer.android.com/develop/ui/views/layout/webapps/load-local-content
