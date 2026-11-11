"""Small reusable UI building blocks. HTML is built without indentation or
blank lines, otherwise Markdown would turn it into a code block."""

import html

import streamlit as st

from rag.library import Library

from config import (
    SESSION_MESSAGES,
    SESSION_SUMMARY,
    SESSION_REFLECTION,
)


def page_header(title, subtitle=""):
    st.markdown(
        f'<div class="page-title">{html.escape(title)}</div>'
        f'<div class="page-sub">{html.escape(subtitle)}</div>',
        unsafe_allow_html=True
    )


def brand():
    st.markdown(
        '<div class="brand"><div class="brand-logo">S</div>'
        '<div>Studybud <b>AI</b></div></div>',
        unsafe_allow_html=True
    )


def chip(label, ok=True):
    css = "chip-ok" if ok else "chip-off"

    return (
        f'<span class="chip {css}"><span class="dot"></span>'
        f'{html.escape(label)}</span>'
    )


def doc_pill(name):
    st.markdown(
        f'<div class="doc-pill">{html.escape(name)}</div>',
        unsafe_allow_html=True
    )


def hero(title, subtitle, tags):
    tag_html = "".join(
        f'<span class="hero-chip">{html.escape(t)}</span>' for t in tags
    )

    st.markdown(
        '<div class="hero">'
        f'<div class="hero-title">{title}</div>'
        f'<div class="hero-sub">{html.escape(subtitle)}</div>'
        f'<div class="hero-chips">{tag_html}</div>'
        '</div>',
        unsafe_allow_html=True
    )


def go_button(label, page, key, primary=True, disabled=False):
    """A real button that opens another page (centered label, same style everywhere)."""

    clicked = st.button(
        label,
        key=key,
        type="primary" if primary else "secondary",
        disabled=disabled,
        use_container_width=True
    )

    if clicked:
        st.switch_page(page)


def center_column():
    """Middle column used to center a single call-to-action button."""
    _, middle, _ = st.columns([1, 1, 1])
    return middle


def step_tracker():
    """Library -> Study -> Quiz -> Reflection, highlighting where the student is."""

    ss = st.session_state

    summary = ss.get(SESSION_SUMMARY)
    reflection = ss.get(SESSION_REFLECTION)

    done = [
        bool(Library().list_documents()),
        bool(ss.get(SESSION_MESSAGES)) or bool(summary and summary.get("success")),
        bool(ss.get("quiz_completed")),
        bool(reflection and reflection.get("success")),
    ]

    names = ["Library", "Study", "Quiz", "Reflection"]

    active = next((i for i, d in enumerate(done) if not d), None)

    parts = []

    for i, name in enumerate(names):

        if done[i]:
            css = "done"
        elif i == active:
            css = "active"
        else:
            css = "todo"

        parts.append(
            f'<div class="step {css}"><div class="step-dot">{i + 1}</div>'
            f'<div class="step-name">{name}</div></div>'
        )

    st.markdown(
        '<div class="steps">' + "".join(parts) + '</div>',
        unsafe_allow_html=True
    )


def empty_state(title, text, page=None, label=None, key=None):
    st.markdown(
        '<div class="empty-state">'
        f'<div class="empty-title">{html.escape(title)}</div>'
        f'<div class="empty-text">{html.escape(text)}</div>'
        '</div>',
        unsafe_allow_html=True
    )

    if page:
        with center_column():
            go_button(
                label or "Open",
                page,
                key=key or f"empty_{page}"
            )


def render_sources(sources, title="Sources"):
    """Retrieved chunks as small cards with page badges."""

    if not sources:
        return

    with st.expander(f"{title} ({len(sources)})"):

        for i, source in enumerate(sources, start=1):

            if isinstance(source, dict):
                text, page = source.get("text", ""), source.get("page")
                where = " / ".join(
                    part for part in (source.get("subject"), source.get("document")) if part
                )
            else:
                text, page, where = str(source), None, ""

            snippet = text if len(text) <= 600 else text[:600].rstrip() + "…"

            label = html.escape(where) if where else f"Source {i}"

            if page:
                label += f" · Page {page}"

            badge = f'<span class="badge">{label}</span>'

            body = html.escape(snippet).replace("\n", "<br>")

            st.markdown(
                f'<div class="source-card">{badge}'
                f'<div class="source-text">{body}</div></div>',
                unsafe_allow_html=True
            )


def score_card(percentage, correct, total):
    passed = percentage >= 50
    css = "score-pass" if passed else "score-fail"
    status = "PASS" if passed else "FAIL"
    message = "Great work." if passed else "Review the answers below and try again."

    st.markdown(
        f'<div class="score-card {css}">'
        f'<div class="score-big">{percentage:.0f}%</div>'
        f'<div class="score-sub">{correct} / {total} correct. {message}</div>'
        f'<div class="score-status">{status}</div>'
        '</div>',
        unsafe_allow_html=True
    )


def library_sidebar():
    """The folders (subjects) and their chapters, shown in the sidebar."""

    library = Library()

    subjects = library.list_subjects()

    if not subjects:
        st.caption("No subjects yet. Create one in the Library page.")
        return

    for subject in subjects:

        documents = library.list_documents(subject["id"])

        with st.expander(f"{subject['name']}  ({len(documents)})"):

            if not documents:
                st.caption("No documents yet")

            for document in documents:
                st.caption(f"{document['title']}  ·  {document['pages']} pages")
