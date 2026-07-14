"""
Hybrid retrieval for the Technical agent: combines dense (Chroma) and sparse
(BM25) retrieval using Reciprocal Rank Fusion (RRF), the same pattern used in
the DocChat project.
"""

import os
import pickle
from functools import lru_cache

from langchain_chroma import Chroma

from app.config import CHROMA_PERSIST_DIR, get_embeddings

BM25_INDEX_PATH = os.path.join(os.path.dirname(__file__), "bm25_index.pkl")

RRF_K = 60  # standard RRF smoothing constant


@lru_cache(maxsize=1)
def _load_dense_store() -> Chroma:
    return Chroma(
        persist_directory=CHROMA_PERSIST_DIR,
        embedding_function=get_embeddings(),
        collection_name="support_docs",
    )


@lru_cache(maxsize=1)
def _load_sparse_index():
    with open(BM25_INDEX_PATH, "rb") as f:
        return pickle.load(f)


def _dense_search(query: str, top_k: int) -> list[str]:
    """Returns chunk identifiers ranked by dense similarity."""
    store = _load_dense_store()
    results = store.similarity_search(query, k=top_k)
    return [f"{d.metadata['source']}::{d.metadata['chunk_index']}" for d in results], results


def _sparse_search(query: str, top_k: int):
    """Returns chunk identifiers ranked by BM25 score."""
    data = _load_sparse_index()
    bm25 = data["bm25"]
    docs = data["docs"]
    scores = bm25.get_scores(query.lower().split())
    ranked_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
    ids = [f"{docs[i].metadata['source']}::{docs[i].metadata['chunk_index']}" for i in ranked_idx]
    result_docs = [docs[i] for i in ranked_idx]
    return ids, result_docs


def hybrid_search(query: str, top_k: int = 5, candidate_k: int = 10) -> list[dict]:
    """
    Runs dense + sparse retrieval independently, fuses the two ranked lists
    with Reciprocal Rank Fusion, and returns the top_k fused results.

    RRF score for a document = sum over each ranker of 1 / (RRF_K + rank)
    """
    dense_ids, dense_docs = _dense_search(query, candidate_k)
    sparse_ids, sparse_docs = _sparse_search(query, candidate_k)

    doc_lookup = {}
    for cid, doc in zip(dense_ids, dense_docs):
        doc_lookup[cid] = doc
    for cid, doc in zip(sparse_ids, sparse_docs):
        doc_lookup.setdefault(cid, doc)

    fused_scores: dict[str, float] = {}
    for rank, cid in enumerate(dense_ids):
        fused_scores[cid] = fused_scores.get(cid, 0.0) + 1.0 / (RRF_K + rank + 1)
    for rank, cid in enumerate(sparse_ids):
        fused_scores[cid] = fused_scores.get(cid, 0.0) + 1.0 / (RRF_K + rank + 1)

    ranked = sorted(fused_scores.items(), key=lambda kv: kv[1], reverse=True)[:top_k]

    results = []
    for cid, score in ranked:
        doc = doc_lookup[cid]
        results.append(
            {
                "chunk_id": cid,
                "source": doc.metadata["source"],
                "content": doc.page_content,
                "rrf_score": round(score, 5),
            }
        )
    return results
