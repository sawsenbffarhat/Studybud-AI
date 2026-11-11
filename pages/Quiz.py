import time

import streamlit as st

from components.ui import empty_state, go_button, page_header, score_card
from rag.library import Library
from services.quiz_service import QuizService
from utils.session import get_language

from config import SESSION_REFLECTION

st.set_page_config(page_title="Quiz", layout="wide")

service = QuizService()
library = Library()

page_header(
    "Quiz",
    "Test yourself on your notes and review every answer."
)

subjects_with_documents = [
    subject for subject in library.list_subjects() if subject["documents"] > 0
]

if not subjects_with_documents:

    empty_state(
        "Your library is empty",
        "Add a subject and its PDFs first, then generate a quiz from them.",
        "pages/Library.py",
        "Open Library",
        key="quiz_empty"
    )
    st.stop()

defaults = {
    "quiz": None,
    "current_question": 0,
    "score": 0,
    "answers": {},
    "current_quiz_review": None,
    "review_error": None,
    "quiz_submitted": False
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

latest_quiz_defaults = {
    "quiz_completed": False,
    "quiz_score": None,
    "quiz_total": None,
    "quiz_correct": None,
    "quiz_wrong": None,
    "quiz_percentage": None,
    "quiz_status": None,
    "quiz_review": None,
    "quiz_overall_performance_summary": None,
    "quiz_agent_message": None,
    "quiz_history": [],
    "quiz_id": None
}

for k, v in latest_quiz_defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


def _store_latest_quiz(score_result, review=None):
    """Keep the latest quiz (the Quiz Agent's message) and add it to the history."""
    st.session_state.quiz_completed = True
    st.session_state.quiz_score = score_result["score"]
    st.session_state.quiz_total = score_result["total"]
    st.session_state.quiz_correct = score_result["score"]
    st.session_state.quiz_wrong = score_result["total"] - score_result["score"]
    st.session_state.quiz_percentage = score_result["percentage"]
    st.session_state.quiz_status = score_result["status"]
    st.session_state.quiz_review = review
    st.session_state.quiz_overall_performance_summary = (
        review.get("overall_learning_report", {}).get("overall_performance")
        if review else None
    )
    st.session_state.quiz_agent_message = service.create_reflection_message(
        score_result, review
    )

    # One history entry per quiz (re-submitting replaces it)
    quiz_id = st.session_state.quiz_id
    history = [
        item for item in st.session_state.quiz_history
        if item["id"] != quiz_id
    ]
    history.append({
        "id": quiz_id,
        "percentage": round(score_result["percentage"], 1)
    })
    st.session_state.quiz_history = history


def go_to(question_index):
    """Button callback for the question navigator."""
    st.session_state.current_question = question_index


def finish_quiz():
    """Score the quiz and generate the answer review."""

    score_result = service.calculate_score(quiz, st.session_state.answers)
    st.session_state.score = score_result["score"]
    st.session_state.current_question = total

    with st.spinner("Reviewing your answers..."):

        review_result = service.review_quiz(
            quiz,
            st.session_state.answers,
            provider=provider,
            language=get_language()
        )

        if review_result["success"]:
            st.session_state.current_quiz_review = review_result["review"]
            st.session_state.review_error = None
            st.session_state.quiz_submitted = True
            _store_latest_quiz(score_result, review_result["review"])
        else:
            st.session_state.current_quiz_review = None
            st.session_state.review_error = review_result["message"]
            _store_latest_quiz(score_result)

    st.rerun()


provider = "auto"

with st.sidebar:
    st.markdown("##### Quiz on")

    subject_names = {sub["id"]: sub["name"] for sub in subjects_with_documents}

    subject_id = st.selectbox(
        "Subject",
        list(subject_names.keys()),
        format_func=lambda i: subject_names[i],
        key="quiz_subject"
    )

    chapter_documents = library.list_documents(subject_id)
    chapter_titles = {d["id"]: d["title"] for d in chapter_documents}
    chapter_ids = list(chapter_titles.keys())

    selected_ids = st.multiselect(
        "Chapters",
        chapter_ids,
        default=chapter_ids,
        format_func=lambda i: chapter_titles[i],
        key=f"quiz_chapters_{subject_id}_" + "-".join(str(i) for i in chapter_ids)
    )

    st.markdown("##### Quiz settings")
    difficulty = st.selectbox("Difficulty", ["Easy","Medium","Hard"])
    question_type = st.selectbox("Question Type", ["MCQ","True / False","Mixed"])
    num_questions = st.slider("Number of Questions",5,20,5,step=5)

    st.toggle(
        "Instant feedback",
        key="instant_feedback",
        help="Show whether each answer is right as soon as you pick it."
    )

    # Adaptive quiz: the Quiz Agent reuses what it learned from the last quiz
    previous_message = st.session_state.quiz_agent_message
    weak_topics = previous_message.weak_topics[:5] if previous_message else []

    focus_weak = False

    if weak_topics:
        focus_weak = st.checkbox(
            "Focus on my weak topics",
            key="focus_weak_topics",
            help="Use the weak topics from your last quiz: " + "; ".join(weak_topics)
        )

    if st.button("Generate Quiz", type="primary", use_container_width=True):

        if not selected_ids:
            st.error("Select at least one chapter.")
        else:
            with st.spinner("Generating quiz..."):
                result = service.generate_quiz(
                    provider=provider,
                    difficulty=difficulty,
                    question_type=question_type,
                    num_questions=num_questions,
                    language=get_language(),
                    focus_topics=weak_topics if focus_weak else None,
                    doc_ids=selected_ids
                )

            if result["success"]:
                st.session_state.quiz = result["quiz"]
                st.session_state.quiz_id = time.time_ns()
                st.session_state.quiz_doc_ids = list(selected_ids)
                st.session_state.quiz_scope_label = (
                    f"{subject_names[subject_id]}: "
                    + (
                        "all chapters"
                        if len(selected_ids) == len(chapter_ids)
                        else ", ".join(chapter_titles[i] for i in selected_ids)
                    )
                )
                st.session_state.current_question = 0
                st.session_state.score = 0
                st.session_state.answers = {}
                st.session_state.current_quiz_review = None
                st.session_state.review_error = None
                st.session_state.quiz_submitted = False
                st.session_state.pop(SESSION_REFLECTION, None)
                for key in list(st.session_state.keys()):
                    if str(key).startswith("radio_"):
                        st.session_state.pop(key, None)
                st.rerun()
            else:
                st.error(result["message"])

if not st.session_state.quiz:

    empty_state(
        "Ready when you are",
        "Pick the subject and chapters in the sidebar, choose difficulty and length, then click Generate Quiz."
    )

    st.stop()

if st.session_state.get("quiz_scope_label"):
    st.caption(f"Quiz on: {st.session_state.quiz_scope_label}")

quiz = st.session_state.quiz
total = len(quiz)
index = st.session_state.current_question

# =====================================================
# Results screen: score and answer review only
# =====================================================
if index >= total:

    percentage = (st.session_state.score / total) * 100 if total else 0

    score_card(percentage, st.session_state.score, total)

    if (
        percentage >= 50
        and st.session_state.get("balloons_done_for") != st.session_state.quiz_id
    ):
        st.balloons()
        st.session_state.balloons_done_for = st.session_state.quiz_id

    # ---- The AI review failed: let the student retry ----
    if st.session_state.review_error:

        st.error(st.session_state.review_error)

        _, retry_col, _ = st.columns([1, 1, 1])

        with retry_col:
            if st.button("Retry review", type="primary", use_container_width=True):
                finish_quiz()

    # ---- Answer review ----
    if st.session_state.current_quiz_review:

        review = st.session_state.current_quiz_review

        st.subheader("Answer review")

        for item in review["questions"]:
            is_correct = item["status"].strip().lower() == "correct"
            label = "Correct" if is_correct else "Incorrect"
            with st.expander(f"Question {item['question_number']}  ·  {label}"):
                if is_correct:
                    st.success(f"Status: {label}")
                else:
                    st.error(f"Status: {label}")
                st.write(f"**Your answer:** {item['your_answer']}")
                st.write(f"**Correct answer:** {item['correct_answer']}")
                st.write(f"**Explanation:** {item['explanation']}")

    action1, action2 = st.columns(2)

    with action1:
        if st.session_state.quiz_submitted:
            go_button(
                "Get my reflection",
                "pages/Reflection.py",
                key="quiz_to_reflection"
            )

    with action2:
        if st.button("Generate new quiz", use_container_width=True):
            for k, v in defaults.items():
                st.session_state[k] = v
            st.session_state.pop(SESSION_REFLECTION, None)
            st.rerun()

    st.stop()

# =====================================================
# Question screen
# =====================================================
answers = st.session_state.answers

st.progress(
    (index + 1) / total,
    text=f"Question {index + 1} of {total}  ·  {len(answers)} answered"
)

# Question navigator: jump to any question
per_row = 10

for start in range(0, total, per_row):

    count = min(per_row, total - start)
    columns = st.columns(count)

    for offset, column in enumerate(columns):

        number = start + offset

        column.button(
            str(number + 1),
            key=f"nav_{number}",
            type="primary" if number == index else "secondary",
            on_click=go_to,
            args=(number,),
            use_container_width=True
        )

q = quiz[index]

# True / False questions have 2 options (A, B); MCQs have 4 (A-D)
keys = sorted(q["options"].keys())
options = [f"{key}. {q['options'][key]}" for key in keys]

saved_answer = answers.get(index)

with st.container(border=True):

    st.markdown(f"**Question {index + 1}**")
    st.markdown(f"##### {q['question']}")

    selected = st.radio(
        "Choose your answer",
        options,
        index=keys.index(saved_answer) if saved_answer in keys else None,
        key=f"radio_{index}",
        label_visibility="collapsed"
    )

    # Save selected answer automatically
    if selected:
        answers[index] = selected[0]

    # Instant feedback mode
    if selected and st.session_state.get("instant_feedback"):

        correct = q["answer"]

        if selected[0] == correct:
            st.success(f"Correct. {q['explanation']}")
        else:
            st.error(
                f"Not quite. The correct answer is "
                f"**{correct}. {q['options'][correct]}**\n\n{q['explanation']}"
            )

c1, c2 = st.columns(2)

with c1:
    if st.button("Previous", disabled=index==0, use_container_width=True):
        st.session_state.current_question -= 1
        st.rerun()

with c2:
    if index < total-1:
        if st.button("Next", type="primary", use_container_width=True):
            st.session_state.current_question += 1
            st.rerun()
    else:
        all_answered = len(answers) == total

        if not all_answered:
            st.caption("Answer every question before submitting the quiz.")

        if st.button(
            "Submit quiz",
            type="primary",
            disabled=not all_answered,
            use_container_width=True
        ):
            finish_quiz()
