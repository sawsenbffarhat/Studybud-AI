from rag.library import Library
from rag.vector_store import VectorStore
from agents.ai_provider import AIProvider
from services.scope_service import ScopeResolver
from utils.language import language_instruction

from config import MAX_CONTEXT_CHARS, MAX_SUMMARY_DOCS, SUMMARY_DOC_CHARS


class SummaryService:

    def __init__(self):
        self.library = Library()
        self.vector_store = VectorStore()
        self.ai_provider = AIProvider()
        self.resolver = ScopeResolver(self.library)

    # ------------------------------------------------------

    @staticmethod
    def _final_format():
        return """# Summary
Write a concise summary.

# Key Points
- Bullet Point 1
- Bullet Point 2
- Bullet Point 3

# Important Concepts
Mention the important concepts discussed.

# Exam Tips
Give useful exam preparation tips based on these notes."""

    def _summarize_one(self, document, request, provider, language):

        text, chunks = self.vector_store.get_context(
            max_chars=MAX_CONTEXT_CHARS,
            doc_ids=[document["id"]]
        )

        prompt = f"""
You are an expert study assistant.

Summarize the lecture notes below. The student asked: "{request}"
Focus on what the student asked for.

{language_instruction(language)}

Create the response using the following format.

{self._final_format()}

Lecture Notes ({document["subject"]}: {document["title"]}):

{text}
"""

        summary = self.ai_provider.invoke(
            prompt, provider=provider, task="summary"
        )

        return summary, len(chunks), len(text)

    def _summarize_many(self, subject, documents, request, provider, language):

        parts = []
        total_chunks = 0
        total_chars = 0

        for document in documents:

            text, chunks = self.vector_store.get_context(
                max_chars=SUMMARY_DOC_CHARS,
                doc_ids=[document["id"]]
            )

            prompt = f"""
Summarize this chapter in 150 to 200 words. Keep the key terms, definitions
and important facts. {language_instruction(language)}

Chapter: {document["title"]}

{text}
"""

            parts.append(
                (
                    document["title"],
                    self.ai_provider.invoke(
                        prompt, provider=provider, task="summary"
                    )
                )
            )

            total_chunks += len(chunks)
            total_chars += len(text)

        joined = "\n\n".join(f"## {title}\n{summary}" for title, summary in parts)

        prompt = f"""
You are an expert study assistant.

Below are summaries of several chapters of the subject "{subject}".
The student asked: "{request}"

{language_instruction(language)}

Combine them into ONE study summary using the following format. Mention
the chapter names where it helps.

{self._final_format()}

Chapter summaries:

{joined}
"""

        summary = self.ai_provider.invoke(
            prompt, provider=provider, task="summary"
        )

        return summary, total_chunks, total_chars

    # ------------------------------------------------------

    def summarize(self, request, provider="auto", language="English"):
        """Summarize whatever the student's sentence asks for."""

        request = (request or "").strip()

        if not request:
            return {
                "success": False,
                "message": "Type what you want summarized, for example: summary of chapter 1 of math."
            }

        try:

            scope = self.resolver.resolve(request)

            if not scope["ok"]:
                return {"success": False, "message": scope["message"]}

            documents = scope["documents"]

            if len(documents) > MAX_SUMMARY_DOCS:
                return {
                    "success": False,
                    "message": (
                        f"That matches {len(documents)} documents. Please ask for at most "
                        f"{MAX_SUMMARY_DOCS} at once, for example one chapter or a range of chapters."
                    )
                }

            if len(documents) == 1:
                summary, chunks, characters = self._summarize_one(
                    documents[0], request, provider, language
                )
            else:
                summary, chunks, characters = self._summarize_many(
                    scope["subject"], documents, request, provider, language
                )

            return {
                "success": True,
                "summary": summary,
                "label": scope["label"],
                "documents": [d["title"] for d in documents],
                "chunks": chunks,
                "characters": characters
            }

        except Exception as e:

            return {
                "success": False,
                "message": str(e)
            }
