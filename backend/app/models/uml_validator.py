"""
GeneradorUML — Validador UML 2.5+

Valida la conformidad del diagrama con las reglas semánticas de UML 2.5.
Documenta qué elementos están implementados y cómo se validan.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from .uml_model import (
    UMLDiagram, UMLClass, UMLRelationship, UMLAttribute, UMLOperation,
    RelationshipType, Visibility
)


class ValidationSeverity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """A single validation issue found in the diagram."""
    severity: ValidationSeverity
    message: str
    element_id: Optional[str] = None
    element_name: Optional[str] = None
    rule: str = ""

    def to_dict(self) -> dict:
        return {
            "severity": self.severity.value,
            "message": self.message,
            "elementId": self.element_id,
            "elementName": self.element_name,
            "rule": self.rule,
        }


@dataclass
class ValidationResult:
    """Result of validating a UML diagram."""
    is_valid: bool = True
    issues: list[ValidationIssue] = field(default_factory=list)

    def add_error(self, message: str, element_id: str = None,
                  element_name: str = None, rule: str = ""):
        self.is_valid = False
        self.issues.append(ValidationIssue(
            severity=ValidationSeverity.ERROR,
            message=message,
            element_id=element_id,
            element_name=element_name,
            rule=rule,
        ))

    def add_warning(self, message: str, element_id: str = None,
                    element_name: str = None, rule: str = ""):
        self.issues.append(ValidationIssue(
            severity=ValidationSeverity.WARNING,
            message=message,
            element_id=element_id,
            element_name=element_name,
            rule=rule,
        ))

    def add_info(self, message: str, element_id: str = None,
                 element_name: str = None, rule: str = ""):
        self.issues.append(ValidationIssue(
            severity=ValidationSeverity.INFO,
            message=message,
            element_id=element_id,
            element_name=element_name,
            rule=rule,
        ))

    def to_dict(self) -> dict:
        return {
            "isValid": self.is_valid,
            "issues": [i.to_dict() for i in self.issues],
            "errorCount": sum(1 for i in self.issues if i.severity == ValidationSeverity.ERROR),
            "warningCount": sum(1 for i in self.issues if i.severity == ValidationSeverity.WARNING),
            "infoCount": sum(1 for i in self.issues if i.severity == ValidationSeverity.INFO),
        }


# Valid UML primitive types and common Java/Dart types
VALID_TYPES = {
    # UML primitive types
    "String", "Integer", "Boolean", "Real", "UnlimitedNatural",
    # Java types commonly used in class diagrams
    "int", "long", "float", "double", "boolean", "char", "byte", "short",
    "Long", "Float", "Double", "Byte", "Short", "Character",
    "Date", "LocalDate", "LocalDateTime", "BigDecimal",
    "List", "Set", "Map", "Collection",
    "void", "Object",
}

VALID_MULTIPLICITIES = {"0..1", "1", "0..*", "1..*", "*"}

JAVA_RESERVED_WORDS = {
    "abstract", "assert", "boolean", "break", "byte", "case", "catch", "char",
    "class", "const", "continue", "default", "do", "double", "else", "enum",
    "extends", "final", "finally", "float", "for", "goto", "if", "implements",
    "import", "instanceof", "int", "interface", "long", "native", "new",
    "package", "private", "protected", "public", "return", "short", "static",
    "strictfp", "super", "switch", "synchronized", "this", "throw", "throws",
    "transient", "try", "void", "volatile", "while",
}


class UMLValidator:
    """
    Validates UML 2.5+ class diagrams.

    Implemented validations:
    - Class names: non-empty, unique, valid identifiers, PascalCase convention
    - Attribute names: non-empty, valid identifiers, unique within class
    - Attribute types: recognized UML/Java types or references to diagram classes
    - Operation names: non-empty, valid identifiers
    - Relationship integrity: source/target classes exist
    - Multiplicity values: valid UML multiplicity syntax
    - Generalization rules: no circular inheritance, no multiple inheritance cycles
    - Interface rules: interfaces should not have non-abstract operations
    - Composition rules: a class cannot be composed by multiple parents
    - No isolated classes warning
    - Naming conventions (warnings)
    """

    def __init__(self, diagram: UMLDiagram):
        self.diagram = diagram
        self.result = ValidationResult()
        self._class_names: set[str] = set()

    def validate(self) -> ValidationResult:
        """Run all validations and return the result."""
        self.result = ValidationResult()
        self._class_names = {c.name for c in self.diagram.classes}

        if not self.diagram.classes:
            self.result.add_warning(
                "El diagrama no contiene ninguna clase.",
                rule="diagram.empty"
            )
            return self.result

        self._validate_classes()
        self._validate_relationships()
        self._validate_inheritance_cycles()
        self._validate_composition_constraints()
        self._validate_interface_rules()
        self._validate_isolated_classes()

        return self.result

    def _validate_classes(self):
        """Validate all classes in the diagram."""
        seen_names: set[str] = set()

        for cls in self.diagram.classes:
            # Class name must not be empty
            if not cls.name or not cls.name.strip():
                self.result.add_error(
                    "Una clase tiene el nombre vacío.",
                    element_id=cls.id,
                    rule="class.name.empty"
                )
                continue

            # Class name must be unique
            if cls.name in seen_names:
                self.result.add_error(
                    f"Nombre de clase duplicado: '{cls.name}'.",
                    element_id=cls.id,
                    element_name=cls.name,
                    rule="class.name.duplicate"
                )
            seen_names.add(cls.name)

            # Class name should be a valid identifier
            if not cls.name.isidentifier():
                self.result.add_error(
                    f"El nombre de clase '{cls.name}' no es un identificador válido.",
                    element_id=cls.id,
                    element_name=cls.name,
                    rule="class.name.invalid"
                )

            # Class name should be PascalCase (warning)
            if cls.name and cls.name[0].islower():
                self.result.add_warning(
                    f"La clase '{cls.name}' no sigue la convención PascalCase.",
                    element_id=cls.id,
                    element_name=cls.name,
                    rule="class.name.convention"
                )

            # Class name should not be a Java reserved word
            if cls.name.lower() in JAVA_RESERVED_WORDS:
                self.result.add_error(
                    f"El nombre de clase '{cls.name}' es una palabra reservada de Java.",
                    element_id=cls.id,
                    element_name=cls.name,
                    rule="class.name.reserved"
                )

            # Validate attributes
            self._validate_attributes(cls)

            # Validate operations
            self._validate_operations(cls)

    def _validate_attributes(self, cls: UMLClass):
        """Validate attributes of a class."""
        seen_attrs: set[str] = set()

        for attr in cls.attributes:
            if not attr.name or not attr.name.strip():
                self.result.add_error(
                    f"La clase '{cls.name}' tiene un atributo sin nombre.",
                    element_id=attr.id,
                    element_name=cls.name,
                    rule="attribute.name.empty"
                )
                continue

            if attr.name in seen_attrs:
                self.result.add_error(
                    f"Atributo duplicado '{attr.name}' en la clase '{cls.name}'.",
                    element_id=attr.id,
                    element_name=f"{cls.name}.{attr.name}",
                    rule="attribute.name.duplicate"
                )
            seen_attrs.add(attr.name)

            if not attr.name.isidentifier():
                self.result.add_error(
                    f"El nombre de atributo '{attr.name}' en '{cls.name}' no es un identificador válido.",
                    element_id=attr.id,
                    element_name=f"{cls.name}.{attr.name}",
                    rule="attribute.name.invalid"
                )

            # Check if type is valid
            base_type = attr.type.split("<")[0].split("[")[0].strip()
            if base_type not in VALID_TYPES and base_type not in self._class_names:
                self.result.add_warning(
                    f"El tipo '{attr.type}' del atributo '{attr.name}' en '{cls.name}' no es un tipo reconocido.",
                    element_id=attr.id,
                    element_name=f"{cls.name}.{attr.name}",
                    rule="attribute.type.unknown"
                )

            # Attribute name convention (camelCase warning)
            if attr.name and attr.name[0].isupper():
                self.result.add_warning(
                    f"El atributo '{attr.name}' en '{cls.name}' no sigue la convención camelCase.",
                    element_id=attr.id,
                    element_name=f"{cls.name}.{attr.name}",
                    rule="attribute.name.convention"
                )

    def _validate_operations(self, cls: UMLClass):
        """Validate operations of a class."""
        for op in cls.operations:
            if not op.name or not op.name.strip():
                self.result.add_error(
                    f"La clase '{cls.name}' tiene una operación sin nombre.",
                    element_id=op.id,
                    element_name=cls.name,
                    rule="operation.name.empty"
                )
                continue

            if not op.name.isidentifier():
                self.result.add_error(
                    f"El nombre de operación '{op.name}' en '{cls.name}' no es un identificador válido.",
                    element_id=op.id,
                    element_name=f"{cls.name}.{op.name}",
                    rule="operation.name.invalid"
                )

            # Validate parameters
            seen_params: set[str] = set()
            for param in op.parameters:
                if not param.name or not param.name.strip():
                    self.result.add_warning(
                        f"Un parámetro de '{cls.name}.{op.name}()' no tiene nombre.",
                        element_id=param.id,
                        element_name=f"{cls.name}.{op.name}",
                        rule="parameter.name.empty"
                    )
                elif param.name in seen_params:
                    self.result.add_error(
                        f"Parámetro duplicado '{param.name}' en '{cls.name}.{op.name}()'.",
                        element_id=param.id,
                        element_name=f"{cls.name}.{op.name}",
                        rule="parameter.name.duplicate"
                    )
                else:
                    seen_params.add(param.name)

    def _validate_relationships(self):
        """Validate all relationships in the diagram."""
        class_ids = {c.id for c in self.diagram.classes}

        for rel in self.diagram.relationships:
            # Source class must exist
            if rel.source.class_id not in class_ids:
                self.result.add_error(
                    f"La relación '{rel.name or rel.id}' referencia una clase origen inexistente.",
                    element_id=rel.id,
                    rule="relationship.source.missing"
                )

            # Target class must exist
            if rel.target.class_id not in class_ids:
                self.result.add_error(
                    f"La relación '{rel.name or rel.id}' referencia una clase destino inexistente.",
                    element_id=rel.id,
                    rule="relationship.target.missing"
                )

            # Source and target should not be the same (warning for non-associations)
            if (rel.source.class_id == rel.target.class_id and
                    rel.type in (RelationshipType.GENERALIZATION, RelationshipType.REALIZATION)):
                self.result.add_error(
                    f"Una clase no puede heredar de sí misma.",
                    element_id=rel.id,
                    rule="relationship.self.inheritance"
                )

            # Validate multiplicities
            for end_name, end in [("origen", rel.source), ("destino", rel.target)]:
                if (end.multiplicity and
                        end.multiplicity not in VALID_MULTIPLICITIES):
                    self.result.add_warning(
                        f"La multiplicidad '{end.multiplicity}' en el extremo {end_name} "
                        f"de la relación '{rel.name or rel.id}' no es una multiplicidad estándar.",
                        element_id=rel.id,
                        rule="relationship.multiplicity.nonstandard"
                    )

    def _validate_inheritance_cycles(self):
        """Check for circular inheritance."""
        # Build adjacency list for generalization
        parent_map: dict[str, list[str]] = {}
        for rel in self.diagram.relationships:
            if rel.type == RelationshipType.GENERALIZATION:
                if rel.source.class_id not in parent_map:
                    parent_map[rel.source.class_id] = []
                parent_map[rel.source.class_id].append(rel.target.class_id)

        # DFS to detect cycles
        visited: set[str] = set()
        in_stack: set[str] = set()

        def has_cycle(node: str) -> bool:
            if node in in_stack:
                return True
            if node in visited:
                return False
            visited.add(node)
            in_stack.add(node)
            for parent in parent_map.get(node, []):
                if has_cycle(parent):
                    return True
            in_stack.discard(node)
            return False

        for class_id in parent_map:
            visited.clear()
            in_stack.clear()
            if has_cycle(class_id):
                cls = self.diagram.get_class(class_id)
                self.result.add_error(
                    f"Se detectó herencia circular involucrando la clase '{cls.name if cls else class_id}'.",
                    element_id=class_id,
                    element_name=cls.name if cls else None,
                    rule="inheritance.cycle"
                )
                break  # One cycle error is enough

    def _validate_composition_constraints(self):
        """A class should not be the target of multiple compositions."""
        composition_targets: dict[str, list[str]] = {}
        for rel in self.diagram.relationships:
            if rel.type == RelationshipType.COMPOSITION:
                target_id = rel.target.class_id
                source_cls = self.diagram.get_class(rel.source.class_id)
                if target_id not in composition_targets:
                    composition_targets[target_id] = []
                composition_targets[target_id].append(
                    source_cls.name if source_cls else rel.source.class_id
                )

        for target_id, sources in composition_targets.items():
            if len(sources) > 1:
                target_cls = self.diagram.get_class(target_id)
                self.result.add_error(
                    f"La clase '{target_cls.name if target_cls else target_id}' es compuesta por "
                    f"múltiples clases: {', '.join(sources)}. En UML, un objeto solo puede "
                    f"pertenecer a una composición.",
                    element_id=target_id,
                    element_name=target_cls.name if target_cls else None,
                    rule="composition.multiple.owners"
                )

    def _validate_interface_rules(self):
        """Interfaces should only have abstract operations (no implementation)."""
        for cls in self.diagram.classes:
            if cls.is_interface:
                for op in cls.operations:
                    if not op.is_abstract and not op.is_static:
                        self.result.add_warning(
                            f"La interfaz '{cls.name}' contiene la operación '{op.name}' "
                            f"que no está marcada como abstracta.",
                            element_id=op.id,
                            element_name=f"{cls.name}.{op.name}",
                            rule="interface.operation.notabstract"
                        )

                if cls.attributes:
                    self.result.add_warning(
                        f"La interfaz '{cls.name}' tiene atributos. Las interfaces "
                        f"normalmente solo declaran constantes.",
                        element_id=cls.id,
                        element_name=cls.name,
                        rule="interface.has.attributes"
                    )

    def _validate_isolated_classes(self):
        """Warn about classes with no relationships."""
        connected_ids: set[str] = set()
        for rel in self.diagram.relationships:
            connected_ids.add(rel.source.class_id)
            connected_ids.add(rel.target.class_id)

        for cls in self.diagram.classes:
            if cls.id not in connected_ids and len(self.diagram.classes) > 1:
                self.result.add_info(
                    f"La clase '{cls.name}' no tiene relaciones con otras clases.",
                    element_id=cls.id,
                    element_name=cls.name,
                    rule="class.isolated"
                )
