import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from main import ask


class FakeResponse:
    def __init__(self, content: str):
        self.content = content


class FakeLlm:
    def __init__(self):
        self.messages = []

    def invoke(self, messages):
        self.messages.append(messages)
        rendered = str(messages)
        if "Debales source" in rendered and "SERP source" in rendered:
            return FakeResponse("Combined answer from Debales RAG and SerpAPI.")
        if "Debales source" in rendered:
            return FakeResponse("Answer from Debales RAG.")
        if "SERP source" in rendered:
            return FakeResponse("Answer from SerpAPI.")
        return FakeResponse("Unexpected answer.")


def test_chitchat_conversation_skips_rag_serp_and_llm(monkeypatch):
    def fail_rag(*_args, **_kwargs):
        raise AssertionError("RAG should not run for chitchat.")

    def fail_serp(*_args, **_kwargs):
        raise AssertionError("SerpAPI should not run for chitchat.")

    def fail_llm():
        raise AssertionError("LLM should not run for chitchat.")

    monkeypatch.setattr("agent.nodes.retrieve_debales_context", fail_rag)
    monkeypatch.setattr("agent.nodes.search_web", fail_serp)
    monkeypatch.setattr("agent.nodes.get_llm", fail_llm)

    result = ask("hello")

    assert result["route"] == "chitchat"
    assert "Debales AI Assistant" in result["answer"]
    assert result["sources"] == []


def test_debales_conversation_uses_rag_only(monkeypatch):
    fake_llm = FakeLlm()
    calls = {"rag": 0, "serp": 0}

    def fake_rag(query, k):
        calls["rag"] += 1
        assert query.startswith("Debales AI ")
        return (
            "[Debales source 1: Homepage]\nDebales AI provides logistics AI agents.",
            ["https://debales.ai/"],
        )

    def fake_serp(*_args, **_kwargs):
        calls["serp"] += 1
        return "[SERP source]\nShould not be used.", ["https://example.com"]

    monkeypatch.setattr("agent.nodes.retrieve_debales_context", fake_rag)
    monkeypatch.setattr("agent.nodes.search_web", fake_serp)
    monkeypatch.setattr("agent.nodes.get_llm", lambda: fake_llm)

    result = ask("what services do you provide")

    assert result["route"] == "debales"
    assert result["answer"] == "Answer from Debales RAG."
    assert result["sources"] == ["https://debales.ai/"]
    assert calls == {"rag": 1, "serp": 0}


def test_external_conversation_uses_serpapi_only(monkeypatch):
    fake_llm = FakeLlm()
    calls = {"rag": 0, "serp": 0}

    def fake_rag(*_args, **_kwargs):
        calls["rag"] += 1
        return "[Debales source]\nShould not be used.", ["https://debales.ai/"]

    def fake_serp(query, max_results):
        calls["serp"] += 1
        assert query == "what is the capital of France"
        return (
            "[SERP source 1: Capital]\nURL: https://example.com/france\nParis is the capital.",
            ["https://example.com/france"],
        )

    monkeypatch.setattr("agent.nodes.retrieve_debales_context", fake_rag)
    monkeypatch.setattr("agent.nodes.search_web", fake_serp)
    monkeypatch.setattr("agent.nodes.get_llm", lambda: fake_llm)

    result = ask("what is the capital of France")

    assert result["route"] == "external"
    assert result["answer"] == "Answer from SerpAPI."
    assert result["sources"] == ["https://example.com/france"]
    assert calls == {"rag": 0, "serp": 1}


def test_mixed_conversation_uses_rag_and_serpapi(monkeypatch):
    fake_llm = FakeLlm()
    calls = {"rag": 0, "serp": 0}

    def fake_rag(query, k):
        calls["rag"] += 1
        assert "Debales AI" in query
        return (
            "[Debales source 1: Integrations]\nDebales AI integrates with logistics systems.",
            ["https://debales.ai/integrations"],
        )

    def fake_serp(query, max_results):
        calls["serp"] += 1
        assert query == "compare Debales AI with current logistics automation tools"
        return (
            "[SERP source 1: Market]\nURL: https://example.com/market\nCurrent market context.",
            ["https://example.com/market"],
        )

    monkeypatch.setattr("agent.nodes.retrieve_debales_context", fake_rag)
    monkeypatch.setattr("agent.nodes.search_web", fake_serp)
    monkeypatch.setattr("agent.nodes.get_llm", lambda: fake_llm)

    result = ask("compare Debales AI with current logistics automation tools")

    assert result["route"] == "both"
    assert result["answer"] == "Combined answer from Debales RAG and SerpAPI."
    assert result["sources"] == ["https://debales.ai/integrations", "https://example.com/market"]
    assert calls == {"rag": 1, "serp": 1}


def test_unknown_external_conversation_does_not_hallucinate_when_serpapi_fails(monkeypatch):
    def fail_llm():
        raise AssertionError("LLM should not run without context.")

    monkeypatch.setattr(
        "agent.nodes.search_web",
        lambda *_args, **_kwargs: ("SERP API search failed: SERPAPI_API_KEY is missing.", []),
    )
    monkeypatch.setattr("agent.nodes.get_llm", fail_llm)

    result = ask("who is the CEO of some unknown company")

    assert result["route"] == "external"
    assert result["no_context"] is True
    assert "I don't have enough information" in result["answer"]
    assert "SERPAPI_API_KEY is missing" in result["answer"]
