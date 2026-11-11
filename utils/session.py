"""Helpers for the per-browser-session state (chat, quiz, summary)."""

import streamlit as st

from config import (
    SESSION_MESSAGES,
    SESSION_QUIZ,
    SESSION_SUMMARY,
    SESSION_REFLECTION,
)

# Everything that belongs to the current chat / quiz. The library itself
# (subjects and documents) is permanent and is NOT touched by this.
LEARNING_STATE_KEYS = [
    SESSION_MESSAGES,
    SESSION_QUIZ,
    SESSION_SUMMARY,
    SESSION_REFLECTION,
    "current_question",
    "score",
    "answers",
    "current_quiz_review",
    "review_error",
    "quiz_submitted",
    "quiz_completed",
    "quiz_score",
    "quiz_total",
    "quiz_correct",
    "quiz_wrong",
    "quiz_percentage",
    "quiz_status",
    "quiz_review",
    "quiz_overall_performance_summary",
    "quiz_agent_message",
    "quiz_history",
    "quiz_id",
    "quiz_doc_ids",
    "quiz_scope_label",
    "balloons_done_for",
    "focus_weak_topics",
    "pending_question",
]


def get_language():
    return st.session_state.get("language", "English")


def reset_learning_state():
    """Forget chat, quiz, summary and reflection."""

    for key in LEARNING_STATE_KEYS:
        st.session_state.pop(key, None)

    for key in list(st.session_state.keys()):
        if str(key).startswith("radio_"):
            st.session_state.pop(key, None)
