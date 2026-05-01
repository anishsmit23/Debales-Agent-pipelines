# Debales AI Assistant

A LangGraph chatbot centered around Debales AI.

Routing rules:

- Debales queries -> local Debales RAG knowledge base.
- Non-Debales queries -> SerpAPI web search.
- Mixed queries -> both Debales RAG and SerpAPI.
- Unknown/no-context queries -> no hallucination fallback.

Company-relative wording is treated as Debales AI. For example, "you guys", "your services", "what do you provide", and "your company" all route to Debales RAG.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Add your keys to `.env`:

```env
GROQ_API_KEY=your_groq_api_key_here
SERPAPI_API_KEY=your_serpapi_key_here
```

`HF_TOKEN` is optional. It only helps Hugging Face downloads get higher rate limits.

The app reads configuration from `.env` through `settings.py`. Optional values:

```env
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_TEMPERATURE=0
USE_LLM_ROUTER=false
RAG_TOP_K=4
WEB_SEARCH_MAX_RESULTS=5
SERPAPI_ENGINE=google
SERPAPI_LOCATION=
SERPAPI_TIMEOUT=20
DEBALES_START_URLS=https://debales.ai/,https://debales.ai/blog,https://debales.ai/integrations
SCRAPER_MAX_PAGES=80
SCRAPER_DELAY_SECONDS=0.5
RAW_DIR=data/raw
CHROMA_DIR=chroma_db
CHROMA_COLLECTION=debales_ai_knowledge
EMBEDDING_MODEL=all-MiniLM-L6-v2
HF_TOKEN=
```

## Build The Debales AI Knowledge Base

Scrape Debales AI pages:

```bash
python -m scraper.scrape
```

Build the Chroma vector database:

```bash
python -m rag.ingest
```

This creates:

- `data/raw/*.txt`
- `chroma_db/`

If Debales questions return the no-context fallback, re-run:

```bash
python -m scraper.scrape
python -m rag.ingest
```

## Run The Chatbot

```bash
python main.py
```

## Tests

```bash
pytest
```

## Project Structure

```text
scraper/scrape.py      Scrapes Debales AI pages into text files
rag/ingest.py          Chunks, embeds, and stores content in Chroma
rag/retriever.py       Retrieves relevant Debales chunks
tools/serp_tool.py     SerpAPI search wrapper
agent/state.py         LangGraph state schema
agent/nodes.py         Router, RAG, SERP, aggregation, answer nodes
agent/graph.py         LangGraph workflow
main.py                CLI entry point
```

## Hallucination Guard

The answer node never calls the LLM without context. If RAG and SerpAPI both return no context, it returns:

```text
I don't have enough information to answer that based on available sources.
```
