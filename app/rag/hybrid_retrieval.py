import math
import re
from typing import List, Dict, Any, Tuple
from app.rag.vector_store import get_collection, get_collection_name_for_paper
from app.observability.tracing import trace_execution


class BM25Okapi:
    """
    Lightweight, pure Python implementation of BM25Okapi algorithm.
    """

    def __init__(self, corpus: List[str], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = len(corpus)
        self.doc_tokens = [self._tokenize(doc) for doc in corpus]
        self.doc_lens = [len(tokens) for tokens in self.doc_tokens]
        self.avgdl = sum(self.doc_lens) / self.corpus_size if self.corpus_size > 0 else 0.0

        # Term frequency per document
        self.doc_freqs: List[Dict[str, int]] = []
        # Inverse document frequency
        self.df: Dict[str, int] = {}

        for tokens in self.doc_tokens:
            freq: Dict[str, int] = {}
            for token in tokens:
                freq[token] = freq.get(token, 0) + 1
            self.doc_freqs.append(freq)

            for token in set(tokens):
                self.df[token] = self.df.get(token, 0) + 1

        self.idf: Dict[str, float] = {}
        for token, freq in self.df.items():
            # BM25 IDF formula with smoothing
            idf_val = math.log((self.corpus_size - freq + 0.5) / (freq + 0.5) + 1.0)
            self.idf[token] = max(0.0, idf_val)

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"\w+", text.lower())

    def get_scores(self, query: str) -> List[float]:
        query_tokens = self._tokenize(query)
        scores = [0.0] * self.corpus_size

        if self.corpus_size == 0 or self.avgdl == 0:
            return scores

        for token in query_tokens:
            if token not in self.idf:
                continue
            idf = self.idf[token]
            for idx, doc_freq in enumerate(self.doc_freqs):
                freq = doc_freq.get(token, 0)
                if freq == 0:
                    continue
                doc_len = self.doc_lens[idx]
                numerator = freq * (self.k1 + 1.0)
                denominator = freq + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avgdl))
                scores[idx] += idf * (numerator / denominator)

        return scores


@trace_execution("hybrid_search")
def hybrid_search(
    query: str,
    k: int = 5,
    paper_id: str | None = None,
    rrf_k: int = 60,
    dense_weight: float = 0.5,
    keyword_weight: float = 0.5,
) -> Dict[str, Any]:
    """
    Hybrid retrieval combining Dense Vector Search (ChromaDB cosine similarity)
    and Sparse Keyword Search (BM25Okapi) using Reciprocal Rank Fusion (RRF).

    Returns a ChromaDB-like query result format:
    {
        "documents": [[doc1, doc2, ...]],
        "metadatas": [[meta1, meta2, ...]],
        "distances": [[dist1, dist2, ...]],
        "rrf_scores": [[score1, score2, ...]]
    }
    """
    collection_name = get_collection_name_for_paper(paper_id)
    collection = get_collection(collection_name)

    # 1. Fetch all documents for BM25 keyword search
    all_chunks = collection.get(include=["documents", "metadatas"])
    doc_ids = all_chunks.get("ids", [])
    documents = all_chunks.get("documents", [])
    metadatas = all_chunks.get("metadatas", [])

    if not doc_ids or not documents:
        return {"documents": [[]], "metadatas": [[]], "distances": [[]], "rrf_scores": [[]]}

    # Map chunk_id to document data
    id_to_data = {
        doc_ids[i]: {
            "document": documents[i],
            "metadata": metadatas[i],
            "index": i,
        }
        for i in range(len(doc_ids))
    }

    # 2. Dense Vector Search
    fetch_k = min(len(doc_ids), max(k * 3, 20))
    dense_ranks: Dict[str, int] = {}
    dense_distances: Dict[str, float] = {}

    try:
        dense_results = collection.query(
            query_texts=[query],
            n_results=fetch_k,
            include=["documents", "metadatas", "distances"],
        )

        if dense_results and dense_results.get("ids") and len(dense_results["ids"]) > 0:
            for rank, (chunk_id, dist) in enumerate(
                zip(dense_results["ids"][0], dense_results["distances"][0]), start=1
            ):
                dense_ranks[chunk_id] = rank
                dense_distances[chunk_id] = dist
    except Exception:
        pass


    # 3. BM25 Keyword Search
    bm25 = BM25Okapi(documents)
    bm25_scores = bm25.get_scores(query)

    # Rank documents by BM25 score descending
    sorted_bm25_indices = sorted(
        range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True
    )

    keyword_ranks: Dict[str, int] = {}
    for rank, idx in enumerate(sorted_bm25_indices[:fetch_k], start=1):
        if bm25_scores[idx] > 0:
            chunk_id = doc_ids[idx]
            keyword_ranks[chunk_id] = rank

    # 4. Reciprocal Rank Fusion (RRF)
    all_candidate_ids = set(dense_ranks.keys()).union(set(keyword_ranks.keys()))
    if not all_candidate_ids:
        # Fallback to top BM25 items if dense had no results
        all_candidate_ids = set(doc_ids[:fetch_k])

    rrf_scores: Dict[str, float] = {}
    for chunk_id in all_candidate_ids:
        d_rank = dense_ranks.get(chunk_id, None)
        k_rank = keyword_ranks.get(chunk_id, None)

        score = 0.0
        if d_rank is not None:
            score += dense_weight * (1.0 / (rrf_k + d_rank))
        if k_rank is not None:
            score += keyword_weight * (1.0 / (rrf_k + k_rank))

        rrf_scores[chunk_id] = score

    # Sort candidate chunks by RRF score descending
    ranked_ids = sorted(all_candidate_ids, key=lambda c_id: rrf_scores[c_id], reverse=True)[:k]

    res_docs = []
    res_metas = []
    res_dists = []
    res_scores = []

    for c_id in ranked_ids:
        chunk_data = id_to_data[c_id]
        res_docs.append(chunk_data["document"])
        res_metas.append(chunk_data["metadata"])
        res_dists.append(dense_distances.get(c_id, 0.0))
        res_scores.append(rrf_scores[c_id])

    return {
        "documents": [res_docs],
        "metadatas": [res_metas],
        "distances": [res_dists],
        "rrf_scores": [res_scores],
    }
