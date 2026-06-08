from unittest.mock import patch
from fastapi.testclient import TestClient

def test_chat_no_active_provider(client: TestClient):
    response = client.post("/api/v1/chat", json={"message": "hello"})
    assert response.status_code == 400
    assert "No active provider configured" in response.json()["detail"]

@patch("app.services.chat.run_rag")
@patch("app.services.chat.run_llm")
def test_chat_success(mock_llm, mock_rag, client: TestClient):
    # Setup active provider
    client.post("/api/v1/llm-providers", json={
        "name": "P1", "provider": "openai", "model": "gpt-4", "api_key": "k1"
    })
    # Manually activate it in DB since we mocked the connection test in other tests 
    # but here we can just use the endpoint if we mock the connection test again
    with patch("app.api.llm_providers.test_provider_connection") as mock_conn:
        mock_conn.return_value = (True, "OK")
        resp = client.get("/api/v1/llm-providers")
        p_id = resp.json()[0]["id"]
        client.post(f"/api/v1/llm-providers/{p_id}/activate")

    mock_rag.return_value = "Test RAG Context"
    mock_llm.return_value = "Hello from AI"
    
    response = client.post("/api/v1/chat", json={"message": "hello"})
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Hello from AI"
    assert "components" in data
    # "hello" should trigger suggestion chips
    assert data["components"][0]["type"] == "suggestion_chips"

@patch("app.services.chat.run_rag")
@patch("app.services.chat.run_llm")
def test_chat_with_components(mock_llm, mock_rag, client: TestClient):
    # Setup active provider
    client.post("/api/v1/llm-providers", json={
        "name": "P1", "provider": "openai", "model": "gpt-4", "api_key": "k1"
    })
    with patch("app.api.llm_providers.test_provider_connection") as mock_conn:
        mock_conn.return_value = (True, "OK")
        p_id = client.get("/api/v1/llm-providers").json()[0]["id"]
        client.post(f"/api/v1/llm-providers/{p_id}/activate")

    mock_rag.return_value = "Test RAG Context"
    mock_llm.return_value = "print('hello')"
    
    # Test "code" trigger
    response = client.post("/api/v1/chat", json={"message": "show me some code"})
    assert response.status_code == 200
    assert response.json()["components"][0]["type"] == "code_block"
    
    # Test "doc" trigger
    response = client.post("/api/v1/chat", json={"message": "search in docs"})
    assert response.status_code == 200
    assert response.json()["components"][0]["type"] == "citation_group"
    
    # Test "action" trigger
    response = client.post("/api/v1/chat", json={"message": "do some action"})
    assert response.status_code == 200
    assert response.json()["components"][0]["type"] == "action_buttons"
