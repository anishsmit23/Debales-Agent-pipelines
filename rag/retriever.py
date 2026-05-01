from __future__ import annotations

import re
from pathlib import Path

from rag.config import CHROMA_DIR, COLLECTION_NAME, RAW_DIR
from rag.embeddings import get_embeddings
from rag.vectorstore import Chroma


def get_vectorstore(with_embeddings: bool = True) -> Chroma:
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=get_embeddings() if with_embeddings else None,
        persist_directory=str(CHROMA_DIR),
    )


def _query_terms(query: str) -> set[str]:
    stopwords = {
        "a",
        "an",
        "and",
        "are",
        "about",
        "ai",
        "for",
        "is",
        "me",
        "of",
        "the",
        "to",
        "what",
        "who",
    }
    return {
        term
        for term in re.findall(r"[a-z0-9]+", query.lower())
        if len(term) > 2 and term not in stopwords
    }


def _read_raw_page(path: Path) -> tuple[str, str, str]:
    text = path.read_text(encoding="utf-8", errors="ignore").strip()
    lines = text.splitlines()
    url = lines[0].replace("URL:", "", 1).strip() if lines and lines[0].startswith("URL:") else str(path)
    title = lines[1].replace("TITLE:", "", 1).strip() if len(lines) > 1 and lines[1].startswith("TITLE:") else path.stem
    return url, title, text


def retrieve_raw_debales_context(query: str, k: int = 3) -> tuple[str, list[str]]:
    raw_paths = sorted(RAW_DIR.glob("*.txt"))
    if not raw_paths:
        return "", []

    terms = _query_terms(query)
    scored_pages: list[tuple[int, Path, str, str, str]] = []
    for path in raw_paths:
        url, title, text = _read_raw_page(path)
        haystack = f"{path.stem} {title} {text}".lower()
        score = sum(haystack.count(term) for term in terms)
        if "debales" in query.lower() and path.name == "debales-ai.txt":
            score += 10
        if score > 0:
            scored_pages.append((score, path, url, title, text))

    homepage = RAW_DIR / "debales-ai.txt"
    if not scored_pages and "debales" in query.lower() and homepage.exists():
        url, title, text = _read_raw_page(homepage)
        scored_pages.append((1, homepage, url, title, text))

    if not scored_pages:
        return "", []

    chunks: list[str] = []
    sources: list[str] = []
    for index, (_score, _path, url, title, text) in enumerate(
        sorted(scored_pages, key=lambda page: page[0], reverse=True)[:k],
        start=1,
    ):
        sources.append(url)
        chunks.append(f"[Debales raw source {index}: {title}]\n{text[:3500]}")
    return "\n\n".join(chunks), sorted(set(sources))


def retrieve_debales_context(query: str, k: int = 4) -> tuple[str, list[str]]:
    try:
        try:
            count_store = get_vectorstore(with_embeddings=False)
            if count_store._collection.count() == 0:
                return retrieve_raw_debales_context(query, k=min(k, 3))
        except Exception:
            pass

        vectorstore = get_vectorstore()
        docs = vectorstore.similarity_search(query, k=k)
    except Exception:
        return retrieve_raw_debales_context(query, k=min(k, 3))

    if not docs:
        return retrieve_raw_debales_context(query, k=min(k, 3))

    chunks: list[str] = []
    sources: list[str] = []
    for index, doc in enumerate(docs, start=1):
        source = doc.metadata.get("source") or doc.metadata.get("path") or "Debales AI knowledge base"
        title = doc.metadata.get("title") or source
        sources.append(str(source))
        chunks.append(f"[Debales source {index}: {title}]\n{doc.page_content}")
    return "\n\n".join(chunks), sorted(set(sources))
