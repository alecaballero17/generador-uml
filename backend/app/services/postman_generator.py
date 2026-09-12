"""
GeneradorUML — Generador de Colección Postman

Genera un archivo JSON importable en Postman con requests para cada endpoint CRUD,
variables de entorno, ejemplos de body, y tests básicos.
"""

from __future__ import annotations
import json
import uuid
from ..models.uml_model import UMLDiagram, UMLClass, UMLAttribute
from .springboot_generator import to_pascal_case, to_camel_case, to_snake_case, pluralize, get_java_type


def _generate_sample_value(attr_type: str, attr_name: str) -> object:
    """Generate a sample value for a given type."""
    type_lower = attr_type.lower()
    name_lower = attr_name.lower()

    if "id" == name_lower:
        return 1
    if type_lower in ("string",):
        if "nombre" in name_lower or "name" in name_lower:
            return "Ejemplo"
        if "email" in name_lower or "correo" in name_lower:
            return "ejemplo@mail.com"
        if "telefono" in name_lower or "phone" in name_lower:
            return "+591 12345678"
        if "direccion" in name_lower or "address" in name_lower:
            return "Av. Ejemplo 123"
        if "descripcion" in name_lower or "description" in name_lower:
            return "Descripción de ejemplo"
        return f"valor_{attr_name}"
    if type_lower in ("integer", "int", "long"):
        return 1
    if type_lower in ("float", "double", "real", "bigdecimal"):
        return 10.5
    if type_lower in ("boolean",):
        return True
    if type_lower in ("date", "localdate"):
        return "2026-01-15"
    if type_lower in ("localdatetime",):
        return "2026-01-15T10:30:00"
    return f"valor_{attr_name}"


class PostmanGenerator:
    """Generates a Postman collection from a UML diagram."""

    def __init__(self, diagram: UMLDiagram, base_url: str = "{{baseUrl}}",
                 port: str = "8080"):
        self.diagram = diagram
        self.base_url = base_url
        self.port = port

    def generate(self) -> dict:
        """Generate the complete Postman collection."""
        collection = {
            "info": {
                "_postman_id": str(uuid.uuid4()),
                "name": f"{self.diagram.name} - API Collection",
                "description": f"Colección de Postman generada por GeneradorUML para el diagrama: {self.diagram.name}",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "item": [],
            "variable": [
                {"key": "baseUrl", "value": f"http://localhost:{self.port}", "type": "string"},
                {"key": "port", "value": self.port, "type": "string"}
            ]
        }

        for cls in self.diagram.classes:
            if cls.is_interface:
                continue
            folder = self._generate_entity_folder(cls)
            collection["item"].append(folder)

        return collection

    def generate_json(self, indent: int = 2) -> str:
        """Generate the collection as a JSON string."""
        return json.dumps(self.generate(), indent=indent, ensure_ascii=False)

    def _generate_entity_folder(self, cls: UMLClass) -> dict:
        """Generate a folder with CRUD requests for an entity."""
        class_name = to_pascal_case(cls.name)
        path = to_snake_case(pluralize(cls.name)).replace("_", "-")
        sample_body = self._generate_sample_body(cls)

        return {
            "name": class_name,
            "item": [
                self._get_all_request(class_name, path),
                self._get_by_id_request(class_name, path),
                self._create_request(class_name, path, sample_body),
                self._update_request(class_name, path, sample_body),
                self._delete_request(class_name, path),
                self._count_request(class_name, path),
            ]
        }

    def _generate_sample_body(self, cls: UMLClass) -> dict:
        """Generate a sample request body for POST/PUT."""
        body = {}
        for attr in cls.attributes:
            if attr.name.lower() == "id":
                continue
            body[to_camel_case(attr.name)] = _generate_sample_value(attr.type, attr.name)
        return body

    def _get_all_request(self, class_name: str, path: str) -> dict:
        return {
            "name": f"Obtener todos los {class_name}",
            "request": {
                "method": "GET",
                "header": [],
                "url": {
                    "raw": f"{{{{baseUrl}}}}/api/{path}",
                    "host": ["{{baseUrl}}"],
                    "path": ["api", path]
                }
            },
            "response": [],
            "event": [{
                "listen": "test",
                "script": {
                    "exec": [
                        "pm.test('Status code is 200', function () {",
                        "    pm.response.to.have.status(200);",
                        "});",
                        "pm.test('Response is an array', function () {",
                        "    var jsonData = pm.response.json();",
                        "    pm.expect(jsonData).to.be.an('array');",
                        "});"
                    ],
                    "type": "text/javascript"
                }
            }]
        }

    def _get_by_id_request(self, class_name: str, path: str) -> dict:
        return {
            "name": f"Obtener {class_name} por ID",
            "request": {
                "method": "GET",
                "header": [],
                "url": {
                    "raw": f"{{{{baseUrl}}}}/api/{path}/1",
                    "host": ["{{baseUrl}}"],
                    "path": ["api", path, "1"]
                }
            },
            "response": [],
            "event": [{
                "listen": "test",
                "script": {
                    "exec": [
                        "pm.test('Status code is 200', function () {",
                        "    pm.response.to.have.status(200);",
                        "});",
                        "pm.test('Response has id', function () {",
                        "    var jsonData = pm.response.json();",
                        "    pm.expect(jsonData).to.have.property('id');",
                        "});"
                    ],
                    "type": "text/javascript"
                }
            }]
        }

    def _create_request(self, class_name: str, path: str, body: dict) -> dict:
        return {
            "name": f"Crear {class_name}",
            "request": {
                "method": "POST",
                "header": [
                    {"key": "Content-Type", "value": "application/json"}
                ],
                "body": {
                    "mode": "raw",
                    "raw": json.dumps(body, indent=2, ensure_ascii=False),
                    "options": {"raw": {"language": "json"}}
                },
                "url": {
                    "raw": f"{{{{baseUrl}}}}/api/{path}",
                    "host": ["{{baseUrl}}"],
                    "path": ["api", path]
                }
            },
            "response": [],
            "event": [{
                "listen": "test",
                "script": {
                    "exec": [
                        "pm.test('Status code is 201', function () {",
                        "    pm.response.to.have.status(201);",
                        "});",
                        "pm.test('Response has id', function () {",
                        "    var jsonData = pm.response.json();",
                        "    pm.expect(jsonData).to.have.property('id');",
                        "});"
                    ],
                    "type": "text/javascript"
                }
            }]
        }

    def _update_request(self, class_name: str, path: str, body: dict) -> dict:
        return {
            "name": f"Actualizar {class_name}",
            "request": {
                "method": "PUT",
                "header": [
                    {"key": "Content-Type", "value": "application/json"}
                ],
                "body": {
                    "mode": "raw",
                    "raw": json.dumps(body, indent=2, ensure_ascii=False),
                    "options": {"raw": {"language": "json"}}
                },
                "url": {
                    "raw": f"{{{{baseUrl}}}}/api/{path}/1",
                    "host": ["{{baseUrl}}"],
                    "path": ["api", path, "1"]
                }
            },
            "response": [],
            "event": [{
                "listen": "test",
                "script": {
                    "exec": [
                        "pm.test('Status code is 200', function () {",
                        "    pm.response.to.have.status(200);",
                        "});"
                    ],
                    "type": "text/javascript"
                }
            }]
        }

    def _delete_request(self, class_name: str, path: str) -> dict:
        return {
            "name": f"Eliminar {class_name}",
            "request": {
                "method": "DELETE",
                "header": [],
                "url": {
                    "raw": f"{{{{baseUrl}}}}/api/{path}/1",
                    "host": ["{{baseUrl}}"],
                    "path": ["api", path, "1"]
                }
            },
            "response": [],
            "event": [{
                "listen": "test",
                "script": {
                    "exec": [
                        "pm.test('Status code is 200', function () {",
                        "    pm.response.to.have.status(200);",
                        "});",
                        "pm.test('Deleted flag is true', function () {",
                        "    var jsonData = pm.response.json();",
                        "    pm.expect(jsonData.deleted).to.be.true;",
                        "});"
                    ],
                    "type": "text/javascript"
                }
            }]
        }

    def _count_request(self, class_name: str, path: str) -> dict:
        return {
            "name": f"Contar {class_name}",
            "request": {
                "method": "GET",
                "header": [],
                "url": {
                    "raw": f"{{{{baseUrl}}}}/api/{path}/count",
                    "host": ["{{baseUrl}}"],
                    "path": ["api", path, "count"]
                }
            },
            "response": [],
            "event": [{
                "listen": "test",
                "script": {
                    "exec": [
                        "pm.test('Status code is 200', function () {",
                        "    pm.response.to.have.status(200);",
                        "});",
                        "pm.test('Response has count', function () {",
                        "    var jsonData = pm.response.json();",
                        "    pm.expect(jsonData).to.have.property('count');",
                        "});"
                    ],
                    "type": "text/javascript"
                }
            }]
        }
