from langchain_community.embeddings import HuggingFaceEmbeddings

from rag.config import EMBEDDING_MODEL


def get_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
