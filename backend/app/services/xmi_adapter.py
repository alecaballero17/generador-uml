"""
GeneradorUML — Adaptador XMI 2.1

Importa y exporta diagramas UML en formato XMI 2.1 (ISO/IEC 19509),
compatible con Enterprise Architect (Sparx Systems) y StarUML.

Este adaptador mantiene un modelo interno común y convierte bidireccionalmente.
Informa de cualquier elemento no soportado o pérdida de información.
"""

from __future__ import annotations
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element, SubElement
from typing import Optional
import uuid
import re

from ..models.uml_model import (
    UMLDiagram, UMLClass, UMLAttribute, UMLOperation, UMLParameter,
    UMLRelationship, RelationshipEnd, Position, Size,
    Visibility, RelationshipType
)

# XMI / UML Namespaces
XMI_NS = "http://www.omg.org/spec/XMI/20131001"
UML_NS = "http://www.omg.org/spec/UML/20131001"

VISIBILITY_MAP = {
    "public": Visibility.PUBLIC,
    "private": Visibility.PRIVATE,
    "protected": Visibility.PROTECTED,
    "package": Visibility.PACKAGE,
}
VISIBILITY_REVERSE = {
    Visibility.PUBLIC: "public",
    Visibility.PRIVATE: "private",
    Visibility.PROTECTED: "protected",
    Visibility.PACKAGE: "package",
    "+": "public",
    "-": "private",
    "#": "protected",
    "~": "package",
}

REL_TYPE_MAP = {
    "association": "uml:Association",
    "aggregation": "uml:Association",
    "composition": "uml:Association",
    "generalization": "uml:Generalization",
    "realization": "uml:Realization",
    "dependency": "uml:Dependency",
}


class XMIAdapter:
    """Bidirectional XMI 2.1 adapter for UML class diagrams."""

    def __init__(self):
        self.warnings: list[str] = []
        self.unsupported_elements: list[str] = []

    @staticmethod
    def _get_xmi_attr(el: Element, name: str) -> str:
        """Obtiene un atributo XML/XMI soportando diferentes prefijos de namespace o sin namespace."""
        target = name.lower()
        for k, v in el.attrib.items():
            local = k.split("}")[-1].lower() if "}" in k else k.lower()
            if local == target or local == f"xmi:{target}":
                return v
        return el.get(name, "")

    # ─── Export (UMLDiagram → XMI) ─────────────────────────────────────

    def export_to_xmi(self, diagram: UMLDiagram) -> str:
        """Export a UML diagram to XMI 2.1 XML string."""
        self.warnings = []

        # Root element
        root = Element("xmi:XMI")
        root.set("xmlns:xmi", XMI_NS)
        root.set("xmlns:uml", UML_NS)
        root.set("xmi:version", "2.1")

        # Documentation
        doc = SubElement(root, "xmi:Documentation")
        doc.set("exporter", "GeneradorUML")
        doc.set("exporterVersion", "1.0")

        # Model
        model = SubElement(root, "uml:Model")
        model.set("xmi:type", "uml:Model")
        model.set("xmi:id", f"model_{diagram.id}")
        model.set("name", diagram.name)

        # Classes
        class_id_map: dict[str, str] = {}
        for cls in diagram.classes:
            xmi_id = f"class_{cls.id}"
            class_id_map[cls.id] = xmi_id
            class_el = self._export_class(model, cls, xmi_id)

        # Relationships
        for rel in diagram.relationships:
            self._export_relationship(model, rel, class_id_map)

        # Enterprise Architect visual diagram extension
        ext = SubElement(root, "xmi:Extension")
        ext.set("extender", "Enterprise Architect")
        ext.set("extenderID", "6.5")
        diagrams_el = SubElement(ext, "diagrams")
        diag_el = SubElement(diagrams_el, "diagram")
        diag_el.set("xmi:id", f"ea_diag_{diagram.id}")
        diag_model = SubElement(diag_el, "model")
        diag_model.set("package", f"model_{diagram.id}")
        diag_model.set("name", diagram.name)
        diag_props = SubElement(diag_el, "properties")
        diag_props.set("name", diagram.name)
        diag_props.set("type", "Logical")

        diag_elements = SubElement(diag_el, "elements")
        for cls in diagram.classes:
            xmi_id = class_id_map.get(cls.id)
            if not xmi_id:
                continue
            el_node = SubElement(diag_elements, "element")
            el_node.set("subject", xmi_id)
            x = int(cls.position.x) if cls.position else 100
            y = int(cls.position.y) if cls.position else 100
            w = int(cls.size.width) if cls.size else 200
            h = int(cls.size.height) if cls.size else 120
            el_node.set("geometry", f"Left={x};Top={y};Right={x+w};Bottom={y+h};")

        diag_connectors = SubElement(diag_el, "connectors")
        for rel in diagram.relationships:
            conn_node = SubElement(diag_connectors, "connector")
            conn_node.set("subject", f"rel_{rel.id}")
            conn_node.set("style", "Mode=3;EO=1;")

        # Serialize
        ET.indent(root, space="  ")
        return ET.tostring(root, encoding="unicode", xml_declaration=True)

    def _export_class(self, parent: Element, cls: UMLClass, xmi_id: str) -> Element:
        """Export a single class to XMI."""
        el = SubElement(parent, "packagedElement")
        el.set("xmi:type", "uml:Class" if not cls.is_interface else "uml:Interface")
        el.set("xmi:id", xmi_id)
        el.set("name", cls.name)
        el.set("visibility", VISIBILITY_REVERSE.get(cls.visibility, "public"))
        if cls.is_abstract:
            el.set("isAbstract", "true")

        # Attributes
        for attr in cls.attributes:
            attr_el = SubElement(el, "ownedAttribute")
            attr_el.set("xmi:type", "uml:Property")
            attr_el.set("xmi:id", f"attr_{attr.id}")
            attr_el.set("name", attr.name)
            attr_el.set("visibility", VISIBILITY_REVERSE.get(attr.visibility, "private"))
            if attr.is_static:
                attr_el.set("isStatic", "true")
            if attr.is_final:
                attr_el.set("isReadOnly", "true")
            if attr.is_derived:
                attr_el.set("isDerived", "true")
            if attr.multiplicity:
                self._add_multiplicity(attr_el, attr.multiplicity)
            if attr.default_value is not None:
                default = SubElement(attr_el, "defaultValue")
                default.set("xmi:type", "uml:LiteralString")
                default.set("value", str(attr.default_value))

            # Type
            type_el = SubElement(attr_el, "type")
            type_el.set("xmi:type", "uml:PrimitiveType")
            type_el.set("href", f"http://www.omg.org/spec/UML/20131001/PrimitiveTypes.xmi#{attr.type}")

        # Operations
        for op in cls.operations:
            op_el = SubElement(el, "ownedOperation")
            op_el.set("xmi:type", "uml:Operation")
            op_el.set("xmi:id", f"op_{op.id}")
            op_el.set("name", op.name)
            op_el.set("visibility", VISIBILITY_REVERSE.get(op.visibility, "public"))
            if op.is_abstract:
                op_el.set("isAbstract", "true")
            if op.is_static:
                op_el.set("isStatic", "true")

            # Return type
            if op.return_type and op.return_type != "void":
                ret_el = SubElement(op_el, "ownedParameter")
                ret_el.set("xmi:type", "uml:Parameter")
                ret_el.set("name", "return")
                ret_el.set("direction", "return")
                ret_type = SubElement(ret_el, "type")
                ret_type.set("xmi:type", "uml:PrimitiveType")
                ret_type.set("href", f"http://www.omg.org/spec/UML/20131001/PrimitiveTypes.xmi#{op.return_type}")

            # Parameters
            for param in op.parameters:
                param_el = SubElement(op_el, "ownedParameter")
                param_el.set("xmi:type", "uml:Parameter")
                param_el.set("xmi:id", f"param_{param.id}")
                param_el.set("name", param.name)
                param_el.set("direction", "in")
                p_type = SubElement(param_el, "type")
                p_type.set("xmi:type", "uml:PrimitiveType")
                p_type.set("href", f"http://www.omg.org/spec/UML/20131001/PrimitiveTypes.xmi#{param.type}")

        return el

    def _export_relationship(self, parent: Element, rel: UMLRelationship,
                             class_id_map: dict[str, str]) -> Optional[Element]:
        """Export a relationship to XMI."""
        source_xmi = class_id_map.get(rel.source.class_id)
        target_xmi = class_id_map.get(rel.target.class_id)
        if not source_xmi or not target_xmi:
            self.warnings.append(f"Relación '{rel.id}' referencia clases inexistentes, omitida.")
            return None

        if rel.type == RelationshipType.GENERALIZATION:
            child = next((el for el in parent if el.get("xmi:id") == source_xmi), None)
            if child is None:
                self.warnings.append(f"No se encontró la clase hija de {rel.id}.")
                return None
            generalization = SubElement(child, "generalization")
            generalization.set("xmi:type", "uml:Generalization")
            generalization.set("xmi:id", f"rel_{rel.id}")
            generalization.set("general", target_xmi)
            return generalization

        el = SubElement(parent, "packagedElement")

        if rel.type in (RelationshipType.ASSOCIATION, RelationshipType.AGGREGATION, RelationshipType.COMPOSITION):
            el.set("xmi:type", "uml:Association")
            el.set("xmi:id", f"rel_{rel.id}")
            if rel.name:
                el.set("name", rel.name)

            # Source end
            source_end = SubElement(el, "ownedEnd")
            source_end.set("xmi:type", "uml:Property")
            source_end.set("xmi:id", f"end_s_{rel.id}")
            source_end.set("type", source_xmi)
            if rel.source.role:
                source_end.set("name", rel.source.role)

            # Aggregation kind
            if rel.type == RelationshipType.AGGREGATION:
                source_end.set("aggregation", "shared")
            elif rel.type == RelationshipType.COMPOSITION:
                source_end.set("aggregation", "composite")

            # Source multiplicity
            if rel.source.multiplicity:
                self._add_multiplicity(source_end, rel.source.multiplicity)

            # Target end
            target_end = SubElement(el, "ownedEnd")
            target_end.set("xmi:type", "uml:Property")
            target_end.set("xmi:id", f"end_t_{rel.id}")
            target_end.set("type", target_xmi)
            if rel.target.role:
                target_end.set("name", rel.target.role)
            if rel.target.multiplicity:
                self._add_multiplicity(target_end, rel.target.multiplicity)

        elif rel.type == RelationshipType.REALIZATION:
            el.set("xmi:type", "uml:Realization")
            el.set("xmi:id", f"rel_{rel.id}")
            el.set("client", source_xmi)
            el.set("supplier", target_xmi)

        elif rel.type == RelationshipType.DEPENDENCY:
            el.set("xmi:type", "uml:Dependency")
            el.set("xmi:id", f"rel_{rel.id}")
            el.set("client", source_xmi)
            el.set("supplier", target_xmi)

        return el

    def _add_multiplicity(self, parent: Element, mult_str: str):
        """Add multiplicity lower/upper bounds."""
        # Handle both string and enum Multiplicity values
        if hasattr(mult_str, 'value'):
            mult_str = mult_str.value
        mult_str = str(mult_str)
        parts = mult_str.split("..")
        if len(parts) == 2:
            lower, upper = parts
        else:
            lower, upper = ("0", "*") if parts[0] == "*" else (parts[0], parts[0])

        lower_el = SubElement(parent, "lowerValue")
        lower_el.set("xmi:type", "uml:LiteralInteger")
        lower_el.set("value", lower if lower != "*" else "-1")

        upper_el = SubElement(parent, "upperValue")
        upper_el.set("xmi:type", "uml:LiteralUnlimitedNatural")
        upper_el.set("value", upper if upper != "*" else "-1")

    # ─── Import (XMI → UMLDiagram) ─────────────────────────────────────

    def import_from_xmi(self, xmi_content: str) -> UMLDiagram:
        """Import a UML diagram from an XMI 2.1 XML string."""
        self.warnings = []
        self.unsupported_elements = []

        root = ET.fromstring(xmi_content)

        # Register namespaces
        ns = {
            "xmi": XMI_NS,
            "uml": UML_NS,
        }

        # Find the model
        model_el = root.find(".//uml:Model", ns)
        if model_el is None:
            model_el = root.find(".//{http://www.omg.org/spec/UML/20131001}Model")
        if model_el is None:
            for elem in root.iter():
                tag_name = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
                x_type = self._get_xmi_attr(elem, "type")
                if tag_name == "Model" or x_type == "uml:Model":
                    model_el = elem
                    break

        if model_el is None:
            self.warnings.append("No se encontró un elemento uml:Model en el XMI.")
            return UMLDiagram()

        diagram = UMLDiagram()
        diagram.name = model_el.get("name", "Imported Diagram")

        # Parse classes
        xmi_to_class: dict[str, UMLClass] = {}
        x_offset = 50
        y_offset = 50

        def package_elements(container):
            for element in container:
                x_type = self._get_xmi_attr(element, "type")
                tag_name = element.tag.split("}")[-1]
                if x_type == "uml:Package" or tag_name == "Package":
                    yield from package_elements(element)
                else:
                    yield element
        elements = list(package_elements(model_el))
        # Resolve every class before any relation, independent of document order.
        elements.sort(key=lambda el: 0 if self._get_xmi_attr(el, "type") in ("uml:Class", "uml:Interface") or el.tag.split("}")[-1] in ("Class", "Interface") else 1)
        for el in elements:
            xmi_type = self._get_xmi_attr(el, "type")
            tag = el.tag.split("}")[-1] if "}" in el.tag else el.tag

            if xmi_type in ("uml:Class", "uml:Interface") or tag in ("Class", "Interface"):
                cls = self._parse_class(el, ns)
                cls.position.x = x_offset
                cls.position.y = y_offset
                x_offset += 250
                if x_offset > 800:
                    x_offset = 50
                    y_offset += 200

                xmi_id = self._get_xmi_attr(el, "id") or el.get("id", "")
                if xmi_id:
                    xmi_to_class[xmi_id] = cls
                diagram.add_class(cls)

                if xmi_type == "uml:Interface" or tag == "Interface":
                    cls.is_interface = True

            elif xmi_type == "uml:Association" or tag == "Association":
                rel = self._parse_association(el, ns, xmi_to_class)
                if rel:
                    diagram.add_relationship(rel)

            elif xmi_type in ("uml:Realization", "uml:Dependency") or tag in ("Realization", "Dependency"):
                rel = self._parse_directed_rel(el, ns, xmi_to_class, xmi_type)
                if rel:
                    diagram.add_relationship(rel)

            else:
                self.unsupported_elements.append(f"{tag} ({xmi_type})")

        for el in elements:
            child_id = self._get_xmi_attr(el, "id") or el.get("id", "")
            child = xmi_to_class.get(child_id)
            if child is None:
                continue
            for generalization in el:
                if generalization.tag.split("}")[-1].lower() != "generalization":
                    continue
                parent_ref = generalization.get("general") or self._get_xmi_attr(generalization, "general")
                parent = xmi_to_class.get(parent_ref)
                if parent is None:
                    self.warnings.append("Herencia con clase padre desconocida, omitida.")
                    continue
                diagram.add_relationship(UMLRelationship(
                    type=RelationshipType.GENERALIZATION,
                    source=RelationshipEnd(class_id=child.id),
                    target=RelationshipEnd(class_id=parent.id)))

        # Parse Enterprise Architect visual layout if present
        for elem in root.iter():
            tag_local = elem.tag.split("}")[-1].lower()
            if tag_local == "element":
                subj = elem.get("subject") or self._get_xmi_attr(elem, "subject")
                geom = elem.get("geometry") or ""
                if subj and subj in xmi_to_class and "Left=" in geom:
                    cls = xmi_to_class[subj]
                    m_left = re.search(r'Left=(-?\d+)', geom)
                    m_top = re.search(r'Top=(-?\d+)', geom)
                    m_right = re.search(r'Right=(-?\d+)', geom)
                    m_bottom = re.search(r'Bottom=(-?\d+)', geom)
                    if m_left and m_top:
                        left = abs(int(m_left.group(1)))
                        top = abs(int(m_top.group(1)))
                        width = abs(int(m_right.group(1)) - int(m_left.group(1))) if m_right else 200
                        height = abs(int(m_bottom.group(1)) - int(m_top.group(1))) if m_bottom else 120
                        cls.position = Position(x=left, y=top)
                        cls.size = Size(width=max(width, 100), height=max(height, 60))

        return diagram

    def _parse_class(self, el: Element, ns: dict) -> UMLClass:
        """Parse a class element from XMI."""
        cls = UMLClass()
        cls.name = el.get("name", "UnknownClass")
        vis = el.get("visibility", "public")
        cls.visibility = VISIBILITY_MAP.get(vis, "+")
        cls.is_abstract = el.get("isAbstract", "false").lower() == "true"

        # Parse attributes
        for attr_el in el:
            tag = attr_el.tag.split("}")[-1] if "}" in attr_el.tag else attr_el.tag
            xmi_type = attr_el.get("{%s}type" % XMI_NS, "")

            if tag == "ownedAttribute" or xmi_type == "uml:Property":
                attr = UMLAttribute()
                attr.name = attr_el.get("name", "")
                attr.visibility = VISIBILITY_MAP.get(attr_el.get("visibility", "private"), "-")
                attr.is_static = attr_el.get("isStatic", "false").lower() == "true"
                attr.is_final = attr_el.get("isReadOnly", "false").lower() == "true"
                attr.is_derived = attr_el.get("isDerived", "false").lower() == "true"
                default = attr_el.find("defaultValue")
                if default is not None:
                    attr.default_value = default.get("value", "")
                lower, upper = attr_el.find("lowerValue"), attr_el.find("upperValue")
                if lower is not None or upper is not None:
                    lo = lower.get("value", "1") if lower is not None else "1"
                    hi = upper.get("value", "1") if upper is not None else "1"
                    hi = "*" if hi == "-1" else hi
                    attr.multiplicity = lo if lo == hi else f"{lo}..{hi}"

                # Parse type
                type_el = attr_el.find("type")
                if type_el is not None:
                    href = type_el.get("href", "")
                    attr.type = href.split("#")[-1] if "#" in href else "String"
                else:
                    attr.type = attr_el.get("type", "String")

                if attr.name:
                    cls.attributes.append(attr)

            elif tag == "ownedOperation" or xmi_type == "uml:Operation":
                op = UMLOperation()
                op.name = attr_el.get("name", "")
                op.visibility = VISIBILITY_MAP.get(attr_el.get("visibility", "public"), "+")
                op.is_abstract = attr_el.get("isAbstract", "false").lower() == "true"
                op.is_static = attr_el.get("isStatic", "false").lower() == "true"

                # Parse parameters
                for param_el in attr_el:
                    p_tag = param_el.tag.split("}")[-1] if "}" in param_el.tag else param_el.tag
                    if p_tag == "ownedParameter":
                        direction = param_el.get("direction", "in")
                        if direction == "return":
                            p_type = param_el.find("type")
                            if p_type is not None:
                                href = p_type.get("href", "")
                                op.return_type = href.split("#")[-1] if "#" in href else "void"
                        else:
                            param = UMLParameter()
                            param.name = param_el.get("name", "")
                            p_type = param_el.find("type")
                            if p_type is not None:
                                href = p_type.get("href", "")
                                param.type = href.split("#")[-1] if "#" in href else "String"
                            op.parameters.append(param)

                if op.name:
                    cls.operations.append(op)

        cls.computeHeight() if hasattr(cls, 'computeHeight') else None
        return cls

    def _parse_association(self, el: Element, ns: dict,
                           xmi_to_class: dict[str, UMLClass]) -> Optional[UMLRelationship]:
        """Parse an association from XMI."""
        ends = []
        for child in el:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            x_type = self._get_xmi_attr(child, "type")
            if tag == "ownedEnd" or x_type == "uml:Property":
                end_type = child.get("type") or self._get_xmi_attr(child, "type")
                if not end_type or end_type == "uml:Property":
                    type_sub = child.find("type")
                    if type_sub is not None:
                        end_type = self._get_xmi_attr(type_sub, "idref") or type_sub.get("href", "")

                end_role = child.get("name")
                end_agg = child.get("aggregation", "none")

                # Parse multiplicity
                mult = "1"
                lower_el = child.find("lowerValue")
                upper_el = child.find("upperValue")
                if lower_el is not None and upper_el is not None:
                    lower = lower_el.get("value", "1")
                    upper = upper_el.get("value", "1")
                    if lower == "-1": lower = "*"
                    if upper == "-1": upper = "*"
                    mult = f"{lower}..{upper}" if lower != upper else lower

                ends.append({
                    "type": end_type, "role": end_role,
                    "aggregation": end_agg, "multiplicity": mult,
                })

        if len(ends) < 2:
            self.warnings.append(f"Asociación con menos de 2 extremos, omitida.")
            return None

        # Determine relationship type
        rel_type = RelationshipType.ASSOCIATION
        if ends[0].get("aggregation") == "shared":
            rel_type = RelationshipType.AGGREGATION
        elif ends[0].get("aggregation") == "composite":
            rel_type = RelationshipType.COMPOSITION

        # Find classes
        source_cls = xmi_to_class.get(ends[0]["type"])
        target_cls = xmi_to_class.get(ends[1]["type"])
        if not source_cls or not target_cls:
            self.warnings.append("Asociación referencia clases no encontradas en el modelo.")
            return None

        rel = UMLRelationship()
        rel.type = rel_type
        rel.name = el.get("name")
        rel.source = RelationshipEnd(
            class_id=source_cls.id,
            role=ends[0].get("role"),
            multiplicity=ends[0]["multiplicity"],
        )
        rel.target = RelationshipEnd(
            class_id=target_cls.id,
            role=ends[1].get("role"),
            multiplicity=ends[1]["multiplicity"],
        )
        return rel

    def _parse_directed_rel(self, el: Element, ns: dict,
                            xmi_to_class: dict[str, UMLClass],
                            xmi_type: str) -> Optional[UMLRelationship]:
        """Parse a directed relationship (realization, dependency)."""
        client_id = el.get("client", "") or self._get_xmi_attr(el, "client")
        supplier_id = el.get("supplier", "") or self._get_xmi_attr(el, "supplier")
        if not client_id:
            c_el = el.find("client")
            if c_el is not None:
                client_id = self._get_xmi_attr(c_el, "idref") or c_el.get("href", "")
        if not supplier_id:
            s_el = el.find("supplier")
            if s_el is not None:
                supplier_id = self._get_xmi_attr(s_el, "idref") or s_el.get("href", "")

        source = xmi_to_class.get(client_id)
        target = xmi_to_class.get(supplier_id)
        if not source or not target:
            self.warnings.append(f"Relación dirigida referencia clases no encontradas.")
            return None

        rel = UMLRelationship()
        if "Realization" in xmi_type:
            rel.type = RelationshipType.REALIZATION
        else:
            rel.type = RelationshipType.DEPENDENCY
        rel.source = RelationshipEnd(class_id=source.id)
        rel.target = RelationshipEnd(class_id=target.id)
        return rel
