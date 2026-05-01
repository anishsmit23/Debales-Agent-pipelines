import os

from tools.serp_tool import search_web


def test_serpapi_missing_key_fails_closed(monkeypatch):
    monkeypatch.delenv("SERPAPI_API_KEY", raising=False)

    context, sources = search_web("latest logistics news")

    assert context.startswith("SERP API search failed:")
    assert sources == []


def test_serpapi_extracts_answer_box_and_organic_results(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "answer_box": {
                    "answer": "Paris",
                    "link": "https://example.com/paris",
                },
                "organic_results": [
                    {
                        "title": "France facts",
                        "link": "https://example.com/france",
                        "snippet": "France is a country in Europe.",
                    }
                ],
            }

    captured = {}

    def fake_get(url, params, timeout):
        captured["url"] = url
        captured["params"] = params
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setenv("SERPAPI_API_KEY", "test-key")
    monkeypatch.setattr("tools.serp_tool.requests.get", fake_get)

    context, sources = search_web("capital of France", max_results=3)

    assert captured["params"]["api_key"] == "test-key"
    assert captured["params"]["engine"] == os.getenv("SERPAPI_ENGINE", "google")
    assert captured["params"]["q"] == "capital of France"
    assert "SERP answer box" in context
    assert "France facts" in context
    assert sources == ["https://example.com/france", "https://example.com/paris"]
