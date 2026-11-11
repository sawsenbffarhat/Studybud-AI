"""Permanent library of subjects (folders) and documents (chapters), in SQLite."""

import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from config import LIBRARY_DB_PATH


def natural_key(text):
    """Sort 'Chapter 2' before 'Chapter 10'."""
    return [
        int(part) if part.isdigit() else part.lower()
        for part in re.split(r"(\d+)", text or "")
    ]


class Library:
    """
    Subject -> documents. A subject is like a folder in Drive ("Math"),
    a document is one PDF of that subject ("Chapter 1").
    """

    def __init__(self, db_path=LIBRARY_DB_PATH):

        self.db_path = str(db_path)

        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

    @contextmanager
    def _connect(self):

        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")

        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _init_db(self):

        with self._connect() as db:

            db.execute(
                """
                CREATE TABLE IF NOT EXISTS subjects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            db.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject_id INTEGER NOT NULL
                        REFERENCES subjects(id) ON DELETE CASCADE,
                    title TEXT NOT NULL,
                    file_name TEXT,
                    file_path TEXT,
                    file_hash TEXT,
                    pages INTEGER DEFAULT 0,
                    chunks INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(subject_id, file_hash)
                )
                """
            )

    # ------------------------------------------------------
    # Subjects
    # ------------------------------------------------------

    @staticmethod
    def _clean_name(name, what):

        name = re.sub(r"\s+", " ", (name or "")).strip()

        if not name:
            raise ValueError(f"Please enter a {what} name.")

        if len(name) > 80:
            raise ValueError(f"The {what} name is too long (max 80 characters).")

        return name

    def create_subject(self, name):

        name = self._clean_name(name, "subject")

        try:
            with self._connect() as db:
                cursor = db.execute(
                    "INSERT INTO subjects (name) VALUES (?)", (name,)
                )
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            raise ValueError("A subject with this name already exists.")

    def list_subjects(self):
        """Subjects with their document count, A to Z."""

        with self._connect() as db:
            rows = db.execute(
                """
                SELECT s.id, s.name, COUNT(d.id) AS documents
                FROM subjects s
                LEFT JOIN documents d ON d.subject_id = s.id
                GROUP BY s.id
                ORDER BY s.name COLLATE NOCASE
                """
            ).fetchall()

        return [dict(row) for row in rows]

    def get_subject(self, subject_id):

        with self._connect() as db:
            row = db.execute(
                "SELECT id, name FROM subjects WHERE id = ?", (subject_id,)
            ).fetchone()

        return dict(row) if row else None

    def rename_subject(self, subject_id, name):

        name = self._clean_name(name, "subject")

        try:
            with self._connect() as db:
                db.execute(
                    "UPDATE subjects SET name = ? WHERE id = ?",
                    (name, subject_id)
                )
        except sqlite3.IntegrityError:
            raise ValueError("A subject with this name already exists.")

    def delete_subject(self, subject_id):
        """Delete a subject and its documents. Returns the removed documents."""

        documents = self.list_documents(subject_id)

        with self._connect() as db:
            db.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))

        return documents

    # ------------------------------------------------------
    # Documents
    # ------------------------------------------------------

    def add_document(
        self,
        subject_id,
        title,
        file_name,
        file_path,
        file_hash,
        pages,
        chunks
    ):

        title = self._clean_name(title, "document")

        try:
            with self._connect() as db:
                cursor = db.execute(
                    """
                    INSERT INTO documents
                        (subject_id, title, file_name, file_path,
                         file_hash, pages, chunks)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        subject_id, title, file_name, str(file_path),
                        file_hash, pages, chunks
                    )
                )
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            raise ValueError("This PDF is already in the subject.")

    def find_by_hash(self, subject_id, file_hash):

        with self._connect() as db:
            row = db.execute(
                """
                SELECT id, title FROM documents
                WHERE subject_id = ? AND file_hash = ?
                """,
                (subject_id, file_hash)
            ).fetchone()

        return dict(row) if row else None

    def update_chunk_count(self, doc_id, chunks):

        with self._connect() as db:
            db.execute(
                "UPDATE documents SET chunks = ? WHERE id = ?",
                (chunks, doc_id)
            )

    def list_documents(self, subject_id=None):
        """Documents in natural order (Chapter 2 before Chapter 10)."""

        query = """
            SELECT d.id, d.subject_id, s.name AS subject, d.title,
                   d.file_name, d.file_path, d.pages, d.chunks, d.created_at
            FROM documents d
            JOIN subjects s ON s.id = d.subject_id
        """

        params = ()

        if subject_id is not None:
            query += " WHERE d.subject_id = ?"
            params = (subject_id,)

        with self._connect() as db:
            rows = db.execute(query, params).fetchall()

        documents = [dict(row) for row in rows]

        documents.sort(
            key=lambda d: (d["subject"].lower(), natural_key(d["title"]))
        )

        return documents

    def get_document(self, doc_id):

        for document in self.list_documents():
            if document["id"] == doc_id:
                return document

        return None

    def documents_by_ids(self, doc_ids):
        """{doc_id: document} for the given ids."""

        wanted = set(doc_ids)

        return {
            d["id"]: d for d in self.list_documents() if d["id"] in wanted
        }

    def rename_document(self, doc_id, title):

        title = self._clean_name(title, "document")

        with self._connect() as db:
            db.execute(
                "UPDATE documents SET title = ? WHERE id = ?",
                (title, doc_id)
            )

    def delete_document(self, doc_id):
        """Delete a document. Returns the removed document (or None)."""

        document = self.get_document(doc_id)

        with self._connect() as db:
            db.execute("DELETE FROM documents WHERE id = ?", (doc_id,))

        return document
