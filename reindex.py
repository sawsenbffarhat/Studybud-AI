"""Rebuild every vector in ChromaDB from the saved PDFs (data/uploads).

Run this ONCE after changing EMBEDDING_MODEL or CHUNK_SIZE / CHUNK_OVERLAP.
Stop the app and back up the data/ folder first:

    python reindex.py
"""

from rag.library import Library
from rag.vector_store import VectorStore
from rag.embeddings import EmbeddingModel
from rag.chunker import TextChunker
from utils.file_loader import PDFLoader

library, store = Library(), VectorStore()
model, chunker, loader = EmbeddingModel(), TextChunker(), PDFLoader()

for d in library.list_documents():
    pages = loader.extract_pages(d["file_path"])
    pieces = [(p["page"], t) for p in pages for t in chunker.split_text(p["text"])]
    texts = [t for _, t in pieces]

    store.delete_document(d["id"])          # remove old vectors
    store.add_documents(
        ids=[f"doc{d['id']}_chunk{i}" for i in range(len(pieces))],
        embeddings=model.encode(texts).tolist(),
        documents=texts,
        metadatas=[
            {"doc_id": d["id"], "subject_id": d["subject_id"],
             "page": page, "chunk_index": i}
            for i, (page, _) in enumerate(pieces)
        ],
    )
    library.update_chunk_count(d["id"], len(pieces))
    print("Re-indexed:", d["subject"], "/", d["title"], len(pieces), "chunks")

print("Done.")