import asyncio

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app import main


@pytest.fixture
def isolated_projects(tmp_path, monkeypatch):
    original_projects = main.projects.copy()
    main.projects.clear()
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    monkeypatch.setattr(main, "OUTPUT_DIR", output_dir)
    try:
        yield output_dir
    finally:
        main.projects.clear()
        main.projects.update(original_projects)


def project_payload(project_id):
    return {
        "projectId": project_id,
        "name": "Proyecto de seguridad",
        "diagram": {
            "id": "diagram-security",
            "name": "Proyecto de seguridad",
            "classes": [],
            "relationships": [],
        },
    }


def test_valid_legacy_id_can_save_load_and_delete(isolated_projects):
    project_id = "proj_test_1"
    with TestClient(main.app) as client:
        saved = client.post("/api/projects/save", json=project_payload(project_id))
        assert saved.status_code == 200
        assert saved.json() == {"projectId": project_id, "saved": True}
        assert (isolated_projects / "projects" / f"{project_id}.json").is_file()

        loaded = client.get(f"/api/projects/{project_id}")
        assert loaded.status_code == 200
        assert loaded.json()["id"] == project_id

        deleted = client.delete(f"/api/projects/{project_id}")
        assert deleted.status_code == 200
        assert deleted.json() == {"deleted": True}
        assert not (isolated_projects / "projects" / f"{project_id}.json").exists()


@pytest.mark.parametrize(
    "project_id",
    [
        "",
        "../outside",
        r"..\outside",
        "/tmp/outside",
        r"C:\outside",
        "nested/path",
        r"nested\path",
        "..%2Foutside",
        "..%5Coutside",
        "space id",
    ],
)
def test_unsafe_project_ids_are_rejected_before_persistence(project_id, isolated_projects):
    with TestClient(main.app) as client:
        response = client.post("/api/projects/save", json=project_payload(project_id))
    assert response.status_code == 400
    assert response.json()["detail"] == "Identificador de proyecto inválido"
    assert not (isolated_projects / "outside.json").exists()


@pytest.mark.parametrize("project_id", ["../outside", r"..\outside", "/tmp/outside", "nested/path", "..%2Foutside"])
def test_unsafe_project_ids_are_rejected_by_load_and_delete(project_id, isolated_projects):
    for endpoint in (main.get_project, main.delete_project):
        with pytest.raises(HTTPException) as error:
            asyncio.run(endpoint(project_id))
        assert error.value.status_code == 400
