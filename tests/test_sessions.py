def test_create_session(client):
    resp = client.post("/sessions", json={"title": "My test session"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "My test session"
    assert "id" in body
    assert body["message_count"] == 0


def test_create_session_default_title(client):
    resp = client.post("/sessions", json={})
    assert resp.status_code == 201
    assert resp.json()["title"] == "New conversation"


def test_list_sessions_empty(client):
    resp = client.get("/sessions")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_sessions_returns_created(client):
    client.post("/sessions", json={"title": "A"})
    client.post("/sessions", json={"title": "B"})
    resp = client.get("/sessions")
    assert resp.status_code == 200
    titles = [s["title"] for s in resp.json()]
    assert "A" in titles
    assert "B" in titles


def test_get_session_not_found(client):
    resp = client.get("/sessions/999")
    assert resp.status_code == 404


def test_get_session_with_messages(client):
    s = client.post("/sessions", json={"title": "ctx"}).json()
    client.post(f"/sessions/{s['id']}/messages", json={"message": "hello"})
    resp = client.get(f"/sessions/{s['id']}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["message_count"] == 2  # user + assistant
    assert body["messages"][0]["role"] == "user"
    assert body["messages"][1]["role"] == "assistant"


def test_send_message_returns_assistant_reply(client):
    s = client.post("/sessions", json={"title": "chat"}).json()
    resp = client.post(f"/sessions/{s['id']}/messages", json={"message": "ping"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["role"] == "assistant"
    assert len(body["content"]) > 0
    assert body["provider"] in {"mock", "fallback"}


def test_send_message_to_missing_session(client):
    resp = client.post("/sessions/999/messages", json={"message": "hello"})
    assert resp.status_code == 404


def test_multi_turn_context_carried(client):
    s = client.post("/sessions", json={"title": "multi-turn"}).json()
    client.post(f"/sessions/{s['id']}/messages", json={"message": "My name is Atlas."})
    resp = client.post(f"/sessions/{s['id']}/messages", json={"message": "What did I just say?"})
    assert resp.status_code == 201
    # The mock provider echoes the prompt which includes history
    assert "Atlas" in resp.json()["content"]


def test_delete_session(client):
    s = client.post("/sessions", json={"title": "to delete"}).json()
    resp = client.delete(f"/sessions/{s['id']}")
    assert resp.status_code == 204
    assert client.get(f"/sessions/{s['id']}").status_code == 404


def test_delete_nonexistent_session(client):
    resp = client.delete("/sessions/999")
    assert resp.status_code == 404


def test_delete_cascades_messages(client):
    s = client.post("/sessions", json={"title": "cascade"}).json()
    client.post(f"/sessions/{s['id']}/messages", json={"message": "hi"})
    client.delete(f"/sessions/{s['id']}")
    resp = client.get("/sessions")
    ids = [x["id"] for x in resp.json()]
    assert s["id"] not in ids
