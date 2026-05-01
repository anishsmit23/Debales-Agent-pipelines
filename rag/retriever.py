from __future__ import annotations

from langchain_community.vectorstores import Chroma

from rag.config import CHROMA_DIR, COLLECTION_NAME
from rag.embeddings import get_embeddings


def get_vectorstore() -> Chroma:
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=get_embeddings(),
        persist_directory=str(CHROMA_DIR),
    )


def retrieve_debales_context(query: str, k: int = 4) -> tuple[str, list[str]]:
    vectorstore = get_vectorstore()
    docs = vectorstore.similarity_search(query, k=k)
    if not docs:
        return "", []

    chunks: list[str] = []
    sources: list[str] = []
    for index, doc in enumerate(docs, start=1):
        source = doc.metadata.get("source") or doc.metadata.get("path") or "Debales AI knowledge base"
        title = doc.metadata.get("title") or source
        sources.append(str(source))
        chunks.append(f"[Debales source {index}: {title}]\n{doc.page_content}")
    return "\n\n".join(chunks), sorted(set(sources))
