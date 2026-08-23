import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
CHROMA_DIR = DATA_DIR / "chroma"

# LLM Provider: "ollama" or "groq"
MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "groq")

# Ollama settings
OLLAMA_MODEL_NAME = "qwen3:1.7b"
EMBEDDING_MODEL_NAME = "nomic-embed-text"

# Groq settings
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL_NAME = "qwen/qwen3.6-27b"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K = 5