"""ChromaDB vector store for semantic retrieval of past research."""
import os
import hashlib
from typing import Any


class ResearchVectorStore:
    def __init__(self, persist_dir: str = None):
        self._collection = None
        self._available = False

        path = persist_dir or os.getenv("CHROMA_DB_PATH", "./chroma_db")
        try:
            import chromadb
            client = chromadb.PersistentClient(path=path)
            self._collection = client.get_or_create_collection(
                name="research_findings",
                metadata={"hnsw:space": "cosine"},
            )
            self._available = True
            print("✅ ChromaDB connected")
        except Exception as e:
            print(f"⚠️  ChromaDB unavailable ({e}), vector store disabled")

    @property
    def available(self) -> bool:
        return self._available

    def store(self, query: str, findings: dict) -> None:
        if not self._available:
            return
        try:
            doc_id = hashlib.md5(query.lower().strip().encode()).hexdigest()
            text = f"Query: {query}\n\nFindings: {findings.get('summary', '')}"
            self._collection.upsert(
                ids=[doc_id],
                documents=[text],
                metadatas=[{"query": query, "agent_count": findings.get("agent_count", 0)}],
            )
        except Exception as e:
            print(f"⚠️  ChromaDB store error: {e}")

    def query_similar(self, query: str, n_results: int = 3) -> list[dict]:
        if not self._available:
            return []
        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=min(n_results, self._collection.count()),
            )
            if not results["documents"] or not results["documents"][0]:
                return []
            return [
                {"text": doc, "metadata": meta}
                for doc, meta in zip(
                    results["documents"][0], results["metadatas"][0]
                )
            ]
        except Exception:
            return []
