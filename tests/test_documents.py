def test_ingest_returns_document(client):
    resp = client.post("/documents", json={"text": "Hello world document content."})
    assert resp.status_code == 201
    body = resp.json()
    assert "id" in body
    assert body["chunks"] >= 1
    assert body["source"] == "upload"


def test_ingest_custom_source(client):
    resp = client.post("/documents", json={"text": "Some text.", "source": "manual"})
    assert resp.status_code == 201
    assert resp.json()["source"] == "manual"


def test_ingest_empty_text_returns_error(client):
    resp = client.post("/documents", json={"text": ""})
    assert resp.status_code == 422  # Pydantic min_length rejects before handler


def test_ingest_whitespace_only_returns_error(client):
    resp = client.post("/documents", json={"text": "   "})
    assert resp.status_code == 400
    assert resp.json()["code"] == "text_required"


def test_tail_chunk_stored(client):
    # ISS-1 regression: a document whose length is chunk_size + 1 must produce 2 chunks
    long_text = "a" * 401  # default chunk_size is 400
    resp = client.post("/documents", json={"text": long_text})
    assert resp.status_code == 201
    assert resp.json()["chunks"] == 2
