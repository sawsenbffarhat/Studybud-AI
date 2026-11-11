import streamlit as st

from agents.ai_provider import AIProvider
from components.styles import load_css
from components.ui import (
    brand, center_column, chip, go_button, hero, library_sidebar, step_tracker
)
from rag.library import Library
from utils.language import LANGUAGES
from utils.session import reset_learning_state

from config import APP_VERSION


st.set_page_config(
    page_title="Studybud AI",
    page_icon=":material/school:",
    layout="wide",
    initial_sidebar_state="expanded"
)

load_css()


# ---------- Sidebar (shown on every page) ----------
with st.sidebar:

    brand()

    st.markdown("##### Response language")

    st.selectbox(
        "Response Language",
        LANGUAGES,
        key="language",
        label_visibility="collapsed"
    )

    st.markdown("##### My subjects")

    library_sidebar()

    go_button(
        "Manage library",
        "pages/Library.py",
        key="sidebar_library",
        primary=False
    )

    st.markdown("##### AI providers")

    providers = AIProvider().available_providers()

    st.markdown(
        chip("Groq", "Groq" in providers)
        + chip("OpenRouter", "OpenRouter" in providers),
        unsafe_allow_html=True
    )

    if not providers:
        st.warning("No API key found. Add one to your .env file.")

    if st.button("Reset chat and quiz", use_container_width=True):
        reset_learning_state()
        st.rerun()

    st.divider()


def app_page():

    library = Library()

    subjects = library.list_subjects()
    documents = library.list_documents()

    has_documents = len(documents) > 0

    hero(
        "Turn your lecture notes into<br>summaries, answers and quizzes",
        "Organize your courses in subjects, add the PDF of every chapter and "
        "let Studybud AI summarize, answer and test you. Everything is saved.",
        ["Subjects and chapters", "Search with page citations", "English and French"]
    )

    step_tracker()

    if has_documents:
        st.markdown(
            f"**Your library:** {len(subjects)} subject(s), {len(documents)} document(s)"
        )
    else:
        st.markdown("Start by creating a subject and adding the PDFs of its chapters.")

        with center_column():
            go_button(
                "Open library",
                "pages/Library.py",
                key="home_library"
            )

    st.markdown("### What you can do")

    features = [
        (
            "Summary",
            "Type what you need, for example a summary of chapter 1 of Math.",
            "pages/Summary.py", "Open Summary"
        ),
        (
            "Ask AI",
            "Ask a question or type a word. It searches your whole library.",
            "pages/Ask_AI.py", "Open Ask AI"
        ),
        (
            "Quiz",
            "Pick a subject and chapters in the sidebar, then take a quiz.",
            "pages/Quiz.py", "Open Quiz"
        ),
        (
            "Reflection",
            "Get personal feedback and a study plan based on your quiz result.",
            "pages/Reflection.py", "Open Reflection"
        ),
    ]

    columns = st.columns(4)

    for column, (title, text, page, label) in zip(columns, features):

        with column:
            with st.container(border=True):

                st.markdown(
                    f'<div class="feature-title">{title}</div>'
                    f'<div class="feature-text">{text}</div>',
                    unsafe_allow_html=True
                )

                go_button(
                    label,
                    page,
                    key=f"home_{page}",
                    primary=False,
                    disabled=not has_documents
                )

    st.caption(
        f"Version {APP_VERSION} | Powered by Streamlit, LangChain, Groq, OpenRouter and ChromaDB"
    )


pages = [
    st.Page(app_page, title="Home", icon=":material/home:", default=True),
    st.Page("pages/Library.py", title="Library", icon=":material/folder:"),
    st.Page("pages/Summary.py", title="Summary", icon=":material/article:"),
    st.Page("pages/Ask_AI.py", title="Ask AI", icon=":material/forum:"),
    st.Page("pages/Quiz.py", title="Quiz", icon=":material/quiz:"),
    st.Page("pages/Reflection.py", title="Reflection", icon=":material/insights:"),
]

navigation = st.navigation(pages)
navigation.run()