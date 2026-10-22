def test_ask_with_no_documents(client):
    resp = client.post("/ask", json={"question": "What is the capital of France?"})
    assert resp.status_code == 200
    body = resp.json()
    assert "answer" in body
    assert "chunk_ids" in body
    assert isinstance(body["chunk_ids"], list)


def test_ask_uses_ingested_content(client):
    client.post("/documents", json={"text": "The capital of France is Paris."})
    resp = client.post("/ask", json={"question": "capital of France"})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["chunk_ids"]) > 0


def test_ask_empty_question_returns_error(client):
    resp = client.post("/ask", json={"question": ""})
    assert resp.status_code == 422  # Pydantic min_length


def test_ask_whitespace_question_returns_error(client):
    resp = client.post("/ask", json={"question": "   "})
    assert resp.status_code == 400
    body = resp.json()
    assert body["code"] == "question_required"
