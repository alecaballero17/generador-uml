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
"""

from __future__ import annotations
import os
import json
from pathlib import Path
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
        from ..models.association_classes import normalize_association_classes
        self.diagram = normalize_association_classes(diagram)
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
        if not name:
            return ""
        if "_" in name:
            parts = name.split('_')
            return parts[0].lower() + ''.join(p.capitalize() for p in parts[1:])
        return name[0].lower() + name[1:]

    def _to_pascal_case(self, name: str) -> str:
        return ''.join(p.capitalize() for p in re.split(r'[^a-zA-Z0-9]', name) if p)

    def _humanize_name(self, name: str) -> str:
        """Convert technical UML/REST names (ventaId) into mobile labels."""
        spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name).replace("_", " ")
        words = []
        for word in spaced.split():
            lowered = word.lower()
            if lowered == "id":
                words.append("ID")
            elif lowered == "ids":
                words.append("IDs")
            else:
                words.append(word[:1].upper() + word[1:])
        return " ".join(words) or "Valor"

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

    def _is_required_attribute(self, attr: UMLAttribute) -> bool:
        """Use the same required semantics in generated mobile forms as the API."""
        multiplicity = str(getattr(attr, "multiplicity", "") or "")
        constraints = getattr(attr, "constraints", []) or []
        return multiplicity in ("1", "1..*") or any(
            "required" in str(constraint).lower() or "notnull" in str(constraint).lower()
            for constraint in constraints
        )

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

        # 3. Inicio y navegación adaptados a las entidades del diagrama
        files["lib/screens/dashboard_screen.dart"] = self._generate_dashboard()

        # 4. Por cada entidad: Model, Service, ListScreen, DetailScreen, FormScreen
        for original in self.entities:
            cls = self._rest_schema(original)
            snake = self._to_snake_case(cls.name)
            files[f"lib/models/{snake}.dart"] = self._generate_model(cls)
            files[f"lib/services/{snake}_service.dart"] = self._generate_entity_service(cls)
            files[f"lib/screens/{snake}/{snake}_list_screen.dart"] = self._generate_list_screen(cls)
            files[f"lib/screens/{snake}/{snake}_detail_screen.dart"] = self._generate_detail_screen(cls)
            files[f"lib/screens/{snake}/{snake}_form_screen.dart"] = self._generate_form_screen(cls)

        # 4b. Modelos para interfaces y clases abstractas
        non_entities = [c for c in self.diagram.classes if c.is_interface or c.is_abstract]
        for c in non_entities:
            snake = self._to_snake_case(c.name)
            model_path = f"lib/models/{snake}.dart"
            if model_path not in files:
                files[model_path] = self._generate_abstract_or_interface_model(c)

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

        # Flutter 3.19 scaffolds Gradle 7 / Android Gradle Plugin 7 projects.
        # Those versions cannot run with the Java 21 runtime bundled by current
        # Android Studio installations, preventing a generated app from being
        # compiled into an APK.  Upgrade the Android build tooling after the
        # scaffold is created so the generated project builds on current SDKs.
        settings = Path(output_dir) / "android/settings.gradle"
        if settings.exists():
            settings_text = settings.read_text(encoding="utf-8")
            settings_text = settings_text.replace(
                'id "com.android.application" version "7.3.0" apply false',
                'id "com.android.application" version "8.4.2" apply false',
            ).replace(
                'id "org.jetbrains.kotlin.android" version "1.7.10" apply false',
                'id "org.jetbrains.kotlin.android" version "1.9.24" apply false',
            )
            settings.write_text(settings_text, encoding="utf-8")

        wrapper = Path(output_dir) / "android/gradle/wrapper/gradle-wrapper.properties"
        if wrapper.exists():
            wrapper_text = wrapper.read_text(encoding="utf-8")
            wrapper_text = wrapper_text.replace(
                "gradle-7.6.3-all.zip", "gradle-8.6-all.zip"
            )
            wrapper.write_text(wrapper_text, encoding="utf-8")

        # Pin Android API 21 and the NDK requested
        # by current Flutter plugins as well, so the generated APK has a
        # reproducible Android toolchain configuration.
        app_gradle = Path(output_dir) / "android/app/build.gradle"
        if app_gradle.exists():
            app_gradle_text = app_gradle.read_text(encoding="utf-8")
            app_gradle_text = app_gradle_text.replace(
                "ndkVersion flutter.ndkVersion",
                'ndkVersion "26.1.10909125"',
            ).replace(
                "minSdkVersion flutter.minSdkVersion",
                "minSdkVersion 21",
            )
            app_gradle.write_text(app_gradle_text, encoding="utf-8")

        manifest = Path(output_dir) / "android/app/src/main/AndroidManifest.xml"
        if manifest.exists():
            text = manifest.read_text(encoding="utf-8")
            text = re.sub(r'\s*<uses-permission android:name="android.permission.RECORD_AUDIO"\s*/>', '', text)
            if 'android.permission.INTERNET' not in text:
                text = text.replace('    <application', '    <uses-permission android:name="android.permission.INTERNET"/>\n    <application', 1)
            if 'android:usesCleartextTraffic' not in text:
                text = text.replace('<application', '<application android:usesCleartextTraffic="true"', 1)
            manifest.write_text(text, encoding="utf-8")
        import plistlib
        info = Path(output_dir) / "ios/Runner/Info.plist"
        if info.exists():
            data = plistlib.loads(info.read_bytes())
            data.pop('NSMicrophoneUsageDescription', None)
            data.pop('NSSpeechRecognitionUsageDescription', None)
            data.update(NSAppTransportSecurity={"NSAllowsLocalNetworking": True})
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
- **Dirección configurada**: `{self.api_base_url}`
- **Dispositivo Físico**: Cambia la dirección en Ajustes > Conexión o en `lib/services/api_config.dart` (ejemplo: `http://192.168.1.50:8080/api`).
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
5. **Inicio adaptable**: Secciones y formularios derivados de las clases del diagrama, sin asistentes adicionales.
"""

    def _generate_api_config(self) -> str:
        return """import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

/// Configuración global de la API REST del backend Spring Boot.
class ApiConfig {
  /// URL base por defecto: localhost si corre en Web/Desktop, o 10.0.2.2 si corre en emulador Android.
  static String baseUrl = __DEFAULT_API_URL__;

  /// Timeout estándar para peticiones HTTP en segundos.
  static const Duration timeoutDuration = Duration(seconds: 10);

  /// Cabeceras estándar para peticiones JSON.
  static Map<String, String> get headers => {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      };

  /// Permite actualizar la URL base en tiempo de ejecución (ej. desde el menú lateral para IP LAN).
  static Future<void> load() async {
    final prefs = await SharedPreferences.getInstance();
    baseUrl = prefs.getString('backend_url') ?? baseUrl;
  }

  static Future<void> setBaseUrl(String newUrl) async {
    final uri = Uri.tryParse(newUrl.trim());
    if (uri == null || !['http', 'https'].contains(uri.scheme) || uri.host.isEmpty) {
      throw const FormatException('Escribe una dirección http o https válida');
    }
    baseUrl = newUrl.trim().replaceFirst(RegExp(r'/+$'), '');
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('backend_url', baseUrl);
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
""".replace('__DEFAULT_API_URL__', self._dart_string(self.api_base_url))

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

    @staticmethod
    def _dart_string(value: str) -> str:
        return json.dumps(value, ensure_ascii=False).replace('$', r'\$')

    def _mobile_template(self, name: str) -> str:
        return (Path(__file__).resolve().parent.parent / 'templates' / name).read_text(encoding='utf-8-sig')

    def _generate_main(self) -> str:
        return self._mobile_template('flutter_main.dart').replace('__TITLE__', self._dart_string(self.raw_app_name))

    def _generate_dashboard(self) -> str:
        imports, modules = [], []
        icons = ['inventory_2_outlined', 'people_outline_rounded', 'receipt_long_outlined', 'category_outlined']
        for index, cls in enumerate(self.entities):
            snake = self._to_snake_case(cls.name)
            imports += [f"import '{snake}/{snake}_list_screen.dart';", f"import '{snake}/{snake}_form_screen.dart';"]
            modules.append(f"_Module({self._dart_string(self._humanize_name(cls.name))}, {self._dart_string(self._get_endpoint_path(cls.name))}, Icons.{icons[index % len(icons)]}, (_) => const {cls.name}ListScreen(), (_) => const {cls.name}FormScreen()),")
        return (self._mobile_template('flutter_dashboard.dart')
                .replace('__TITLE__', self._dart_string(self._humanize_name(self.raw_app_name)))
                .replace('__IMPORTS__', '\n'.join(imports))
                .replace('__MODULES__', '\n'.join(modules)))

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
                from_json_fields.append(
                    f"      {attr.name}: (json['{attr.name}'] as List?)?.map((x) => x is Map ? (x['id'] as num?)?.toInt() ?? 0 : (x is num ? x.toInt() : int.tryParse(x.toString()) ?? 0)).where((x) => x != 0).toList(),"
                )
            elif dtype == "DateTime":
                from_json_fields.append(
                    f"      {attr.name}: json['{attr.name}'] != null ? DateTime.tryParse(json['{attr.name}'].toString()) : null,"
                )
            elif dtype == "int":
                from_json_fields.append(
                    f"      {attr.name}: json['{attr.name}'] is Map ? int.tryParse(json['{attr.name}']['id']?.toString() ?? '') : (json['{attr.name}'] != null ? int.tryParse(json['{attr.name}'].toString()) : null),"
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
  }}{self._generate_dart_operations(cls)}
}}
"""

    def _generate_dart_operations(self, cls: UMLClass) -> str:
        methods = []
        own_op_names = set()

        for op in getattr(cls, 'operations', []):
            own_op_names.add(op.name)
            return_type = self._dart_type(op.return_type) if op.return_type and op.return_type != "void" else "void"
            param_parts = []
            for p in getattr(op, 'parameters', []):
                p_type = self._dart_type(p.type)
                param_parts.append(f"{p_type} {self._to_camel_case(p.name)}")
            params_str = ", ".join(param_parts)
            static_kw = "static " if getattr(op, "is_static", False) else ""
            method_name = self._to_camel_case(op.name)

            if return_type == "void":
                body = "    // Regla de negocio UML\n    // TODO: Implementar lógica personalizada\n"
            elif return_type == "int":
                body = "    return 0;\n"
            elif return_type == "double":
                body = "    return 0.0;\n"
            elif return_type == "bool":
                body = "    return false;\n"
            elif return_type == "String":
                body = "    return '';\n"
            elif return_type == "DateTime":
                body = "    return DateTime.now();\n"
            else:
                body = f"    throw UnimplementedError('Operación UML {op.name} no implementada');\n"

            methods.append(f"""  /// Operación UML: {op.name}
  {static_kw}{return_type} {method_name}({params_str}) {{
{body}  }}""")

        # Realized interface operations that aren't yet defined
        for rel in self.diagram.relationships:
            if rel.type == RelationshipType.REALIZATION and rel.source.class_id == cls.id:
                iface = self.diagram.get_class(rel.target.class_id)
                if iface:
                    for op in getattr(iface, 'operations', []):
                        if op.name not in own_op_names:
                            own_op_names.add(op.name)
                            return_type = self._dart_type(op.return_type) if op.return_type and op.return_type != "void" else "void"
                            param_parts = [f"{self._dart_type(p.type)} {self._to_camel_case(p.name)}" for p in getattr(op, 'parameters', [])]
                            params_str = ", ".join(param_parts)
                            method_name = self._to_camel_case(op.name)
                            if return_type == "void":
                                body = "    // Implementación de interfaz UML\n"
                            elif return_type == "int":
                                body = "    return 0;\n"
                            elif return_type == "double":
                                body = "    return 0.0;\n"
                            elif return_type == "bool":
                                body = "    return false;\n"
                            elif return_type == "String":
                                body = "    return '';\n"
                            else:
                                body = f"    throw UnimplementedError('Operación {op.name} no implementada');\n"

                            methods.append(f"""  /// Implementación de interfaz: {iface.name}.{op.name}
  @override
  {return_type} {method_name}({params_str}) {{
{body}  }}""")

        if not methods:
            return ""
        return "\n\n  // ── Operaciones UML ──\n" + "\n\n".join(methods)

    def _generate_abstract_or_interface_model(self, cls: UMLClass) -> str:
        decl_kind = "interface class" if getattr(cls, 'is_interface', False) else "abstract class"
        fields = []
        for attr in getattr(cls, 'attributes', []):
            dtype = self._dart_type(attr.type)
            fields.append(f"  abstract {dtype}? {attr.name};")

        methods = []
        for op in getattr(cls, 'operations', []):
            return_type = self._dart_type(op.return_type) if op.return_type and op.return_type != "void" else "void"
            param_parts = [f"{self._dart_type(p.type)} {self._to_camel_case(p.name)}" for p in getattr(op, 'parameters', [])]
            params_str = ", ".join(param_parts)
            methods.append(f"  {return_type} {self._to_camel_case(op.name)}({params_str});")

        body_parts = []
        if fields:
            body_parts.append("  // Atributos\n" + "\n".join(fields))
        if methods:
            body_parts.append("  // Operaciones\n" + "\n".join(methods))
        body = "\n\n".join(body_parts) if body_parts else "  // Sin miembros definidos"

        return f"""/// {cls.name} ({'Interfaz' if cls.is_interface else 'Clase abstracta'} UML)
{decl_kind} {cls.name} {{
{body}
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
  bool isCached = false;

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
        isCached = false;
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
        isCached = true;
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
                            ? Text('{self._humanize_name(subtitle_attr.name)}: ${{_displayValue(item.{subtitle_attr.name})}}')
                            : null,"""

        return f"""import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
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
  String _displayValue(dynamic value) => value is DateTime ? DateFormat('dd/MM/yyyy').format(value) : value?.toString() ?? 'Sin dato';
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
        title: const Text('{self._humanize_name(cls.name)}'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadData,
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        icon: const Icon(Icons.add),
        label: const Text('Nuevo registro'),
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
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 4, 20, 4),
            child: Align(alignment: Alignment.centerLeft, child: Text(
              _isLoading ? 'Buscando tus registros…' : '${{_filteredItems.length}} registros · toca uno para ver sus detalles',
              style: TextStyle(fontSize: 12, color: theme.colorScheme.onSurface.withOpacity(.6)),
            )),
          ),
          if (_service.isCached && !_isLoading)
            const Padding(padding: EdgeInsets.symmetric(horizontal: 20, vertical: 8), child: Text('Copia guardada · sin conexión. Conecta el servidor para guardar cambios.', style: TextStyle(fontSize: 12, color: Color(0xFFE0B97C)))),
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
                'Comprueba la conexión en Inicio → Ajustes y vuelve a intentarlo.',
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
                'Usa «Nuevo registro» para empezar.',
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
      padding: const EdgeInsets.fromLTRB(20, 8, 20, 100),
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
              item.{display_attr.name} == null ? 'Sin {self._humanize_name(display_attr.name).lower()}' : _displayValue(item.{display_attr.name}),
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
            lname = attr.name.lower()
            ltype = str(attr.type).lower()
            if lname in ('id', 'uuid', 'codigo', 'cod', 'identificador'):
                icon_code = "Icons.tag"
            elif any(k in lname for k in ('fecha', 'date', 'hora', 'time', 'timestamp')) or ltype in ('date', 'localdate', 'datetime', 'localdatetime', 'timestamp'):
                icon_code = "Icons.calendar_today"
            elif any(k in lname for k in ('precio', 'costo', 'total', 'monto', 'saldo', 'importe', 'salario', 'pago', 'subtotal')) or ltype in ('double', 'float', 'bigdecimal', 'decimal'):
                icon_code = "Icons.attach_money"
            elif any(k in lname for k in ('correo', 'email', 'mail')):
                icon_code = "Icons.email_outlined"
            elif any(k in lname for k in ('telefono', 'tel', 'phone', 'celular', 'movil')):
                icon_code = "Icons.phone_outlined"
            elif any(k in lname for k in ('activo', 'habilitado', 'enabled', 'active')) or ltype in ('bool', 'boolean'):
                icon_code = "Icons.toggle_on_outlined"
            elif any(k in lname for k in ('descripcion', 'detalle', 'observacion', 'notas', 'comentario', 'nota')):
                icon_code = "Icons.notes"
            elif any(k in lname for k in ('direccion', 'ubicacion', 'ciudad', 'pais', 'calle')):
                icon_code = "Icons.place_outlined"
            elif any(k in lname for k in ('nombre', 'name', 'titulo', 'apellido', 'cliente', 'usuario', 'user')):
                icon_code = "Icons.person_outline"
            elif attr.type == 'RelationIds' or lname.endswith('id') or lname.endswith('ids'):
                icon_code = "Icons.link"
            else:
                icon_code = "Icons.label_outline"

            fields_widgets.append(f"""
            _DetailTile(
              label: '{attr.name.capitalize()}',
              value: item.{attr.name} == null ? 'No especificado' : '${{item.{attr.name}}}',
              icon: {icon_code},
            ),""")
        fields_str = "\n".join(fields_widgets)

        # Collect operations from class and realized interfaces
        all_ops = list(getattr(cls, 'operations', []))
        known_op_names = {op.name for op in all_ops}
        for rel in self.diagram.relationships:
            if rel.type == RelationshipType.REALIZATION and rel.source.class_id == cls.id:
                iface = self.diagram.get_class(rel.target.class_id)
                if iface:
                    for op in getattr(iface, 'operations', []):
                        if op.name not in known_op_names:
                            known_op_names.add(op.name)
                            all_ops.append(op)

        operations_card_str = ""
        if all_ops:
            op_items = []
            for op in all_ops:
                op_method = self._to_camel_case(op.name)
                ret_type = op.return_type or "void"
                vis_symbol = "+"
                vis_color = "Colors.green"
                if op.visibility == Visibility.PRIVATE:
                    vis_symbol = "-"
                    vis_color = "Colors.red"
                elif op.visibility == Visibility.PROTECTED:
                    vis_symbol = "#"
                    vis_color = "Colors.orange"
                elif op.visibility == Visibility.PACKAGE:
                    vis_symbol = "~"
                    vis_color = "Colors.blue"

                params_desc = ", ".join(f"{p.name}: {p.type}" for p in getattr(op, 'parameters', []))
                sig = f"{vis_symbol} {op.name}({params_desc}): {ret_type}"

                call_args = []
                for p in getattr(op, 'parameters', []):
                    pt = self._dart_type(p.type)
                    if pt == "int":
                        call_args.append("0")
                    elif pt == "double":
                        call_args.append("0.0")
                    elif pt == "bool":
                        call_args.append("false")
                    elif pt == "DateTime":
                        call_args.append("DateTime.now()")
                    elif pt == "List<int>":
                        call_args.append("const []")
                    elif pt == "String":
                        call_args.append("''")
                    else:
                        call_args.append("null as dynamic")
                call_args_str = ", ".join(call_args)
                invocation = f"item.{op_method}({call_args_str});"
                result_suffix = " correctamente."
                if ret_type != "void":
                    invocation = "final res = " + invocation
                    result_suffix = ": $res"

                op_items.append(f"""
                  ListTile(
                    contentPadding: EdgeInsets.zero,
                    leading: CircleAvatar(
                      radius: 14,
                      backgroundColor: {vis_color}.withOpacity(0.2),
                      child: Text('{vis_symbol}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: {vis_color})),
                    ),
                    title: Text('{op.name}', style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                    subtitle: Text('{sig}', style: const TextStyle(fontSize: 11, fontFamily: 'monospace')),
                    trailing: FilledButton.tonal(
                      style: FilledButton.styleFrom(padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4), minimumSize: const Size(60, 32)),
                      onPressed: () {{
                        try {{
                          {invocation}
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              content: Text('Operación {op.name}() ejecutada{result_suffix}'),
                              backgroundColor: Colors.teal,
                            ),
                          );
                        }} catch (e) {{
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(content: Text('Error en {op.name}(): $e')),
                          );
                        }}
                      }},
                      child: const Text('Ejecutar', style: TextStyle(fontSize: 12)),
                    ),
                  ),""")

            op_items_str = "\n".join(op_items)
            operations_card_str = f"""
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      CircleAvatar(
                        backgroundColor: theme.colorScheme.secondaryContainer,
                        child: Icon(Icons.code, color: theme.colorScheme.onSecondaryContainer),
                      ),
                      const SizedBox(width: 12),
                      Text(
                        'Operaciones y Métodos UML',
                        style: (theme.textTheme.titleMedium ?? const TextStyle()).copyWith(fontWeight: FontWeight.bold),
                      ),
                    ],
                  ),
                  const Divider(height: 24),
                  {op_items_str}
                ],
              ),
            ),
          ),"""

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
          ),{operations_card_str}
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
        controllers_dispose = []
        form_fields_widgets = []
        model_construction_fields = []
        required_date_checks = []

        for attr in cls.attributes:
            if attr.name in (pk.name, "version"):
                continue

            dtype = self._dart_type(attr.type)
            required = self._is_required_attribute(attr)
            c_name = f"_{attr.name}Controller"

            if dtype == "bool":
                controllers_decl.append(f"  bool _{attr.name} = false;")
                controllers_init.append(f"    _{attr.name} = widget.item?.{attr.name} ?? false;")
                form_fields_widgets.append(f"""
              SwitchListTile(
                title: const Text('{self._humanize_name(attr.name)}'),
                value: _{attr.name},
                onChanged: (val) => setState(() => _{attr.name} = val),
              ),
              const SizedBox(height: 12),""")
                model_construction_fields.append(f"        {attr.name}: _{attr.name},")
            elif dtype == "DateTime":
                controllers_decl.append(f"  DateTime? _{attr.name};")
                controllers_init.append(f"    _{attr.name} = widget.item?.{attr.name};")
                if required:
                    required_date_checks.append(f"""    if (_{attr.name} == null) {{
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Selecciona {self._humanize_name(attr.name).lower()}')),
      );
      return;
    }}""")
                form_fields_widgets.append(f"""
              ListTile(
                contentPadding: EdgeInsets.zero,
                title: Text('{self._humanize_name(attr.name)}: ${{_{attr.name} != null ? DateFormat('dd/MM/yyyy').format(_{attr.name}!) : "Seleccionar fecha"}}'),
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
                controllers_decl.append(f"  final TextEditingController {c_name} = TextEditingController();")
                controllers_dispose.append(f"    {c_name}.dispose();")
                if dtype == "List<int>":
                    controllers_init.append(f"    {c_name}.text = (widget.item != null && widget.item!.{attr.name} != null) ? widget.item!.{attr.name}!.join(',') : '';")
                else:
                    controllers_init.append(f"    {c_name}.text = (widget.item != null && widget.item!.{attr.name} != null) ? '${{widget.item!.{attr.name}}}' : '';")

                kb_type = "TextInputType.text"
                if dtype in ("int", "double"):
                    kb_type = "const TextInputType.numberWithOptions(signed: true, decimal: " + ("true" if dtype == "double" else "false") + ")"

                validator_logic = ""
                if required:
                    validator_logic = f"""if (val == null || val.trim().isEmpty) {{
                  return 'El campo {attr.name} es obligatorio';
                }}"""
                if dtype == "int":
                    validator_logic += """
                if (val != null && val.trim().isNotEmpty && int.tryParse(val) == null) {
                  return 'Ingrese un número entero válido';
                }"""
                elif dtype == "double":
                    validator_logic += """
                if (val != null && val.trim().isNotEmpty && double.tryParse(val) == null) {
                  return 'Ingrese un valor numérico válido';
                }"""
                elif dtype == "List<int>":
                    validator_logic += """
                if (val != null && val.trim().isNotEmpty && val.split(',').any((id) => int.tryParse(id.trim()) == null)) {
                  return 'Ingrese IDs numéricos separados por comas';
                }"""

                human_name = self._humanize_name(attr.name)
                label = human_name + (" *" if required else " (opcional)")
                if dtype == "List<int>":
                    relation_name = self._humanize_name(attr.name[:-3]) if attr.name.endswith("Ids") else human_name
                    hint = f"IDs de {relation_name} separados por comas"
                elif attr.name.endswith("Id"):
                    relation_name = self._humanize_name(attr.name[:-2])
                    hint = f"ID de {relation_name}"
                else:
                    hint = f"Ingrese {human_name.lower()}"

                form_fields_widgets.append(f"""
              TextFormField(
                controller: {c_name},
                keyboardType: {kb_type},
                decoration: const InputDecoration(
                  labelText: '{label}',
                  hintText: '{hint}',
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
        controllers_dispose_str = "\n".join(controllers_dispose)
        form_fields_str = "\n".join(form_fields_widgets)
        model_construction_str = "\n".join(model_construction_fields)
        required_date_checks_str = "\n".join(required_date_checks)
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

  @override
  void dispose() {{
{controllers_dispose_str}
    super.dispose();
  }}

  Future<void> _save() async {{
    if (!_formKey.currentState!.validate()) return;
{required_date_checks_str}

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
        title: Text(isEdit ? 'Editar {self._humanize_name(cls.name)}' : 'Nuevo registro'),
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            Container(
              padding: const EdgeInsets.all(20), margin: const EdgeInsets.only(bottom: 24),
              decoration: BoxDecoration(color: Theme.of(context).colorScheme.primary.withOpacity(.10), borderRadius: BorderRadius.circular(20)),
              child: Row(children: [
                Icon(isEdit ? Icons.edit_note_rounded : Icons.note_add_outlined, size: 30, color: Theme.of(context).colorScheme.primary),
                const SizedBox(width: 14), Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  const Text('{self._humanize_name(cls.name)}', style: TextStyle(fontSize: 19, fontWeight: FontWeight.w700)),
                  const SizedBox(height: 4), const Text('Completa la información. Los campos con * son obligatorios.', style: TextStyle(fontSize: 12)),
                ])),
              ]),
            ),
            {form_fields_str}
            const SizedBox(height: 12),
          ],
        ),
      ),
      bottomNavigationBar: SafeArea(
        minimum: const EdgeInsets.fromLTRB(20, 12, 20, 16),
        child: FilledButton.icon(
              style: FilledButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 16)),
              icon: _isSaving
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                    )
                  : const Icon(Icons.save),
              label: Text(
                _isSaving ? 'Guardando…' : (isEdit ? 'Guardar cambios' : 'Crear registro'),
                style: const TextStyle(fontSize: 16),
              ),
              onPressed: _isSaving ? null : _save,
        ),
      ),
    );
  }}
}}
"""

    def _generate_widget_test(self) -> str:
        first = self._humanize_name(self.entities[0].name) if self.entities else ''
        return (self._mobile_template('flutter_widget_test.dart')
                .replace('__PACKAGE__', self.app_name)
                .replace('__FIRST_MODULE__', self._dart_string(first))
                .replace('__HAS_MODULES__', 'true' if self.entities else 'false'))
