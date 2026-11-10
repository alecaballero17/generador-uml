import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.app.models.uml_model import UMLDiagram, UMLClass, UMLAttribute, UMLRelationship, RelationshipEnd
from backend.app.models.association_classes import normalize_association_classes
from backend.app.models.uml_validator import UMLValidator
from backend.app.services.springboot_generator import SpringBootGenerator
from backend.app.services.flutter_generator import FlutterGenerator
from backend.app.services.postman_generator import PostmanGenerator
from backend.app.services.photo_vision import normalize_proposal


def diagram():
    return UMLDiagram(name='PruebaAsociacion',classes=[
        UMLClass(id='v',name='Venta',attributes=[UMLAttribute(name='fecha',type='LocalDate')]),
        UMLClass(id='p',name='Producto',attributes=[UMLAttribute(name='nombre',type='String')]),
        UMLClass(id='d',name='Detalle',attributes=[UMLAttribute(name='cantidad',type='Integer'),UMLAttribute(name='precioUnitario',type='Double')]),
    ],relationships=[UMLRelationship(id='vp',source=RelationshipEnd(class_id='v',multiplicity='*',navigable=False),target=RelationshipEnd(class_id='p',multiplicity='1..*',navigable=False),association_class_id='d')])


def test_roundtrip_and_lowering_without_changing_canvas():
    original=diagram()
    restored=UMLDiagram.from_dict(original.to_dict())
    lowered=normalize_association_classes(restored)
    assert original.to_dict()==restored.to_dict()
    assert len(restored.relationships)==1
    assert [(r.source.class_id,r.source.multiplicity,r.target.class_id,r.target.multiplicity) for r in lowered.relationships]==[('v','1','d','1..*'),('p','1','d','*')]
    assert not any(r.association_class_id for r in lowered.relationships)
    result=UMLValidator(restored).validate()
    assert result.is_valid
    assert not any(w.element_id=='d' and w.rule=='class.isolated' for w in result.issues)


@pytest.mark.parametrize('field,value',[('association_class_id','missing'),('association_class_id','v')])
def test_invalid_class_reference(field,value):
    model=diagram();setattr(model.relationships[0],field,value)
    with pytest.raises(ValueError):normalize_association_classes(model)
    assert not UMLValidator(model).validate().is_valid


def test_all_generators_use_detail_foreign_keys_not_an_extra_join_table():
    model=diagram()
    spring=SpringBootGenerator(model).generate()
    detail=next(value for key,value in spring.items() if key.endswith('/Detalle.java'))
    assert 'venta_id' in detail and 'producto_id' in detail
    assert 'cantidad' in detail and 'precioUnitario' in detail
    assert not any('@ManyToMany' in value for value in spring.values())
    flutter=FlutterGenerator(model).generate_all()
    form=flutter['lib/screens/detalle/detalle_form_screen.dart']
    assert 'ventaId' in form and 'productoId' in form
    postman=PostmanGenerator(model)
    assert len(postman.diagram.relationships)==2
    assert postman.generate()['item']
    assert len(model.relationships)==1


def test_vision_keeps_direct_many_to_many_and_linked_class():
    proposal=normalize_proposal(dict(classes=[dict(name=n,attributes=[]) for n in ['Venta','Producto','Detalle']],relationships=[dict(source='Venta',target='Producto',type='association',sourceMult='*',targetMult='1..*',associationClass='Detalle')]))
    assert proposal['connections']==[[0,1]]
    assert proposal['suggestions'][0]['associationClass']==2
    assert proposal['suggestions'][0]['targetMult']=='1..*'


def test_older_client_cannot_silently_remove_association_class(tmp_path):
    from backend.app.services.collaboration import Store
    store=Store(tmp_path/'collaboration.sqlite3')
    project=store.create(diagram().to_dict())
    old=diagram().to_dict();old['relationships'][0].pop('associationClassId')
    with pytest.raises(ValueError,match='versión anterior'):
        store.update(project['projectId'],0,old)
    assert store.snapshot(project['projectId'])['diagram']['relationships'][0]['associationClassId']=='d'
