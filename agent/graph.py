from __future__ import annotations

from langgraph.graph import END, StateGraph

from agent.nodes import aggregator_node, answer_node, rag_node, router_node, serp_node
from agent.state import AgentState


def route_after_router(state: AgentState) -> str:
    route = state.get("route") or "external"
    if route == "chitchat":
        return "answer"
    if route == "debales":
        return "rag"
    if route == "both":
        return "rag_for_both"
    return "serp"


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("router", router_node)
    graph.add_node("rag", rag_node)
    graph.add_node("serp", serp_node)
    graph.add_node("aggregator", aggregator_node)
    graph.add_node("answer", answer_node)

    graph.set_entry_point("router")
    graph.add_conditional_edges(
        "router",
        route_after_router,
        {
            "rag": "rag",
            "serp": "serp",
            "rag_for_both": "rag",
            "answer": "answer",
        },
    )
    graph.add_conditional_edges(
        "rag",
        lambda state: "serp" if state.get("route") == "both" else "aggregator",
        {"serp": "serp", "aggregator": "aggregator"},
    )
    graph.add_edge("serp", "aggregator")
    graph.add_edge("aggregator", "answer")
    graph.add_edge("answer", END)
    return graph.compile()


app = build_graph()
