from fastapi.testclient import TestClient
from app.main import app


def test_drive_configuration_exposes_only_valid_public_client_id(monkeypatch):
    monkeypatch.setenv('GOOGLE_DRIVE_CLIENT_ID', '123-example.apps.googleusercontent.com')
    monkeypatch.setenv('GOOGLE_CLIENT_SECRET', 'must-never-be-returned')
    response = TestClient(app).get('/api/integrations/google-drive')
    assert response.json() == {'configured': True, 'clientId': '123-example.apps.googleusercontent.com'}
    assert response.headers['cache-control'] == 'no-store'
    assert 'must-never-be-returned' not in response.text


def test_missing_or_invalid_drive_client_is_not_exposed(monkeypatch):
    monkeypatch.delenv('GOOGLE_DRIVE_CLIENT_ID', raising=False)
    assert TestClient(app).get('/api/integrations/google-drive').json() == {'configured': False, 'clientId': ''}
    monkeypatch.setenv('GOOGLE_DRIVE_CLIENT_ID', 'invalid-configuration')
    assert TestClient(app).get('/api/integrations/google-drive').json() == {'configured': False, 'clientId': ''}
