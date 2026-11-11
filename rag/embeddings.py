from functools import lru_cache

from sentence_transformers import SentenceTransformer

from config import EMBEDDING_MODEL


@lru_cache(maxsize=1)
def _load_model(model_name):
    """Load the model once per process (not on every Streamlit rerun)."""
    return SentenceTransformer(model_name)


class EmbeddingModel:
    """
    Generates vector embeddings
    for text chunks.
    """

    def __init__(self):
        self.model = _load_model(EMBEDDING_MODEL)

    def encode(self, texts):
        return self.model.encode(texts, show_progress_bar=False)
