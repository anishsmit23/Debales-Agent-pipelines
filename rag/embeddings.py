import warnings

from rag.config import EMBEDDING_MODEL

try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:  # pragma: no cover
    warnings.filterwarnings(
        "ignore",
        message=r"The class `HuggingFaceEmbeddings` was deprecated.*",
        category=Warning,
    )
    from langchain_community.embeddings import HuggingFaceEmbeddings


def get_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
