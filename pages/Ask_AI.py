import streamlit as st

from components.ui import empty_state, page_header, render_sources
from rag.library import Library
from services.chat_service import ChatService
from utils.session import get_language

from config import SESSION_MESSAGES


st.set_page_config(
    page_title="Ask AI",
    layout="wide"
)

SUGGESTIONS = [
    "What are the important exam topics?",
    "Explain the main concepts.",
    "Give me revision notes.",
    "What definitions should I remember?",
    "Summarize the key ideas.",
]

library = Library()

page_header(
    "Ask Your Notes",
    "Ask a question, or type a word or a sentence. I search everything in your "
    "library and tell you where it comes from."
)

subjects = library.list_subjects()

if not library.list_documents():

    empty_state(
        "Your library is empty",
        "Add a subject and its PDFs first, then come back to ask questions.",
        "pages/Library.py",
        "Open Library",
        key="ask_empty"
    )
    st.stop()

service = ChatService()

# ---------- Where to search ----------
ALL = "All subjects"

options = [ALL] + [s["name"] for s in subjects if s["documents"] > 0]

if st.session_state.get("ask_scope") not in options:
    st.session_state.pop("ask_scope", None)

scope_col, _ = st.columns([1, 2])

with scope_col:
    scope = st.selectbox("Search in", options, key="ask_scope")

if scope == ALL:
    doc_ids = None
else:
    subject = next(s for s in subjects if s["name"] == scope)
    doc_ids = [d["id"] for d in library.list_documents(subject["id"])]

if SESSION_MESSAGES not in st.session_state:
    st.session_state[SESSION_MESSAGES] = []

messages = st.session_state[SESSION_MESSAGES]

provider = "auto"


def ask(question):
    """Button callback: send a suggested question to the chat."""
    st.session_state["pending_question"] = question


# The chat box is pinned to the bottom of the page, wherever it is called.
typed = st.chat_input("Ask a question, or type a word or a sentence...")
prompt = typed or st.session_state.pop("pending_question", None)

# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:

    if messages:

        st.markdown("##### Try asking")

        for i, question in enumerate(SUGGESTIONS):
            st.button(
                question,
                key=f"suggest_side_{i}",
                on_click=ask,
                args=(question,),
                use_container_width=True
            )

        st.divider()

    st.metric("Messages", len(messages))

    if st.button("Clear Chat", use_container_width=True):
        st.session_state[SESSION_MESSAGES] = []
        st.rerun()

# -----------------------------
# Empty chat: clickable suggestions
# -----------------------------
if not messages and not prompt:

    with st.container(border=True):

        st.markdown("**What would you like to know?**")
        st.caption("Click a question to start, or type your own below.")

        left, right = st.columns(2)

        for i, question in enumerate(SUGGESTIONS):
            with (left if i % 2 == 0 else right):
                st.button(
                    question,
                    key=f"suggest_main_{i}",
                    on_click=ask,
                    args=(question,),
                    use_container_width=True
                )

# -----------------------------
# Chat History
# -----------------------------
for message in messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])

        if message["role"] == "assistant" and message.get("sources"):
            render_sources(message["sources"])

# -----------------------------
# New question
# -----------------------------
if prompt:

    messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):

        with st.spinner("Searching your library..."):
            prepared = service.prepare(
                prompt,
                language=get_language(),
                doc_ids=doc_ids
            )

        if not prepared["success"]:

            st.error(prepared["message"])

            messages.append(
                {"role": "assistant", "content": prepared["message"]}
            )

        else:

            answer = None

            try:
                # Text appears live while the model is writing
                answer = st.write_stream(
                    service.stream_answer(prepared["prompt"], provider)
                )
            except Exception as e:
                st.error(str(e))
                messages.append(
                    {"role": "assistant", "content": f"Error: {e}"}
                )

            if answer is not None:

                if not str(answer).strip():

                    st.warning("The model returned an empty answer. Please try again.")

                else:

                    render_sources(prepared["sources"])

                    messages.append(
                        {
                            "role": "assistant",
                            "content": answer,
                            "sources": prepared["sources"]
                        }
                    )
