def test_chat_mock_reply(client):
    response = client.post("/chat", json={"message": "hello atlas"})
    assert response.status_code == 200
    body = response.json()
    assert "reply" in body
    assert "mock" in body["reply"].lower() or body["provider"] in {"mock", "cache"}
