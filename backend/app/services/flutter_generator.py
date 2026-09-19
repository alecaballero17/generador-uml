"""
GeneradorUML — Generador Flutter 3.x

Genera una aplicación móvil completa y compilable en Flutter 3.x a partir
del modelo de clases UML (UMLDiagram).

Incluye:
- pubspec.yaml con dependencias (http, intl)
- lib/main.dart con tema Material 3 moderno y navegación
- lib/models/{entidad}.dart (fromJson, toJson, copyWith)
- lib/services/{entidad}_service.dart (CRUD HTTP contra el backend Spring Boot)
- lib/services/api_config.dart (configuración de URL con soporte para emulador, LAN y web)
- lib/services/offline_cache_service.dart (caché local para funcionamiento offline)
- lib/screens/{entidad}/{entidad}_list_screen.dart (búsqueda, pull-to-refresh, estados vacío/error/carga)
- lib/screens/{entidad}/{entidad}_detail_screen.dart (vista detallada y relaciones)
- lib/screens/{entidad}/{entidad}_form_screen.dart (formulario validado para crear y editar)
- lib/screens/dashboard_screen.dart (panel principal con accesos rápidos y estado del servidor)
- lib/screens/assistant_screen.dart (asistente local de voz y comandos en lenguaje natural)
"""

from __future__ import annotations
import os
import re
from typing import Dict, List, Any, Optional
from ..models.uml_model import (
    UMLDiagram, UMLClass, UMLAttribute, UMLOperation, UMLRelationship,
    RelationshipType, Multiplicity, Visibility
)


class FlutterGenerator:
    """Generador de aplicaciones Flutter 3.x a partir de diagramas UML."""

    # Mapeo de tipos UML a tipos Dart
    TYPE_MAP = {
        "String": "String",
        "string": "String",
        "text": "String",
        "char": "String",
        "varchar": "String",
        "Integer": "int",
        "int": "int",
        "Long": "int",
        "long": "int",
        "Short": "int",
        "short": "int",
        "Byte": "int",
        "byte": "int",
        "Double": "double",
        "double": "double",
        "Float": "double",
        "float": "double",
        "BigDecimal": "double",
        "decimal": "double",
        "Boolean": "bool",
        "boolean": "bool",
        "bool": "bool",
        "LocalDate": "DateTime",
        "date": "DateTime",
        "LocalDateTime": "DateTime",
        "DateTime": "DateTime",
        "timestamp": "DateTime",
        "Date": "DateTime",
        "Time": "String",
        "UUID": "String",
        "uuid": "String",
        "byte[]": "String",
        "Blob": "String",
    }

    def __init__(
        self,
        diagram: UMLDiagram,
        app_name: Optional[str] = None,
        package_name: str = "com.generated.app",
        api_base_url: str = "http://10.0.2.2:8080/api",
    ):
        self.diagram = diagram
        self.raw_app_name = app_name or diagram.name or "AppGenerada"
        self.app_name = self._to_snake_case(self.raw_app_name)
        self.package_name = package_name
        self.api_base_url = api_base_url

        # Identificar entidades normales (no interfaces puras ni clases abstractas)
        self.entities = [c for c in diagram.classes if not c.is_interface and not c.is_abstract]
        if not self.entities:
            self.entities = list(diagram.classes)

    def _to_snake_case(self, name: str) -> str:
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
        clean = re.sub(r'[^a-z0-9_]', '_', s2)
        return re.sub(r'_+', '_', clean).strip('_') or "flutter_app"

    def _to_camel_case(self, name: str) -> str:
        parts = name.split('_')
        return parts[0].lower() + ''.join(p.capitalize() for p in parts[1:])

    def _to_pascal_case(self, name: str) -> str:
        return ''.join(p.capitalize() for p in re.split(r'[^a-zA-Z0-9]', name) if p)

    def _pluralize(self, name: str) -> str:
        """Simple English pluralization matching Spring Boot generator."""
        if name.endswith("s") or name.endswith("x") or name.endswith("z"):
            return name + "es"
        if name.endswith("y") and name[-2:] not in ("ay", "ey", "oy", "uy"):
            return name[:-1] + "ies"
        return name + "s"

    def _get_endpoint_path(self, class_name: str) -> str:
        """Compute the REST endpoint path matching the Spring Boot controller.

        This MUST produce the same path as SpringBootGenerator._get_endpoint_path.
        Uses snake_case of pluralized name converted to kebab-case.
        Example: OrdenCompra -> orden-compras
        """
        return self._to_snake_case(self._pluralize(class_name)).replace("_", "-")

    def _dart_type(self, uml_type: str) -> str:
        return "List<int>" if uml_type == "RelationIds" else self.TYPE_MAP.get(uml_type, "String")

    def _get_primary_key(self, cls: UMLClass) -> UMLAttribute:
        for attr in cls.attributes:
            if attr.name == "id":
                return attr
        # Si no hay explícito, usar id
        return UMLAttribute(name="id", type="Long", visibility=Visibility.PUBLIC)

    def _get_display_field(self, cls: UMLClass) -> UMLAttribute:
        """Encuentra el atributo más idóneo para títulos/display en listas."""
        candidates = ["nombre", "name", "titulo", "title", "descripcion", "description", "codigo", "codigo_barra"]
        for attr in cls.attributes:
            if attr.name.lower() in candidates:
                return attr
        for attr in cls.attributes:
            if attr.name.lower() not in ("id", f"{cls.name.lower()}id", f"{cls.name.lower()}_id"):
                return attr
        return cls.attributes[0] if cls.attributes else UMLAttribute(name="id", type="Long")

    def _get_subtitle_field(self, cls: UMLClass) -> Optional[UMLAttribute]:
        display = self._get_display_field(cls)
        for attr in cls.attributes:
            if attr.name != display.name and attr.name.lower() not in ("id", "password"):
                return attr
        return None

    def _rest_schema(self, cls):
        import copy
        from .rest_contract import relation_specs, attributes
        from .springboot_generator import SpringBootGenerator
        result = copy.deepcopy(cls)
        result.attributes = copy.deepcopy(attributes(self.diagram, cls))
        result.attributes.append(UMLAttribute(name="version", type="Long", is_derived=True))
        for spec in relation_specs(SpringBootGenerator(self.diagram), cls):
            if spec["owner"]:
                attr = UMLAttribute(name=spec["key"], type="RelationIds" if spec["many"] else "Long")
                attr.constraints = ["required"] if spec["required"] else []
                result.attributes.append(attr)
        return result

    def generate_all(self) -> Dict[str, str]:
        """Genera todos los archivos del proyecto Flutter y retorna un dict {ruta_relativa: contenido}."""
        files: Dict[str, str] = {}

        # 1. pubspec.yaml
        files["pubspec.yaml"] = self._generate_pubspec()
        files["analysis_options.yaml"] = self._generate_analysis_options()
        files["README.md"] = self._generate_readme()

        # 2. Configuración y servicios base
        files["lib/main.dart"] = self._generate_main()
        files["lib/services/api_config.dart"] = self._generate_api_config()
        files["lib/services/offline_cache_service.dart"] = self._generate_offline_cache()

        # 3. Pantalla de Dashboard y Asistente
        files["lib/screens/dashboard_screen.dart"] = self._generate_dashboard()
        files["lib/screens/assistant_screen.dart"] = self._generate_assistant()

        # 4. Por cada entidad: Model, Service, ListScreen, DetailScreen, FormScreen
        for original in self.entities:
            cls = self._rest_schema(original)
            snake = self._to_snake_case(cls.name)
            files[f"lib/models/{snake}.dart"] = self._generate_model(cls)
            files[f"lib/services/{snake}_service.dart"] = self._generate_entity_service(cls)
            files[f"lib/screens/{snake}/{snake}_list_screen.dart"] = self._generate_list_screen(cls)
            files[f"lib/screens/{snake}/{snake}_detail_screen.dart"] = self._generate_detail_screen(cls)
            files[f"lib/screens/{snake}/{snake}_form_screen.dart"] = self._generate_form_screen(cls)

        # 5. Tests básicos
        files["test/widget_test.dart"] = self._generate_widget_test()

        return files

    def generate_to_disk(self, output_dir: str) -> List[str]:
        """Escribe todos los archivos generados a disco y devuelve la lista de rutas absolutas."""
        import subprocess, shutil
        from pathlib import Path
        flutter = shutil.which("flutter") or shutil.which("flutter.bat")
        if not flutter:
            raise RuntimeError("Flutter SDK no disponible: se necesita para entregar proyectos web/Android/iOS completos")
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        scaffold = subprocess.run([flutter, "create", "--no-pub", "--platforms=web,android,ios", "--org", self.package_name, "--project-name", self.app_name, str(Path(output_dir).resolve())], capture_output=True, text=True, errors="replace", timeout=180)
        if scaffold.returncode:
            raise RuntimeError("No se pudo preparar Flutter: " + scaffold.stderr[-1000:])
        manifest = Path(output_dir) / "android/app/src/main/AndroidManifest.xml"
        if manifest.exists():
            text = manifest.read_text(encoding="utf-8")
            if 'android.permission.RECORD_AUDIO' not in text:
                text = text.replace("    <application", '    <uses-permission android:name="android.permission.INTERNET"/>\n    <uses-permission android:name="android.permission.RECORD_AUDIO"/>\n    <application android:usesCleartextTraffic="true"')
            manifest.write_text(text, encoding="utf-8")
        import plistlib
        info = Path(output_dir) / "ios/Runner/Info.plist"
        if info.exists():
            data = plistlib.loads(info.read_bytes())
            data.update(NSMicrophoneUsageDescription="Dictar comandos para gestionar registros", NSSpeechRecognitionUsageDescription="Transcribir comandos de voz", NSAppTransportSecurity={"NSAllowsLocalNetworking": True})
            info.write_bytes(plistlib.dumps(data))
        generated_files = self.generate_all()
        written_paths: List[str] = []

        for rel_path, content in generated_files.items():
            full_path = os.path.join(output_dir, rel_path.replace("/", os.sep))
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            written_paths.append(full_path)

        return written_paths

    # ─────────────────────────────────────────────────────────────────────────
    # Generación de archivos individuales
    # ─────────────────────────────────────────────────────────────────────────

    def _generate_pubspec(self) -> str:
        return f"""name: {self.app_name}
description: "Aplicación móvil generada automáticamente por GeneradorUML a partir del diagrama '{self.diagram.name}'"
publish_to: 'none'
version: 1.0.0+1

environment:
  sdk: '>=3.0.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter
  http: ^1.2.0
  intl: ^0.19.0
  shared_preferences: ^2.2.0
  speech_to_text: ^6.6.0

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^3.0.0

flutter:
  uses-material-design: true
"""

    def _generate_analysis_options(self) -> str:
        return """include: package:flutter_lints/flutter.yaml

linter:
  rules:
    prefer_const_constructors: true
    prefer_const_literals_to_create_immutables: true
    avoid_print: false
"""

    def _generate_readme(self) -> str:
        entity_bullets = "\n".join([f"- **{cls.name}**: CRUD completo con sincronización REST" for cls in self.entities])
        return f"""# {self.raw_app_name} — App Móvil Flutter

Aplicación móvil generada automáticamente por **GeneradorUML** a partir del diagrama de clases UML.

## Entidades Incluidas
{entity_bullets}

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
"""

    def _generate_api_config(self) -> str:
        return """import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

/// Configuración global de la API REST del backend Spring Boot.
class ApiConfig {
  /// URL base por defecto: localhost si corre en Web/Desktop, o 10.0.2.2 si corre en emulador Android.
  static String baseUrl = kIsWeb ? 'http://localhost:8080/api' : 'http://10.0.2.2:8080/api';

  /// Timeout estándar para peticiones HTTP en segundos.
  static const Duration timeoutDuration = Duration(seconds: 10);

  /// Cabeceras estándar para peticiones JSON.
  static Map<String, String> get headers => {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      };

  /// Permite actualizar la URL base en tiempo de ejecución (ej. desde el menú lateral para IP LAN).
  static void setBaseUrl(String newUrl) {
    baseUrl = newUrl.endsWith('/') ? newUrl.substring(0, newUrl.length - 1) : newUrl;
  }

  /// Verifica si el servidor backend Spring Boot está accesible.
  static Future<bool> checkConnection() async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/health'))
          .timeout(const Duration(seconds: 3));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }
}
"""

    def _generate_offline_cache(self) -> str:
        return """import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

/// Servicio de caché local persistente con SharedPreferences para soporte offline.
/// Los datos se guardan en disco y sobreviven al cierre de la aplicación.
class OfflineCacheService {
  static final OfflineCacheService _instance = OfflineCacheService._internal();
  factory OfflineCacheService() => _instance;
  OfflineCacheService._internal();

  static const String _prefix = 'offline_cache_';

  /// Guarda todos los registros de una entidad en caché persistente.
  Future<void> saveAll(String entityName, List<Map<String, dynamic>> items) async {
    final prefs = await SharedPreferences.getInstance();
    final jsonString = jsonEncode(items);
    await prefs.setString('$_prefix$entityName', jsonString);
  }

  /// Obtiene todos los registros cacheados de una entidad.
  Future<List<Map<String, dynamic>>> getAll(String entityName) async {
    final prefs = await SharedPreferences.getInstance();
    final jsonString = prefs.getString('$_prefix$entityName');
    if (jsonString == null || jsonString.isEmpty) return [];
    try {
      final List<dynamic> decoded = jsonDecode(jsonString);
      return decoded.cast<Map<String, dynamic>>();
    } catch (_) {
      return [];
    }
  }

  /// Guarda o actualiza un registro individual en la caché.
  Future<void> saveOne(String entityName, Map<String, dynamic> item, {String idKey = 'id'}) async {
    final list = await getAll(entityName);
    final id = item[idKey];
    final index = list.indexWhere((i) => i[idKey] == id);
    if (index >= 0) {
      list[index] = item;
    } else {
      list.add(item);
    }
    await saveAll(entityName, list);
  }

  /// Elimina un registro de la caché por ID.
  Future<void> removeOne(String entityName, dynamic id, {String idKey = 'id'}) async {
    final list = await getAll(entityName);
    list.removeWhere((i) => i[idKey] == id);
    await saveAll(entityName, list);
  }

  /// Limpia toda la caché offline.
  Future<void> clear() async {
    final prefs = await SharedPreferences.getInstance();
    final keys = prefs.getKeys().where((k) => k.startsWith(_prefix));
    for (final key in keys) {
      await prefs.remove(key);
    }
  }
}
"""

    def _generate_main(self) -> str:
        title = self.diagram.name or "GeneradorUML App"

        return f"""import 'package:flutter/material.dart';
import 'screens/dashboard_screen.dart';

void main() {{
  runApp(const UMLGeneratedApp());
}}

class UMLGeneratedApp extends StatefulWidget {{
  const UMLGeneratedApp({{super.key}});

  @override
  State<UMLGeneratedApp> createState() => _UMLGeneratedAppState();
}}

class _UMLGeneratedAppState extends State<UMLGeneratedApp> {{
  ThemeMode _themeMode = ThemeMode.system;

  void _toggleTheme() {{
    setState(() {{
      _themeMode = _themeMode == ThemeMode.dark ? ThemeMode.light : ThemeMode.dark;
    }});
  }}

  @override
  Widget build(BuildContext context) {{
    return MaterialApp(
      title: '{title}',
      debugShowCheckedModeBanner: false,
      themeMode: _themeMode,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF6366F1),
          brightness: Brightness.light,
        ),
        appBarTheme: const AppBarTheme(
          centerTitle: true,
          elevation: 0,
        ),
        cardTheme: CardTheme(
          elevation: 2,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        ),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
          ),
        ),
      ),
      darkTheme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF6366F1),
          brightness: Brightness.dark,
        ),
        appBarTheme: const AppBarTheme(
          centerTitle: true,
          elevation: 0,
        ),
        cardTheme: CardTheme(
          elevation: 3,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        ),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
          ),
        ),
      ),
      home: DashboardScreen(onToggleTheme: _toggleTheme),
    );
  }}
}}
"""

    def _generate_dashboard(self) -> str:
        entities_tiles = []
        for cls in self.entities:
            snake = self._to_snake_case(cls.name)
            entities_tiles.append(f"""
            _EntityCard(
              title: '{cls.name}',
              description: '{len(cls.attributes)} atributos, CRUD completo',
              icon: Icons.table_chart_rounded,
              onTap: () => Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const {cls.name}ListScreen()),
              ),
            ),""")
        entities_tiles_str = "\n".join(entities_tiles)

        return f"""import 'package:flutter/material.dart';
import '../services/api_config.dart';
import 'assistant_screen.dart';
{chr(10).join([f"import '{self._to_snake_case(c.name)}/{self._to_snake_case(c.name)}_list_screen.dart';" for c in self.entities])}

class DashboardScreen extends StatefulWidget {{
  final VoidCallback onToggleTheme;
  const DashboardScreen({{super.key, required this.onToggleTheme}});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}}

class _DashboardScreenState extends State<DashboardScreen> {{
  bool _isCheckingBackend = false;
  bool? _isBackendOnline;
  final TextEditingController _urlController = TextEditingController(text: ApiConfig.baseUrl);

  @override
  void initState() {{
    super.initState();
    _checkServer();
  }}

  Future<void> _checkServer() async {{
    setState(() => _isCheckingBackend = true);
    final online = await ApiConfig.checkConnection();
    if (mounted) {{
      setState(() {{
        _isBackendOnline = online;
        _isCheckingBackend = false;
      }});
    }}
  }}

  void _showConfigDialog() {{
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Configuración de Servidor'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Dirección del backend Spring Boot:',
              style: TextStyle(fontSize: 13, color: Colors.grey),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _urlController,
              decoration: const InputDecoration(
                hintText: 'http://10.0.2.2:8080/api',
                prefixIcon: Icon(Icons.link),
              ),
            ),
            const SizedBox(height: 12),
            const Text(
              '• Android Emulator: http://10.0.2.2:8080/api\\n'
              '• Celular en la misma red: http://192.168.x.x:8080/api\\n'
              '• Web/Desktop: http://localhost:8080/api',
              style: TextStyle(fontSize: 11, color: Colors.grey),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () {{
              ApiConfig.setBaseUrl(_urlController.text.trim());
              Navigator.pop(ctx);
              _checkServer();
            }},
            child: const Text('Guardar'),
          ),
        ],
      ),
    );
  }}

  @override
  Widget build(BuildContext context) {{
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text('{self.diagram.name or "GeneradorUML"}'),
        actions: [
          IconButton(
            tooltip: 'Cambiar tema',
            icon: const Icon(Icons.brightness_medium),
            onPressed: widget.onToggleTheme,
          ),
          IconButton(
            tooltip: 'Configurar servidor',
            icon: const Icon(Icons.settings),
            onPressed: _showConfigDialog,
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _checkServer,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // Banner de estado del backend
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: _isBackendOnline == true
                    ? Colors.green.withOpacity(0.12)
                    : Colors.amber.withOpacity(0.12),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(
                  color: _isBackendOnline == true ? Colors.green : Colors.amber,
                  width: 1.5,
                ),
              ),
              child: Row(
                children: [
                  Icon(
                    _isBackendOnline == true ? Icons.cloud_done : Icons.cloud_off,
                    color: _isBackendOnline == true ? Colors.green : Colors.amber.shade800,
                    size: 32,
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          _isBackendOnline == true
                              ? 'Servidor Conectado'
                              : 'Modo Offline / Servidor no detectado',
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            color: _isBackendOnline == true
                                ? Colors.green.shade900
                                : Colors.amber.shade900,
                          ),
                        ),
                        Text(
                          _isBackendOnline == true
                              ? ApiConfig.baseUrl
                              : 'Usando caché local. Toca para reintentar.',
                          style: TextStyle(
                            fontSize: 12,
                            color: theme.colorScheme.onSurface.withOpacity(0.7),
                          ),
                        ),
                      ],
                    ),
                  ),
                  if (_isCheckingBackend)
                    const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  else
                    IconButton(
                      icon: const Icon(Icons.refresh),
                      onPressed: _checkServer,
                    ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // Tarjeta de Asistente IA / Voz
            Card(
              color: colorScheme.primaryContainer,
              child: InkWell(
                borderRadius: BorderRadius.circular(16),
                onTap: () => Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const AssistantScreen()),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Row(
                    children: [
                      CircleAvatar(
                        radius: 28,
                        backgroundColor: colorScheme.primary,
                        child: const Icon(Icons.mic, color: Colors.white, size: 28),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Asistente de consultas y voz',
                              style: theme.textTheme.titleMedium?.copyWith(
                                fontWeight: FontWeight.bold,
                                color: colorScheme.onPrimaryContainer,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              'Consulta registros o abre formularios con texto y voz',
                              style: theme.textTheme.bodySmall?.copyWith(
                                color: colorScheme.onPrimaryContainer.withOpacity(0.8),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const Icon(Icons.arrow_forward_ios, size: 16),
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(height: 24),

            // Título de Módulos
            Row(
              children: [
                const Icon(Icons.folder_open, size: 20),
                const SizedBox(width: 8),
                Text(
                  'Entidades del Diagrama ({len(self.entities)})',
                  style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                ),
              ],
            ),
            const SizedBox(height: 12),

            // Lista de entidades
            {entities_tiles_str}
          ],
        ),
      ),
    );
  }}
}}

class _EntityCard extends StatelessWidget {{
  final String title;
  final String description;
  final IconData icon;
  final VoidCallback onTap;

  const _EntityCard({{
    required this.title,
    required this.description,
    required this.icon,
    required this.onTap,
  }});

  @override
  Widget build(BuildContext context) {{
    final theme = Theme.of(context);
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
        leading: CircleAvatar(
          backgroundColor: theme.colorScheme.secondaryContainer,
          child: Icon(icon, color: theme.colorScheme.onSecondaryContainer),
        ),
        title: Text(
          title,
          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
        ),
        subtitle: Text(description),
        trailing: const Icon(Icons.chevron_right),
        onTap: onTap,
      ),
    );
  }}
}}
"""

    def _generate_assistant(self) -> str:
        entities_names = ", ".join([f"'{c.name}'" for c in self.entities])
        assistant_imports = []
        actions = []
        for entity in self.entities:
            snake = self._to_snake_case(entity.name)
            display = self._get_display_field(entity).name
            assistant_imports += [f"import '../services/{snake}_service.dart';", f"import '{snake}/{snake}_form_screen.dart';"]
            actions.append(f"""      case '{entity.name}':
        if (create) {{
          await Navigator.push(context, MaterialPageRoute(builder: (_) => const {entity.name}FormScreen()));
          return 'Formulario de {entity.name} abierto. El registro solo se guarda al pulsar Crear.';
        }}
        final items = await {entity.name}Service().getAll();
        if (count) return '${{items.length}} registros de {entity.name} disponibles.';
        if (items.isEmpty) return 'No hay registros de {entity.name} disponibles.';
        return items.take(20).map((item) => '${{item.id}}: ${{item.{display}}}').join('\\n');
""")
        assistant_imports_str = "\n".join(assistant_imports)
        actions_str = "\n".join(actions)
        return f"""import 'package:flutter/material.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;
import '../services/api_config.dart';
import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
{assistant_imports_str}

/// Asistente local de comandos de voz y texto con reconocimiento de voz real.
class AssistantScreen extends StatefulWidget {{
  const AssistantScreen({{super.key}});

  @override
  State<AssistantScreen> createState() => _AssistantScreenState();
}}

class _AssistantScreenState extends State<AssistantScreen> {{
  final TextEditingController _commandController = TextEditingController();
  final List<_ChatMessage> _messages = [];
  bool _isListening = false;
  bool _speechAvailable = false;
  final stt.SpeechToText _speech = stt.SpeechToText();

  final List<String> _entities = [{entities_names}];

  @override
  void initState() {{
    super.initState();
    _restoreHistory();
    _messages.add(
      const _ChatMessage(
        text: '¡Hola! Soy tu asistente de GeneradorUML. Puedes consultar datos o darme comandos como:\\n'
            '• "¿Cuántos registros hay en [entidad]?"\\n'
            '• "Listar [entidad]"\\n'
            '• "Crear nuevo [entidad]"\\n'
            '• "Estado del servidor"',
        isUser: false,
      ),
    );
  }}

  /// Inicializa el motor de reconocimiento de voz.
  Future<void> _initSpeech() async {{
    try {{
      _speechAvailable = await _speech.initialize(
        onError: (error) {{
          debugPrint('Speech error: ${{error.errorMsg}}');
          if (mounted) {{
            setState(() => _isListening = false);
          }}
        }},
        onStatus: (status) {{
          if (status == 'notListening' && mounted) {{
            setState(() => _isListening = false);
          }}
        }},
      );
    }} catch (e) {{
      debugPrint('Speech init failed: $e');
      _speechAvailable = false;
    }}
    if (mounted) setState(() {{}});
  }}

  bool _busy = false;

  Future<void> _restoreHistory() async {{
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getString('assistant_history_${{ApiConfig.baseUrl}}');
    if (saved == null || !mounted) return;
    try {{
      final list = jsonDecode(saved) as List;
      setState(() {{
        _messages.addAll(list.map((m) => _ChatMessage(text: m['text'] as String, isUser: m['isUser'] as bool)));
      }});
    }} catch (_) {{ /* Historial anterior incompatible. */ }}
  }}

  Future<void> _saveHistory() async {{
    final prefs = await SharedPreferences.getInstance();
    final recent = _messages.skip(_messages.length > 100 ? _messages.length - 100 : 0);
    await prefs.setString('assistant_history_${{ApiConfig.baseUrl}}', jsonEncode(recent.map((m) => {{'text': m.text, 'isUser': m.isUser}}).toList()));
  }}

  Future<String> _runCommand(String entity, bool create, bool count) async {{
    switch (entity) {{
{actions_str}
      default: return 'Indica una entidad: ${{_entities.join(", ")}}.';
    }}
  }}

  Future<void> _processCommand(String text) async {{
    if (text.trim().isEmpty || _busy) return;
    final userText = text.trim();
    _commandController.clear();
    setState(() {{
      _busy = true;
      _messages.add(_ChatMessage(text: userText, isUser: true));
    }});
    String response;
    try {{
      final lower = userText.toLowerCase();
      if (lower.contains('servidor') || lower.contains('conexión')) {{
        response = await ApiConfig.checkConnection() ? 'Servidor disponible.' : 'Servidor no disponible. Las consultas pueden usar los datos guardados en este dispositivo.';
      }} else {{
        final entities = _entities.where((e) => lower.replaceAll(' ', '').contains(e.toLowerCase())).toList();
        final create = RegExp(r'crear|nuevo|nueva|registrar').hasMatch(lower);
        final count = RegExp(r'cuantos|cuántos|total|contar').hasMatch(lower);
        final list = RegExp(r'listar|mostrar|consultar|ver').hasMatch(lower);
        if (entities.length == 1 && (create || count || list)) {{
          response = await _runCommand(entities.single, create, count);
        }} else {{
          response = 'Usa "listar", "contar" o "crear" y una entidad: ${{_entities.join(", ")}}. Las consultas muestran registros disponibles, incluidos los guardados localmente.';
        }}
      }}
    }} catch (e) {{
      response = 'No se pudo completar la operación: $e';
    }}
    if (!mounted) return;
    setState(() {{
      _busy = false;
      _messages.add(_ChatMessage(text: response, isUser: false));
    }});
    await _saveHistory();
  }}

  /// Inicia o detiene la escucha de voz real con speech_to_text.
  void _toggleVoiceInput() async {{
    if (_isListening) {{
      await _speech.stop();
      setState(() => _isListening = false);
      return;
    }}

    if (!_speechAvailable) await _initSpeech();
    if (!mounted) return;
    if (!_speechAvailable) {{
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Reconocimiento de voz no disponible en este dispositivo.'),
          duration: Duration(seconds: 3),
        ),
      );
      return;
    }}

    setState(() => _isListening = true);

    await _speech.listen(
      onResult: (result) {{
        if (result.finalResult && result.recognizedWords.isNotEmpty) {{
          _processCommand(result.recognizedWords);
          setState(() => _isListening = false);
        }} else if (!result.finalResult) {{
          // Mostrar texto parcial mientras se dicta
          setState(() {{
            _commandController.text = result.recognizedWords;
          }});
        }}
      }},
      localeId: 'es_ES',
      listenOptions: stt.SpeechListenOptions(
        listenMode: stt.ListenMode.confirmation,
        cancelOnError: true,
      ),
      listenFor: const Duration(seconds: 15),
      pauseFor: const Duration(seconds: 3),
    );
  }}

  @override
  void dispose() {{
    _speech.stop();
    _commandController.dispose();
    super.dispose();
  }}

  @override
  Widget build(BuildContext context) {{
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Asistente Local'),
        actions: [
          if (_speechAvailable)
            const Padding(
              padding: EdgeInsets.only(right: 12),
              child: Chip(
                avatar: Icon(Icons.mic, size: 16),
                label: Text('Voz activa', style: TextStyle(fontSize: 11)),
              ),
            )
          else
            const Padding(
              padding: EdgeInsets.only(right: 12),
              child: Chip(
                avatar: Icon(Icons.mic_off, size: 16),
                label: Text('Sin voz', style: TextStyle(fontSize: 11)),
              ),
            ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: _messages.length,
              itemBuilder: (context, index) {{
                final msg = _messages[index];
                return Align(
                  alignment: msg.isUser ? Alignment.centerRight : Alignment.centerLeft,
                  child: Container(
                    margin: const EdgeInsets.only(bottom: 12),
                    padding: const EdgeInsets.all(14),
                    constraints: BoxConstraints(
                      maxWidth: MediaQuery.of(context).size.width * 0.78,
                    ),
                    decoration: BoxDecoration(
                      color: msg.isUser
                          ? colorScheme.primary
                          : colorScheme.surfaceVariant,
                      borderRadius: BorderRadius.only(
                        topLeft: const Radius.circular(16),
                        topRight: const Radius.circular(16),
                        bottomLeft: Radius.circular(msg.isUser ? 16 : 4),
                        bottomRight: Radius.circular(msg.isUser ? 4 : 16),
                      ),
                    ),
                    child: Text(
                      msg.text,
                      style: TextStyle(
                        color: msg.isUser ? colorScheme.onPrimary : colorScheme.onSurfaceVariant,
                        fontSize: 14,
                      ),
                    ),
                  ),
                );
              }},
            ),
          ),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: theme.colorScheme.surface,
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.05),
                  blurRadius: 10,
                  offset: const Offset(0, -2),
                ),
              ],
            ),
            child: SafeArea(
              child: Row(
                children: [
                  IconButton.filled(
                    style: IconButton.styleFrom(
                      backgroundColor: _isListening ? Colors.red : colorScheme.primaryContainer,
                      foregroundColor: _isListening ? Colors.white : colorScheme.onPrimaryContainer,
                    ),
                    icon: Icon(_isListening ? Icons.mic : Icons.mic_none),
                    onPressed: _toggleVoiceInput,
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: TextField(
                      controller: _commandController,
                      decoration: InputDecoration(
                        hintText: _isListening ? 'Escuchando...' : 'Escribe o dicta un comando...',
                        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                      ),
                      onSubmitted: _processCommand,
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton.filled(
                    icon: const Icon(Icons.send),
                    onPressed: () => _processCommand(_commandController.text),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }}
}}

class _ChatMessage {{
  final String text;
  final bool isUser;
  const _ChatMessage({{required this.text, required this.isUser}});
}}
"""

    def _generate_model(self, cls: UMLClass) -> str:
        pk = self._get_primary_key(cls)
        attributes = list(cls.attributes)
        if not any(a.name == pk.name for a in attributes):
            attributes.insert(0, pk)

        fields_decl = []
        constructor_params = []
        from_json_fields = []
        to_json_fields = []
        copy_with_params = []
        copy_with_assigns = []

        for attr in attributes:
            dtype = self._dart_type(attr.type)
            is_pk = (attr.name == pk.name)
            is_nullable = is_pk or dtype in ("DateTime", "int", "double", "bool", "List<int>") or getattr(attr, 'is_optional', False)

            null_mark = "?" if is_nullable else ""
            fields_decl.append(f"  final {dtype}{null_mark} {attr.name};")

            if is_nullable:
                constructor_params.append(f"    this.{attr.name},")
            else:
                constructor_params.append(f"    required this.{attr.name},")

            # fromJson
            if dtype == "List<int>":
                from_json_fields.append(f"      {attr.name}: (json['{attr.name}'] as List?)?.map((x) => (x as num).toInt()).toList(),")
            elif dtype == "DateTime":
                from_json_fields.append(
                    f"      {attr.name}: json['{attr.name}'] != null ? DateTime.tryParse(json['{attr.name}'].toString()) : null,"
                )
            elif dtype == "int":
                from_json_fields.append(
                    f"      {attr.name}: json['{attr.name}'] != null ? int.tryParse(json['{attr.name}'].toString()) : null,"
                )
            elif dtype == "double":
                from_json_fields.append(
                    f"      {attr.name}: json['{attr.name}'] != null ? double.tryParse(json['{attr.name}'].toString()) : null,"
                )
            elif dtype == "bool":
                from_json_fields.append(
                    f"      {attr.name}: json['{attr.name}'] == true || json['{attr.name}'] == 'true' || json['{attr.name}'] == 1 ? true : false,"
                )
            else:
                from_json_fields.append(
                    f"      {attr.name}: json['{attr.name}']?.toString() ?? '',"
                )

            # toJson
            if dtype == "DateTime":
                to_json_fields.append(f"      '{attr.name}': {attr.name}?.toIso8601String()" + (".split('T').first" if attr.type in ('Date', 'LocalDate') else "") + ",")
            else:
                to_json_fields.append(f"      '{attr.name}': {attr.name},")

            copy_with_params.append(f"    {dtype}? {attr.name},")
            copy_with_assigns.append(f"      {attr.name}: {attr.name} ?? this.{attr.name},")

        fields_str = "\n".join(fields_decl)
        constructor_str = "\n".join(constructor_params)
        from_json_str = "\n".join(from_json_fields)
        to_json_str = "\n".join(to_json_fields)
        copy_with_p_str = "\n".join(copy_with_params)
        copy_with_a_str = "\n".join(copy_with_assigns)

        return f"""/// Modelo de datos para la entidad {cls.name}
class {cls.name} {{
{fields_str}

  const {cls.name}({{
{constructor_str}
  }});

  factory {cls.name}.fromJson(Map<String, dynamic> json) {{
    return {cls.name}(
{from_json_str}
    );
  }}

  Map<String, dynamic> toJson() {{
    return {{
{to_json_str}
    }};
  }}

  {cls.name} copyWith({{
{copy_with_p_str}
  }}) {{
    return {cls.name}(
{copy_with_a_str}
    );
  }}
}}
"""

    def _generate_entity_service(self, cls: UMLClass) -> str:
        snake = self._to_snake_case(cls.name)
        pk = self._get_primary_key(cls)
        endpoint = f"/{self._get_endpoint_path(cls.name)}"

        return f"""import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/{snake}.dart';
import 'api_config.dart';
import 'offline_cache_service.dart';

/// Servicio CRUD para la entidad {cls.name} contra el backend Spring Boot.
class {cls.name}Service {{
  final String _endpoint = '{endpoint}';
  final OfflineCacheService _cache = OfflineCacheService();

  String get _url => '${{ApiConfig.baseUrl}}$_endpoint';

  /// Obtiene todos los registros (con respaldo offline en caché)
  Future<List<{cls.name}>> getAll() async {{
    try {{
      final response = await http
          .get(Uri.parse(_url), headers: ApiConfig.headers)
          .timeout(ApiConfig.timeoutDuration);

      if (response.statusCode == 200) {{
        final dynamic data = jsonDecode(utf8.decode(response.bodyBytes));
        List<dynamic> list;
        if (data is Map<String, dynamic> && data.containsKey('content')) {{
          list = data['content'] as List<dynamic>;
        }} else if (data is List<dynamic>) {{
          list = data;
        }} else {{
          list = [];
        }}

        final items = list.map((item) => {cls.name}.fromJson(item as Map<String, dynamic>)).toList();
        // Guardar en caché offline
        await _cache.saveAll('{snake}', list.cast<Map<String, dynamic>>());
        return items;
      }} else {{
        throw Exception('Error del servidor: ${{response.statusCode}}');
      }}
    }} catch (e) {{
      // Fallback a caché offline si la red falla
      final cached = await _cache.getAll('{snake}');
      if (cached.isNotEmpty) {{
        return cached.map((item) => {cls.name}.fromJson(item)).toList();
      }}
      rethrow;
    }}
  }}

  /// Obtiene un registro por ID
  Future<{cls.name}> getById(dynamic id) async {{
    final response = await http
        .get(Uri.parse('$_url/$id'), headers: ApiConfig.headers)
        .timeout(ApiConfig.timeoutDuration);

    if (response.statusCode == 200) {{
      final data = jsonDecode(utf8.decode(response.bodyBytes));
      return {cls.name}.fromJson(data);
    }} else {{
      throw Exception('No se encontró el registro con ID $id');
    }}
  }}

  /// Crea un nuevo registro
  Future<{cls.name}> create({cls.name} item) async {{
    final body = jsonEncode(item.toJson());
    final response = await http
        .post(Uri.parse(_url), headers: ApiConfig.headers, body: body)
        .timeout(ApiConfig.timeoutDuration);

    if (response.statusCode == 200 || response.statusCode == 201) {{
      final data = jsonDecode(utf8.decode(response.bodyBytes));
      final created = {cls.name}.fromJson(data);
      await _cache.saveOne('{snake}', data, idKey: '{pk.name}');
      return created;
    }} else {{
      throw Exception('Error al crear registro: ${{response.body}}');
    }}
  }}

  /// Actualiza un registro existente
  Future<{cls.name}> update(dynamic id, {cls.name} item) async {{
    final body = jsonEncode(item.toJson());
    final response = await http
        .put(Uri.parse('$_url/$id'), headers: ApiConfig.headers, body: body)
        .timeout(ApiConfig.timeoutDuration);

    if (response.statusCode == 200) {{
      final data = jsonDecode(utf8.decode(response.bodyBytes));
      final updated = {cls.name}.fromJson(data);
      await _cache.saveOne('{snake}', data, idKey: '{pk.name}');
      return updated;
    }} else {{
      throw Exception('Error al actualizar registro: ${{response.body}}');
    }}
  }}

  /// Elimina un registro por ID
  Future<bool> delete(dynamic id) async {{
    final response = await http
        .delete(Uri.parse('$_url/$id'), headers: ApiConfig.headers)
        .timeout(ApiConfig.timeoutDuration);

    if (response.statusCode == 200 || response.statusCode == 204) {{
      await _cache.removeOne('{snake}', id, idKey: '{pk.name}');
      return true;
    }} else {{
      throw Exception('Error al eliminar registro');
    }}
  }}
}}
"""

    def _generate_list_screen(self, cls: UMLClass) -> str:
        snake = self._to_snake_case(cls.name)
        pk = self._get_primary_key(cls)
        display_attr = self._get_display_field(cls)
        subtitle_attr = self._get_subtitle_field(cls)

        subtitle_code = ""
        if subtitle_attr:
            subtitle_code = f"""subtitle: item.{subtitle_attr.name} != null
                            ? Text('{subtitle_attr.name.capitalize()}: ${{item.{subtitle_attr.name}}}')
                            : null,"""

        return f"""import 'package:flutter/material.dart';
import '../../models/{snake}.dart';
import '../../services/{snake}_service.dart';
import '{snake}_detail_screen.dart';
import '{snake}_form_screen.dart';

/// Pantalla de listado para la entidad {cls.name} con búsqueda, pull-to-refresh y estados completos.
class {cls.name}ListScreen extends StatefulWidget {{
  const {cls.name}ListScreen({{super.key}});

  @override
  State<{cls.name}ListScreen> createState() => _{cls.name}ListScreenState();
}}

class _{cls.name}ListScreenState extends State<{cls.name}ListScreen> {{
  final {cls.name}Service _service = {cls.name}Service();
  List<{cls.name}> _items = [];
  List<{cls.name}> _filteredItems = [];
  bool _isLoading = true;
  String? _errorMessage;
  final TextEditingController _searchController = TextEditingController();

  @override
  void initState() {{
    super.initState();
    _loadData();
    _searchController.addListener(_filterData);
  }}

  @override
  void dispose() {{
    _searchController.dispose();
    super.dispose();
  }}

  Future<void> _loadData() async {{
    setState(() {{
      _isLoading = true;
      _errorMessage = null;
    }});
    try {{
      final data = await _service.getAll();
      if (mounted) {{
        setState(() {{
          _items = data;
          _filteredItems = data;
          _isLoading = false;
        }});
      }}
    }} catch (e) {{
      if (mounted) {{
        setState(() {{
          _errorMessage = e.toString();
          _isLoading = false;
        }});
      }}
    }}
  }}

  void _filterData() {{
    final query = _searchController.text.toLowerCase();
    setState(() {{
      if (query.isEmpty) {{
        _filteredItems = _items;
      }} else {{
        _filteredItems = _items.where((item) {{
          final text = (item.{display_attr.name} == null ? '' : '${{item.{display_attr.name}}}').toLowerCase();
          return text.contains(query);
        }}).toList();
      }}
    }});
  }}

  Future<void> _deleteItem({cls.name} item) async {{
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Confirmar eliminación'),
        content: Text('¿Deseas eliminar este registro de {cls.name}?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: Colors.red),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Eliminar'),
          ),
        ],
      ),
    );

    if (confirmed == true && item.{pk.name} != null) {{
      try {{
        await _service.delete(item.{pk.name});
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Registro eliminado correctamente')),
        );
        _loadData();
      }} catch (e) {{
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error al eliminar: $e')),
        );
      }}
    }}
  }}

  @override
  Widget build(BuildContext context) {{
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Módulo {cls.name}'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadData,
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        icon: const Icon(Icons.add),
        label: const Text('Nuevo'),
        onPressed: () async {{
          final created = await Navigator.push<bool>(
            context,
            MaterialPageRoute(builder: (_) => const {cls.name}FormScreen()),
          );
          if (created == true) _loadData();
        }},
      ),
      body: Column(
        children: [
          // Barra de búsqueda
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
            child: TextField(
              controller: _searchController,
              decoration: InputDecoration(
                hintText: 'Buscar en {cls.name}...',
                prefixIcon: const Icon(Icons.search),
                suffixIcon: _searchController.text.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.clear),
                        onPressed: () => _searchController.clear(),
                      )
                    : null,
              ),
            ),
          ),

          // Contenido principal según estado
          Expanded(
            child: RefreshIndicator(
              onRefresh: _loadData,
              child: _buildBody(theme),
            ),
          ),
        ],
      ),
    );
  }}

  Widget _buildBody(ThemeData theme) {{
    // Estado de carga
    if (_isLoading) {{
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 16),
            Text('Cargando registros...'),
          ],
        ),
      );
    }}

    // Estado de error
    if (_errorMessage != null) {{
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 56, color: Colors.red),
              const SizedBox(height: 16),
              Text(
                'No se pudo conectar con el servidor',
                style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              Text(
                _errorMessage!,
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 12, color: Colors.grey),
              ),
              const SizedBox(height: 20),
              FilledButton.icon(
                icon: const Icon(Icons.refresh),
                label: const Text('Reintentar'),
                onPressed: _loadData,
              ),
            ],
          ),
        ),
      );
    }}

    // Estado vacío
    if (_filteredItems.isEmpty) {{
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.inbox_outlined, size: 64, color: theme.colorScheme.outline),
              const SizedBox(height: 16),
              Text(
                _searchController.text.isEmpty
                    ? 'No hay registros en {cls.name}'
                    : 'Sin resultados para "${{_searchController.text}}"',
                style: theme.textTheme.titleMedium,
              ),
              const SizedBox(height: 8),
              const Text(
                'Toca el botón "+ Nuevo" para agregar el primer registro.',
                textAlign: TextAlign.center,
                style: TextStyle(color: Colors.grey),
              ),
            ],
          ),
        ),
      );
    }}

    // Lista de resultados
    return ListView.builder(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      itemCount: _filteredItems.length,
      itemBuilder: (context, index) {{
        final item = _filteredItems[index];
        return Card(
          margin: const EdgeInsets.only(bottom: 10),
          child: ListTile(
            leading: CircleAvatar(
              backgroundColor: theme.colorScheme.primaryContainer,
              child: Text(
                '${{index + 1}}',
                style: TextStyle(color: theme.colorScheme.onPrimaryContainer, fontWeight: FontWeight.bold),
              ),
            ),
            title: Text(
              item.{display_attr.name} == null ? 'Sin {display_attr.name}' : '${{item.{display_attr.name}}}',
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
            {subtitle_code}
            trailing: PopupMenuButton<String>(
              onSelected: (value) async {{
                if (value == 'edit') {{
                  final updated = await Navigator.push<bool>(
                    context,
                    MaterialPageRoute(builder: (_) => {cls.name}FormScreen(item: item)),
                  );
                  if (updated == true) _loadData();
                }} else if (value == 'delete') {{
                  _deleteItem(item);
                }}
              }},
              itemBuilder: (context) => [
                const PopupMenuItem(
                  value: 'edit',
                  child: Row(
                    children: [Icon(Icons.edit, size: 18), SizedBox(width: 8), Text('Editar')],
                  ),
                ),
                const PopupMenuItem(
                  value: 'delete',
                  child: Row(
                    children: [Icon(Icons.delete, size: 18, color: Colors.red), SizedBox(width: 8), Text('Eliminar', style: TextStyle(color: Colors.red))],
                  ),
                ),
              ],
            ),
            onTap: () async {{
              final modified = await Navigator.push<bool>(
                context,
                MaterialPageRoute(builder: (_) => {cls.name}DetailScreen(item: item)),
              );
              if (modified == true) _loadData();
            }},
          ),
        );
      }},
    );
  }}
}}
"""

    def _generate_detail_screen(self, cls: UMLClass) -> str:
        snake = self._to_snake_case(cls.name)
        pk = self._get_primary_key(cls)

        fields_widgets = []
        for attr in cls.attributes:
            fields_widgets.append(f"""
            _DetailTile(
              label: '{attr.name.capitalize()}',
              value: item.{attr.name} == null ? 'No especificado' : '${{item.{attr.name}}}',
              icon: Icons.label_outline,
            ),""")
        fields_str = "\n".join(fields_widgets)

        return f"""import 'package:flutter/material.dart';
import '../../models/{snake}.dart';
import '../../services/{snake}_service.dart';
import '{snake}_form_screen.dart';

/// Pantalla de detalle para la entidad {cls.name}.
class {cls.name}DetailScreen extends StatefulWidget {{
  final {cls.name} item;
  const {cls.name}DetailScreen({{super.key, required this.item}});

  @override
  State<{cls.name}DetailScreen> createState() => _{cls.name}DetailScreenState();
}}

class _{cls.name}DetailScreenState extends State<{cls.name}DetailScreen> {{
  late {cls.name} item;
  final {cls.name}Service _service = {cls.name}Service();

  @override
  void initState() {{
    super.initState();
    item = widget.item;
  }}

  Future<void> _delete() async {{
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Eliminar'),
        content: const Text('¿Estás seguro de eliminar este registro?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancelar')),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: Colors.red),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Eliminar'),
          ),
        ],
      ),
    );

    if (confirmed == true && item.{pk.name} != null) {{
      try {{
        await _service.delete(item.{pk.name});
        if (mounted) Navigator.pop(context, true);
      }} catch (e) {{
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error al eliminar: $e')),
        );
      }}
    }}
  }}

  @override
  Widget build(BuildContext context) {{
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Text('{cls.name} #${{item.{pk.name} ?? ""}}'),
        actions: [
          IconButton(
            icon: const Icon(Icons.edit),
            tooltip: 'Editar',
            onPressed: () async {{
              final updated = await Navigator.push<bool>(
                context,
                MaterialPageRoute(builder: (_) => {cls.name}FormScreen(item: item)),
              );
              if (updated == true && mounted) {{
                Navigator.pop(context, true);
              }}
            }},
          ),
          IconButton(
            icon: const Icon(Icons.delete, color: Colors.redAccent),
            tooltip: 'Eliminar',
            onPressed: _delete,
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      CircleAvatar(
                        backgroundColor: theme.colorScheme.primaryContainer,
                        child: Icon(Icons.info_outline, color: theme.colorScheme.onPrimaryContainer),
                      ),
                      const SizedBox(width: 12),
                      Text(
                        'Detalles del Registro',
                        style: (theme.textTheme.titleMedium ?? const TextStyle()).copyWith(fontWeight: FontWeight.bold),
                      ),
                    ],
                  ),
                  const Divider(height: 24),
                  {fields_str}
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }}
}}

class _DetailTile extends StatelessWidget {{
  final String label;
  final String value;
  final IconData icon;

  const _DetailTile({{required this.label, required this.value, required this.icon}});

  @override
  Widget build(BuildContext context) {{
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 20, color: Colors.grey),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label, style: const TextStyle(fontSize: 12, color: Colors.grey)),
                const SizedBox(height: 2),
                Text(value, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w500)),
              ],
            ),
          ),
        ],
      ),
    );
  }}
}}
"""

    def _generate_form_screen(self, cls: UMLClass) -> str:
        snake = self._to_snake_case(cls.name)
        pk = self._get_primary_key(cls)

        controllers_decl = []
        controllers_init = []
        form_fields_widgets = []
        model_construction_fields = []

        for attr in cls.attributes:
            if attr.name in (pk.name, "version"):
                continue

            dtype = self._dart_type(attr.type)
            c_name = f"_{attr.name}Controller"

            if dtype == "bool":
                controllers_decl.append(f"  bool _{attr.name} = false;")
                controllers_init.append(f"    _{attr.name} = widget.item?.{attr.name} ?? false;")
                form_fields_widgets.append(f"""
              SwitchListTile(
                title: const Text('{attr.name.capitalize()}'),
                value: _{attr.name},
                onChanged: (val) => setState(() => _{attr.name} = val),
              ),
              const SizedBox(height: 12),""")
                model_construction_fields.append(f"        {attr.name}: _{attr.name},")
            elif dtype == "DateTime":
                controllers_decl.append(f"  DateTime? _{attr.name};")
                controllers_init.append(f"    _{attr.name} = widget.item?.{attr.name};")
                form_fields_widgets.append(f"""
              ListTile(
                contentPadding: EdgeInsets.zero,
                title: Text('Fecha {attr.name.capitalize()}: ${{_{attr.name} != null ? DateFormat('yyyy-MM-dd').format(_{attr.name}!) : "Sin seleccionar"}}'),
                trailing: const Icon(Icons.calendar_today),
                onTap: () async {{
                  final picked = await showDatePicker(
                    context: context,
                    initialDate: _{attr.name} ?? DateTime.now(),
                    firstDate: DateTime(2000),
                    lastDate: DateTime(2100),
                  );
                  if (picked != null) setState(() => _{attr.name} = picked);
                }},
              ),
              const SizedBox(height: 12),""")
                model_construction_fields.append(f"        {attr.name}: _{attr.name},")
            else:
                if dtype == "List<int>":
                    controllers_init.append(f"    {c_name}.text = (widget.item != null && widget.item!.{attr.name} != null) ? widget.item!.{attr.name}!.join(',') : '';")
                else:
                    controllers_init.append(f"    {c_name}.text = (widget.item != null && widget.item!.{attr.name} != null) ? '${{widget.item!.{attr.name}}}' : '';")

                kb_type = "TextInputType.text"
                if dtype in ("int", "double"):
                    kb_type = "TextInputType.number"

                validator_logic = f"""if (val == null || val.trim().isEmpty) {{
                  return 'El campo {attr.name} es obligatorio';
                }}"""
                if dtype == "int":
                    validator_logic += """
                if (int.tryParse(val) == null) {
                  return 'Ingrese un número entero válido';
                }"""
                elif dtype == "double":
                    validator_logic += """
                if (double.tryParse(val) == null) {
                  return 'Ingrese un valor numérico válido';
                }"""

                form_fields_widgets.append(f"""
              TextFormField(
                controller: {c_name},
                keyboardType: {kb_type},
                decoration: const InputDecoration(
                  labelText: '{attr.name.capitalize()}',
                  hintText: 'Ingrese {attr.name}',
                ),
                validator: (val) {{
                  {validator_logic}
                  return null;
                }},
              ),
              const SizedBox(height: 16),""")

                if dtype == "List<int>":
                    model_construction_fields.append(f"        {attr.name}: {c_name}.text.trim().isEmpty ? [] : {c_name}.text.split(',').map((v) => int.parse(v.trim())).toList(),")
                elif dtype == "int":
                    model_construction_fields.append(f"        {attr.name}: int.tryParse({c_name}.text.trim()),")
                elif dtype == "double":
                    model_construction_fields.append(f"        {attr.name}: double.tryParse({c_name}.text.trim()),")
                else:
                    model_construction_fields.append(f"        {attr.name}: {c_name}.text.trim(),")

        controllers_decl_str = "\n".join(controllers_decl)
        controllers_init_str = "\n".join(controllers_init)
        form_fields_str = "\n".join(form_fields_widgets)
        model_construction_str = "\n".join(model_construction_fields)
        has_date = any(self._dart_type(a.type) == "DateTime" for a in cls.attributes)
        intl_import = "import 'package:intl/intl.dart';\n" if has_date else ""

        return f"""import 'package:flutter/material.dart';
{intl_import}import '../../models/{snake}.dart';
import '../../services/{snake}_service.dart';

/// Formulario para crear o editar registros de {cls.name} con validaciones completas.
class {cls.name}FormScreen extends StatefulWidget {{
  final {cls.name}? item;
  const {cls.name}FormScreen({{super.key, this.item}});

  @override
  State<{cls.name}FormScreen> createState() => _{cls.name}FormScreenState();
}}

class _{cls.name}FormScreenState extends State<{cls.name}FormScreen> {{
  final _formKey = GlobalKey<FormState>();
  final {cls.name}Service _service = {cls.name}Service();
  bool _isSaving = false;

{controllers_decl_str}

  @override
  void initState() {{
    super.initState();
{controllers_init_str}
  }}

  Future<void> _save() async {{
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isSaving = true);

    try {{
      final itemToSave = {cls.name}(
        {pk.name}: widget.item?.{pk.name},
        version: widget.item?.version,
{model_construction_str}
      );

      if (widget.item == null) {{
        await _service.create(itemToSave);
      }} else {{
        await _service.update(widget.item!.{pk.name}, itemToSave);
      }}

      if (mounted) {{
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(widget.item == null ? 'Registro creado con éxito' : 'Registro actualizado con éxito'),
          ),
        );
        Navigator.pop(context, true);
      }}
    }} catch (e) {{
      if (mounted) {{
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error al guardar: $e'), backgroundColor: Colors.red),
        );
      }}
    }} finally {{
      if (mounted) setState(() => _isSaving = false);
    }}
  }}

  @override
  Widget build(BuildContext context) {{
    final isEdit = widget.item != null;

    return Scaffold(
      appBar: AppBar(
        title: Text(isEdit ? 'Editar {cls.name}' : 'Nuevo {cls.name}'),
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            {form_fields_str}
            const SizedBox(height: 24),
            FilledButton.icon(
              style: FilledButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 16)),
              icon: _isSaving
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                    )
                  : const Icon(Icons.save),
              label: Text(
                _isSaving ? 'Guardando...' : (isEdit ? 'Actualizar {cls.name}' : 'Crear {cls.name}'),
                style: const TextStyle(fontSize: 16),
              ),
              onPressed: _isSaving ? null : _save,
            ),
          ],
        ),
      ),
    );
  }}
}}
"""

    def _generate_widget_test(self) -> str:
        return f"""import 'package:flutter_test/flutter_test.dart';
import 'package:flutter/material.dart';
import 'package:{self.app_name}/main.dart';

void main() {{
  testWidgets('Carga inicial de la aplicación {self.raw_app_name}', (WidgetTester tester) async {{
    await tester.pumpWidget(const UMLGeneratedApp());
    expect(find.byType(MaterialApp), findsOneWidget);
  }});
}}
"""
