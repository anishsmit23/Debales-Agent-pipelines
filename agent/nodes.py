from __future__ import annotations

import os

from langchain_groq import ChatGroq

from agent.prompts import ANSWER_SYSTEM_PROMPT, ROUTER_PROMPT
from agent.state import AgentState
from rag.retriever import retrieve_debales_context
from settings import env_bool, env_int, env_str
from tools.serp_tool import search_web


DEBALES_KEYWORDS = {
    "debales",
    "debales ai",
    "your company",
    "your product",
    "your services",
    "integration",
    "integrations",
    "pricing",
    "features",
    "blog",
}

EXTERNAL_HINTS = {
    "latest",
    "today",
    "current",
    "news",
    "compare",
    "alternative",
    "competitor",
    "market",
    "industry",
    "recent",
}


def get_llm() -> ChatGroq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is missing. Add it to .env before chatting.")
    return ChatGroq(
        model=env_str("GROQ_MODEL", "llama-3.3-70b-versatile"),
        api_key=api_key,
        temperature=float(env_str("GROQ_TEMPERATURE", "0")),
    )


def classify_query(query: str, use_llm_router: bool = False) -> str:
    q = query.lower()
    mentions_debales = any(keyword in q for keyword in DEBALES_KEYWORDS)
    needs_external = any(keyword in q for keyword in EXTERNAL_HINTS)

    if mentions_debales and needs_external:
        return "both"
    if mentions_debales:
        return "debales"

    if use_llm_router:
        llm = get_llm()
        result = llm.invoke(ROUTER_PROMPT.format(query=query)).content.strip().lower()
        if result in {"debales", "external", "both"}:
            return result

    return "external"


def router_node(state: AgentState) -> AgentState:
    use_llm_router = env_bool("USE_LLM_ROUTER", False)
    route = classify_query(state["query"], use_llm_router=use_llm_router)
    return {**state, "route": route}


def rag_node(state: AgentState) -> AgentState:
    context, sources = retrieve_debales_context(state["query"], k=env_int("RAG_TOP_K", 4))
    return {
        **state,
        "rag_context": context,
        "sources": sorted(set(state.get("sources", []) + sources)),
    }


def serp_node(state: AgentState) -> AgentState:
    context, sources = search_web(state["query"], max_results=env_int("WEB_SEARCH_MAX_RESULTS", 5))
    if context.startswith("Web search failed:"):
        context = ""
    return {
        **state,
        "serp_context": context,
        "sources": sorted(set(state.get("sources", []) + sources)),
    }


def aggregator_node(state: AgentState) -> AgentState:
    contexts = [
        context
        for context in [state.get("rag_context"), state.get("serp_context")]
        if context and context.strip()
    ]
    combined = "\n\n---\n\n".join(contexts)
    return {**state, "context": combined, "no_context": not bool(combined)}


def answer_node(state: AgentState) -> AgentState:
    if state.get("no_context"):
        return {
            **state,
            "answer": "I don't have enough information to answer that based on available sources.",
        }

    llm = get_llm()
    messages = [
        ("system", ANSWER_SYSTEM_PROMPT.format(context=state["context"])),
        ("human", state["query"]),
    ]
    response = llm.invoke(messages)
    return {**state, "answer": response.content}
