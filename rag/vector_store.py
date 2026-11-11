from functools import lru_cache

import chromadb
from chromadb.config import Settings

from config import (
    CHROMA_DB_PATH,
    COLLECTION_NAME,
    KEYWORD_HITS,
    MAX_CONTEXT_CHARS,
    RETRIEVAL_TOP_K,
)

from rag.embeddings import EmbeddingModel


@lru_cache(maxsize=1)
def _get_client(path):
    """One Chroma client per process."""
    return chromadb.PersistentClient(
        path=path,
        settings=Settings(anonymized_telemetry=False)
    )


class VectorStore:
    """
    One permanent ChromaDB collection holding the chunks of every document.

    Every chunk carries {"doc_id", "subject_id", "page", "chunk_index"}.
    Passing doc_ids limits a search to chosen documents (a chapter, several
    chapters or a whole subject). doc_ids=None means "everything".
    """

    def __init__(self, collection_name=None):

        self.collection_name = collection_name or COLLECTION_NAME

        self.client = _get_client(CHROMA_DB_PATH)

        self._embedding_model = None

        self.collection = self.client.get_or_create_collection(
            name=self.collection_name
        )

    @property
    def embedding_model(self):
        """Loaded lazily, so services that never search stay light."""
        if self._embedding_model is None:
            self._embedding_model = EmbeddingModel()

        return self._embedding_model

    # ------------------------------------------------------
    # Helpers
    # ------------------------------------------------------

    @staticmethod
    def _where(doc_ids):
        """Chroma filter for a list of document ids."""

        if doc_ids is None:
            return None

        doc_ids = list(doc_ids)

        if len(doc_ids) == 1:
            return {"doc_id": doc_ids[0]}

        return {"doc_id": {"$in": doc_ids}}

    @staticmethod
    def _scope_kwargs(where):
        return {"where": where} if where else {}

    def count(self, doc_ids=None):

        if doc_ids is not None and len(list(doc_ids)) == 0:
            return 0

        result = self.collection.get(
            include=[],
            **self._scope_kwargs(self._where(doc_ids))
        )

        return len(result["ids"])

    # ------------------------------------------------------
    # Writing
    # ------------------------------------------------------

    def add_documents(
        self,
        ids,
        embeddings,
        documents,
        metadatas=None,
        batch_size=500
    ):

        for start in range(0, len(ids), batch_size):

            end = start + batch_size

            kwargs = {}

            if metadatas is not None:
                kwargs["metadatas"] = metadatas[start:end]

            self.collection.add(
                ids=ids[start:end],
                embeddings=embeddings[start:end],
                documents=documents[start:end],
                **kwargs
            )

    def delete_document(self, doc_id):
        """Remove every chunk of one document."""
        self.collection.delete(where={"doc_id": doc_id})

    # ------------------------------------------------------
    # Searching
    # ------------------------------------------------------

    @staticmethod
    def _pack(ids, documents, metadatas, distances=None):
        return {
            "ids": ids,
            "documents": documents,
            "metadatas": metadatas,
            "distances": distances or [None] * len(ids)
        }

    def search(
        self,
        query,
        n_results=RETRIEVAL_TOP_K,
        doc_ids=None
    ):
        """Semantic search (meaning), optionally limited to some documents."""

        total = self.count(doc_ids)

        if total == 0:
            return self._pack([], [], [])

        query_embedding = self.embedding_model.encode(
            [query]
        )[0].tolist()

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(n_results, total),
            **self._scope_kwargs(self._where(doc_ids))
        )

        return self._pack(
            results["ids"][0],
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        )

    def keyword_search(
        self,
        query,
        doc_ids=None,
        limit=KEYWORD_HITS
    ):
        """
        Exact match for a word or a short sentence (the semantic search can
        miss exact terms). Chroma's text match is case-sensitive, so a few
        spellings of the query are tried.
        """

        text = " ".join((query or "").replace("?", " ").split()).strip(" .,!;:")

        if not text or len(text.split()) > 5 or len(text) < 2:
            return self._pack([], [], [])

        if doc_ids is not None and len(list(doc_ids)) == 0:
            return self._pack([], [], [])

        variants = []

        for variant in (text, text.lower(), text.capitalize(), text.title(), text.upper()):
            if variant not in variants:
                variants.append(variant)

        found = {}

        for variant in variants:

            if len(found) >= limit:
                break

            result = self.collection.get(
                where_document={"$contains": variant},
                limit=limit,
                include=["documents", "metadatas"],
                **self._scope_kwargs(self._where(doc_ids))
            )

            for chunk_id, doc, meta in zip(
                result["ids"], result["documents"], result["metadatas"]
            ):
                if chunk_id not in found and len(found) < limit:
                    found[chunk_id] = (doc, meta)

        return self._pack(
            list(found.keys()),
            [value[0] for value in found.values()],
            [value[1] for value in found.values()]
        )

    # ------------------------------------------------------
    # Reading whole documents
    # ------------------------------------------------------

    def get_all_chunks(self, doc_ids=None):
        """Chunks in reading order (documents in the given order)."""

        if doc_ids is not None and len(list(doc_ids)) == 0:
            return []

        result = self.collection.get(
            include=["documents", "metadatas"],
            **self._scope_kwargs(self._where(doc_ids))
        )

        order = {}

        if doc_ids is not None:
            order = {doc_id: i for i, doc_id in enumerate(doc_ids)}

        chunks = []

        for chunk_id, text, meta in zip(
            result["ids"], result["documents"], result["metadatas"]
        ):

            meta = meta or {}

            chunks.append({
                "id": chunk_id,
                "text": text,
                "doc_id": meta.get("doc_id"),
                "page": meta.get("page"),
                "chunk_index": meta.get("chunk_index", 0)
            })

        chunks.sort(
            key=lambda c: (
                order.get(c["doc_id"], c["doc_id"] or 0),
                c["chunk_index"]
            )
        )

        return chunks

    @staticmethod
    def _sample_evenly(chunks, budget):
        """Pick chunks spread across the whole text within a character budget."""

        if budget <= 0 or not chunks:
            return []

        total = sum(len(chunk["text"]) for chunk in chunks)

        if total <= budget:
            return list(chunks)

        wanted = max(1, int(len(chunks) * budget / total))

        picked = []
        used = 0

        for i in range(wanted):

            chunk = chunks[int(i * len(chunks) / wanted)]

            if used + len(chunk["text"]) > budget and picked:
                break

            picked.append(chunk)
            used += len(chunk["text"])

        return picked

    def get_context(
        self,
        max_chars=MAX_CONTEXT_CHARS,
        focus_queries=None,
        doc_ids=None
    ):
        """
        Build the lecture context for summary / quiz / reflection.

        - Small scopes are returned completely.
        - Big scopes are sampled evenly across all their pages.
        - focus_queries (for example weak topics) are searched semantically
          first and get up to 70% of the budget.

        Returns:
            (context_text, list_of_chunks_used)
        """

        chunks = self.get_all_chunks(doc_ids)

        if not chunks:
            return "", []

        selected = {}
        budget = max_chars

        if focus_queries:

            focus_budget = int(max_chars * 0.7)
            used = 0

            by_id = {chunk["id"]: chunk for chunk in chunks}

            for query in focus_queries:

                result = self.search(query, n_results=3, doc_ids=doc_ids)

                for chunk_id in result["ids"]:

                    chunk = by_id.get(chunk_id)

                    if chunk is None or chunk_id in selected:
                        continue

                    if used + len(chunk["text"]) > focus_budget:
                        continue

                    selected[chunk_id] = chunk
                    used += len(chunk["text"])

            budget = max_chars - used

        remaining = [
            chunk for chunk in chunks
            if chunk["id"] not in selected
        ]

        for chunk in self._sample_evenly(remaining, budget):
            selected[chunk["id"]] = chunk

        position = {chunk["id"]: i for i, chunk in enumerate(chunks)}

        final = sorted(
            selected.values(),
            key=lambda chunk: position[chunk["id"]]
        )

        context = "\n\n".join(chunk["text"] for chunk in final)

        return context, final
