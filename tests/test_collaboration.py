import copy
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.services import collaboration as collab


def diagram():
    return {'name':'Prueba','classes':[{'id':'a','name':'Usuario','attributes':[],'position':{'x':0,'y':0}}], 'relationships':[]}


def test_merge_independent_attributes_and_conflicting_name():
    base=diagram(); local=copy.deepcopy(base); remote=copy.deepcopy(base)
    local['classes'][0]['attributes'].append({'id':'attr1','name':'nombre'})
    remote['classes'][0]['position']['x']=120
    result=collab.merge(base,local,remote)
    assert result['classes'][0]['attributes'][0]['name']=='nombre'
    assert result['classes'][0]['position']['x']==120
    local['name']='A'; remote['name']='B'
    with pytest.raises(collab.MergeConflict): collab.merge(base,local,remote)


def test_delete_versus_edit_is_conflict():
    base=diagram(); local=copy.deepcopy(base); remote=copy.deepcopy(base)
    local['classes']=[]; remote['classes'][0]['name']='Editada'
    with pytest.raises(collab.MergeConflict): collab.merge(base,local,remote)


def test_store_persists_authority_and_revisions(tmp_path):
    path=tmp_path/'collab.sqlite'
    store=collab.Store(path); project=store.create(diagram()); room=project['projectId']
    assert store.role(room,project['token'])=='admin'
    assert store.role(room,'fake') is None
    local=diagram(); local['name']='Persistido'; store.update(room,0,local)
    reloaded=collab.Store(path)
    assert reloaded.snapshot(room)['revision']==1
    assert reloaded.snapshot(room)['diagram']['name']=='Persistido'
    assert reloaded.role(room,project['token'])=='admin'


def receive_type(ws, kind):
    for _ in range(10):
        msg=ws.receive_json()
        if msg['type']==kind: return msg
    raise AssertionError(kind)


def test_shared_websockets_permissions_merge_and_conflict(tmp_path,monkeypatch):
    store=collab.Store(tmp_path/'collab.sqlite'); monkeypatch.setattr(collab,'store',store)
    monkeypatch.setattr(collab,'connections',{}); monkeypatch.setattr(collab,'locks',{})
    app=FastAPI(); app.include_router(collab.router)
    with TestClient(app) as client:
        project=client.post('/api/collaboration/projects',json={'diagram':diagram()}).json(); room=project['projectId']
        headers={'Authorization':'Bearer '+project['token']}
        editor=client.post(f'/api/collaboration/{room}/invite',headers=headers,json={'role':'editor'}).json()['token']
        viewer=client.post(f'/api/collaboration/{room}/invite',headers=headers,json={'role':'viewer'}).json()['token']
        assert client.post(f'/api/collaboration/{room}/invite',headers={'Authorization':'Bearer '+editor},json={'role':'editor'}).status_code==403
        with client.websocket_connect(f'/ws/collaboration/{room}') as one, client.websocket_connect(f'/ws/collaboration/{room}') as two:
            one.send_json({'token':project['token']}); receive_type(one,'snapshot')
            two.send_json({'token':editor}); receive_type(two,'snapshot')
            left=diagram(); left['classes'][0]['name']='Cuenta'
            right=diagram(); right['classes'][0]['position']['x']=200
            one.send_json({'type':'update','revision':0,'diagram':left}); receive_type(one,'ack')
            two.send_json({'type':'update','revision':0,'diagram':right}); merged=receive_type(two,'ack')
            assert merged['diagram']['classes'][0]['name']=='Cuenta'
            assert merged['diagram']['classes'][0]['position']['x']==200
            conflict=diagram(); conflict['classes'][0]['name']='Persona'
            two.send_json({'type':'update','revision':0,'diagram':conflict})
            assert receive_type(two,'conflict')['revision']==2
        with client.websocket_connect(f'/ws/collaboration/{room}') as readonly:
            readonly.send_json({'token':viewer}); assert receive_type(readonly,'snapshot')['role']=='viewer'
            readonly.send_json({'type':'update','revision':2,'diagram':diagram()})
            assert receive_type(readonly,'error')['message']=='Enlace de solo lectura'
        assert store.snapshot(room)['revision']==2

def test_reconnect_merges_offline_changes_and_isolates_rooms(tmp_path, monkeypatch):
    store=collab.Store(tmp_path/'reconnect.sqlite')
    monkeypatch.setattr(collab,'store',store)
    monkeypatch.setattr(collab,'connections',{})
    monkeypatch.setattr(collab,'locks',{})
    monkeypatch.setattr(collab,'_rate_limits',{})
    app=FastAPI();app.include_router(collab.router)
    with TestClient(app) as client:
        project=client.post('/api/collaboration/projects',json={'diagram':diagram()}).json()
        other=client.post('/api/collaboration/projects',json={'diagram':diagram()}).json()
        room=project['projectId'];token=project['token']
        offline=diagram();offline['classes'][0]['attributes'].append({'id':'correo','name':'correo','type':'String'})
        with client.websocket_connect(f'/ws/collaboration/{room}') as online:
            online.send_json({'token':token});receive_type(online,'snapshot')
            edited=diagram();edited['classes'][0]['position']['x']=410
            online.send_json({'type':'update','revision':0,'diagram':edited});receive_type(online,'ack')
        with client.websocket_connect(f'/ws/collaboration/{room}') as reconnect:
            reconnect.send_json({'token':token});assert receive_type(reconnect,'snapshot')['revision']==1
            reconnect.send_json({'type':'update','revision':0,'diagram':offline})
            result=receive_type(reconnect,'ack')
            assert result['diagram']['classes'][0]['position']['x']==410
            assert result['diagram']['classes'][0]['attributes'][0]['name']=='correo'
        assert store.snapshot(other['projectId'])['revision']==0
        assert store.role(other['projectId'],token) is None
        persisted=collab.Store(tmp_path/'reconnect.sqlite').snapshot(room)
        assert persisted['diagram']==result['diagram']


def test_revision_history_and_rollback(tmp_path, monkeypatch):
    store = collab.Store(tmp_path / 'revisions.sqlite')
    monkeypatch.setattr(collab, 'store', store)
    monkeypatch.setattr(collab, 'connections', {})
    monkeypatch.setattr(collab, 'locks', {})
    monkeypatch.setattr(collab, '_rate_limits', {})
    app = FastAPI()
    app.include_router(collab.router)

    with TestClient(app) as client:
        project = client.post('/api/collaboration/projects', json={'diagram': diagram()}).json()
        room = project['projectId']
        admin_token = project['token']
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        # Create editor
        editor_token = client.post(f'/api/collaboration/{room}/invite', headers=admin_headers, json={'role': 'editor'}).json()['token']
        editor_headers = {'Authorization': f'Bearer {editor_token}'}

        # Rev 1
        d1 = diagram()
        d1['classes'][0]['name'] = 'VersionUno'
        store.update(room, 0, d1)

        # Rev 2
        d2 = diagram()
        d2['classes'][0]['name'] = 'VersionDos'
        store.update(room, 1, d2)

        # List revisions
        rev_resp = client.get(f'/api/collaboration/{room}/revisions', headers=editor_headers)
        assert rev_resp.status_code == 200
        rev_data = rev_resp.json()
        assert rev_data['currentRevision'] == 2
        assert rev_data['revisions'] == [0, 1, 2]

        # Unauthorized cannot list
        assert client.get(f'/api/collaboration/{room}/revisions', headers={'Authorization': 'Bearer bad'}).status_code == 403

        # Editor cannot revert
        assert client.post(f'/api/collaboration/{room}/revert/1', headers=editor_headers).status_code == 403

        # Connect WebSocket to test real-time broadcast of rollback
        with client.websocket_connect(f'/ws/collaboration/{room}') as ws:
            ws.send_json({'token': editor_token})
            receive_type(ws, 'snapshot')

            # Admin reverts to Revision 1
            revert_resp = client.post(f'/api/collaboration/{room}/revert/1', headers=admin_headers)
            assert revert_resp.status_code == 200
            revert_data = revert_resp.json()
            assert revert_data['revision'] == 3
            assert revert_data['diagram']['classes'][0]['name'] == 'VersionUno'
            assert revert_data['revertedFrom'] == 2
            assert revert_data['revertedTo'] == 1

            # WebSocket received snapshot of rev 3
            ws_snapshot = receive_type(ws, 'snapshot')
            assert ws_snapshot['revision'] == 3
            assert ws_snapshot['diagram']['classes'][0]['name'] == 'VersionUno'

        # Invalid target revision
        assert client.post(f'/api/collaboration/{room}/revert/99', headers=admin_headers).status_code == 400

