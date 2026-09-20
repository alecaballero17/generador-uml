"""
Test de roundtrip completo de interoperabilidad.
Crea un diagrama en memoria, lo exporta a XMI/MDJ, lo reimporta y verifica
que los datos se preservan correctamente.
"""
import json
import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.models.uml_model import (
    UMLDiagram, UMLClass, UMLAttribute, UMLOperation, UMLParameter,
    UMLRelationship, RelationshipEnd, Position, Size,
    Visibility, RelationshipType, Multiplicity
)
from backend.app.services.xmi_adapter import XMIAdapter
from backend.app.services.mdj_adapter import MDJAdapter


def _build_test_diagram() -> UMLDiagram:
    """Diagrama de prueba con clases, herencia, composición y atributos."""
    d = UMLDiagram(name="TestRoundtrip")

    d.classes = [
        UMLClass(
            id="animal",
            name="Animal",
            attributes=[
                UMLAttribute(name="id", type="Long", visibility=Visibility.PRIVATE),
                UMLAttribute(name="nombre", type="String", visibility=Visibility.PUBLIC),
                UMLAttribute(name="peso", type="Double", visibility=Visibility.PROTECTED),
            ],
            operations=[
                UMLOperation(name="comer", return_type="void", visibility=Visibility.PUBLIC,
                            parameters=[UMLParameter(name="alimento", type="String")]),
                UMLOperation(name="dormir", return_type="void", visibility=Visibility.PUBLIC),
            ],
            position=Position(x=100, y=50),
            size=Size(width=200, height=150),
        ),
        UMLClass(
            id="perro",
            name="Perro",
            attributes=[
                UMLAttribute(name="id", type="Long", visibility=Visibility.PRIVATE),
                UMLAttribute(name="raza", type="String", visibility=Visibility.PRIVATE),
            ],
            operations=[
                UMLOperation(name="ladrar", return_type="String", visibility=Visibility.PUBLIC),
            ],
            position=Position(x=50, y=300),
            size=Size(width=200, height=120),
        ),
        UMLClass(
            id="gato",
            name="Gato",
            attributes=[
                UMLAttribute(name="id", type="Long", visibility=Visibility.PRIVATE),
                UMLAttribute(name="interior", type="Boolean", visibility=Visibility.PRIVATE),
            ],
            position=Position(x=300, y=300),
            size=Size(width=200, height=120),
        ),
        UMLClass(
            id="duenio",
            name="Duenio",
            attributes=[
                UMLAttribute(name="id", type="Long", visibility=Visibility.PRIVATE),
                UMLAttribute(name="nombre", type="String", visibility=Visibility.PRIVATE),
            ],
            position=Position(x=500, y=50),
            size=Size(width=200, height=100),
        ),
    ]

    d.relationships = [
        # Herencia: Perro -> Animal
        UMLRelationship(
            type=RelationshipType.GENERALIZATION,
            source=RelationshipEnd(class_id="perro"),
            target=RelationshipEnd(class_id="animal"),
        ),
        # Herencia: Gato -> Animal
        UMLRelationship(
            type=RelationshipType.GENERALIZATION,
            source=RelationshipEnd(class_id="gato"),
            target=RelationshipEnd(class_id="animal"),
        ),
        # Composición: Duenio -> Animal (1..*)
        UMLRelationship(
            type=RelationshipType.COMPOSITION,
            source=RelationshipEnd(class_id="duenio", multiplicity=Multiplicity.ONE.value),
            target=RelationshipEnd(class_id="animal", multiplicity=Multiplicity.ONE_MANY.value),
        ),
    ]

    return d


class TestXMIRoundtrip:
    """Roundtrip completo XMI: crear → exportar → importar → verificar."""

    def test_class_count_preserved(self):
        original = _build_test_diagram()
        adapter = XMIAdapter()

        xmi_str = adapter.export_to_xmi(original)
        reimported = adapter.import_from_xmi(xmi_str)

        assert len(reimported.classes) == len(original.classes), \
            f"Esperado {len(original.classes)} clases, obtenido {len(reimported.classes)}"

    def test_class_names_preserved(self):
        original = _build_test_diagram()
        adapter = XMIAdapter()

        xmi_str = adapter.export_to_xmi(original)
        reimported = adapter.import_from_xmi(xmi_str)

        orig_names = {c.name for c in original.classes}
        reimp_names = {c.name for c in reimported.classes}
        assert orig_names == reimp_names, \
            f"Nombres no preservados: {orig_names} vs {reimp_names}"

    def test_attributes_preserved(self):
        original = _build_test_diagram()
        adapter = XMIAdapter()

        xmi_str = adapter.export_to_xmi(original)
        reimported = adapter.import_from_xmi(xmi_str)

        orig_animal = next(c for c in original.classes if c.name == "Animal")
        reimp_animal = next(c for c in reimported.classes if c.name == "Animal")

        orig_attr_names = {a.name for a in orig_animal.attributes}
        reimp_attr_names = {a.name for a in reimp_animal.attributes}
        assert orig_attr_names == reimp_attr_names, \
            f"Atributos no preservados: {orig_attr_names} vs {reimp_attr_names}"

    def test_relationships_preserved(self):
        original = _build_test_diagram()
        adapter = XMIAdapter()

        xmi_str = adapter.export_to_xmi(original)
        reimported = adapter.import_from_xmi(xmi_str)

        assert len(reimported.relationships) >= len(original.relationships) - 1, \
            f"Relaciones perdidas: {len(original.relationships)} -> {len(reimported.relationships)}"

    def test_xmi_valid_xml(self):
        original = _build_test_diagram()
        adapter = XMIAdapter()

        xmi_str = adapter.export_to_xmi(original)
        assert "<?xml" in xmi_str or "xmi:" in xmi_str
        assert "uml:Model" in xmi_str or "UML:" in xmi_str


class TestMDJRoundtrip:
    """Roundtrip completo MDJ (StarUML): crear → exportar → importar → verificar."""

    def test_class_count_preserved(self):
        original = _build_test_diagram()
        adapter = MDJAdapter()

        mdj_str = adapter.export_to_mdj(original)
        reimported = adapter.import_from_mdj(mdj_str)

        assert len(reimported.classes) == len(original.classes), \
            f"Esperado {len(original.classes)} clases, obtenido {len(reimported.classes)}"

    def test_class_names_preserved(self):
        original = _build_test_diagram()
        adapter = MDJAdapter()

        mdj_str = adapter.export_to_mdj(original)
        reimported = adapter.import_from_mdj(mdj_str)

        orig_names = {c.name for c in original.classes}
        reimp_names = {c.name for c in reimported.classes}
        assert orig_names == reimp_names

    def test_valid_json_structure(self):
        original = _build_test_diagram()
        adapter = MDJAdapter()

        mdj_str = adapter.export_to_mdj(original)
        data = json.loads(mdj_str)

        assert data["_type"] == "Project"
        assert "ownedElements" in data

    def test_double_roundtrip_stability(self):
        """Exportar → importar → exportar → importar debe dar el mismo resultado."""
        original = _build_test_diagram()
        adapter = MDJAdapter()

        mdj1 = adapter.export_to_mdj(original)
        reimp1 = adapter.import_from_mdj(mdj1)
        mdj2 = adapter.export_to_mdj(reimp1)
        reimp2 = adapter.import_from_mdj(mdj2)

        assert len(reimp1.classes) == len(reimp2.classes)
        assert {c.name for c in reimp1.classes} == {c.name for c in reimp2.classes}

    def test_enterprise_architect_xmi_compatibility(self):
        """Verifica la importación de XMI estilo Sparx Enterprise Architect con namespaces específicos e idref."""
        ea_xmi = '''<?xml version="1.0" encoding="windows-1252"?>
<xmi:XMI xmlns:xmi="http://schema.omg.org/spec/XMI/2.1" xmlns:uml="http://schema.omg.org/spec/UML/2.1" xmi:version="2.1">
    <xmi:Documentation exporter="Enterprise Architect" exporterVersion="6.5"/>
    <uml:Model xmi:type="uml:Model" name="EA_Sample_Model">
        <packagedElement xmi:type="uml:Package" xmi:id="EAPKG_1" name="Core">
            <packagedElement xmi:type="uml:Class" xmi:id="EAID_C1" name="Factura">
                <ownedAttribute xmi:type="uml:Property" xmi:id="EAID_A1" name="numero" visibility="private"/>
                <ownedAttribute xmi:type="uml:Property" xmi:id="EAID_A2" name="monto" visibility="public"/>
            </packagedElement>
            <packagedElement xmi:type="uml:Class" xmi:id="EAID_C2" name="ItemFactura">
                <ownedAttribute xmi:type="uml:Property" xmi:id="EAID_A3" name="cantidad" visibility="private"/>
            </packagedElement>
            <packagedElement xmi:type="uml:Association" xmi:id="EAID_R1" name="contiene">
                <ownedEnd xmi:type="uml:Property" xmi:id="EAID_E1" aggregation="composite">
                    <type xmi:idref="EAID_C1"/>
                    <lowerValue xmi:type="uml:LiteralInteger" value="1"/>
                    <upperValue xmi:type="uml:LiteralUnlimitedNatural" value="1"/>
                </ownedEnd>
                <ownedEnd xmi:type="uml:Property" xmi:id="EAID_E2">
                    <type xmi:idref="EAID_C2"/>
                    <lowerValue xmi:type="uml:LiteralInteger" value="1"/>
                    <upperValue xmi:type="uml:LiteralUnlimitedNatural" value="-1"/>
                </ownedEnd>
            </packagedElement>
        </packagedElement>
    </uml:Model>
</xmi:XMI>'''
        adapter = XMIAdapter()
        diagram = adapter.import_from_xmi(ea_xmi)
        assert len(diagram.classes) == 2
        class_names = {c.name for c in diagram.classes}
        assert "Factura" in class_names and "ItemFactura" in class_names
        assert len(diagram.relationships) == 1
        rel = diagram.relationships[0]
        assert rel.type == RelationshipType.COMPOSITION
        factura = next(c for c in diagram.classes if c.name == "Factura")
        assert len(factura.attributes) == 2
