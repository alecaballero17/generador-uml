import json
import threading
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.build_pipeline import BuildPipeline
from app.models.uml_model import UMLDiagram
from app.services.postman_generator import PostmanGenerator


def sales():
    return json.loads((Path(__file__).parents[1] / 'examples/ventas_defensa.json').read_text())


def test_build_endpoint_is_disabled_on_public_deployment(monkeypatch):
    monkeypatch.delenv('UML_LOCAL_BUILD', raising=False)
    client = TestClient(app, base_url='http://localhost')
    assert client.post('/api/builds', json={'diagram': sales()}).status_code == 403


def test_build_rejects_cross_origin_and_invalid_package(monkeypatch):
    monkeypatch.setenv('UML_LOCAL_BUILD', '1')
    client = TestClient(app, base_url='http://localhost')
    assert client.post('/api/builds', json={'diagram': sales()}, headers={'Origin': 'https://attacker.example'}).status_code == 403
    assert client.post('/api/builds', json={'diagram': sales(), 'basePackage': '../escape'}).status_code == 422
    assert client.get('/api/builds/not-a-job').status_code == 404


def test_failure_releases_queue_and_keeps_evidence(tmp_path, monkeypatch):
    pipeline = BuildPipeline(tmp_path)
    monkeypatch.setattr('app.services.build_pipeline.shutil.which', lambda tool: tool)
    finished = threading.Event()
    def fail(*args, **kwargs):
        raise RuntimeError('Fallo simulado de compilador')
    monkeypatch.setattr('app.services.build_pipeline.SpringBootGenerator.generate_to_disk', fail)
    original = pipeline._build
    def run(*args):
        try:
            original(*args)
        finally:
            finished.set()
    monkeypatch.setattr(pipeline, '_build', run)
    job = pipeline.start(UMLDiagram.from_dict(sales()), 'com.example.demo')
    assert finished.wait(5)
    status = pipeline.status(job)
    assert status['state'] == 'failed'
    assert 'Fallo simulado' in status['log']
    assert pipeline.active is None
    assert json.loads((pipeline.directory(job) / 'diagrama.json').read_text())['name'] == 'VentasDefensa'
    with pytest.raises(ValueError):
        pipeline.directory('../escape')


def test_postman_sales_creation_dependencies_versions_and_cleanup():
    collection = PostmanGenerator(UMLDiagram.from_dict(sales())).generate()
    folders = {f['name']: f for f in collection['item'] if 'item' in f}
    names = list(folders)
    assert names.index('Cliente') < names.index('Venta') < names.index('Detalle')
    create = folders['Venta']['item'][0]
    assert create['request']['method'] == 'POST'
    assert '"clienteId": {{ClienteId}}' in create['request']['body']['raw']
    assert 'VentaId' in '\n'.join(create['event'][0]['script']['exec'])
    update = next(i for i in folders['Venta']['item'] if i['request']['method'] == 'PUT')
    assert '"version": {{VentaVersion}}' in update['request']['body']['raw']
    assert '{{VentaId}}' in update['request']['url']['raw']
    deletes = collection['item'][-1]['item']
    assert deletes[0]['name'] == 'Eliminar Detalle'
