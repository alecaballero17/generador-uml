import xml.etree.ElementTree as ET
from app.services.xmi_adapter import XMIAdapter
from app.models.uml_model import UMLDiagram,UMLClass,UMLRelationship,RelationshipEnd,RelationshipType

def test_xmi_inheritance_roundtrip():
    diagram=UMLDiagram()
    child,parent=UMLClass(name='Alumno'),UMLClass(name='Persona')
    diagram.add_class(child);diagram.add_class(parent)
    diagram.add_relationship(UMLRelationship(type=RelationshipType.GENERALIZATION,source=RelationshipEnd(class_id=child.id),target=RelationshipEnd(class_id=parent.id)))
    adapter=XMIAdapter()
    imported=adapter.import_from_xmi(adapter.export_to_xmi(diagram))
    assert len(imported.relationships)==1
    names={c.id:c.name for c in imported.classes}
    rel=imported.relationships[0]
    assert rel.type==RelationshipType.GENERALIZATION
    assert (names[rel.source.class_id],names[rel.target.class_id])==('Alumno','Persona')

def test_xmi_relation_before_classes():
    diagram=UMLDiagram()
    a,b=UMLClass(name='Usuario'),UMLClass(name='Pedido')
    diagram.add_class(a);diagram.add_class(b)
    diagram.add_relationship(UMLRelationship(type=RelationshipType.ASSOCIATION,source=RelationshipEnd(class_id=a.id),target=RelationshipEnd(class_id=b.id)))
    adapter=XMIAdapter();root=ET.fromstring(adapter.export_to_xmi(diagram))
    model=list(root)[1];relation=list(model)[-1];model.remove(relation);model.insert(0,relation)
    imported=adapter.import_from_xmi(ET.tostring(root,encoding='unicode'))
    assert len(imported.classes)==2
    assert len(imported.relationships)==1

def test_xmi_attribute_properties_and_nested_package():
    from app.models.uml_model import UMLAttribute
    diagram=UMLDiagram()
    cls=UMLClass(name='Ficha')
    cls.attributes.append(UMLAttribute(name='alias',type='String',multiplicity='0..*',default_value='',is_final=True,is_derived=True))
    diagram.add_class(cls)
    adapter=XMIAdapter();root=ET.fromstring(adapter.export_to_xmi(diagram))
    model=list(root)[1];element=list(model)[0];model.remove(element)
    package=ET.SubElement(model,'packagedElement',{'{http://www.omg.org/spec/XMI/20131001}type':'uml:Package','name':'Dominio'})
    package.append(element)
    imported=adapter.import_from_xmi(ET.tostring(root,encoding='unicode'))
    attr=imported.classes[0].attributes[0]
    assert attr.multiplicity=='0..*'
    assert attr.default_value==''
    assert attr.is_final and attr.is_derived
