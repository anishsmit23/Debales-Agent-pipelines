from __future__ import annotations

import argparse
from pathlib import Path

from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag.config import CHROMA_DIR, COLLECTION_NAME, RAW_DIR
from rag.embeddings import get_embeddings


def load_raw_documents(raw_dir: Path = RAW_DIR) -> list[Document]:
    documents: list[Document] = []
    for path in sorted(raw_dir.glob("*.txt")):
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            continue

        source_url = ""
        title = path.stem
        lines = text.splitlines()
        if lines and lines[0].startswith("URL:"):
            source_url = lines[0].replace("URL:", "", 1).strip()
        if len(lines) > 1 and lines[1].startswith("TITLE:"):
            title = lines[1].replace("TITLE:", "", 1).strip()

        documents.append(
            Document(
                page_content=text,
                metadata={"source": source_url or str(path), "title": title, "path": str(path)},
            )
        )
    return documents


def split_documents(documents: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1800,
        chunk_overlap=180,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_documents(documents)


def ingest(raw_dir: Path = RAW_DIR, chroma_dir: Path = CHROMA_DIR) -> int:
    documents = load_raw_documents(raw_dir)
    if not documents:
        raise RuntimeError(f"No .txt documents found in {raw_dir}. Run scraper/scrape.py first.")

    chunks = split_documents(documents)
    embeddings = get_embeddings()

    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(chroma_dir),
    )
    vectorstore.delete_collection()
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=str(chroma_dir),
    )
    vectorstore.persist()
    return len(chunks)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Debales AI Chroma vector database.")
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--chroma-dir", type=Path, default=CHROMA_DIR)
    args = parser.parse_args()

    count = ingest(raw_dir=args.raw_dir, chroma_dir=args.chroma_dir)
    print(f"Ingested {count} chunks into {args.chroma_dir}")


if __name__ == "__main__":
    main()
