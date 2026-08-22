from app.rag.vector_store import search

def evaluate_retrieval(question: str, relevant_pages: list[int], k: int = 5) -> dict:
    """
    Evaluate retrieval quality for a single question.

    Returns:
        dict with keys: recall, precision, mrr, retrieved_pages, relevant_pages
    """
    results = search(question, k=k)

    # Extract pages from metadata
    retrieved_pages = [meta["page"] for meta in results["metadatas"][0]]

    # Compute hits
    hits = [1 if page in relevant_pages else 0 for page in retrieved_pages]

    recall = 1 if any(hits) else 0
    precision = sum(hits) / k if k > 0 else 0

    # MRR: rank of first relevant page
    rank = None
    for i, h in enumerate(hits, start=1):
        if h:
            rank = i
            break
    mrr = 1 / rank if rank else 0

    return {
        "recall": recall,
        "precision": precision,
        "mrr": mrr,
        "retrieved_pages": retrieved_pages,
        "relevant_pages": relevant_pages,
    }