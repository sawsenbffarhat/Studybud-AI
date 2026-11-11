import os
from dotenv import load_dotenv

# ==========================================================
# Load Environment Variables
# ==========================================================
load_dotenv()

# ==========================================================
# Application
# ==========================================================
APP_NAME = "Studybud AI"
APP_VERSION = "1.1.0"

# ==========================================================
# AI Providers
# ==========================================================
DEFAULT_PROVIDER = "auto"

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# ==========================================================
# Models (both can be overridden from .env / Streamlit secrets)
# ==========================================================
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "google/gemma-4-26b-a4b-it:free"
)

# ==========================================================
# Library (subjects and documents) + ChromaDB
# ==========================================================
# SQLite file that stores subjects and documents (permanent, survives restarts)
LIBRARY_DB_PATH = "data/library.db"

# ONE persistent collection for every chunk of every document.
# Each chunk is tagged with its doc_id, so searches can be limited to
# a subject or to chosen chapters.
CHROMA_DB_PATH = "data/chroma_db"
COLLECTION_NAME = "studymate_library"

# ==========================================================
# Embeddings
# ==========================================================
# Multilingual (English + French). Changing this model requires running
# `python reindex.py` once, because old vectors are not comparable.
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# ==========================================================
# Upload Settings
# ==========================================================
UPLOAD_FOLDER = "data/uploads"

SUPPORTED_FILE_TYPES = [
    "pdf"
]

# Enforced through .streamlit/config.toml (server.maxUploadSize)
MAX_UPLOAD_SIZE_MB = 50

# ==========================================================
# Text Chunking (used by rag/chunker.py)
# ==========================================================
# Smaller chunks: the multilingual model reads only ~128 tokens per chunk.
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

# ==========================================================
# Retrieval / Context Settings
# ==========================================================
# Chunks retrieved for Ask AI
RETRIEVAL_TOP_K = 6

# Extra exact-match hits (a word or short sentence) added to Ask AI results
KEYWORD_HITS = 4

# Summaries of several chapters: at most this many documents at once,
# each one is condensed first (SUMMARY_DOC_CHARS characters) and then combined.
MAX_SUMMARY_DOCS = 8
SUMMARY_DOC_CHARS = 8000

# Max characters of lecture text sent to the LLM for summary / quiz / reflection.
# Long documents are sampled evenly instead of being cut off after the start.
# (~12,000 chars is roughly 3,000 tokens, which fits free-tier limits.)
MAX_CONTEXT_CHARS = 12000

# ==========================================================
# UI Settings
# ==========================================================
SIDEBAR_STATE = "expanded"

LAYOUT = "wide"

# ==========================================================
# Theme Colors
# ==========================================================
PRIMARY_COLOR = "#2563EB"

SUCCESS_COLOR = "#16A34A"

WARNING_COLOR = "#F59E0B"

ERROR_COLOR = "#DC2626"

BACKGROUND_COLOR = "#FFFFFF"

SIDEBAR_COLOR = "#F8FAFC"

BORDER_COLOR = "#E5E7EB"

TEXT_COLOR = "#111827"

# ==========================================================
# Session Keys
# ==========================================================
SESSION_MESSAGES = "messages"

SESSION_QUIZ = "quiz"

SESSION_SUMMARY = "summary_result"

SESSION_REFLECTION = "reflection_result"