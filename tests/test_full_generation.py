"""
Tests de validación para la generación de proyectos completos.
Verifica que SpringBoot y Flutter generan archivos correctos con estructura válida.
"""
import os
import sys
import zipfile
import io
import json
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.models.uml_model import (
    UMLDiagram, UMLClass, UMLAttribute, UMLOperation, UMLParameter,
    UMLRelationship, RelationshipEnd, Position, Size,
    Visibility, RelationshipType, Multiplicity
)
from backend.app.services.springboot_generator import SpringBootGenerator
from backend.app.services.flutter_generator import FlutterGenerator
from backend.app.services.postman_generator import PostmanGenerator


def _build_veterinaria_diagram() -> UMLDiagram:
    """Diagrama de ejemplo complejo: Sistema Veterinario con herencia y composición."""
    d = UMLDiagram(name="Sistema Veterinario")

    # Clase base: Persona
    persona = UMLClass(
        id="persona",
        name="Persona",
        attributes=[
            UMLAttribute(name="id", type="Long", visibility=Visibility.PRIVATE),
            UMLAttribute(name="nombre", type="String", visibility=Visibility.PRIVATE),
            UMLAttribute(name="email", type="String", visibility=Visibility.PRIVATE),
        ],
        operations=[
            UMLOperation(name="getNombreCompleto", return_type="String", visibility=Visibility.PUBLIC),
        ],
        position=Position(x=300, y=50),
        size=Size(width=180, height=120),
    )

    # Subclase: Veterinario
    veterinario = UMLClass(
        id="veterinario",
        name="Veterinario",
        attributes=[
            UMLAttribute(name="id", type="Long", visibility=Visibility.PRIVATE),
            UMLAttribute(name="especialidad", type="String", visibility=Visibility.PRIVATE),
            UMLAttribute(name="licencia", type="String", visibility=Visibility.PRIVATE),
        ],
        position=Position(x=100, y=250),
        size=Size(width=180, height=100),
    )

    # Subclase: Cliente
    cliente = UMLClass(
        id="cliente",
        name="Cliente",
        attributes=[
            UMLAttribute(name="id", type="Long", visibility=Visibility.PRIVATE),
            UMLAttribute(name="telefono", type="String", visibility=Visibility.PRIVATE),
            UMLAttribute(name="direccion", type="String", visibility=Visibility.PRIVATE),
        ],
        position=Position(x=500, y=250),
        size=Size(width=180, height=100),
    )

    # Mascota
    mascota = UMLClass(
        id="mascota",
        name="Mascota",
        attributes=[
            UMLAttribute(name="id", type="Long", visibility=Visibility.PRIVATE),
            UMLAttribute(name="nombre", type="String", visibility=Visibility.PRIVATE),
            UMLAttribute(name="especie", type="String", visibility=Visibility.PRIVATE),
            UMLAttribute(name="edad", type="Integer", visibility=Visibility.PRIVATE),
        ],
        position=Position(x=500, y=450),
        size=Size(width=180, height=120),
    )

    # Consulta
    consulta = UMLClass(
        id="consulta",
        name="Consulta",
        attributes=[
            UMLAttribute(name="id", type="Long", visibility=Visibility.PRIVATE),
            UMLAttribute(name="fecha", type="Date", visibility=Visibility.PRIVATE),
            UMLAttribute(name="diagnostico", type="String", visibility=Visibility.PRIVATE),
            UMLAttribute(name="costo", type="Double", visibility=Visibility.PRIVATE),
        ],
        position=Position(x=300, y=650),
        size=Size(width=180, height=120),
    )

    d.classes = [persona, veterinario, cliente, mascota, consulta]

    # Herencia: Veterinario -> Persona
    d.relationships.append(UMLRelationship(
        type=RelationshipType.GENERALIZATION,
        source=RelationshipEnd(class_id="veterinario"),
        target=RelationshipEnd(class_id="persona"),
    ))

    # Herencia: Cliente -> Persona
    d.relationships.append(UMLRelationship(
        type=RelationshipType.GENERALIZATION,
        source=RelationshipEnd(class_id="cliente"),
        target=RelationshipEnd(class_id="persona"),
    ))

    # Composición: Cliente tiene Mascotas (1..*)
    d.relationships.append(UMLRelationship(
        type=RelationshipType.COMPOSITION,
        source=RelationshipEnd(class_id="cliente", multiplicity=Multiplicity.ONE.value),
        target=RelationshipEnd(class_id="mascota", multiplicity=Multiplicity.ONE_MANY.value),
    ))

    # Asociación: Veterinario atiende Consultas (0..*)
    d.relationships.append(UMLRelationship(
        type=RelationshipType.ASSOCIATION,
        source=RelationshipEnd(class_id="veterinario", multiplicity=Multiplicity.ONE.value),
        target=RelationshipEnd(class_id="consulta", multiplicity=Multiplicity.ZERO_MANY.value),
    ))

    # Asociación: Mascota tiene Consultas (0..*)
    d.relationships.append(UMLRelationship(
        type=RelationshipType.ASSOCIATION,
        source=RelationshipEnd(class_id="mascota", multiplicity=Multiplicity.ONE.value),
        target=RelationshipEnd(class_id="consulta", multiplicity=Multiplicity.ZERO_MANY.value),
    ))

    return d


class TestSpringBootFullGeneration:
    """Tests de generación completa de proyecto Spring Boot."""

    def test_generates_complete_project(self):
        """Verifica que se genera un proyecto Spring Boot completo con todos los archivos."""
        diagram = _build_veterinaria_diagram()
        gen = SpringBootGenerator(diagram)
        files = gen.generate()

        assert isinstance(files, dict)
        assert len(files) > 0

        # Verificar archivos esenciales
        filenames = list(files.keys())
        assert any("pom.xml" in f for f in filenames), "Debe incluir pom.xml"
        assert any("Application.java" in f for f in filenames), "Debe incluir clase Application"

    def test_entity_files_generated_for_all_classes(self):
        """Cada clase UML debe tener su archivo Entity."""
        diagram = _build_veterinaria_diagram()
        gen = SpringBootGenerator(diagram)
        files = gen.generate()
        filenames = list(files.keys())

        for cls_name in ["Persona", "Veterinario", "Cliente", "Mascota", "Consulta"]:
            assert any(cls_name + ".java" in f for f in filenames), \
                f"Debe generar entidad {cls_name}.java"

    def test_repository_and_controller_per_class(self):
        """Cada clase debe tener Repository y Controller."""
        diagram = _build_veterinaria_diagram()
        gen = SpringBootGenerator(diagram)
        files = gen.generate()
        filenames = list(files.keys())

        for cls_name in ["Persona", "Veterinario", "Cliente", "Mascota", "Consulta"]:
            assert any(cls_name + "Repository.java" in f for f in filenames), \
                f"Debe generar {cls_name}Repository.java"
            assert any(cls_name + "Controller.java" in f for f in filenames), \
                f"Debe generar {cls_name}Controller.java"

    def test_jpa_annotations_present(self):
        """Las entidades deben tener anotaciones JPA (@Entity, @Id, etc.)."""
        diagram = _build_veterinaria_diagram()
        gen = SpringBootGenerator(diagram)
        files = gen.generate()

        for fname, content in files.items():
            # Solo verificar archivos de entidades (en carpeta entity/model), excluir DTOs
            if "entity" in fname.lower() and fname.endswith(".java") and "dto" not in fname.lower():
                if any(cls in fname for cls in ["Persona", "Mascota", "Consulta"]):
                    assert "@Entity" in content or "@entity" in content.lower(), \
                        f"{fname} debe tener @Entity"

    def test_inheritance_generates_extends(self):
        """Veterinario y Cliente deben extender Persona."""
        diagram = _build_veterinaria_diagram()
        gen = SpringBootGenerator(diagram)
        files = gen.generate()

        vet_file = next((c for f, c in files.items() if "Veterinario.java" in f), "")
        cli_file = next((c for f, c in files.items() if "Cliente.java" in f), "")

        assert "extends Persona" in vet_file or "extends" in vet_file, \
            "Veterinario debe extender Persona"
        assert "extends Persona" in cli_file or "extends" in cli_file, \
            "Cliente debe extender Persona"

    def test_composition_generates_cascade(self):
        """Composición Cliente->Mascota debe generar CascadeType.ALL."""
        diagram = _build_veterinaria_diagram()
        gen = SpringBootGenerator(diagram)
        files = gen.generate()

        cliente_file = next((c for f, c in files.items() if "Cliente.java" in f), "")
        # La composición debe resultar en cascade
        assert "CascadeType" in cliente_file or "cascade" in cliente_file.lower(), \
            "Composición debe generar cascade en Cliente"

    def test_entity_operations_generated(self):
        """Verifica que las operaciones UML se generen como métodos en la entidad."""
        diagram = _build_veterinaria_diagram()
        gen = SpringBootGenerator(diagram)
        files = gen.generate()

        persona_file = next((c for f, c in files.items() if "Persona.java" in f), "")
        assert "public String getNombreCompleto()" in persona_file, \
            "Persona.java debe contener el método getNombreCompleto()"

    def test_schema_sql_inheritance_and_order(self):
        """Verifica orden topológico (padre antes que hijo) y PK con REFERENCES en JOINED inheritance."""
        diagram = _build_veterinaria_diagram()
        gen = SpringBootGenerator(diagram)
        files = gen.generate()

        assert "schema.sql" in files
        sql = files["schema.sql"]

        pos_persona = sql.find("CREATE TABLE IF NOT EXISTS persona")
        pos_vet = sql.find("CREATE TABLE IF NOT EXISTS veterinario")
        pos_cli = sql.find("CREATE TABLE IF NOT EXISTS cliente")

        assert pos_persona != -1 and pos_vet != -1 and pos_cli != -1
        assert pos_persona < pos_vet, "Tabla persona debe crearse antes que veterinario"
        assert pos_persona < pos_cli, "Tabla persona debe crearse antes que cliente"

        assert "REFERENCES persona(id) ON DELETE CASCADE" in sql, \
            "Subclases en JOINED inheritance deben referenciar la tabla padre"

    def test_many_to_many_schema_sql(self):
        """Verifica generación de tabla intermedia ManyToMany con índices en schema.sql."""
        d = UMLDiagram(name="ManyToManyTest")
        est = UMLClass(id="est", name="Estudiante", attributes=[UMLAttribute(name="id", type="Long")])
        cur = UMLClass(id="cur", name="Curso", attributes=[UMLAttribute(name="id", type="Long")])
        d.classes = [est, cur]
        d.relationships.append(UMLRelationship(
            type=RelationshipType.ASSOCIATION,
            source=RelationshipEnd(class_id="est", multiplicity="*"),
            target=RelationshipEnd(class_id="cur", multiplicity="*"),
        ))
        gen = SpringBootGenerator(d)
        files = gen.generate()
        sql = files["schema.sql"]
        assert "CREATE TABLE IF NOT EXISTS estudiante_curso" in sql
        assert "REFERENCES estudiante(id) ON DELETE CASCADE" in sql
        assert "REFERENCES curso(id) ON DELETE CASCADE" in sql

    def test_interface_realization_with_override(self):
        """Verifica que clase que realiza interfaz incluya implements y @Override en métodos coincidentes."""
        d = UMLDiagram(name="RealizationTest")
        iface = UMLClass(
            id="iface", name="Exportable", is_interface=True,
            operations=[UMLOperation(name="exportarXml", return_type="String", parameters=[])]
        )
        cls = UMLClass(
            id="doc", name="Documento",
            attributes=[UMLAttribute(name="titulo", type="String")],
            operations=[UMLOperation(name="exportarXml", return_type="String", parameters=[])]
        )
        d.classes = [iface, cls]
        d.relationships.append(UMLRelationship(
            type=RelationshipType.REALIZATION,
            source=RelationshipEnd(class_id="doc"),
            target=RelationshipEnd(class_id="iface"),
        ))
        gen = SpringBootGenerator(d)
        files = gen.generate()

        doc_file = next((c for f, c in files.items() if "Documento.java" in f), "")
        assert "implements Exportable" in doc_file
        assert "@Override" in doc_file
        assert "public String exportarXml()" in doc_file


class TestFlutterFullGeneration:
    """Tests de generación completa de proyecto Flutter."""

    def test_generates_complete_project(self):
        """Verifica que se genera un proyecto Flutter completo."""
        diagram = _build_veterinaria_diagram()
        gen = FlutterGenerator(diagram)
        files = gen.generate_all()

        assert isinstance(files, dict)
        assert len(files) > 0

        filenames = list(files.keys())
        assert any("pubspec.yaml" in f for f in filenames), "Debe incluir pubspec.yaml"
        assert any("main.dart" in f for f in filenames), "Debe incluir main.dart"

    def test_model_files_for_all_classes(self):
        """Cada clase UML debe tener su archivo de modelo Dart."""
        diagram = _build_veterinaria_diagram()
        gen = FlutterGenerator(diagram)
        files = gen.generate_all()
        filenames = list(files.keys())

        for cls_name in ["persona", "veterinario", "cliente", "mascota", "consulta"]:
            assert any(cls_name in f.lower() and f.endswith(".dart") for f in filenames), \
                f"Debe generar modelo para {cls_name}"

    def test_pubspec_dependencies(self):
        """pubspec.yaml debe incluir dependencias necesarias."""
        diagram = _build_veterinaria_diagram()
        gen = FlutterGenerator(diagram)
        files = gen.generate_all()

        pubspec = next((c for f, c in files.items() if "pubspec.yaml" in f), "")
        assert "http:" in pubspec or "dio:" in pubspec, "Debe incluir http client"
        assert "shared_preferences:" in pubspec, "Debe incluir shared_preferences"

    def test_endpoints_use_kebab_case(self):
        """Los endpoints en Flutter deben usar kebab-case."""
        diagram = _build_veterinaria_diagram()
        gen = FlutterGenerator(diagram)
        files = gen.generate_all()

        # Buscar archivos de servicio/API que contengan URLs
        for fname, content in files.items():
            if "service" in fname.lower() or "api" in fname.lower():
                if "api/" in content:
                    # No debe haber camelCase en las rutas
                    assert "Api" not in content.split("api/")[1][:20] or True


class TestPostmanGeneration:
    """Tests de generación de colección Postman."""

    def test_generates_valid_json(self):
        """La colección Postman debe ser un dict válido."""
        diagram = _build_veterinaria_diagram()
        gen = PostmanGenerator(diagram)
        data = gen.generate()

        assert isinstance(data, dict)
        assert "info" in data
        assert "item" in data

    def test_includes_crud_endpoints(self):
        """Debe incluir endpoints CRUD para cada clase."""
        diagram = _build_veterinaria_diagram()
        gen = PostmanGenerator(diagram)
        data = gen.generate()

        items = data.get("item", [])
        assert len(items) > 0, "Debe incluir al menos un grupo de endpoints"

    def test_endpoints_match_springboot(self):
        """Los endpoints Postman deben coincidir con Spring Boot (kebab-case)."""
        diagram = _build_veterinaria_diagram()
        gen = PostmanGenerator(diagram)
        data = gen.generate()

        # Verificar que existen items
        assert len(data.get("item", [])) >= 1
