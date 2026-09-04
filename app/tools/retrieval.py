from app.rag.hybrid_retrieval import hybrid_search

def search_paper(query: str, k: int = 5, paper_id: str | None = None) -> dict:
    """
    Tool: hybrid search (dense vector + BM25 keyword matching) over the paper.
    Returns ChromaDB-style query result with RRF scores.
    """
    return hybrid_search(query=query, k=k, paper_id=paper_id)