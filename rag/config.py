from settings import PROJECT_ROOT, env_path, env_str


DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = env_path("RAW_DIR", DATA_DIR / "raw")
CHROMA_DIR = env_path("CHROMA_DIR", PROJECT_ROOT / "chroma_db")
COLLECTION_NAME = env_str("CHROMA_COLLECTION", "debales_ai_knowledge")
EMBEDDING_MODEL = env_str("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
