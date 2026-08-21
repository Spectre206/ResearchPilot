from app.rag.vector_store import search

def search_paper(query: str, k: int = 5) -> dict:
    """
    Tool: semantic search over the paper.
    Returns ChromaDB query result.
    """
    return search(query, k=k)