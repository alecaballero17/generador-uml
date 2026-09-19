# Graficador UML Android — prueba local

APK del editor, paquete com.generadoruml.mobile. Interfaz y modelos se empaquetan localmente en assets; no carga la web de la computadora.

Estado: primera compilación; pendiente comprobar instalación, dictado y rendimiento en Android. La precisión del modelo de voz no cambia al empaquetarlo. La foto todavía interpreta texto, no conectores. La colaboración y generación requieren configurar conexión al servidor; no están integradas en esta primera versión Android. El selector de archivos permite elegir una foto, captura directa pendiente.

Compilar: copiar frontend a app/src/main/assets, usar JDK de Android Studio y ejecutar gradlew.bat assembleDebug desde esta carpeta. No incluir assets duplicados ni local.properties en Git.

Fuentes: https://developer.android.com/develop/ui/views/layout/webapps/load-local-content
