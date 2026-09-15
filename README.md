# GeneradorUML — Herramienta CASE de Ingeniería de Software

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI_0.100+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Spring Boot](https://img.shields.io/badge/Generated_Backend-Spring_Boot_3.x-6DB33F?logo=springboot&logoColor=white)](https://spring.io/projects/spring-boot)
[![Flutter](https://img.shields.io/badge/Generated_Mobile-Flutter_3.x-02569B?logo=flutter&logoColor=white)](https://flutter.dev)
[![UML](https://img.shields.io/badge/Standard-UML_2.5+-blue)](https://www.omg.org/spec/UML/)
[![XMI](https://img.shields.io/badge/Interoperability-XMI_2.1_ISO/IEC_19509-orange)](https://www.omg.org/spec/XMI/)

**GeneradorUML** es una herramienta CASE (Computer-Aided Software Engineering) integral que permite crear, editar e interpretar diagramas de clases UML 2.5+, y a partir de ellos generar una aplicación de producción completa y funcional de extremo a extremo:
- **Backend:** Spring Boot 3.x con Java 17, Spring Data JPA / Hibernate, controladores REST y PostgreSQL.
- **Frontend Móvil:** Aplicación completa Flutter 3.x con Material 3, pantallas CRUD con formularios reactivos, validación, búsqueda, caché offline y pantalla de Asistente IA/Voz.
- **Colección Postman:** Postman Collection v2.1.0 con peticiones CRUD automáticas y scripts de prueba de aserción.
- **Interoperabilidad:** Importación y exportación bidireccional XMI 2.1 (Enterprise Architect y StarUML) y StarUML `.mdj`.
- **Computer Vision & OCR:** Interpretación de fotografías de diagramas en pizarras o papel con pipeline de validación humana (*Human-in-the-Loop*).
- **Voz:** Entrada de comandos de modelado en lenguaje natural en español (Web Speech API).
- **Editor Web:** Lienzo vectorial interactivo SVG con tema oscuro, glassmorphism, soporte para deshacer/rehacer y colaboración en tiempo real con WebSockets.

---

## 🚀 Inicio Rápido

### 1. Clonar el repositorio y acceder a la carpeta:
```bash
cd generador-uml
```

### 2. Instalar dependencias del backend:
```bash
cd backend
pip install -r requirements.txt
```

### 3. Iniciar el servidor GeneradorUML:
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Abrir en el navegador:
Ingresa a [http://localhost:8000](http://localhost:8000).

---

## 📂 Estructura del Repositorio

```
generador-uml/
├── backend/
│   ├── app/
│   │   ├── main.py                      # FastAPI REST API y WebSockets
│   │   ├── models/
│   │   │   ├── uml_model.py             # Metamodelo UML 2.5+ interno
│   │   │   └── uml_validator.py         # Validador semántico de diagramas
│   │   └── services/
│   │       ├── springboot_generator.py  # Generador Spring Boot 3 + JPA + PostgreSQL
│   │       ├── flutter_generator.py     # Generador Flutter 3.x + Material 3
│   │       ├── postman_generator.py     # Generador Postman Collection v2.1.0
│   │       ├── xmi_adapter.py           # Adaptador bidireccional XMI 2.1
│   │       ├── mdj_adapter.py           # Adaptador bidireccional StarUML .mdj
│   │       └── photo_interpreter.py     # Computer Vision (OpenCV) + OCR (Tesseract)
│   └── requirements.txt
├── frontend/
│   ├── index.html                       # Editor web SPA
│   ├── css/index.css                    # Sistema de diseño oscuro y glassmorphism
│   └── js/app.js                        # Lógica del canvas SVG, voz, foto y WebSockets
├── examples/
│   └── veterinaria.json                 # Caso de prueba oficial (5 clases, 4 relaciones)
├── docs/
│   ├── manual_usuario.md                # Manual de usuario completo paso a paso
│   └── arquitectura.md                  # Documento de arquitectura y decisiones de diseño
└── output/                              # Directorio de aplicaciones generadas
```

---

## 🧪 Ejecución de Pruebas de Verificación

Se incluyen scripts de verificación automatizada en Python para validar todos los componentes:

### 1. Prueba de Generación Completa (Spring Boot + Flutter + Postman):
```bash
python -c "
from backend.app.models.uml_model import UMLDiagram
from backend.app.services.springboot_generator import SpringBootGenerator
from backend.app.services.flutter_generator import FlutterGenerator
from backend.app.services.postman_generator import PostmanGenerator
import json

diag = UMLDiagram.from_dict(json.load(open('examples/veterinaria.json', encoding='utf-8')))
sb = SpringBootGenerator(diag).generate_to_disk('output/test_sb')
fl = FlutterGenerator(diag).generate_to_disk('output/test_fl')
pm = PostmanGenerator(diag).generate_dict()
print(f'OK: {len(sb)} archivos Spring Boot, {len(fl)} archivos Flutter, {len(pm[\"item\"])} carpetas Postman')
"
```

### 2. Prueba de Intercambio Bidireccional XMI 2.1 y StarUML MDJ:
```bash
python -c "
import json
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)
vet_data = json.load(open('examples/veterinaria.json', encoding='utf-8'))

# XMI 2.1
xmi = client.post('/api/export/xmi', json={'diagram': vet_data}).json()['xmi']
imp_xmi = client.post('/api/import/xmi', files={'file': ('v.xmi', xmi.encode('utf-8'))}).json()['diagram']
assert len(imp_xmi['classes']) == 5

# StarUML MDJ
mdj = client.post('/api/export/mdj', json={'diagram': vet_data}).json()
imp_mdj = client.post('/api/import/mdj', files={'file': ('v.mdj', json.dumps(mdj).encode('utf-8'))}).json()['diagram']
assert len(imp_mdj['classes']) == 5
print('Interoperabilidad XMI 2.1 y StarUML MDJ verificada al 100%')
"
```

---

### Backend Spring Boot:
```bash
cd output/<directorio_generado>/springboot
# Usar Maven instalado:
mvn clean compile spring-boot:run
# O usar el Maven Wrapper incluido en Windows:
.\mvnw.cmd spring-boot:run
```
Acceso REST: `http://localhost:8080/api/<entidad>`

### App Móvil / Web Flutter:
El generador produce la arquitectura completa Dart/Material 3 (`lib/`, `pubspec.yaml`). Para generar los archivos de plataforma nativa (Web, Windows, Android):
```bash
cd output/<directorio_generado>/flutter_app
# 1. Crear las plataformas nativas necesarias:
flutter create .
# 2. Instalar dependencias:
flutter pub get
# 3. Ejecutar en Chrome (Web) o dispositivo móvil/desktop:
flutter run -d chrome
```

### Colección Postman:
Importa el archivo `postman_collection.json` directamente en Postman y ejecuta las peticiones preconfiguradas con aserciones automatizadas.

---

## 📖 Documentación

- [Manual de Usuario](docs/manual_usuario.md): Guía paso a paso para modelar clases, usar el dictado por voz, cargar fotos de pizarras y generar aplicaciones.
- [Documento de Arquitectura](docs/arquitectura.md): Decisiones técnicas de ingeniería, mapeo JPA de composiciones/asociaciones, modelo de concurrencia y adaptadores XMI/MDJ.

---
*GeneradorUML — Proyecto Académico de Ingeniería de Software.*
