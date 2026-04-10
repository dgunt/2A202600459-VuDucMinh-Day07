from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb  # noqa: F401

            # TODO: initialize chromadb client + collection
            # Use ephemeral client (in-memory) for isolation between tests
            client = chromadb.EphemeralClient()
            #client = chromadb.PersistentClient(path="./chroma_db")
            # Delete collection if exists to ensure fresh start for tests
            try:
                client.delete_collection(name=self._collection_name)
            except Exception:
                pass
            self._collection = client.get_or_create_collection(name=self._collection_name)
            self._use_chroma = True
        except Exception as e:
            print(f"[DEBUG] ChromaDB initialization failed: {e}")
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        # TODO: build a normalized stored record for one document
        content = doc.content
        metadata = dict(doc.metadata or {})

        # Giữ nguyên metadata cũ, nhưng bổ sung doc_id để delete/filter hoạt động
        metadata["doc_id"] = doc.id
        embedding = self._embedding_fn(content)

        return {
        "id": str(self._next_index),
        "content": content,
        "embedding": embedding,
        "metadata": metadata,
        }
        #raise NotImplementedError("Implement EmbeddingStore._make_record")

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        # TODO: run in-memory similarity search over provided records
        query_embedding = self._embedding_fn(query)

        scored: list[dict[str, Any]] = []
        for record in records:
            score = _dot(query_embedding, record["embedding"])
            scored.append(
                {
                    "content": record["content"],
                    "metadata": record["metadata"],
                    "score": score,
                }
            )

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]
        #raise NotImplementedError("Implement EmbeddingStore._search_records")

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        # TODO: embed each doc and add to store
        if not docs:
            return

        records = []
        ids = []
        documents = []
        embeddings = []
        metadatas = []

        for doc in docs:
            record = self._make_record(doc)
            records.append(record)

            ids.append(record["id"])
            documents.append(record["content"])
            embeddings.append(record["embedding"])
            metadatas.append(record["metadata"])

            self._next_index += 1

        if self._use_chroma and self._collection is not None:
            self._collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
            )
        else:
            self._store.extend(records)
        #raise NotImplementedError("Implement EmbeddingStore.add_documents")

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        # TODO: embed query, compute similarities, return top_k
        if top_k <= 0:
            return []

        if self._use_chroma and self._collection is not None:
            results = self._collection.query(
                query_embeddings=[self._embedding_fn(query)],
                n_results=top_k,
            )

            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0] if "distances" in results else []

            output: list[dict[str, Any]] = []
            for i, content in enumerate(documents):
                item: dict[str, Any] = {
                    "content": content,
                    "metadata": metadatas[i] if i < len(metadatas) else {},
                }
                # ChromaDB returns distances (lower = more similar)
                # Convert to similarity score (higher = more similar) for consistent interface
                # cosine_similarity = 1 - cosine_distance
                if i < len(distances):
                    item["score"] = 1 - distances[i]  # Convert distance to similarity
                output.append(item)
            # Re-sort by score descending (in case ChromaDB doesn't)
            output.sort(key=lambda x: x.get("score", 0), reverse=True)
            return output

        return self._search_records(query, self._store, top_k)
        #raise NotImplementedError("Implement EmbeddingStore.search")

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        # TODO
        if self._use_chroma and self._collection is not None:
            return int(self._collection.count())
        return len(self._store)
        #raise NotImplementedError("Implement EmbeddingStore.get_collection_size")

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        # TODO: filter by metadata, then search among filtered chunks
        if top_k <= 0:
            return []

        metadata_filter = metadata_filter or {}

        if self._use_chroma and self._collection is not None:
            where = metadata_filter if metadata_filter else None
            results = self._collection.query(
                query_embeddings=[self._embedding_fn(query)],
                n_results=top_k,
                where=where,
            )

            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0] if "distances" in results else []

            output: list[dict[str, Any]] = []
            for i, content in enumerate(documents):
                item: dict[str, Any] = {
                    "content": content,
                    "metadata": metadatas[i] if i < len(metadatas) else {},
                }
                # ChromaDB returns distances (lower = more similar)
                # Convert to similarity score (higher = more similar)
                # cosine_similarity = 1 - cosine_distance
                if i < len(distances):
                    item["score"] = 1 - distances[i]
                output.append(item)
            # Re-sort by score descending
            output.sort(key=lambda x: x.get("score", 0), reverse=True)
            return output

        filtered_records = self._store
        if metadata_filter:
            filtered_records = [
                record
                for record in self._store
                if all(record["metadata"].get(k) == v for k, v in metadata_filter.items())
            ]

        return self._search_records(query, filtered_records, top_k)
        #raise NotImplementedError("Implement EmbeddingStore.search_with_filter")

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        # TODO: remove all stored chunks where metadata['doc_id'] == doc_id
        if self._use_chroma and self._collection is not None:
            results = self._collection.get(where={"doc_id": doc_id})
            ids = results.get("ids", [])
            if not ids:
                return False
            self._collection.delete(ids=ids)
            return True

        original_len = len(self._store)
        self._store = [
            record
            for record in self._store
            if record["metadata"].get("doc_id") != doc_id
        ]
        return len(self._store) != original_len
        #raise NotImplementedError("Implement EmbeddingStore.delete_document")
