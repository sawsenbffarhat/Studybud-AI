"""
Measure retrieval quality (hit rate @ k) on questions you wrote yourself.

1. Copy tests/eval_questions.example.json to tests/eval_questions.json
2. For every question put a keyword/phrase that MUST appear in the
   chunk that answers it ("expected_keyword").
3. Run:
      python -m tests.eval_retrieval data/uploads/lecture1.pdf tests/eval_questions.json

The PDF is added to a temporary subject, evaluated, and removed again, so
your real library is not touched.

A question is a "hit" when at least one of the top-k retrieved chunks
contains its expected_keyword (case-insensitive).
"""

import json
import sys

from rag.library import Library
from rag.vector_store import VectorStore
from services.document_service import DocumentService

K_VALUES = (1, 3, 6)


def main(pdf_path, questions_path):

    with open(questions_path, encoding="utf-8") as f:
        questions = json.load(f)

    library = Library()
    service = DocumentService()

    subject_id = library.create_subject("__eval__")

    try:

        with open(pdf_path, "rb") as f:
            info = service.add_pdf(subject_id, "eval.pdf", f.read())

        if not info["success"]:
            sys.exit(info["message"])

        print(f"Indexed {info['chunks']} chunks from {info['pages']} pages\n")

        store = VectorStore()
        doc_ids = [d["id"] for d in library.list_documents(subject_id)]

        hits = {k: 0 for k in K_VALUES}

        for item in questions:

            results = store.search(
                item["question"], n_results=max(K_VALUES), doc_ids=doc_ids
            )
            keyword = item["expected_keyword"].lower()

            for k in K_VALUES:
                if any(keyword in doc.lower() for doc in results["documents"][:k]):
                    hits[k] += 1

        print(f"Questions: {len(questions)}")

        for k in K_VALUES:
            print(f"Hit rate @ {k}: {hits[k] / len(questions):.0%}")

    finally:
        service.delete_subject(subject_id)


if __name__ == "__main__":

    if len(sys.argv) != 3:
        sys.exit("Usage: python -m tests.eval_retrieval <pdf> <questions.json>")

    main(sys.argv[1], sys.argv[2])
