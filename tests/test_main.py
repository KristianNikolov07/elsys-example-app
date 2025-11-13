import os
import sys
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from main import app, STORAGE_DIR

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_storage_dir(tmp_path):

    original_dir = STORAGE_DIR
    test_dir = tmp_path / "storage"
    test_dir.mkdir()
    app.dependency_overrides[STORAGE_DIR] = test_dir

    import main
    main.STORAGE_DIR = test_dir

    yield test_dir

    main.STORAGE_DIR = original_dir


def test_root():
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert "File Storage API" in data["message"]
    assert "GET /files/{filename}" in data["endpoints"]


def test_health_check():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["service"] == "File Storage API"


def test_store_and_get_file(tmp_path):
    filename = "example.txt"
    file_content = b"Hello, world!"
    response = client.post(
        "/files",
        files={"file": (filename, file_content, "text/plain")}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "File stored successfully"
    assert data["filename"] == filename
    assert data["size"] == len(file_content)

    stored_file = tmp_path / "storage" / filename
    assert stored_file.exists()
    assert stored_file.read_bytes() == file_content

    get_response = client.get(f"/files/{filename}")
    assert get_response.status_code == 200
    assert get_response.content == file_content


def test_get_nonexistent_file():
    res = client.get("/files/does_not_exist.txt")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"]


def test_list_files(tmp_path):
    for i in range(3):
        (tmp_path / "storage" / f"file_{i}.txt").write_text(f"data{i}")

    res = client.get("/files")
    assert res.status_code == 200
    data = res.json()
    assert "files" in data
    assert len(data["files"]) == 3
    assert all(f"file_{i}.txt" in data["files"] for i in range(3))
