import os
import json
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

class VectorStore:
    def __init__(self, dim: int = 384):
        self.dim = dim
        self.index = faiss.IndexFlatL2(dim)
        self.id_map = []  # list of dicts storing metadata
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    def add_documents(self, docs: list[dict]):
        """docs = [{"id": <str>, "text": <str>, "metadata": {...}}]"""
        texts = [d["text"] for d in docs]
        vectors = self.model.encode(texts, normalize_embeddings=True)
        vectors = np.asarray(vectors).astype('float32')
        self.index.add(vectors)
        self.id_map.extend(docs)

    def search(self, query: str, k: int = 5):
        q_vec = self.model.encode([query], normalize_embeddings=True)
        q_vec = np.asarray(q_vec).astype('float32')
        D, I = self.index.search(q_vec, k)
        results = []
        for idx in I[0]:
            if idx < len(self.id_map):
                results.append(self.id_map[idx])
        return results

# Simple persistent store (JSON) for demo purposes
def save_store(store: VectorStore, path: str = "vector_store.json"):
    data = {
        "dim": store.dim,
        "metadata": store.id_map,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_store(path: str = "vector_store.json") -> VectorStore:
    if not os.path.exists(path):
        return VectorStore()
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    store = VectorStore(dim=data.get("dim", 384))
    store.id_map = data.get("metadata", [])
    # Re‑build index from stored vectors (not persisted for simplicity)
    # In a real system you would also persist the faiss index binary.
    return store
