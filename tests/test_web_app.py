from web_app import app, clean_ui_answer


def test_chat_api_requires_message():
    client = app.test_client()

    response = client.post("/api/chat", json={"message": ""})

    assert response.status_code == 400
    assert response.get_json()["error"] == "Message is required."


def test_chat_api_returns_ui_contract(monkeypatch):
    def fake_ask(_query):
        return {
            "route": "debales",
            "rag_context": "[Debales source]\nContext",
            "serp_context": None,
            "serp_error": None,
            "context": "[Debales source]\nContext",
            "no_context": False,
            "answer": "Debales AI answer.",
            "sources": ["https://debales.ai/"],
        }

    monkeypatch.setattr("web_app.ask", fake_ask)
    client = app.test_client()

    response = client.post("/api/chat", json={"message": "what services do you provide"})
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["answer"] == "Debales AI answer."
    assert payload["source"] == "rag"
    assert payload["decision"]["route"] == "RAG"
    assert payload["context"][0]["label"] == "Debales RAG context"
    assert payload["trace"][0]["label"] == "Router"


def test_clean_ui_answer_removes_markdown_heading_hashes():
    assert clean_ui_answer("### Contacting Our Team\nEmail us.") == "Contacting Our Team\nEmail us."
