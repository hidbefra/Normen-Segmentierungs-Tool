import fitz
import pytest
from fastapi.testclient import TestClient

from normen_tool.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_project(tmp_path):
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    pdf_path = project_dir / "sample.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Kapitel 1\nDies ist ein Testdokument.")
    page.insert_text((50, 120), "Fortsetzung des Absatzes ohne Punkt")
    doc.save(pdf_path)
    doc.close()

    return project_dir


def test_open_project_and_list_pdfs(client, sample_project):
    response = client.post("/project/open", json={"project_dir": str(sample_project)})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"created", "loaded"}
    assert str(sample_project) in body["project_dir"]

    response = client.get("/project/status")
    assert response.status_code == 200
    assert response.json()["pdf_count"] == 1

    response = client.get("/project/pdfs")
    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["pdfs"][0]["name"] == "sample.pdf"


def test_open_project_with_duplicate_segment_path_is_corrected(client, sample_project):
    duplicate_path = (
        sample_project.parent / sample_project.parent.name / sample_project.name
    )

    response = client.post("/project/open", json={"project_dir": str(duplicate_path)})
    assert response.status_code == 200

    body = response.json()
    assert body["project_dir"] == str(sample_project.resolve())


def test_get_pdf_pages_and_render_page(client, sample_project):
    client.post("/project/open", json={"project_dir": str(sample_project)})
    response = client.get("/project/pdfs")
    doc_id = response.json()["pdfs"][0]["id"]

    response = client.get(f"/pdf/{doc_id}/pages")
    assert response.status_code == 200
    pages = response.json()["pages"]
    assert len(pages) == 1
    assert pages[0]["page_num"] == 1

    response = client.get(f"/pdf/{doc_id}/rendered/1?format=png&dpi=150")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(b"\x89PNG")


def test_block_crud_and_parse_document(client, sample_project):
    client.post("/project/open", json={"project_dir": str(sample_project)})
    doc_id = client.get("/project/pdfs").json()["pdfs"][0]["id"]

    # Create a manual block
    create_response = client.post(
        "/block",
        json={
            "document_id": doc_id,
            "section": "1.1",
            "content": "Manueller Absatz",
            "block_type": "paragraph",
            "pages": [0],
            "bboxes": [[10, 10, 100, 30]],
            "ai_generated": False,
        },
    )
    assert create_response.status_code == 200
    block_id = create_response.json()["block"]["id"]

    # Get block
    get_response = client.get(f"/block/{block_id}")
    assert get_response.status_code == 200
    assert get_response.json()["block"]["content"] == "Manueller Absatz"

    # Update block
    update_response = client.patch(
        f"/block/{block_id}", json={"content": "Aktualisierter Inhalt"}
    )
    assert update_response.status_code == 200
    assert update_response.json()["block"]["content"] == "Aktualisierter Inhalt"

    # List blocks for document
    list_response = client.get(f"/blocks/{doc_id}")
    assert list_response.status_code == 200
    assert list_response.json()["count"] >= 1

    # Parse the document and create parsed blocks without removing existing blocks
    parse_response = client.post(
        f"/pdf/{doc_id}/parse", json={"overwrite_existing": False}
    )
    assert parse_response.status_code == 200
    assert parse_response.json()["blocks_created"] >= 1

    # Delete the created block
    delete_response = client.delete(f"/block/{block_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted_id"] == block_id

    # Confirm deletion
    not_found_response = client.get(f"/block/{block_id}")
    assert not_found_response.status_code == 404


def test_export_csv(client, sample_project):
    client.post("/project/open", json={"project_dir": str(sample_project)})
    doc_id = client.get("/project/pdfs").json()["pdfs"][0]["id"]

    create_response = client.post(
        "/block",
        json={
            "document_id": doc_id,
            "section": "1.1",
            "content": "Manueller Absatz",
            "block_type": "paragraph",
            "pages": [0],
            "bboxes": [[10, 10, 100, 30]],
            "ai_generated": False,
        },
    )
    assert create_response.status_code == 200

    response = client.get("/export/csv")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "ID,doc_name,section,content,DeepLink_Editor" in response.text
    assert "Manueller Absatz" in response.text
