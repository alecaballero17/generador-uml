"""
GeneradorUML — Modelo UML Interno

Representación del diagrama de clases conforme a UML 2.5+.
Este modelo es el núcleo de la herramienta: los adaptadores de importación/exportación
convierten desde/hacia este formato, y los generadores leen este modelo para producir código.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import uuid
import json
import copy


class Visibility(Enum):
    """Visibilidad UML de atributos y operaciones."""
    PUBLIC = "+"
    PRIVATE = "-"
    PROTECTED = "#"
    PACKAGE = "~"


class RelationshipType(Enum):
    """Tipos de relación UML soportados."""
    ASSOCIATION = "association"
    AGGREGATION = "aggregation"
    COMPOSITION = "composition"
    GENERALIZATION = "generalization"
    REALIZATION = "realization"
    DEPENDENCY = "dependency"


class Multiplicity(Enum):
    """Multiplicidades UML comunes."""
    ZERO_ONE = "0..1"
    ONE = "1"
    ZERO_MANY = "0..*"
    ONE_MANY = "1..*"
    MANY = "*"

    @classmethod
    def from_string(cls, s: str) -> "Multiplicity":
        """Parse a multiplicity string, accepting common aliases."""
        mapping = {
            "0..1": cls.ZERO_ONE,
            "1": cls.ONE,
            "0..*": cls.ZERO_MANY,
            "*": cls.MANY,
            "1..*": cls.ONE_MANY,
        }
        return mapping.get(s.strip(), cls.ONE)


@dataclass
class UMLParameter:
    """Parámetro de una operación UML."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    type: str = "String"
    default_value: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "defaultValue": self.default_value,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UMLParameter":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            type=data.get("type", "String"),
            default_value=data.get("defaultValue"),
        )


@dataclass
class UMLAttribute:
    """Atributo de una clase UML."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    type: str = "String"
    visibility: Visibility = Visibility.PRIVATE
    multiplicity: Optional[str] = None
    default_value: Optional[str] = None
    is_static: bool = False
    is_final: bool = False
    is_derived: bool = False
    constraints: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "visibility": self.visibility.value if hasattr(self.visibility, "value") else str(self.visibility),
            "multiplicity": self.multiplicity,
            "defaultValue": self.default_value,
            "isStatic": self.is_static,
            "isFinal": self.is_final,
            "isDerived": self.is_derived,
            "constraints": self.constraints,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UMLAttribute":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            type=data.get("type", "String"),
            visibility=Visibility(data.get("visibility", "-")),
            multiplicity=data.get("multiplicity"),
            default_value=data.get("defaultValue"),
            is_static=data.get("isStatic", False),
            is_final=data.get("isFinal", False),
            is_derived=data.get("isDerived", False),
            constraints=data.get("constraints", []),
        )

    def to_uml_string(self) -> str:
        """Render the attribute in UML notation, e.g. '- name: String'."""
        parts = [self.visibility.value, " "]
        if self.is_static:
            parts.append("«static» ")
        if self.is_derived:
            parts.append("/")
        parts.append(self.name)
        parts.append(": ")
        parts.append(self.type)
        if self.multiplicity:
            parts.append(f" [{self.multiplicity}]")
        if self.default_value:
            parts.append(f" = {self.default_value}")
        return "".join(parts)


@dataclass
class UMLOperation:
    """Operación (método) de una clase UML."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    parameters: list[UMLParameter] = field(default_factory=list)
    return_type: str = "void"
    visibility: Visibility = Visibility.PUBLIC
    is_abstract: bool = False
    is_static: bool = False
    is_constructor: bool = False
    body_description: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "parameters": [p.to_dict() for p in self.parameters],
            "returnType": self.return_type,
            "visibility": self.visibility.value if hasattr(self.visibility, "value") else str(self.visibility),
            "isAbstract": self.is_abstract,
            "isStatic": self.is_static,
            "isConstructor": self.is_constructor,
            "bodyDescription": self.body_description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UMLOperation":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            parameters=[UMLParameter.from_dict(p) for p in data.get("parameters", [])],
            return_type=data.get("returnType", "void"),
            visibility=Visibility(data.get("visibility", "+")),
            is_abstract=data.get("isAbstract", False),
            is_static=data.get("isStatic", False),
            is_constructor=data.get("isConstructor", False),
            body_description=data.get("bodyDescription"),
        )

    def to_uml_string(self) -> str:
        """Render the operation in UML notation."""
        parts = [self.visibility.value, " "]
        if self.is_abstract:
            parts.append("«abstract» ")
        if self.is_static:
            parts.append("«static» ")
        parts.append(self.name)
        parts.append("(")
        params = []
        for p in self.parameters:
            s = f"{p.name}: {p.type}"
            if p.default_value:
                s += f" = {p.default_value}"
            params.append(s)
        parts.append(", ".join(params))
        parts.append(")")
        if self.return_type and self.return_type != "void":
            parts.append(f": {self.return_type}")
        return "".join(parts)


@dataclass
class Position:
    """Posición visual de un elemento en el canvas."""
    x: float = 0.0
    y: float = 0.0

    def to_dict(self) -> dict:
        return {"x": self.x, "y": self.y}

    @classmethod
    def from_dict(cls, data: dict) -> "Position":
        return cls(x=data.get("x", 0.0), y=data.get("y", 0.0))


@dataclass
class Size:
    """Tamaño visual de un elemento."""
    width: float = 200.0
    height: float = 150.0

    def to_dict(self) -> dict:
        return {"width": self.width, "height": self.height}

    @classmethod
    def from_dict(cls, data: dict) -> "Size":
        return cls(width=data.get("width", 200.0), height=data.get("height", 150.0))


@dataclass
class UMLClass:
    """Clase UML con atributos y operaciones."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    visibility: Visibility = Visibility.PUBLIC
    is_abstract: bool = False
    is_interface: bool = False
    stereotype: Optional[str] = None
    attributes: list[UMLAttribute] = field(default_factory=list)
    operations: list[UMLOperation] = field(default_factory=list)
    position: Position = field(default_factory=Position)
    size: Size = field(default_factory=Size)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "visibility": self.visibility.value if hasattr(self.visibility, "value") else str(self.visibility),
            "isAbstract": self.is_abstract,
            "isInterface": self.is_interface,
            "stereotype": self.stereotype,
            "attributes": [a.to_dict() for a in self.attributes],
            "operations": [o.to_dict() for o in self.operations],
            "position": self.position.to_dict(),
            "size": self.size.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UMLClass":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            visibility=Visibility(data.get("visibility", "+")),
            is_abstract=data.get("isAbstract", False),
            is_interface=data.get("isInterface", False),
            stereotype=data.get("stereotype"),
            attributes=[UMLAttribute.from_dict(a) for a in data.get("attributes", [])],
            operations=[UMLOperation.from_dict(o) for o in data.get("operations", [])],
            position=Position.from_dict(data.get("position", {})),
            size=Size.from_dict(data.get("size", {})),
        )

    def get_display_name(self) -> str:
        """Name for display, with stereotype if present."""
        if self.is_interface:
            return f"«interface»\n{self.name}"
        if self.stereotype:
            return f"«{self.stereotype}»\n{self.name}"
        return self.name


@dataclass
class RelationshipEnd:
    """Un extremo de una relación UML."""
    class_id: str = ""
    role: Optional[str] = None
    multiplicity: str = "1"
    navigable: bool = True

    def to_dict(self) -> dict:
        return {
            "classId": self.class_id,
            "role": self.role,
            "multiplicity": self.multiplicity,
            "navigable": self.navigable,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RelationshipEnd":
        return cls(
            class_id=data.get("classId", ""),
            role=data.get("role"),
            multiplicity=data.get("multiplicity", "1"),
            navigable=data.get("navigable", True),
        )


@dataclass
class UMLRelationship:
    """Relación entre dos clases UML."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: RelationshipType = RelationshipType.ASSOCIATION
    source: RelationshipEnd = field(default_factory=RelationshipEnd)
    target: RelationshipEnd = field(default_factory=RelationshipEnd)
    name: Optional[str] = None
    label: Optional[str] = None
    vertices: list[Position] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "source": self.source.to_dict(),
            "target": self.target.to_dict(),
            "name": self.name,
            "label": self.label,
            "vertices": [v.to_dict() for v in self.vertices],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UMLRelationship":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            type=RelationshipType(data.get("type", "association")),
            source=RelationshipEnd.from_dict(data.get("source", {})),
            target=RelationshipEnd.from_dict(data.get("target", {})),
            name=data.get("name"),
            label=data.get("label"),
            vertices=[Position.from_dict(v) for v in data.get("vertices", [])],
        )


@dataclass
class UMLDiagram:
    """Diagrama de clases UML completo."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Nuevo Diagrama"
    description: str = ""
    classes: list[UMLClass] = field(default_factory=list)
    relationships: list[UMLRelationship] = field(default_factory=list)
    version: str = "1.0.0"
    uml_version: str = "2.5.1"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "classes": [c.to_dict() for c in self.classes],
            "relationships": [r.to_dict() for r in self.relationships],
            "version": self.version,
            "umlVersion": self.uml_version,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UMLDiagram":
        if "diagram" in data and isinstance(data["diagram"], dict):
            data = data["diagram"]
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", "Nuevo Diagrama"),
            description=data.get("description", ""),
            classes=[UMLClass.from_dict(c) for c in data.get("classes", [])],
            relationships=[UMLRelationship.from_dict(r) for r in data.get("relationships", [])],
            version=data.get("version", "1.0.0"),
            uml_version=data.get("umlVersion", "2.5.1"),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
        )

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "UMLDiagram":
        return cls.from_dict(json.loads(json_str))

    def add_class(self, uml_class: UMLClass) -> UMLClass:
        """Add a class to the diagram."""
        self.classes.append(uml_class)
        return uml_class

    def remove_class(self, class_id: str) -> bool:
        """Remove a class and its associated relationships."""
        original_len = len(self.classes)
        self.classes = [c for c in self.classes if c.id != class_id]
        # Remove relationships that reference this class
        self.relationships = [
            r for r in self.relationships
            if r.source.class_id != class_id and r.target.class_id != class_id
        ]
        return len(self.classes) < original_len

    def get_class(self, class_id: str) -> Optional[UMLClass]:
        """Find a class by ID."""
        for c in self.classes:
            if c.id == class_id:
                return c
        return None

    def get_class_by_name(self, name: str) -> Optional[UMLClass]:
        """Find a class by name (case-insensitive)."""
        for c in self.classes:
            if c.name.lower() == name.lower():
                return c
        return None

    def add_relationship(self, rel: UMLRelationship) -> UMLRelationship:
        """Add a relationship to the diagram."""
        self.relationships.append(rel)
        return rel

    def remove_relationship(self, rel_id: str) -> bool:
        """Remove a relationship by ID."""
        original_len = len(self.relationships)
        self.relationships = [r for r in self.relationships if r.id != rel_id]
        return len(self.relationships) < original_len

    def get_relationships_for_class(self, class_id: str) -> list[UMLRelationship]:
        """Get all relationships involving a class."""
        return [
            r for r in self.relationships
            if r.source.class_id == class_id or r.target.class_id == class_id
        ]

    def get_parent_classes(self, class_id: str) -> list[UMLClass]:
        """Get parent classes (via generalization)."""
        parents = []
        for r in self.relationships:
            if (r.type == RelationshipType.GENERALIZATION and
                    r.source.class_id == class_id):
                parent = self.get_class(r.target.class_id)
                if parent:
                    parents.append(parent)
        return parents

    def get_child_classes(self, class_id: str) -> list[UMLClass]:
        """Get child classes (via generalization)."""
        children = []
        for r in self.relationships:
            if (r.type == RelationshipType.GENERALIZATION and
                    r.target.class_id == class_id):
                child = self.get_class(r.source.class_id)
                if child:
                    children.append(child)
        return children

    def deep_copy(self) -> "UMLDiagram":
        """Create a deep copy of this diagram."""
        return copy.deepcopy(self)
