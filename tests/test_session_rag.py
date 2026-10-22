"""Tests for session-aware RAG pipeline (Milestone 3)."""

SAMPLE_TEXT = (
    "The Atlas platform supports pluggable LLM providers including Mock, OpenAI, and Anthropic. "
    "Each provider implements the BaseLLMProvider interface with a complete() method. "
    "The FallbackProvider chains multiple providers and returns the first successful response. "
    "Rate limiting is enforced per client using the X-Client-Id header. "
    "Feature flags control caching, prompt logging, and strict validation modes."
)


# --- Document ingestion ---


def test_upload_document_to_session(client):
    s = client.post("/sessions", json={"title": "rag-session"}).json()
    resp = client.post(
        f"/sessions/{s['id']}/documents",
        json={"text": SAMPLE_TEXT, "filename": "atlas_overview.txt"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["filename"] == "atlas_overview.txt"
    assert body["chunk_count"] >= 1
    assert body["session_id"] == s["id"]


def test_upload_document_missing_session(client):
    resp = client.post(
        "/sessions/999/documents",
        json={"text": SAMPLE_TEXT, "filename": "test.txt"},
    )
    assert resp.status_code == 404


def test_upload_empty_text_rejected(client):
    s = client.post("/sessions", json={}).json()
    resp = client.post(
        f"/sessions/{s['id']}/documents",
        json={"text": "   ", "filename": "empty.txt"},
    )
    assert resp.status_code == 422


def test_upload_missing_text_field_rejected(client):
    s = client.post("/sessions", json={}).json()
    resp = client.post(f"/sessions/{s['id']}/documents", json={"filename": "no-text.txt"})
    assert resp.status_code == 422


# --- Document listing ---


def test_list_documents_empty(client):
    s = client.post("/sessions", json={}).json()
    resp = client.get(f"/sessions/{s['id']}/documents")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_documents_returns_uploaded(client):
    s = client.post("/sessions", json={}).json()
    client.post(f"/sessions/{s['id']}/documents", json={"text": SAMPLE_TEXT, "filename": "a.txt"})
    client.post(f"/sessions/{s['id']}/documents", json={"text": SAMPLE_TEXT, "filename": "b.txt"})
    resp = client.get(f"/sessions/{s['id']}/documents")
    assert resp.status_code == 200
    names = [d["filename"] for d in resp.json()]
    assert "a.txt" in names and "b.txt" in names


# --- Session isolation ---


def test_documents_isolated_between_sessions(client):
    s1 = client.post("/sessions", json={"title": "s1"}).json()
    s2 = client.post("/sessions", json={"title": "s2"}).json()
    client.post(
        f"/sessions/{s1['id']}/documents",
        json={"text": "Secret content for session 1 only.", "filename": "secret.txt"},
    )
    docs_s2 = client.get(f"/sessions/{s2['id']}/documents").json()
    assert docs_s2 == []


# --- Document deletion ---


def test_delete_document(client):
    s = client.post("/sessions", json={}).json()
    doc = client.post(
        f"/sessions/{s['id']}/documents",
        json={"text": SAMPLE_TEXT, "filename": "del.txt"},
    ).json()
    resp = client.delete(f"/sessions/{s['id']}/documents/{doc['id']}")
    assert resp.status_code == 204
    remaining = client.get(f"/sessions/{s['id']}/documents").json()
    assert all(d["id"] != doc["id"] for d in remaining)


def test_delete_document_wrong_session(client):
    s1 = client.post("/sessions", json={}).json()
    s2 = client.post("/sessions", json={}).json()
    doc = client.post(
        f"/sessions/{s1['id']}/documents",
        json={"text": SAMPLE_TEXT, "filename": "owned.txt"},
    ).json()
    resp = client.delete(f"/sessions/{s2['id']}/documents/{doc['id']}")
    assert resp.status_code == 404


# --- RAG-augmented messaging ---


def test_message_includes_sources_when_doc_present(client):
    s = client.post("/sessions", json={"title": "with-docs"}).json()
    client.post(
        f"/sessions/{s['id']}/documents",
        json={"text": SAMPLE_TEXT, "filename": "ref.txt"},
    )
    resp = client.post(
        f"/sessions/{s['id']}/messages",
        json={"message": "What LLM providers are supported?", "use_rag": True},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert "sources" in body
    assert isinstance(body["sources"], list)


def test_message_no_sources_when_no_docs(client):
    s = client.post("/sessions", json={"title": "no-docs"}).json()
    resp = client.post(
        f"/sessions/{s['id']}/messages",
        json={"message": "Hello", "use_rag": True},
    )
    assert resp.status_code == 201
    assert resp.json()["sources"] == []


def test_message_rag_disabled(client):
    s = client.post("/sessions", json={"title": "rag-off"}).json()
    client.post(
        f"/sessions/{s['id']}/documents",
        json={"text": SAMPLE_TEXT, "filename": "ignored.txt"},
    )
    resp = client.post(
        f"/sessions/{s['id']}/messages",
        json={"message": "anything", "use_rag": False},
    )
    assert resp.status_code == 201
    assert resp.json()["sources"] == []


def test_deleted_document_excluded_from_retrieval(client):
    s = client.post("/sessions", json={"title": "delete-rag"}).json()
    doc = client.post(
        f"/sessions/{s['id']}/documents",
        json={"text": "Unique content about the deletion test scenario.", "filename": "temp.txt"},
    ).json()
    client.delete(f"/sessions/{s['id']}/documents/{doc['id']}")

    resp = client.post(
        f"/sessions/{s['id']}/messages",
        json={"message": "Tell me about the deletion test scenario.", "use_rag": True},
    )
    assert resp.status_code == 201
    assert resp.json()["sources"] == []


def test_session_delete_cascades_documents(client):
    s = client.post("/sessions", json={}).json()
    client.post(
        f"/sessions/{s['id']}/documents",
        json={"text": SAMPLE_TEXT, "filename": "cascade.txt"},
    )
    client.delete(f"/sessions/{s['id']}")
    # Session no longer accessible
    assert client.get(f"/sessions/{s['id']}").status_code == 404
