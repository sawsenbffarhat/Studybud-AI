import streamlit as st

from components.ui import (
    center_column, empty_state, go_button, page_header, step_tracker
)
from rag.library import Library
from services.document_service import DocumentService

st.set_page_config(
    page_title="Library",
    layout="wide"
)

library = Library()

page_header(
    "Library",
    "Create a folder for each subject and add the PDFs of its chapters. "
    "Everything is saved, so it is still here the next time you open the app."
)

step_tracker()

notice = st.session_state.pop("library_notice", None)

if notice:
    st.toast(notice)

# ---------- Result of the last upload ----------
report = st.session_state.pop("library_report", None)

if report:

    with st.container(border=True):

        if report["added"]:
            st.markdown(f"**Added to {report['subject']}**")
            for line in report["added"]:
                st.write(line)

        for line in report["skipped"]:
            st.write("Skipped: " + line)

        for line in report["failed"]:
            st.error(line)

# ---------- New subject ----------
with st.form("new_subject", clear_on_submit=True):

    c1, c2 = st.columns([3, 1])

    new_name = c1.text_input(
        "New subject",
        placeholder="New subject name, for example Math, Science or Extra",
        label_visibility="collapsed"
    )

    created = c2.form_submit_button(
        "Create subject",
        type="primary",
        use_container_width=True
    )

if created:

    try:
        new_id = library.create_subject(new_name)
        st.session_state["library_subject"] = new_id
        st.session_state["library_notice"] = f'Subject "{new_name.strip()}" created'
        st.rerun()
    except ValueError as e:
        st.error(str(e))

# ---------- Choose a subject ----------
subjects = library.list_subjects()

if not subjects:

    empty_state(
        "No subjects yet",
        "Create your first subject above, for example Math. "
        "Then add the PDFs of its chapters."
    )
    st.stop()

by_id = {s["id"]: s for s in subjects}
ids = list(by_id.keys())

if st.session_state.get("library_subject") not in ids:
    st.session_state["library_subject"] = ids[0]

subject_id = st.selectbox(
    "Subject",
    ids,
    format_func=lambda i: f"{by_id[i]['name']}  ({by_id[i]['documents']} documents)",
    key="library_subject"
)

subject = by_id[subject_id]
documents = library.list_documents(subject_id)

# ---------- Subject header: rename / delete ----------
c_title, c_rename, c_delete = st.columns([4, 1, 1])

c_title.subheader(subject["name"])

with c_rename.popover("Rename", use_container_width=True):

    new_subject_name = st.text_input(
        "Subject name",
        value=subject["name"],
        key=f"rename_subject_{subject_id}"
    )

    if st.button(
        "Save name",
        key=f"save_subject_{subject_id}",
        type="primary",
        use_container_width=True
    ):
        try:
            library.rename_subject(subject_id, new_subject_name)
            st.rerun()
        except ValueError as e:
            st.error(str(e))

with c_delete.popover("Delete", use_container_width=True):

    st.write(
        f"This permanently deletes the subject and its {len(documents)} document(s)."
    )

    if st.button(
        "Yes, delete subject",
        key=f"delete_subject_{subject_id}",
        type="primary",
        use_container_width=True
    ):
        DocumentService().delete_subject(subject_id)
        st.session_state.pop("library_subject", None)
        st.session_state["library_notice"] = f'Subject "{subject["name"]}" deleted'
        st.rerun()

# ---------- Documents of the subject ----------
if not documents:

    st.caption("No documents yet. Add PDFs below.")

for document in documents:

    with st.container(border=True):

        c1, c2, c3 = st.columns([5, 1, 1])

        c1.markdown(f"**{document['title']}**")
        c1.caption(
            f"{document['file_name']}  ·  {document['pages']} pages  ·  "
            f"{document['chunks']} chunks  ·  added {str(document['created_at'])[:10]}"
        )

        with c2.popover("Rename", use_container_width=True):

            new_title = st.text_input(
                "Document name",
                value=document["title"],
                key=f"rename_doc_{document['id']}"
            )

            if st.button(
                "Save name",
                key=f"save_doc_{document['id']}",
                type="primary",
                use_container_width=True
            ):
                try:
                    library.rename_document(document["id"], new_title)
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

        with c3.popover("Delete", use_container_width=True):

            st.write("This removes the document and everything learned from it.")

            if st.button(
                "Yes, delete",
                key=f"delete_doc_{document['id']}",
                type="primary",
                use_container_width=True
            ):
                DocumentService().delete_document(document["id"])
                st.session_state["library_notice"] = f'"{document["title"]}" deleted'
                st.rerun()

# ---------- Add PDFs ----------
st.markdown(f"**Add PDFs to {subject['name']}**")
st.caption(
    "Text-based PDFs only (no scans). Name each file after its chapter, for "
    "example Chapter 1.pdf, so you can ask for it later."
)

version = st.session_state.get("library_upload_version", 0)

files = st.file_uploader(
    "Select PDFs",
    type=["pdf"],
    accept_multiple_files=True,
    key=f"lib_upload_{subject_id}_{version}",
    label_visibility="collapsed"
)

if files:

    count = len(files)

    with center_column():
        add_clicked = st.button(
            f"Add {count} file{'s' if count > 1 else ''} to {subject['name']}",
            type="primary",
            use_container_width=True,
            key=f"add_files_{subject_id}"
        )

    if add_clicked:

        service = DocumentService()

        added, skipped, failed = [], [], []

        bar = st.progress(0, text="Starting...")

        for number, file in enumerate(files):

            stage = {"count": 0}

            def show_step(message, number=number, name=file.name, stage=stage):
                stage["count"] += 1
                bar.progress(
                    min((number + min(stage["count"] / 4, 0.95)) / count, 1.0),
                    text=f"{name}: {message}..."
                )

            result = service.add_pdf(
                subject_id,
                file.name,
                file.getvalue(),
                progress=show_step
            )

            if result["success"]:
                added.append(
                    f"{result['title']}  ({result['pages']} pages, {result['chunks']} chunks)"
                )
            elif result.get("duplicate"):
                skipped.append(result["message"])
            else:
                failed.append(result["message"])

            bar.progress((number + 1) / count, text=f"{file.name} done")

        bar.empty()

        st.session_state["library_report"] = {
            "subject": subject["name"],
            "added": added,
            "skipped": skipped,
            "failed": failed
        }
        st.session_state["library_upload_version"] = version + 1

        st.rerun()

# ---------- Next steps ----------
if library.list_documents():

    st.markdown("**Next step**")

    n1, n2, n3 = st.columns(3)

    with n1:
        go_button("Summarize", "pages/Summary.py", key="lib_summary")
    with n2:
        go_button("Ask questions", "pages/Ask_AI.py", key="lib_ask")
    with n3:
        go_button("Take a quiz", "pages/Quiz.py", key="lib_quiz")
