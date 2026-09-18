# Sistema Veterinaria — App Móvil Flutter

Aplicación móvil generada automáticamente por **GeneradorUML** a partir del diagrama de clases UML.

## Entidades Incluidas
- **Cliente**: CRUD completo con sincronización REST
- **Mascota**: CRUD completo con sincronización REST
- **Veterinario**: CRUD completo con sincronización REST
- **Cita**: CRUD completo con sincronización REST
- **Tratamiento**: CRUD completo con sincronización REST

## Conexión al Backend Spring Boot
Por defecto, la app está configurada para conectar a:
- **Android Emulator**: `http://10.0.2.2:8080/api`
- **Dispositivo Físico**: Cambia la IP en el menú lateral de la app o en `lib/services/api_config.dart` (ejemplo: `http://192.168.1.50:8080/api`).
- **Web / Desktop**: `http://localhost:8080/api`

## Ejecución
```bash
# 1. Crear las carpetas de plataforma nativa (Web, Windows, Android):
flutter create .

# 2. Instalar dependencias
flutter pub get

# 3. Ejecutar en Chrome (Web), emulador o dispositivo
flutter run -d chrome
# o en móvil: flutter run
```

## Características
1. **Material Design 3**: Interfaz visual moderna, soporte para tema oscuro/claro.
2. **CRUD Completo**: Pantallas de listado, búsqueda, detalle, creación y edición con validaciones.
3. **Manejo de Estados**: Estados de carga, errores con reintento y estado vacío ilustrado.
4. **Caché Offline**: Funciona en modo offline con datos previamente consultados.
5. **Asistente de Voz / IA**: Pantalla de comandos interactivos para consultar y operar entidades.
