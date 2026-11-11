import streamlit as st

from components.ui import center_column, empty_state, page_header
from rag.library import Library
from services.scope_service import ScopeResolver
from services.summary_service import SummaryService
from utils.markdown_utils import split_sections
from utils.session import get_language

from config import DEFAULT_PROVIDER, SESSION_SUMMARY

st.set_page_config(
    page_title="Summary",
    layout="wide"
)

library = Library()

page_header(
    "Summary",
    "Tell me what to summarize. Name the subject and the chapter."
)

documents = library.list_documents()

if not documents:

    empty_state(
        "Your library is empty",
        "Add a subject and its PDFs first, then come back to ask for a summary.",
        "pages/Library.py",
        "Open Library",
        key="summary_empty"
    )
    st.stop()

service = SummaryService()

first = documents[0]

with st.form("summary_form"):

    request = st.text_input(
        "What should I summarize?",
        key="summary_request",
        placeholder=f'For example: I need a summary of chapter 1 of {first["subject"]}'
    )

    _, button_col, _ = st.columns([1, 1, 1])

    submitted = button_col.form_submit_button(
        "Generate Summary",
        type="primary",
        use_container_width=True
    )

st.caption(
    "You can also say \"the whole subject\" or \"chapters 1 to 3\". "
    "Your library: " + ScopeResolver(library).describe_library()
)

if submitted:

    with st.spinner("Finding your notes and writing the summary..."):

        # Stored in session state so it survives reruns
        st.session_state[SESSION_SUMMARY] = service.summarize(
            request,
            provider=DEFAULT_PROVIDER,
            language=get_language()
        )

result = st.session_state.get(SESSION_SUMMARY)

if result is not None:

    if not result["success"]:

        st.error(result["message"])

    else:

        st.markdown(f"**Summary of:** {result['label']}")

        st.caption(
            f"Based on {result['chunks']} chunks "
            f"({result['characters']:,} characters)"
        )

        sections = split_sections(result["summary"])

        if len(sections) >= 2:

            tabs = st.tabs([title for title, _ in sections])

            for tab, (_, body) in zip(tabs, sections):
                with tab:
                    st.markdown(body)

        else:

            with st.container(border=True):
                st.markdown(result["summary"])

        with center_column():
            st.download_button(
                label="Download Summary",
                data=result["summary"],
                file_name="StudyMate_Summary.md",
                mime="text/markdown",
                type="primary",
                use_container_width=True
            )
