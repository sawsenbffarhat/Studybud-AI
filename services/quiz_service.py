import json

from rag.vector_store import VectorStore
from agents.ai_provider import AIProvider
from agents.messages import build_quiz_result_message
from utils.json_utils import parse_llm_json
from utils.language import language_instruction

from config import MAX_CONTEXT_CHARS


class QuizService:

    def __init__(self):

        self.vector_store = VectorStore()
        self.ai_provider = AIProvider()

    def generate_quiz(
        self,
        provider="auto",
        difficulty="Medium",
        question_type="Mixed",
        num_questions=5,
        language="English",
        focus_topics=None,
        doc_ids=None
    ):
        """
        Generate a quiz from the chosen documents (doc_ids = the selected
        subject / chapters).

        focus_topics: weak topics from the previous quiz. When given, the
        passages about those topics are retrieved first (adaptive quiz).
        """

        try:

            context, chunks = self.vector_store.get_context(
                max_chars=MAX_CONTEXT_CHARS,
                focus_queries=focus_topics,
                doc_ids=doc_ids
            )

            if not chunks:

                return {
                    "success": False,
                    "message": "No lecture notes found for this selection. Add PDFs in the Library page first."
                }

            if question_type == "MCQ":
                type_rule = (
                    "Every question MUST be multiple choice with exactly "
                    "4 options (A, B, C, D)."
                )
            elif question_type == "True / False":
                type_rule = (
                    'Every question MUST be a True/False statement with exactly '
                    '2 options: "A": "True" and "B": "False".'
                )
            else:
                type_rule = (
                    "Mix multiple choice questions (exactly 4 options A, B, C, D) "
                    "and True/False questions (exactly 2 options: "
                    '"A": "True" and "B": "False").'
                )

            focus_rule = ""

            if focus_topics:
                focus_rule = (
                    "- The student is weak in these topics, so focus most "
                    "questions on them: " + "; ".join(focus_topics) + "\n"
                )

            prompt = f"""
You are Studybud AI.

Generate a quiz ONLY from the lecture notes provided.

IMPORTANT RULES

- Use ONLY the lecture notes.
- Never invent information.
- Generate exactly {num_questions} questions.
- Difficulty: {difficulty}
- Question Type: {question_type}
- {type_rule}
- Only ONE correct answer.
- "answer" must be the letter of the correct option.
- Provide a short explanation.
{focus_rule}- {language_instruction(language)} Keep the JSON keys and the answer letters in English.
- Return ONLY valid JSON.
- Do NOT use Markdown.
- Do NOT wrap the JSON inside ```json.
- Do NOT write any text before or after the JSON.

JSON FORMAT

[
  {{
    "question": "Question text",
    "options": {{
      "A": "Option A",
      "B": "Option B",
      "C": "Option C",
      "D": "Option D"
    }},
    "answer": "A",
    "explanation": "Short explanation."
  }}
]

LECTURE NOTES

{context}
"""

            content = self.ai_provider.invoke(
                prompt,
                provider=provider,
                task="quiz"
            )

            quiz = parse_llm_json(content)

            quiz = self._validate_quiz(quiz)[:num_questions]

            return {
                "success": True,
                "quiz": quiz
            }

        except json.JSONDecodeError:

            return {
                "success": False,
                "message": "The AI returned an invalid quiz format. Please try again."
            }

        except Exception as e:

            return {
                "success": False,
                "message": str(e)
            }

    @staticmethod
    def _validate_quiz(quiz):
        """Validate the quiz structure and normalise answer letters."""

        if not isinstance(quiz, list) or not quiz:
            raise ValueError("Quiz is not a valid list.")

        for item in quiz:

            if not isinstance(item, dict):
                raise ValueError("Quiz contains an invalid question.")

            for field in ("question", "options", "answer", "explanation"):
                if field not in item:
                    raise ValueError(f"Missing {field}.")

            options = item["options"]

            if not isinstance(options, dict):
                raise ValueError("Options must be an object.")

            if not {"A", "B"}.issubset(options) or not set(options).issubset(
                {"A", "B", "C", "D"}
            ):
                raise ValueError("Options must use the letters A-D (at least A and B).")

            answer = str(item["answer"]).strip().upper()[:1]

            if answer not in options:
                raise ValueError("The correct answer is not one of the options.")

            item["answer"] = answer

        return quiz

    @staticmethod
    def calculate_score(quiz, answers):
        """Calculate the final score from the stored answer choices."""
        score = sum(
            1
            for index, question in enumerate(quiz)
            if answers.get(index) == question.get("answer")
        )

        total = len(quiz)
        percentage = (score / total) * 100 if total else 0

        return {
            "score": score,
            "total": total,
            "percentage": percentage,
            "status": "PASS" if percentage >= 50 else "FAIL"
        }

    @staticmethod
    def create_reflection_message(score_result, review=None):
        """Publish the Quiz Agent's result in the inter-agent protocol."""
        return build_quiz_result_message(score_result, review)

    def review_quiz(
        self,
        quiz,
        answers,
        provider="auto",
        language="English"
    ):
        """Generate one complete, structured review for the submitted quiz."""
        try:
            review_input = []

            for index, question in enumerate(quiz):
                user_answer = answers.get(index)
                review_input.append({
                    "question_number": index + 1,
                    "question": question["question"],
                    "options": question["options"],
                    "your_answer": user_answer or "Not answered",
                    "your_answer_text": (
                        question["options"].get(user_answer, "Not answered")
                        if user_answer else "Not answered"
                    ),
                    "correct_answer": question["answer"],
                    "correct_answer_text": question["options"].get(
                        question["answer"], question["answer"]
                    )
                })

            prompt = f"""
You are Studybud AI, an educational quiz review assistant.

Review the entire quiz in ONE response. Use the supplied questions, user answers,
and correct answers. Do not invent facts that are unrelated to the quiz.
Explain every answer in simple educational language. For incorrect answers,
explain why the user's answer is incorrect and clearly teach the correct concept.
Use the supplied answer text in `your_answer` and `correct_answer` (not only the
option letters). Keep the question order unchanged and return exactly one item
for every question. "status" must be exactly "Correct" or "Incorrect".

{language_instruction(language)} Keep the JSON keys in English.

Return ONLY valid JSON. Do not use Markdown or add text outside the JSON.

JSON FORMAT
{{
  "questions": [
    {{
      "question_number": 1,
      "status": "Correct",
      "your_answer": "Answer text",
      "correct_answer": "Correct answer text",
      "explanation": "Simple educational explanation."
    }}
  ],
  "overall_learning_report": {{
    "overall_performance": "...",
    "strengths": "...",
    "weak_areas": "...",
    "topics_to_revise": "...",
    "study_recommendations": "...",
    "motivational_feedback": "...",
    "estimated_readiness_level": "..."
  }}
}}

QUIZ REVIEW DATA
{json.dumps(review_input, ensure_ascii=False)}
"""

            content = self.ai_provider.invoke(
                prompt,
                provider=provider,
                task="quiz"
            )

            review = parse_llm_json(content)
            self._validate_review(review, len(quiz))

            return {"success": True, "review": review}

        except json.JSONDecodeError:
            return {
                "success": False,
                "message": "The AI returned an invalid quiz review format. Please try again."
            }
        except Exception as e:
            return {"success": False, "message": str(e)}

    @staticmethod
    def _validate_review(review, question_count):
        """Validate the minimum structure required by the review UI."""
        if not isinstance(review, dict):
            raise ValueError("Quiz review is not a valid object.")

        questions = review.get("questions")
        report = review.get("overall_learning_report")

        if not isinstance(questions, list) or len(questions) != question_count:
            raise ValueError("Quiz review does not contain every question.")
        if not isinstance(report, dict):
            raise ValueError("Quiz review is missing the overall learning report.")

        question_fields = {
            "question_number", "status", "your_answer",
            "correct_answer", "explanation"
        }
        report_fields = {
            "overall_performance", "strengths", "weak_areas",
            "topics_to_revise", "study_recommendations",
            "motivational_feedback", "estimated_readiness_level"
        }

        for item in questions:
            if not question_fields.issubset(item):
                raise ValueError("Quiz review is missing question details.")
        if not report_fields.issubset(report):
            raise ValueError("Quiz review is missing report details.")
