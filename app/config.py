import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# LLM
GROQ_API_KEY = os.getenv("GROQ_API_KEY", '')
GROQ_MODEL = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')

# Embeddings
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
GEMINI_EMBEDDING_MODEL = os.getenv('GEMINI_EMBEDDING_MODEL', 'models/gemini-embedding-2-preview')

# Storge Paths
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR =  Path(os.getenv("UPLOAD_DIR", str(BASE_DIR / 'uploads')))
CHROMA_PERSIST_DIR = Path(os.getenv("CHROMA_PERSIST_DIR", str(BASE_DIR/ "data" / "chroma")))

# Creates the directory if it doesn't exist
UPLOAD_DIR.mkdir(parents = True, exist_ok = True)

# For chunking
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 500))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 50))
TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", 5))

# Extensions to entertain
ALLOWED_EXTENSIONS = {'.pdf', '.txt', '.epub'}