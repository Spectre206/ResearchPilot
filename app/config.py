from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
CHROMA_DIR = DATA_DIR / "chroma"

MODEL_PROVIDER = "ollama"
MODEL_NAME = "qwen3:1.7b"          # or "phi4-mini"

EMBEDDING_MODEL_NAME = "nomic-embed-text"   # via Ollama

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K = 5