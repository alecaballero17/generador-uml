from pathlib import Path
import xml.etree.ElementTree as ET
import pytest
from app.models.uml_model import (
    UMLDiagram,UMLClass,UMLAttribute,UMLOperation,UMLRelationship,RelationshipEnd,
    RelationshipType,Position,
)
from app.services.xmi_adapter import XMIAdapter,XMI_NS
from app.services.springboot_generator import SpringBootGenerator


def example():
    model=UMLDiagram(name='VentaProductoAsociacion')
    for key,name in [('v','Venta'),('p','Producto'),('d','Detalle')]:
        model.add_class(UMLClass(id=key,name=name,position=Position(x=100+len(model.classes)*250,y=100)))
    model.classes[2].attributes=[UMLAttribute(name='cantidad',type='Integer'),UMLAttribute(name='precioUnitario',type='Double')]
    model.classes[2].operations=[UMLOperation(name='subtotal',return_type='Double')]
    model.add_relationship(UMLRelationship(id='vp',association_class_id='d',
        source=RelationshipEnd(class_id='v',multiplicity='*',role='ventas',navigable=False),
        target=RelationshipEnd(class_id='p',multiplicity='1..*',role='productos',navigable=False)))
    return model


def test_association_class_is_one_classifier_with_ea_connector_binding():
    adapter=XMIAdapter();xml=adapter.export_to_xmi(example());root=ET.fromstring(xml)
    classifiers=[e for e in root.iter('packagedElement') if e.get('{'+XMI_NS+'}type') in ('uml:Class','uml:AssociationClass')]
    assert len(classifiers)==3
    linked=next(e for e in classifiers if e.get('name')=='Detalle')
    ref=linked.get('{'+XMI_NS+'}id')
    assert linked.get('{'+XMI_NS+'}type')=='uml:AssociationClass'
    assert [e.get('name') for e in linked.findall('ownedAttribute')]==['cantidad','precioUnitario']
    assert len(linked.findall('ownedEnd'))==2
    assert linked.find('ownedOperation').get('name')=='subtotal'
    connector=next(e for e in root.iter('connector'))
    assert connector.find('extendedProperties').get('associationclass')==ref
    assert connector.find('properties').get('subtype')=='Class'
    assert connector.find('properties').get('ea_type')=='Association'
    declarations={e.get('{'+XMI_NS+'}id') for e in root.findall('.//links/Association')}
    assert connector.get('{'+XMI_NS+'}idref') in declarations, 'Strip GUIDs needs a declaration, not only connector idref/conID references'
    assert all(attr.get('isUnique')=='true' for attr in linked.findall('ownedAttribute'))
    class_meta=next(e for e in root.iter('element') if e.get('{'+XMI_NS+'}idref')==ref)
    assert class_meta.find('properties').get('nType')=='17'
    assert class_meta.find('extendedProperties').get('conID')==connector.get('{'+XMI_NS+'}idref')
    ids=[e.get('{'+XMI_NS+'}id') for e in root.iter() if e.get('{'+XMI_NS+'}id')]
    assert len(ids)==len(set(ids)), 'Class and connector must not introduce duplicate XMI identities'


@pytest.mark.parametrize('keep_extension',[True,False])
def test_association_class_roundtrip_preserves_fields_and_codegen(keep_extension):
    adapter=XMIAdapter();root=ET.fromstring(adapter.export_to_xmi(example()))
    if not keep_extension:
        for child in list(root):
            if child.tag.split('}')[-1]=='Extension':root.remove(child)
    model=adapter.import_from_xmi(ET.tostring(root,encoding='unicode'))
    names={c.id:c.name for c in model.classes}
    assert len(model.classes)==3 and len(model.relationships)==1
    rel=model.relationships[0]
    assert (names[rel.source.class_id],names[rel.target.class_id],names[rel.association_class_id])==('Venta','Producto','Detalle')
    assert rel.source.multiplicity in ('*','0..*') and rel.target.multiplicity=='1..*'
    assert not rel.source.navigable and not rel.target.navigable
    assert rel.source.role=='ventas' and rel.target.role=='productos'
    assert rel.name is None
    detalle=next(c for c in model.classes if c.name=='Detalle')
    assert [(a.name,a.type) for a in detalle.attributes]==[('cantidad','Integer'),('precioUnitario','Double')]
    assert detalle.operations[0].name=='subtotal'
    generated=SpringBootGenerator(model).generate()
    entity=next(text for path,text in generated.items() if path.endswith('/Detalle.java'))
    assert 'venta_id' in entity and 'producto_id' in entity
    assert not adapter.warnings and not adapter.unsupported_elements


def test_ea_native_member_refs_and_distinct_connector_identity():
    # External EA fixture: one end is an ownedAttribute of another class,
    # and the connector GUID differs from the AssociationClass GUID.
    adapter=XMIAdapter()
    model=adapter.import_from_xmi((Path(__file__).parent/'fixtures/ea_native_association_class.xmi').read_text(encoding='utf-8'))
    names={c.id:c.name for c in model.classes}
    assert len(model.classes)==3 and len(model.relationships)==1
    rel=model.relationships[0]
    assert (names[rel.source.class_id],names[rel.target.class_id],names[rel.association_class_id])==('CityObjectGroup','AbstractCityObject','Role')
    assert rel.source.multiplicity=='*' and rel.target.multiplicity=='*'
    assert rel.source.navigable is False and rel.target.navigable is True
    assert [a.name for c in model.classes if c.name=='Role' for a in c.attributes]==['role']
    assert not any(c.attributes for c in model.classes if c.name!='Role'), 'Association ends are not business fields'
    assert not adapter.warnings and not adapter.unsupported_elements


def test_ea_class_metadata_also_resolves_the_link():
    adapter=XMIAdapter();root=ET.fromstring(adapter.export_to_xmi(example()))
    # Some EA files retain conID on the class even when connector metadata is minimal.
    next(root.iter('connector')).find('extendedProperties').attrib.pop('associationclass')
    model=adapter.import_from_xmi(ET.tostring(root,encoding='unicode'))
    assert len(model.relationships)==1
    assert model.get_class(model.relationships[0].association_class_id).name=='Detalle'


@pytest.mark.parametrize('kind',list(RelationshipType))
def test_relationship_types_do_not_duplicate_in_ea_extension(kind):
    model=UMLDiagram(classes=[UMLClass(id='a',name='Origen'),UMLClass(id='b',name='Destino',is_interface=kind==RelationshipType.REALIZATION)])
    model.add_relationship(UMLRelationship(type=kind,source=RelationshipEnd(class_id='a',multiplicity='1',navigable=False),target=RelationshipEnd(class_id='b',multiplicity='0..*',navigable=True)))
    adapter=XMIAdapter();restored=adapter.import_from_xmi(adapter.export_to_xmi(model))
    assert len(restored.relationships)==1
    rel=restored.relationships[0]
    assert rel.type==kind
    if kind in (RelationshipType.ASSOCIATION,RelationshipType.AGGREGATION,RelationshipType.COMPOSITION):
        assert rel.source.multiplicity=='1' and rel.target.multiplicity=='0..*'
        assert not rel.source.navigable and rel.target.navigable
