from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        # TODO: store references to store and llm_fn
        self._store = store
        self._llm_fn = llm_fn
        #pass

    def answer(self, question: str, top_k: int = 3) -> str:
        # TODO: retrieve chunks, build prompt, call llm_fn
        chunks = self._store.search(question, top_k=top_k)

        if chunks:
            context = "\n\n".join(
                f"[Chunk {i + 1}]\n{chunk['content']}"
                for i, chunk in enumerate(chunks)
            )
        else:
            context = "No relevant context found in the knowledge base."

        prompt = (
            "You are a helpful assistant answering questions using the provided knowledge base context.\n"
            "Use the context to answer the question as accurately as possible.\n"
            "If the context is insufficient, say that you do not have enough information from the knowledge base.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\n\n"
            "Answer:"
        )

        return self._llm_fn(prompt)
        #raise NotImplementedError("Implement KnowledgeBaseAgent.answer")
