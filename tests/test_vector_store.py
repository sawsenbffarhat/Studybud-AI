"""Add a PDF to a throw-away subject, search it, then delete everything again.

Run from the project folder:  python -m tests.test_vector_store
"""

from rag.library import Library
from rag.vector_store import VectorStore
from services.document_service import DocumentService

PDF = "data/uploads/lecture1.pdf"

library = Library()
service = DocumentService()

subject_id = library.create_subject("__test__")

try:

    with open(PDF, "rb") as f:
        result = service.add_pdf(subject_id, "lecture1.pdf", f.read())

    print(result)

    store = VectorStore()
    doc_ids = [d["id"] for d in library.list_documents(subject_id)]

    hits = store.search("What is this lecture about?", n_results=3, doc_ids=doc_ids)

    for text, meta in zip(hits["documents"], hits["metadatas"]):
        print(f"\n[page {meta.get('page')}] {text[:200]}")

    print("\nVector store works")

finally:
    service.delete_subject(subject_id)
