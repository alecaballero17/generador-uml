"""
GeneradorUML — Adaptador MDJ (StarUML nativo)

Importa y exporta diagramas UML en formato .mdj (JSON nativo de StarUML).
Preserva posiciones visuales para roundtrip.
"""

from __future__ import annotations
import json
import uuid
from typing import Optional

from ..models.uml_model import (
    UMLDiagram, UMLClass, UMLAttribute, UMLOperation, UMLParameter,
    UMLRelationship, RelationshipEnd, Position, Size,
    Visibility, RelationshipType
)


MDJ_VISIBILITY_MAP = {
    "public": "+", "private": "-", "protected": "#", "package": "~",
}
MDJ_VISIBILITY_REVERSE = {v: k for k, v in MDJ_VISIBILITY_MAP.items()}

MDJ_REL_TYPE_MAP = {
    "UMLAssociation": RelationshipType.ASSOCIATION,
    "UMLDependency": RelationshipType.DEPENDENCY,
    "UMLGeneralization": RelationshipType.GENERALIZATION,
    "UMLInterfaceRealization": RelationshipType.REALIZATION,
}


class MDJAdapter:
    """Adapter for StarUML's native .mdj format (JSON)."""

    def __init__(self):
        self.warnings: list[str] = []
        self.unsupported_elements: list[str] = []

    # ─── Import (.mdj → UMLDiagram) ───────────────────────────────────

    def import_from_mdj(self, mdj_content: str) -> UMLDiagram:
        """Import a diagram from a StarUML .mdj JSON string."""
        self.warnings = []
        self.unsupported_elements = []

        data = json.loads(mdj_content)
        diagram = UMLDiagram()

        # StarUML uses a nested structure: Project > Model > elements
        diagram.name = data.get("name", "StarUML Import")

        # Find all classes and relationships recursively
        mdj_id_to_class: dict[str, UMLClass] = {}
        self._pending_relationships = []
        self._pending_views = []
        self._find_elements(data, diagram, mdj_id_to_class)
        parsers = {"UMLAssociation": self._parse_association,
                   "UMLGeneralization": self._parse_generalization,
                   "UMLInterfaceRealization": self._parse_realization,
                   "UMLDependency": self._parse_dependency}
        for node in self._pending_relationships:
            relationship = parsers[node["_type"]](node, mdj_id_to_class)
            if relationship:
                diagram.add_relationship(relationship)
        for node in self._pending_views:
            reference = node.get("model", {})
            cls = mdj_id_to_class.get(reference.get("$ref")) if isinstance(reference, dict) else None
            if cls:
                cls.position = Position(x=node.get("left", 0), y=node.get("top", 0))
                cls.size = Size(width=node.get("width", 200), height=node.get("height", 120))

        return diagram

    def _find_elements(self, node: dict, diagram: UMLDiagram,
                       id_map: dict[str, UMLClass], depth: int = 0):
        """Recursively find UML elements in the MDJ tree."""
        if not isinstance(node, dict):
            return

        node_type = node.get("_type", "")

        if node_type == "UMLClass":
            cls = self._parse_class(node)
            id_map[node.get("_id", "")] = cls
            diagram.add_class(cls)

        elif node_type == "UMLInterface":
            cls = self._parse_class(node)
            cls.is_interface = True
            id_map[node.get("_id", "")] = cls
            diagram.add_class(cls)

        elif node_type in MDJ_REL_TYPE_MAP:
            self._pending_relationships.append(node)
        elif node_type in ("UMLClassView", "UMLInterfaceView"):
            self._pending_views.append(node)

        elif node_type not in ("Project", "UMLModel", "UMLPackage",
                                "UMLClassDiagram", "UMLClassView",
                                "UMLAssociationView", "UMLGeneralizationView",
                                "UMLInterfaceRealizationView", "UMLDependencyView",
                                "ERDDiagram", ""):
            if node_type and depth < 5:
                self.unsupported_elements.append(node_type)

        # Recurse into children
        for key in ("ownedElements", "ownedViews", "attributes",
                     "operations", "ownedParameters"):
            children = node.get(key, [])
            if isinstance(children, list):
                for child in children:
                    self._find_elements(child, diagram, id_map, depth + 1)

    def _parse_class(self, node: dict) -> UMLClass:
        """Parse a UMLClass from MDJ."""
        cls = UMLClass()
        cls.name = node.get("name", "UnknownClass")
        cls.visibility = MDJ_VISIBILITY_MAP.get(
            node.get("visibility", "public"), "+"
        )
        cls.is_abstract = node.get("isAbstract", False)

        # Attributes
        for attr_node in node.get("attributes", []):
            if attr_node.get("_type") == "UMLAttribute":
                attr = UMLAttribute()
                attr.name = attr_node.get("name", "")
                attr.visibility = MDJ_VISIBILITY_MAP.get(
                    attr_node.get("visibility", "private"), "-"
                )
                attr.is_static = attr_node.get("isStatic", False)
                attr.multiplicity = attr_node.get("multiplicity")
                attr.default_value = attr_node.get("defaultValue")
                attr.is_derived = attr_node.get("isDerived", False)

                # Type reference
                type_ref = attr_node.get("type")
                if isinstance(type_ref, str):
                    attr.type = type_ref
                elif isinstance(type_ref, dict):
                    attr.type = type_ref.get("name", "String")
                else:
                    attr.type = "String"

                if attr.name:
                    cls.attributes.append(attr)

        # Operations
        for op_node in node.get("operations", []):
            if op_node.get("_type") == "UMLOperation":
                op = UMLOperation()
                op.name = op_node.get("name", "")
                op.visibility = MDJ_VISIBILITY_MAP.get(
                    op_node.get("visibility", "public"), "+"
                )
                op.is_abstract = op_node.get("isAbstract", False)
                op.is_static = op_node.get("isStatic", False)

                # Return type
                ret_type = op_node.get("returnType")
                if isinstance(ret_type, str):
                    op.return_type = ret_type
                elif isinstance(ret_type, dict):
                    op.return_type = ret_type.get("name", "void")
                else:
                    op.return_type = "void"

                # Parameters
                for param_node in op_node.get("parameters", []):
                    if param_node.get("_type") == "UMLParameter":
                        param = UMLParameter()
                        param.name = param_node.get("name", "")
                        param.default_value = param_node.get("defaultValue")
                        p_type = param_node.get("type")
                        if isinstance(p_type, str):
                            param.type = p_type
                        elif isinstance(p_type, dict):
                            param.type = p_type.get("name", "String")
                        op.parameters.append(param)

                if op.name:
                    cls.operations.append(op)

        return cls

    def _parse_association(self, node: dict,
                           id_map: dict[str, UMLClass]) -> Optional[UMLRelationship]:
        """Parse a UMLAssociation from MDJ."""
        end1 = node.get("end1", {})
        end2 = node.get("end2", {})

        ref1 = end1.get("reference", {})
        ref2 = end2.get("reference", {})

        # References can be inline or just an ID
        ref1_id = ref1.get("$ref", ref1) if isinstance(ref1, dict) else ref1
        ref2_id = ref2.get("$ref", ref2) if isinstance(ref2, dict) else ref2

        cls1 = id_map.get(ref1_id)
        cls2 = id_map.get(ref2_id)

        if not cls1 or not cls2:
            self.warnings.append(f"Asociación '{node.get('name', '')}' referencia clases no encontradas.")
            return None

        # Determine type based on aggregation
        agg1 = end1.get("aggregation", "none")
        agg2 = end2.get("aggregation", "none")

        rel_type = RelationshipType.ASSOCIATION
        if agg1 == "shared" or agg2 == "shared":
            rel_type = RelationshipType.AGGREGATION
        elif agg1 == "composite" or agg2 == "composite":
            rel_type = RelationshipType.COMPOSITION

        rel = UMLRelationship()
        rel.type = rel_type
        rel.name = node.get("name")
        rel.source = RelationshipEnd(
            class_id=cls1.id,
            role=end1.get("name"),
            multiplicity=end1.get("multiplicity", "1"),
        )
        rel.target = RelationshipEnd(
            class_id=cls2.id,
            role=end2.get("name"),
            multiplicity=end2.get("multiplicity", "0..*"),
        )
        return rel

    def _parse_generalization(self, node: dict,
                               id_map: dict[str, UMLClass]) -> Optional[UMLRelationship]:
        """Parse a UMLGeneralization from MDJ."""
        source_ref = node.get("source", {})
        target_ref = node.get("target", {})

        source_id = source_ref.get("$ref", source_ref) if isinstance(source_ref, dict) else source_ref
        target_id = target_ref.get("$ref", target_ref) if isinstance(target_ref, dict) else target_ref

        source_cls = id_map.get(source_id)
        target_cls = id_map.get(target_id)

        if not source_cls or not target_cls:
            self.warnings.append("Generalización referencia clases no encontradas.")
            return None

        rel = UMLRelationship()
        rel.type = RelationshipType.GENERALIZATION
        rel.source = RelationshipEnd(class_id=source_cls.id)
        rel.target = RelationshipEnd(class_id=target_cls.id)
        return rel

    def _parse_realization(self, node: dict,
                            id_map: dict[str, UMLClass]) -> Optional[UMLRelationship]:
        """Parse a UMLInterfaceRealization from MDJ."""
        source_ref = node.get("source", {})
        target_ref = node.get("target", {})

        source_id = source_ref.get("$ref", source_ref) if isinstance(source_ref, dict) else source_ref
        target_id = target_ref.get("$ref", target_ref) if isinstance(target_ref, dict) else target_ref

        source_cls = id_map.get(source_id)
        target_cls = id_map.get(target_id)

        if not source_cls or not target_cls:
            return None

        rel = UMLRelationship()
        rel.type = RelationshipType.REALIZATION
        rel.source = RelationshipEnd(class_id=source_cls.id)
        rel.target = RelationshipEnd(class_id=target_cls.id)
        return rel

    def _parse_dependency(self, node: dict,
                           id_map: dict[str, UMLClass]) -> Optional[UMLRelationship]:
        """Parse a UMLDependency from MDJ."""
        source_ref = node.get("source", {})
        target_ref = node.get("target", {})

        source_id = source_ref.get("$ref", source_ref) if isinstance(source_ref, dict) else source_ref
        target_id = target_ref.get("$ref", target_ref) if isinstance(target_ref, dict) else target_ref

        source_cls = id_map.get(source_id)
        target_cls = id_map.get(target_id)

        if not source_cls or not target_cls:
            return None

        rel = UMLRelationship()
        rel.type = RelationshipType.DEPENDENCY
        rel.source = RelationshipEnd(class_id=source_cls.id)
        rel.target = RelationshipEnd(class_id=target_cls.id)
        return rel

    # ─── Export (UMLDiagram → .mdj) ───────────────────────────────────

    def export_to_mdj(self, diagram: UMLDiagram) -> str:
        """Export a diagram to StarUML .mdj format."""
        self.warnings = []

        project = {
            "_type": "Project",
            "_id": f"proj_{diagram.id}",
            "name": diagram.name,
            "ownedElements": []
        }

        model = {
            "_type": "UMLModel",
            "_id": f"model_{diagram.id}",
            "name": "Model",
            "_parent": {"$ref": project["_id"]},
            "ownedElements": []
        }
        project["ownedElements"].append(model)

        # Export classes
        class_mdj_ids: dict[str, str] = {}
        for cls in diagram.classes:
            mdj_id = f"cls_{cls.id}"
            class_mdj_ids[cls.id] = mdj_id
            cls_node = self._export_class_mdj(cls, mdj_id, model["_id"])
            model["ownedElements"].append(cls_node)

        # Export relationships
        for rel in diagram.relationships:
            rel_node = self._export_rel_mdj(rel, class_mdj_ids, model["_id"])
            if rel_node:
                model["ownedElements"].append(rel_node)

        # Export visual diagram and views for StarUML native rendering
        diag_id = f"diagram_{diagram.id}"
        class_diagram = {
            "_type": "UMLClassDiagram",
            "_id": diag_id,
            "_parent": {"$ref": model["_id"]},
            "name": diagram.name or "Main",
            "ownedViews": []
        }

        class_views: dict[str, str] = {}
        for cls in diagram.classes:
            mdj_id = class_mdj_ids[cls.id]
            view_type = "UMLInterfaceView" if cls.is_interface else "UMLClassView"
            view_id = f"view_{cls.id}"
            class_views[cls.id] = view_id
            view_node = {
                "_type": view_type,
                "_id": view_id,
                "_parent": {"$ref": diag_id},
                "model": {"$ref": mdj_id},
                "left": int(cls.position.x) if cls.position else 100,
                "top": int(cls.position.y) if cls.position else 100,
                "width": int(cls.size.width) if cls.size else 200,
                "height": int(cls.size.height) if cls.size else 120,
            }
            class_diagram["ownedViews"].append(view_node)

        # Connector views for relationships
        rel_view_types = {
            RelationshipType.ASSOCIATION: "UMLAssociationView",
            RelationshipType.AGGREGATION: "UMLAssociationView",
            RelationshipType.COMPOSITION: "UMLAssociationView",
            RelationshipType.GENERALIZATION: "UMLGeneralizationView",
            RelationshipType.REALIZATION: "UMLInterfaceRealizationView",
            RelationshipType.DEPENDENCY: "UMLDependencyView",
        }
        for rel in diagram.relationships:
            tail_view = class_views.get(rel.source.class_id)
            head_view = class_views.get(rel.target.class_id)
            if tail_view and head_view:
                vtype = rel_view_types.get(rel.type, "UMLAssociationView")
                rel_view = {
                    "_type": vtype,
                    "_id": f"view_rel_{rel.id}",
                    "_parent": {"$ref": diag_id},
                    "model": {"$ref": f"rel_{rel.id}"},
                    "tail": {"$ref": tail_view},
                    "head": {"$ref": head_view},
                }
                class_diagram["ownedViews"].append(rel_view)

        model["ownedElements"].append(class_diagram)

        return json.dumps(project, indent=2, ensure_ascii=False)

    def _export_class_mdj(self, cls: UMLClass, mdj_id: str, parent_id: str) -> dict:
        """Export a class to MDJ format."""
        node = {
            "_type": "UMLInterface" if cls.is_interface else "UMLClass",
            "_id": mdj_id,
            "name": cls.name,
            "visibility": MDJ_VISIBILITY_REVERSE.get(cls.visibility, "public"),
            "isAbstract": cls.is_abstract,
            "_parent": {"$ref": parent_id},
            "attributes": [],
            "operations": [],
        }

        for attr in cls.attributes:
            attr_dict = {
                "_type": "UMLAttribute",
                "_id": f"attr_{attr.id}",
                "name": attr.name,
                "visibility": MDJ_VISIBILITY_REVERSE.get(attr.visibility, "private"),
                "type": attr.type,
                "isStatic": attr.is_static,
                "_parent": {"$ref": mdj_id},
            }
            if attr.multiplicity:
                attr_dict["multiplicity"] = attr.multiplicity
            if attr.default_value is not None:
                attr_dict["defaultValue"] = attr.default_value
            if attr.is_derived:
                attr_dict["isDerived"] = attr.is_derived
            node["attributes"].append(attr_dict)

        for op in cls.operations:
            op_node = {
                "_type": "UMLOperation",
                "_id": f"op_{op.id}",
                "name": op.name,
                "visibility": MDJ_VISIBILITY_REVERSE.get(op.visibility, "public"),
                "returnType": op.return_type,
                "isAbstract": op.is_abstract,
                "isStatic": op.is_static,
                "_parent": {"$ref": mdj_id},
                "parameters": [],
            }
            for param in op.parameters:
                p_dict = {
                    "_type": "UMLParameter",
                    "_id": f"param_{param.id}",
                    "name": param.name,
                    "type": param.type,
                    "_parent": {"$ref": op_node["_id"]},
                }
                if param.default_value is not None:
                    p_dict["defaultValue"] = param.default_value
                op_node["parameters"].append(p_dict)
            node["operations"].append(op_node)

        return node

    def _export_rel_mdj(self, rel: UMLRelationship,
                         class_ids: dict[str, str], parent_id: str) -> Optional[dict]:
        """Export a relationship to MDJ format."""
        source_mdj = class_ids.get(rel.source.class_id)
        target_mdj = class_ids.get(rel.target.class_id)
        if not source_mdj or not target_mdj:
            return None

        if rel.type in (RelationshipType.ASSOCIATION, RelationshipType.AGGREGATION, RelationshipType.COMPOSITION):
            agg = "none"
            if rel.type == RelationshipType.AGGREGATION:
                agg = "shared"
            elif rel.type == RelationshipType.COMPOSITION:
                agg = "composite"

            return {
                "_type": "UMLAssociation",
                "_id": f"rel_{rel.id}",
                "name": rel.name or "",
                "_parent": {"$ref": parent_id},
                "end1": {
                    "_type": "UMLAssociationEnd",
                    "reference": {"$ref": source_mdj},
                    "name": rel.source.role or "",
                    "multiplicity": str(rel.source.multiplicity) if hasattr(rel.source.multiplicity, 'value') else rel.source.multiplicity,
                    "aggregation": agg,
                },
                "end2": {
                    "_type": "UMLAssociationEnd",
                    "reference": {"$ref": target_mdj},
                    "name": rel.target.role or "",
                    "multiplicity": str(rel.target.multiplicity) if hasattr(rel.target.multiplicity, 'value') else rel.target.multiplicity,
                },
            }

        elif rel.type == RelationshipType.GENERALIZATION:
            return {
                "_type": "UMLGeneralization",
                "_id": f"rel_{rel.id}",
                "_parent": {"$ref": parent_id},
                "source": {"$ref": source_mdj},
                "target": {"$ref": target_mdj},
            }

        elif rel.type == RelationshipType.REALIZATION:
            return {
                "_type": "UMLInterfaceRealization",
                "_id": f"rel_{rel.id}",
                "_parent": {"$ref": parent_id},
                "source": {"$ref": source_mdj},
                "target": {"$ref": target_mdj},
            }

        elif rel.type == RelationshipType.DEPENDENCY:
            return {
                "_type": "UMLDependency",
                "_id": f"rel_{rel.id}",
                "_parent": {"$ref": parent_id},
                "source": {"$ref": source_mdj},
                "target": {"$ref": target_mdj},
            }

        return None
