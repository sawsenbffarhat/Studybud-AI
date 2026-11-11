"""Check how a sentence is turned into subject + chapters (no AI, no internet).

Run from the project folder:  python -m tests.test_scope
"""

import tempfile
from pathlib import Path

from rag.library import Library
from services.scope_service import ScopeResolver

with tempfile.TemporaryDirectory() as folder:

    library = Library(Path(folder) / "test.db")

    math = library.create_subject("Math")
    science = library.create_subject("Science")

    for number in (1, 2, 10):
        library.add_document(math, f"Chapter {number}", f"c{number}.pdf", "", f"h{number}", 5, 10)

    library.add_document(science, "ITN Module 2", "m2.pdf", "", "hm2", 5, 10)

    resolver = ScopeResolver(library)

    def labels(prompt):
        result = resolver.resolve(prompt)
        return result["label"] if result["ok"] else "ERROR"

    assert labels("I need a summary for chapter 1 of subject math") == "Math: Chapter 1"
    assert labels("chapter 10 of math") == "Math: Chapter 10"
    assert labels("chapters 1 and 2 in math") == "Math: Chapter 1, Chapter 2"
    assert labels("chapters 1 to 2 of math") == "Math: Chapter 1, Chapter 2"
    assert labels("the whole math subject") == "Math (all 3 documents)"
    assert labels("summarize module 2 of science") == "Science: ITN Module 2"
    assert labels("resume du chapitre 2 de math") == "Math: Chapter 2"
    assert labels("chapter 7 of math") == "ERROR"

    print("Scope resolver works")
