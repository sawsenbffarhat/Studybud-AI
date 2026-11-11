import pandas as pd
import streamlit as st

from components.ui import center_column, empty_state, page_header
from services.reflection_service import ReflectionService
from utils.markdown_utils import split_sections
from utils.session import get_language

from config import SESSION_REFLECTION

st.set_page_config(
    page_title="Learning Reflection",
    layout="wide"
)

service = ReflectionService()

page_header(
    "Learning Reflection",
    "Personal feedback based on your latest quiz and your notes."
)

provider = "auto"

if not st.session_state.get("quiz_completed", False):

    empty_state(
        "No completed quiz yet",
        "Finish a quiz first. Your reflection is built from the quiz result.",
        "pages/Quiz.py",
        "Go to Quiz",
        key="reflection_empty"
    )
    st.stop()

# ---------- Latest quiz results ----------
percentage = st.session_state.get("quiz_percentage") or 0
status = st.session_state.get("quiz_status", "FAIL")

with st.container(border=True):

    st.markdown("**Latest quiz**")

    if st.session_state.get("quiz_scope_label"):
        st.caption(st.session_state["quiz_scope_label"])

    m1, m2, m3, m4 = st.columns(4)

    m1.metric("Score", f"{st.session_state.get('quiz_score', 0)} / {st.session_state.get('quiz_total', 0)}")
    m2.metric("Percentage", f"{percentage:.0f}%")
    m3.metric("Correct / Wrong", f"{st.session_state.get('quiz_correct', 0)} / {st.session_state.get('quiz_wrong', 0)}")
    m4.metric("Status", status)

# ---------- Progress across quizzes ----------
history = st.session_state.get("quiz_history", [])

if len(history) >= 2:

    st.markdown("**Your progress across quizzes**")

    chart_data = pd.DataFrame(
        {"Score (%)": [item["percentage"] for item in history]},
        index=[f"Quiz {i}" for i in range(1, len(history) + 1)]
    )

    st.line_chart(chart_data, height=220)

else:

    st.caption("Take another quiz to see a progress chart here.")

# ---------- Generate ----------
with center_column():
    generate = st.button(
        "Generate Reflection",
        type="primary",
        use_container_width=True
    )

if generate:

    with st.spinner("Analyzing your learning progress..."):
        st.session_state[SESSION_REFLECTION] = service.generate_reflection(
            provider=provider,
            quiz_message=st.session_state.get("quiz_agent_message"),
            language=get_language(),
            doc_ids=st.session_state.get("quiz_doc_ids")
        )

result = st.session_state.get(SESSION_REFLECTION)

if result is not None:

    if not result["success"]:

        st.error(result["message"])

    else:

        sections = split_sections(result["reflection"])

        if len(sections) >= 2:

            tabs = st.tabs([title for title, _ in sections])

            for tab, (_, body) in zip(tabs, sections):
                with tab:
                    st.markdown(body)

        else:

            with st.container(border=True):
                st.markdown(result["reflection"])

        with center_column():
            st.download_button(
                label="Download Reflection",
                data=result["reflection"],
                file_name="StudyMate_Reflection.md",
                mime="text/markdown",
                type="primary",
                use_container_width=True
            )
