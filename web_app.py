from __future__ import annotations

import re
from time import perf_counter

from flask import Flask, jsonify, render_template, request

from main import ask


app = Flask(__name__)


ROUTE_LABELS = {
    "debales": ("rag", "RAG", "Debales AI knowledge base answered this query."),
    "external": ("serp", "SerpAPI", "External web search answered this query."),
    "both": ("both", "RAG + SerpAPI", "Debales knowledge and external search were both used."),
    "chitchat": ("direct", "Direct", "Simple conversation handled without retrieval."),
}


def clean_ui_answer(text: str) -> str:
    text = re.sub(r"(?m)^\s{0,3}#{1,6}\s+", "", text)
    text = re.sub(r"(?m)\s+#{1,6}\s*$", "", text)
    return text.strip()


def build_trace(result: dict, elapsed_ms: int) -> list[dict]:
    route = result.get("route") or "external"
    trace = [{"label": "Router", "desc": f"Classified query as {route}.", "state": "done"}]

    if route in {"debales", "both"}:
        trace.append({"label": "RAG Node", "desc": "Retrieved Debales AI knowledge-base context.", "state": "done"})
    if route in {"external", "both"}:
        trace.append({"label": "SerpAPI Node", "desc": "Fetched external search context.", "state": "done"})
    if route != "chitchat":
        trace.append({"label": "Aggregator", "desc": "Combined available context and checked no-context guard.", "state": "done"})

    trace.append({"label": "Answer Node", "desc": f"Generated final response in {elapsed_ms} ms.", "state": "done"})
    return trace


def shape_response(result: dict, elapsed_ms: int) -> dict:
    route = result.get("route") or "external"
    source, label, reason = ROUTE_LABELS.get(route, ROUTE_LABELS["external"])
    if result.get("no_context"):
        source = "none"
        label = "No Context"
        reason = "No usable RAG or SerpAPI context was available, so the fallback was returned."

    context_parts = []
    if result.get("rag_context"):
        context_parts.append({"label": "Debales RAG context", "text": result["rag_context"]})
    if result.get("serp_context"):
        context_parts.append({"label": "SerpAPI context", "text": result["serp_context"]})
    if result.get("serp_error"):
        context_parts.append({"label": "SerpAPI error", "text": result["serp_error"]})
    if result.get("sources"):
        context_parts.append({"label": "Sources", "text": "\n".join(result["sources"])})

    return {
        "answer": clean_ui_answer(
            result.get("answer") or "I don't have enough information to answer that based on available sources."
        ),
        "source": source,
        "context": context_parts,
        "trace": build_trace(result, elapsed_ms),
        "decision": {"route": label, "color": source, "reason": reason},
    }


@app.get("/")
def index():
    return render_template("chat.html")


@app.post("/api/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    query = str(payload.get("message", "")).strip()
    if not query:
        return jsonify({"error": "Message is required."}), 400

    start = perf_counter()
    result = ask(query)
    elapsed_ms = int((perf_counter() - start) * 1000)
    return jsonify(shape_response(result, elapsed_ms))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
