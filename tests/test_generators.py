"""
GeneradorUML — Tests de Integración

Pruebas automatizadas que verifican:
1. Generación Spring Boot: entidades JPA con mappedBy correcto, Jackson annotations, naming consistente
2. Generación Flutter: endpoints sincronizados, modelos nullable, caché async
3. Validación UML: herencia circular, duplicados, integridad referencial
4. XMI round-trip: exportar → importar → comparar
5. MDJ round-trip: exportar → importar → comparar
"""

import pytest
import json
import os
import sys

# Ensure backend package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.app.models.uml_model import (
    UMLDiagram, UMLClass, UMLAttribute, UMLOperation, UMLParameter,
    UMLRelationship, RelationshipEnd, Position, Size,
    Visibility, RelationshipType, Multiplicity
)
from backend.app.models.uml_validator import UMLValidator
from backend.app.services.springboot_generator import SpringBootGenerator, to_snake_case, pluralize
from backend.app.services.flutter_generator import FlutterGenerator
from backend.app.services.xmi_adapter import XMIAdapter
from backend.app.services.mdj_adapter import MDJAdapter


# ─── Fixtures ──────────────────────────────────────────────────────────────

def _build_veterinaria_diagram() -> UMLDiagram:
    """Construye el diagrama de ejemplo 'veterinaria' con 3 clases y 2 relaciones."""
    diag = UMLDiagram(name="Sistema Veterinaria")

    cliente = UMLClass(
        id="cls-cliente", name="Cliente",
        attributes=[
            UMLAttribute(name="id", type="Long", visibility=Visibility.PRIVATE),
            UMLAttribute(name="nombre", type="String", visibility=Visibility.PUBLIC),
            UMLAttribute(name="telefono", type="String", visibility=Visibility.PUBLIC),
        ],
    )
    mascota = UMLClass(
        id="cls-mascota", name="Mascota",
        attributes=[
            UMLAttribute(name="id", type="Long", visibility=Visibility.PRIVATE),
            UMLAttribute(name="nombre", type="String", visibility=Visibility.PUBLIC),
            UMLAttribute(name="especie", type="String", visibility=Visibility.PUBLIC),
            UMLAttribute(name="fechaNacimiento", type="Date", visibility=Visibility.PUBLIC),
        ],
    )
    cita = UMLClass(
        id="cls-cita", name="Cita",
        attributes=[
            UMLAttribute(name="id", type="Long", visibility=Visibility.PRIVATE),
            UMLAttribute(name="fecha", type="Date", visibility=Visibility.PUBLIC),
            UMLAttribute(name="motivo", type="String", visibility=Visibility.PUBLIC),
            UMLAttribute(name="activa", type="Boolean", visibility=Visibility.PUBLIC),
        ],
    )

    diag.classes.extend([cliente, mascota, cita])

    # Cliente 1..* Mascota (Composición)
    diag.relationships.append(
        UMLRelationship(
            type=RelationshipType.COMPOSITION,
            source=RelationshipEnd(class_id="cls-cliente", multiplicity="1"),
            target=RelationshipEnd(class_id="cls-mascota", multiplicity="1..*"),
        )
    )

    # Mascota 1..* Cita (Asociación)
    diag.relationships.append(
        UMLRelationship(
            type=RelationshipType.ASSOCIATION,
            source=RelationshipEnd(class_id="cls-mascota", multiplicity="1"),
            target=RelationshipEnd(class_id="cls-cita", multiplicity="0..*"),
        )
    )

    return diag


# ─── Spring Boot Generator Tests ──────────────────────────────────────────

class TestSpringBootGenerator:
    def setup_method(self):
        self.diagram = _build_veterinaria_diagram()
        self.gen = SpringBootGenerator(self.diagram, base_package="com.test.vet")

    def test_generates_all_entity_files(self):
        files = self.gen.generate()
        src = "src/main/java/com/test/vet"
        assert f"{src}/entity/Cliente.java" in files
        assert f"{src}/entity/Mascota.java" in files
        assert f"{src}/entity/Cita.java" in files

    def test_mapped_by_composition_is_correct(self):
        """mappedBy on Cliente.mascotas should point to the field 'cliente' on Mascota."""
        files = self.gen.generate()
        src = "src/main/java/com/test/vet"
        cliente_entity = files[f"{src}/entity/Cliente.java"]
        assert 'mappedBy = "cliente"' in cliente_entity, \
            f"Expected mappedBy = 'cliente' in Cliente entity"

    def test_mapped_by_association_is_correct(self):
        """mappedBy on Mascota.citas should point to the field 'mascota' on Cita."""
        files = self.gen.generate()
        src = "src/main/java/com/test/vet"
        mascota_entity = files[f"{src}/entity/Mascota.java"]
        assert 'mappedBy = "mascota"' in mascota_entity, \
            f"Expected mappedBy = 'mascota' in Mascota entity"

    def test_json_managed_reference_on_onetomany(self):
        files = self.gen.generate()
        src = "src/main/java/com/test/vet"
        cliente_entity = files[f"{src}/entity/Cliente.java"]
        assert "@JsonManagedReference" in cliente_entity

    def test_json_back_reference_on_manytoone(self):
        files = self.gen.generate()
        src = "src/main/java/com/test/vet"
        mascota_entity = files[f"{src}/entity/Mascota.java"]
        assert "@JsonBackReference" in mascota_entity

    def test_json_ignore_properties_on_entity(self):
        files = self.gen.generate()
        src = "src/main/java/com/test/vet"
        for cls_name in ("Cliente", "Mascota", "Cita"):
            entity = files[f"{src}/entity/{cls_name}.java"]
            assert "@JsonIgnoreProperties" in entity

    def test_endpoint_path_naming(self):
        path = self.gen._get_endpoint_path("OrdenCompra")
        assert path == "orden-compras"
        path2 = self.gen._get_endpoint_path("Cliente")
        assert path2 == "clientes"

    def test_controller_uses_kebab_path(self):
        files = self.gen.generate()
        src = "src/main/java/com/test/vet"
        ctrl = files[f"{src}/controller/ClienteController.java"]
        assert '/api/clientes"' in ctrl

    def test_pom_xml_valid(self):
        files = self.gen.generate()
        pom = files["pom.xml"]
        assert "<groupId>com.test.vet</groupId>" in pom
        assert "spring-boot-starter-data-jpa" in pom


# ─── Flutter Generator Tests ──────────────────────────────────────────────

class TestFlutterGenerator:
    def setup_method(self):
        self.diagram = _build_veterinaria_diagram()
        self.gen = FlutterGenerator(self.diagram, app_name="VetApp")

    def test_generates_all_files(self):
        files = self.gen.generate_all()
        assert "pubspec.yaml" in files
        assert "lib/main.dart" in files

    def test_endpoint_matches_springboot(self):
        sb_gen = SpringBootGenerator(self.diagram)
        for cls in self.diagram.classes:
            sb_path = sb_gen._get_endpoint_path(cls.name)
            flutter_path = self.gen._get_endpoint_path(cls.name)
            assert sb_path == flutter_path, \
                f"Endpoint mismatch for {cls.name}: SB={sb_path}, Flutter={flutter_path}"

    def test_bool_is_nullable_in_model(self):
        files = self.gen.generate_all()
        cita_model = files["lib/models/cita.dart"]
        assert "bool?" in cita_model

    def test_offline_cache_uses_shared_preferences(self):
        files = self.gen.generate_all()
        cache = files["lib/services/offline_cache_service.dart"]
        assert "SharedPreferences" in cache

    def test_pubspec_has_speech_to_text(self):
        files = self.gen.generate_all()
        pubspec = files["pubspec.yaml"]
        assert "speech_to_text" in pubspec

    def test_assistant_uses_real_speech(self):
        files = self.gen.generate_all()
        assistant = files["lib/screens/assistant_screen.dart"]
        assert "speech_to_text" in assistant
        assert "_simulateVoiceInput" not in assistant


# ─── Validation Tests ─────────────────────────────────────────────────────

class TestUMLValidator:
    def test_valid_diagram_passes(self):
        diag = _build_veterinaria_diagram()
        validator = UMLValidator(diag)
        result = validator.validate()
        assert result.is_valid

    def test_circular_inheritance_detected(self):
        diag = UMLDiagram(name="Circular")
        a = UMLClass(id="a", name="A", attributes=[UMLAttribute(name="id", type="Long")])
        b = UMLClass(id="b", name="B", attributes=[UMLAttribute(name="id", type="Long")])
        diag.classes.extend([a, b])
        diag.relationships.append(
            UMLRelationship(
                type=RelationshipType.GENERALIZATION,
                source=RelationshipEnd(class_id="a"),
                target=RelationshipEnd(class_id="b"),
            )
        )
        diag.relationships.append(
            UMLRelationship(
                type=RelationshipType.GENERALIZATION,
                source=RelationshipEnd(class_id="b"),
                target=RelationshipEnd(class_id="a"),
            )
        )
        validator = UMLValidator(diag)
        result = validator.validate()
        errors = [i for i in result.issues if i.severity.value == "error"]
        assert len(errors) > 0

    def test_duplicate_class_names_detected(self):
        diag = UMLDiagram(name="Duplicates")
        a = UMLClass(id="a", name="Cliente", attributes=[UMLAttribute(name="id", type="Long")])
        b = UMLClass(id="b", name="Cliente", attributes=[UMLAttribute(name="id", type="Long")])
        diag.classes.extend([a, b])
        validator = UMLValidator(diag)
        result = validator.validate()
        errors = [i for i in result.issues if i.severity.value == "error"]
        assert len(errors) > 0


# ─── XMI Round-Trip Tests ─────────────────────────────────────────────────

class TestXMIRoundTrip:
    def test_export_import_preserves_classes(self):
        diag = _build_veterinaria_diagram()
        adapter = XMIAdapter()
        xmi_content = adapter.export_to_xmi(diag)
        assert len(xmi_content) > 100
        imported = adapter.import_from_xmi(xmi_content)
        assert len(imported.classes) == len(diag.classes)
        original_names = {c.name for c in diag.classes}
        imported_names = {c.name for c in imported.classes}
        assert original_names == imported_names


# ─── MDJ Round-Trip Tests ─────────────────────────────────────────────────

class TestMDJRoundTrip:
    def test_export_import_preserves_classes(self):
        diag = _build_veterinaria_diagram()
        adapter = MDJAdapter()
        mdj_content = adapter.export_to_mdj(diag)
        assert len(mdj_content) > 100
        imported = adapter.import_from_mdj(mdj_content)
        assert len(imported.classes) == len(diag.classes)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
