"""
Thin wrapper around a local, persistent Chroma vector store.

Uses Chroma's bundled default embedding function (a small ONNX model,
downloaded once on first run) so this works out of the box with no
external embeddings API or account. If you later want higher-quality
retrieval, swap in Voyage AI or OpenAI embeddings here -- everything else
in the app stays the same because qa_engine.py only talks to this module.
"""

import chromadb

from chunking import Chunk

import config


class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=config.CHROMA_DIR)
        self.collection = self.client.get_or_create_collection(name=config.COLLECTION_NAME)

    def reset(self):
        self.client.delete_collection(config.COLLECTION_NAME)
        self.collection = self.client.get_or_create_collection(name=config.COLLECTION_NAME)

    def add_chunks(self, chunks: list[Chunk], batch_size: int = 100):
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            self.collection.add(
                ids=[c.id for c in batch],
                documents=[c.text for c in batch],
                metadatas=[
                    {
                        "source": c.source,
                        "source_id": c.source_id,
                        "url": c.url or "",
                        **{k: v for k, v in c.metadata.items() if isinstance(v, (str, int, float, bool))},
                    }
                    for c in batch
                ],
            )

    def query(self, question: str, top_k: int = None) -> list[dict]:
        top_k = top_k or config.TOP_K
        results = self.collection.query(query_texts=[question], n_results=top_k)

        hits = []
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for text, meta, distance in zip(docs, metas, distances):
            hits.append({"text": text, "metadata": meta, "distance": distance})
        return hits

    def count(self) -> int:
        return self.collection.count()
