import hashlib
import re
import shutil
from pathlib import Path

from utils.file_loader import PDFLoader
from rag.chunker import TextChunker
from rag.embeddings import EmbeddingModel
from rag.library import Library
from rag.vector_store import VectorStore

from config import UPLOAD_FOLDER


def default_title(file_name):
    """'ITN_Module_2.pdf' -> 'ITN Module 2'"""

    stem = Path(file_name).stem.replace("_", " ")

    return re.sub(r"\s+", " ", stem).strip() or "Untitled"


def _safe_name(file_name):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", Path(file_name).name)


class DocumentService:
    """
    Adds PDFs to a subject of the library and removes them again.

    Pipeline: hash -> save file -> extract pages -> chunk -> library row
    -> embed -> store chunks (tagged with doc_id) in ChromaDB.
    """

    def __init__(self):

        self.library = Library()
        self.loader = PDFLoader()
        self.chunker = TextChunker()
        self._embedding_model = None
        self.vector_store = VectorStore()

    @property
    def embedding_model(self):
        """Loaded on first use (deleting documents does not need it)."""
        if self._embedding_model is None:
            self._embedding_model = EmbeddingModel()

        return self._embedding_model

    # ------------------------------------------------------
    # Adding
    # ------------------------------------------------------

    def add_pdf(
        self,
        subject_id,
        file_name,
        data,
        title=None,
        progress=None
    ):
        """
        Add one PDF (bytes) to a subject.

        progress: optional function(message) called at every stage.
        """

        def report(message):
            if progress:
                progress(message)

        file_path = None
        doc_id = None

        try:

            file_hash = hashlib.sha256(data).hexdigest()

            existing = self.library.find_by_hash(subject_id, file_hash)

            if existing:
                return {
                    "success": False,
                    "duplicate": True,
                    "message": (
                        f'"{file_name}" is already in this subject '
                        f'(as "{existing["title"]}").'
                    )
                }

            upload_dir = Path(UPLOAD_FOLDER) / str(subject_id)
            upload_dir.mkdir(parents=True, exist_ok=True)

            file_path = upload_dir / f"{file_hash[:8]}_{_safe_name(file_name)}"
            file_path.write_bytes(data)

            report("Extracting text")

            pages = self.loader.extract_pages(str(file_path))
            page_count = self.loader.page_count

            report(f"Splitting {len(pages)} pages into chunks")

            pieces = []

            for page in pages:
                for text in self.chunker.split_text(page["text"]):
                    pieces.append((page["page"], text))

            if not pieces:
                file_path.unlink(missing_ok=True)
                return {
                    "success": False,
                    "message": (
                        f'No text could be extracted from "{file_name}". '
                        "Scanned PDFs (images) are not supported."
                    )
                }

            doc_id = self.library.add_document(
                subject_id=subject_id,
                title=title or default_title(file_name),
                file_name=file_name,
                file_path=file_path,
                file_hash=file_hash,
                pages=page_count,
                chunks=len(pieces)
            )

            report(f"Creating embeddings for {len(pieces)} chunks")

            texts = [text for _, text in pieces]
            embeddings = self.embedding_model.encode(texts)

            report("Saving to the library")

            self.vector_store.add_documents(
                ids=[f"doc{doc_id}_chunk{i}" for i in range(len(pieces))],
                embeddings=embeddings.tolist(),
                documents=texts,
                metadatas=[
                    {
                        "doc_id": doc_id,
                        "subject_id": subject_id,
                        "page": page_number,
                        "chunk_index": i
                    }
                    for i, (page_number, _) in enumerate(pieces)
                ]
            )

            return {
                "success": True,
                "doc_id": doc_id,
                "title": title or default_title(file_name),
                "pages": page_count,
                "chunks": len(pieces)
            }

        except Exception as e:

            # Roll back a half-finished import
            if doc_id is not None:
                try:
                    self.vector_store.delete_document(doc_id)
                    self.library.delete_document(doc_id)
                except Exception:
                    pass

            if file_path is not None:
                Path(file_path).unlink(missing_ok=True)

            return {
                "success": False,
                "message": f'Could not process "{file_name}": {e}'
            }

    # ------------------------------------------------------
    # Removing
    # ------------------------------------------------------

    def _remove_files(self, document):

        path = document.get("file_path")

        if path:
            Path(path).unlink(missing_ok=True)

    def delete_document(self, doc_id):

        document = self.library.get_document(doc_id)

        if document is None:
            return

        self.vector_store.delete_document(doc_id)
        self.library.delete_document(doc_id)
        self._remove_files(document)

    def delete_subject(self, subject_id):

        for document in self.library.list_documents(subject_id):
            self.vector_store.delete_document(document["id"])
            self._remove_files(document)

        self.library.delete_subject(subject_id)

        shutil.rmtree(Path(UPLOAD_FOLDER) / str(subject_id), ignore_errors=True)
