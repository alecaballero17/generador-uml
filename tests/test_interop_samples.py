import json
from pathlib import Path
from app.services.mdj_adapter import MDJAdapter
from app.services.xmi_adapter import XMIAdapter
from app.models.uml_validator import UMLValidator

DIAGRAMS_DIR = Path(__file__).resolve().parent.parent / "docs" / "diagramas"

def test_import_and_validate_veterinaria_mdj():
    mdj_file = DIAGRAMS_DIR / "diagrama_veterinaria.mdj"
    assert mdj_file.exists(), f"Archivo {mdj_file} no encontrado"
    
    content = mdj_file.read_text(encoding="utf-8")
    adapter = MDJAdapter()
    diagram = adapter.import_from_mdj(content)
    
    # Debe haber clases y relaciones
    assert len(diagram.classes) > 0, "No se importaron clases de veterinaria.mdj"
    assert len(diagram.relationships) > 0, "No se importaron relaciones de veterinaria.mdj"
    
    # Validar el diagrama
    validator = UMLValidator(diagram)
    result = validator.validate()
    # No debe tener errores bloqueantes
    errors = [i for i in result.issues if i.severity.value == "error"]
    assert len(errors) == 0, f"Errores de validación en veterinaria.mdj: {errors}"
    
    # Re-exportar a MDJ
    exported = json.loads(adapter.export_to_mdj(diagram))
    assert "_type" in exported
    assert exported["_type"] == "Project"

def test_import_and_validate_veterinaria_xmi():
    xmi_file = DIAGRAMS_DIR / "diagrama_veterinaria.xmi"
    assert xmi_file.exists(), f"Archivo {xmi_file} no encontrado"
    
    content = xmi_file.read_text(encoding="utf-8")
    adapter = XMIAdapter()
    diagram = adapter.import_from_xmi(content)
    
    assert len(diagram.classes) > 0, "No se importaron clases de veterinaria.xmi"
    assert len(diagram.relationships) > 0, "No se importaron relaciones de veterinaria.xmi"
    
    # Validar que clases contengan atributos
    total_attrs = sum(len(c.attributes) for c in diagram.classes)
    assert total_attrs > 0, "Las clases importadas no tienen atributos"
    
    # Re-exportar a XMI
    exported_xml = adapter.export_to_xmi(diagram)
    assert "xmi:XMI" in exported_xml or "uml:Model" in exported_xml


def test_import_and_validate_software_mdj():
    mdj_file = DIAGRAMS_DIR / "diagrama_generador_uml_software.mdj"
    assert mdj_file.exists(), f"Archivo {mdj_file} no encontrado"

    content = mdj_file.read_text(encoding="utf-8")
    adapter = MDJAdapter()
    diagram = adapter.import_from_mdj(content)

    assert len(diagram.classes) >= 5, "Debe importar las clases del diagrama de software"
    assert len(diagram.relationships) >= 3, "Debe importar las relaciones del diagrama de software"

    validator = UMLValidator(diagram)
    result = validator.validate()
    errors = [i for i in result.issues if i.severity.value == "error"]
    assert len(errors) == 0, f"Errores de validación en software.mdj: {errors}"

    exported = json.loads(adapter.export_to_mdj(diagram))
    assert exported.get("_type") == "Project"


def test_import_and_validate_software_xmi():
    xmi_file = DIAGRAMS_DIR / "diagrama_generador_uml_software.xmi"
    assert xmi_file.exists(), f"Archivo {xmi_file} no encontrado"

    content = xmi_file.read_text(encoding="utf-8")
    adapter = XMIAdapter()
    diagram = adapter.import_from_xmi(content)

    assert len(diagram.classes) >= 5, "Debe importar las clases del diagrama de software XMI"
    assert len(diagram.relationships) >= 3, "Debe importar las relaciones del diagrama de software XMI"

    total_attrs = sum(len(c.attributes) for c in diagram.classes)
    assert total_attrs > 0, "Las clases importadas deben tener atributos"

    exported_xml = adapter.export_to_xmi(diagram)
    assert "xmi:XMI" in exported_xml or "uml:Model" in exported_xml

