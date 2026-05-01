from __future__ import annotations

import warnings

try:
    from langchain_chroma import Chroma
except ImportError:  # pragma: no cover
    warnings.filterwarnings(
        "ignore",
        message=r"The class `Chroma` was deprecated.*",
        category=Warning,
    )
    from langchain_community.vectorstores import Chroma


__all__ = ["Chroma"]
