# Debales AI Agent — Required Software & Pipeline Architecture
# (100% Free APIs — No Credit Card Required)

## Tech Stack Overview

| Layer | Tool / Library | Free Platform | Free Tier |
|---|---|---|---|
| Agent framework | `langgraph` | — (open source) | Unlimited |
| LLM | `langchain-groq` | **Groq** (llama-3.3-70b) | 14,400 req/day free |
| Embeddings | `sentence-transformers` | Runs locally, no API | Unlimited |
| Vector DB | `chromadb` | Runs locally | Unlimited |
| Web scraping | `requests` + `beautifulsoup4` | — (open source) | Unlimited |
| SERP | `duckduckgo-search` | DuckDuckGo (no key needed!) | Unlimited |
| Environment | `python-dotenv` | — (open source) | Unlimited |
| CLI UI | `rich` (optional) | — (open source) | Unlimited |

> Only one API key needed: **Groq** (free, instant signup, no card required)

---

## Required Python Packages

```
langgraph>=0.1.0
langchain>=0.2.0
langchain-groq>=0.1.0
langchain-community>=0.2.0
sentence-transformers>=3.0
chromadb>=0.5.0
requests>=2.31.0
beautifulsoup4>=4.12.0
duckduckgo-search>=6.0.0
python-dotenv>=1.0.0
rich>=13.0.0              # optional, for CLI
```

Install all at once:
```bash
pip install langgraph langchain langchain-groq langchain-community \
            sentence-transformers chromadb requests beautifulsoup4 \
            duckduckgo-search python-dotenv rich
```

---

## Required API Keys (`.env.example`)

```env
GROQ_API_KEY=your_groq_api_key_here
# No other keys needed!
```

Get your free Groq key (takes 1 minute, no card):
- Groq Console: https://console.groq.com → Sign up → API Keys → Create key
- Use model: `llama-3.3-70b-versatile` (best free option, very fast)

DuckDuckGo search requires NO API key at all.

---

## Pipeline Architecture

### Phase 1 — Setup (run once before the chatbot starts)

```
Debales AI Website
  └─ scraper.py (requests + BeautifulSoup)
        └─ Raw text content
              └─ text_splitter (RecursiveCharacterTextSplitter)
                    └─ Chunks (~500 tokens, 50 overlap)
                          └─ Embeddings (sentence-transformers, runs locally)
                                └─ Vector DB (ChromaDB, persisted to ./chroma_db)
```

Pages to scrape:
- `https://debales.ai/`
- `https://debales.ai/blog`  (and all blog post URLs found there)
- `https://debales.ai/integrations` (or equivalent product/integration pages)

### Phase 2 — Runtime (LangGraph workflow per user message)

```
User query
    │
    ▼
[Router Node]  ─── LLM or keyword-based classification
    │
    ├── "debales" ──────► [RAG Node] ── similarity_search(query, k=4)
    │                         │               from ChromaDB
    │                         ▼
    │                   Retrieved chunks
    │
    ├── "external" ─────► [SERP Node] ── SerpAPI.search(query)
    │                         │
    │                         ▼
    │                   Search result snippets
    │
    └── "both" ──────────► [RAG Node] + [SERP Node] (parallel)
                               │               │
                               └──────┬────────┘
                                      ▼
                             [Context Aggregator]
                                      │
                                      ▼
                             [LLM Answer Generator]
                              System prompt + context
                              + hallucination guard
                                      │
                                      ▼
                               Final response → CLI
```

---

## LangGraph Node Descriptions

### `router_node`
- Input: `state["query"]`
- Logic: Ask LLM (or use keyword matching) to classify query as `"debales"`, `"external"`, or `"both"`
- Output: `state["route"]`

### `rag_node`
- Input: `state["query"]`
- Logic: Embed query → search ChromaDB → return top-k chunks
- Output: `state["rag_context"]`

### `serp_node`
- Input: `state["query"]`
- Logic: Call DuckDuckGo search (no key needed) → extract result snippets
- Output: `state["serp_context"]`

### `aggregator_node`
- Input: `state["rag_context"]`, `state["serp_context"]`
- Logic: Concatenate available context; if both are empty → set `state["no_context"] = True`
- Output: `state["context"]`

### `answer_node`
- Input: `state["query"]`, `state["context"]`, `state["no_context"]`
- Logic: If `no_context` → return "I don't have enough information to answer that."
  Otherwise → call LLM with system prompt + context + query
- Output: `state["answer"]`

---

## State Schema (TypedDict)

```python
from typing import TypedDict, Optional

class AgentState(TypedDict):
    query: str
    route: Optional[str]          # "debales" | "external" | "both"
    rag_context: Optional[str]
    serp_context: Optional[str]
    context: Optional[str]
    no_context: bool
    answer: Optional[str]
```

---

## Project File Structure

```
debales-agent/
├── .env                    # API keys (not committed)
├── .env.example            # Template for API keys
├── requirements.txt        # All pip dependencies
├── README.md               # Setup + usage instructions
│
├── scraper/
│   └── scrape.py           # Scrape Debales AI pages → save text
│
├── rag/
│   ├── ingest.py           # Chunk + embed + store in ChromaDB
│   └── retriever.py        # similarity_search wrapper
│
├── tools/
│   └── serp_tool.py        # DuckDuckGo wrapper as LangGraph tool (no key needed)
│
├── agent/
│   ├── state.py            # AgentState TypedDict
│   ├── nodes.py            # All node functions
│   ├── graph.py            # Build + compile LangGraph graph
│   └── prompts.py          # System prompts
│
├── chroma_db/              # Persisted vector store (auto-created)
│
└── main.py                 # CLI entry point
```

---

## System Prompt (answer_node)

```
You are a helpful assistant for Debales AI.
Answer questions based ONLY on the provided context.
If the context does not contain enough information to answer the question,
say: "I don't have enough information to answer that based on available sources."
Do not make up facts or guess.

Context:
{context}
```

---

## Code Snippets for Free APIs

### LLM — Groq (drop-in, replaces OpenAI)
```python
from langchain_groq import ChatGroq

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0,
)
```

### Embeddings — sentence-transformers (fully local, no API)
```python
from langchain_community.embeddings import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2"  # fast, 80MB, downloads once
)
```

### SERP Tool — DuckDuckGo (no key needed)
```python
from duckduckgo_search import DDGS

def search_web(query: str) -> str:
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=5))
    snippets = [r["body"] for r in results if "body" in r]
    return "\n".join(snippets) if snippets else ""
```

---

## Routing Strategy (two options)

**Option A — LLM-based (more robust):**
```python
classification_prompt = """
Classify the following user query into one of three categories:
- "debales": question is about Debales AI (company, product, features, integrations, blog)
- "external": question is about something unrelated to Debales AI
- "both": question requires both Debales AI knowledge and external information

Query: {query}
Return only the category word.
"""
```

**Option B — Keyword-based (simpler, faster):**
```python
DEBALES_KEYWORDS = ["debales", "your product", "your company", "integration", "pricing"]

def classify(query: str) -> str:
    q = query.lower()
    if any(k in q for k in DEBALES_KEYWORDS):
        return "debales"
    return "external"
```

Start with Option B, upgrade to Option A if routing accuracy is poor.

---

## Hallucination Prevention Rules

1. The LLM system prompt must say "answer ONLY from context"
2. If `rag_context` is empty AND `serp_context` is empty → skip LLM, return hardcoded fallback
3. Never let the LLM respond without context being injected into the prompt
4. For RAG results: always check `len(docs) > 0` before passing to LLM

---

## Estimated Build Time

| Task | Time |
|---|---|
| Scraper + ingestion script | 45 min |
| RAG retriever | 30 min |
| SERP tool wrapper | 20 min |
| LangGraph nodes + graph | 60 min |
| CLI + prompt/response loop | 20 min |
| Testing + README | 30 min |
| **Total** | **~3.5 hours** |
