import json

from rag.vector_store import VectorStore
from agents.ai_provider import AIProvider
from agents.messages import QuizResultMessage
from utils.language import language_instruction

from config import MAX_CONTEXT_CHARS


class ReflectionService:

    def __init__(self):
        self.vector_store = VectorStore()
        self.ai_provider = AIProvider()

    def generate_reflection(
        self,
        provider="auto",
        quiz_message=None,
        language="English",
        doc_ids=None
    ):

        try:

            if not isinstance(quiz_message, QuizResultMessage):
                return {
                    "success": False,
                    "message": "No QuizResultMessage was provided by the Quiz Agent."
                }

            # RAG: retrieve the lecture passages that match the weak topics,
            # then fill the rest of the budget across the document.
            text, chunks = self.vector_store.get_context(
                max_chars=MAX_CONTEXT_CHARS,
                focus_queries=quiz_message.weak_topics[:5],
                doc_ids=doc_ids
            )

            if not chunks:

                return {
                    "success": False,
                    "message": "No lecture notes found for this quiz. Add PDFs in the Library page first."
                }

            prompt = f"""
You are an intelligent AI Study Coach.

The Quiz Agent has sent the following structured message. Use it directly;
do not recalculate the score or rebuild the quiz analysis:

{json.dumps(quiz_message.to_dict(), ensure_ascii=False)}

Analyze the following lecture notes in light of that message.
The notes include the passages that match the student's weak topics.

{language_instruction(language)}

Generate a personalized learning reflection using the following format.

# Learning Reflection

## Overall Performance
Write a short paragraph evaluating the student's understanding.

## Strengths
- Point 1
- Point 2
- Point 3

## Weak Areas
- Point 1
- Point 2
- Point 3

## Topics to Revise
- Topic 1
- Topic 2
- Topic 3

## Study Recommendations
Provide practical study tips to improve understanding.

## Motivation
Write a short motivational message.

Lecture Notes:

{text}
"""

            reflection = self.ai_provider.invoke(
                prompt,
                provider=provider,
                task="reflection"
            )

            return {
                "success": True,
                "reflection": reflection
            }

        except Exception as e:

            return {
                "success": False,
                "message": str(e)
            }
