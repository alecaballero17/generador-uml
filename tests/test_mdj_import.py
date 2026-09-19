import json
from app.services.mdj_adapter import MDJAdapter

def test_mdj_forward_reference_and_view():
    source={'_type':'Project','name':'Prueba','ownedElements':[
        {'_type':'UMLGeneralization','source':{'$ref':'child'},'target':{'$ref':'parent'}},
        {'_type':'UMLClass','_id':'child','name':'Alumno'},
        {'_type':'UMLClass','_id':'parent','name':'Persona'},
        {'_type':'UMLClassDiagram','ownedViews':[{'_type':'UMLClassView','model':{'$ref':'child'},'left':350,'top':220,'width':230,'height':150}]}
    ]}
    adapter=MDJAdapter();diagram=adapter.import_from_mdj(json.dumps(source))
    assert len(diagram.relationships)==1
    child=next(c for c in diagram.classes if c.name=='Alumno')
    assert (child.position.x,child.position.y)==(350,220)
    assert child.size.width==230
    assert not adapter.warnings
