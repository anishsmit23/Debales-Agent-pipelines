import pytest

from agent.nodes import build_debales_search_query, classify_query


@pytest.mark.parametrize(
    "query",
    [
        "what are the services you guys provide",
        "what services do you provide",
        "what do you guys offer",
        "tell me about your company",
        "what are your integrations",
        "do you have pricing",
        "what features does your product have",
        "what does Debales AI do",
        "explain Debales AI agents",
    ],
)
def test_company_relative_and_explicit_debales_queries_route_to_debales(query):
    assert classify_query(query) == "debales"


@pytest.mark.parametrize(
    "query",
    [
        "what is the capital of France",
        "how does photosynthesis work",
        "who won the last world cup",
        "best way to learn python",
    ],
)
def test_general_queries_route_external(query):
    assert classify_query(query) == "external"


@pytest.mark.parametrize(
    "query",
    [
        "latest Debales AI news",
        "compare Debales AI with current logistics automation tools",
        "what are recent market alternatives to Debales AI",
    ],
)
def test_debales_queries_with_external_context_route_to_both(query):
    assert classify_query(query) == "both"


@pytest.mark.parametrize(
    "query",
    [
        "hello",
        "hello!",
        "hi",
        "thanks",
        "thank you",
        "bye",
        "good morning",
    ],
)
def test_simple_chitchat_routes_to_chitchat(query):
    assert classify_query(query) == "chitchat"


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("what services do you provide", "Debales AI what services do you provide"),
        ("tell me about your integrations", "Debales AI tell me about your integrations"),
        ("what is Debales AI", "what is Debales AI"),
        ("Explain DEBALES AI agents", "Explain DEBALES AI agents"),
    ],
)
def test_debales_search_query_augmentation(query, expected):
    assert build_debales_search_query(query) == expected


def test_llm_router_invalid_response_falls_back_to_external(monkeypatch):
    class FakeResponse:
        content = "not-a-route"

    class FakeLlm:
        def invoke(self, _prompt):
            return FakeResponse()

    monkeypatch.setattr("agent.nodes.get_llm", lambda: FakeLlm())

    assert classify_query("ambiguous unknown request", use_llm_router=True) == "external"


def test_llm_router_valid_response_is_used(monkeypatch):
    class FakeResponse:
        content = "debales"

    class FakeLlm:
        def invoke(self, _prompt):
            return FakeResponse()

    monkeypatch.setattr("agent.nodes.get_llm", lambda: FakeLlm())

    assert classify_query("tell me more", use_llm_router=True) == "debales"
