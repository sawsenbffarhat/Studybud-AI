from rag.library import Library
from rag.vector_store import VectorStore
from agents.ai_provider import AIProvider
from utils.language import language_instruction

from config import KEYWORD_HITS, RETRIEVAL_TOP_K


class ChatService:

    def __init__(self):

        self.library = Library()
        self.vector_store = VectorStore()
        self.ai_provider = AIProvider()

    # ------------------------------------------------------
    # Step 1: retrieve + build prompt (no LLM call yet)
    # ------------------------------------------------------

    def _retrieve(self, question, doc_ids):
        """
        Hybrid search:
        1. exact matches of a word / short sentence (never missed),
        2. semantic matches (meaning), to fill up the rest.
        """

        exact = self.vector_store.keyword_search(
            question, doc_ids=doc_ids, limit=KEYWORD_HITS
        )

        semantic = self.vector_store.search(
            question, n_results=RETRIEVAL_TOP_K, doc_ids=doc_ids
        )

        merged = []
        seen = set()

        for result in (exact, semantic):
            for chunk_id, text, meta in zip(
                result["ids"], result["documents"], result["metadatas"]
            ):
                if chunk_id in seen:
                    continue
                seen.add(chunk_id)
                merged.append((text, meta or {}))

        return merged[: RETRIEVAL_TOP_K + 2]

    def prepare(self, question, language="English", doc_ids=None):
        """Retrieve the relevant chunks and build the prompt."""

        try:

            if not self.library.list_documents():
                return {
                    "success": False,
                    "message": "Your library is empty. Create a subject and add PDFs in the Library page first."
                }

            if doc_ids is not None and len(doc_ids) == 0:
                return {
                    "success": False,
                    "message": "There are no documents in this subject yet."
                }

            hits = self._retrieve(question, doc_ids)

            if not hits:
                return {
                    "success": False,
                    "message": "I couldn't find anything about this in your library."
                }

            names = self.library.documents_by_ids(
                {meta.get("doc_id") for _, meta in hits}
            )

            blocks = []
            sources = []

            for i, (text, meta) in enumerate(hits, start=1):

                document = names.get(meta.get("doc_id"), {})
                subject = document.get("subject", "")
                title = document.get("title", "")
                page = meta.get("page")

                where = f"{subject} / {title}" if subject else f"Source {i}"
                label = f"[{where}, page {page}]" if page else f"[{where}]"

                blocks.append(f"{label}\n{text}")

                sources.append({
                    "text": text,
                    "page": page,
                    "document": title,
                    "subject": subject
                })

            context = "\n\n-----------------------------\n\n".join(blocks)

            prompt = f"""
You are Studybud AI.

You are helping a university student prepare for exams.

Use ONLY the lecture notes below. They come from the student's own library
(subjects and chapters).

Rules:

1. Answer ONLY using the notes.

2. If the answer is only partially available,
say:

"According to the uploaded lecture notes..." (translate this sentence into the answer language)

3. Never invent information.

4. Never use outside knowledge.

5. If the answer is genuinely unavailable, reply:

"I couldn't find this information in the uploaded lecture notes." (translate this sentence into the answer language)

6. {language_instruction(language)}

7. Use headings where appropriate.

8. Use bullet points whenever possible.

9. Highlight important exam points.

10. Keep the answer clear and easy to understand.

11. Each note block starts with a label like [Math / Chapter 1, page 3].
Mention where the information comes from, for example "(Math / Chapter 1, p. 3)".
If the student asks about a single word or sentence, explain it and say
where it appears.

====================================

LECTURE NOTES

{context}

====================================

STUDENT QUESTION

{question}

====================================

Generate the best possible answer.
"""

            return {
                "success": True,
                "prompt": prompt,
                "sources": sources
            }

        except Exception as e:

            return {
                "success": False,
                "message": str(e)
            }

    # ------------------------------------------------------
    # Step 2a: streamed answer (used by the Ask AI page)
    # ------------------------------------------------------

    def stream_answer(self, prompt, provider="auto"):
        """Generator of answer pieces for st.write_stream."""

        return self.ai_provider.stream(
            prompt,
            provider=provider,
            task="question_answering"
        )

    # ------------------------------------------------------
    # Step 2b: normal (non-streamed) answer
    # ------------------------------------------------------

    def ask_question(
        self,
        question,
        provider="auto",
        language="English",
        doc_ids=None
    ):

        prepared = self.prepare(question, language=language, doc_ids=doc_ids)

        if not prepared["success"]:
            return prepared

        try:

            answer = self.ai_provider.invoke(
                prepared["prompt"],
                provider=provider,
                task="question_answering"
            ).strip()

            return {
                "success": True,
                "answer": answer,
                "sources": prepared["sources"]
            }

        except Exception as e:

            return {
                "success": False,
                "message": str(e)
            }