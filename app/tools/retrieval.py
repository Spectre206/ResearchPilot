from app.rag.vector_store import search, get_collection_name_for_paper

def search_paper(query: str, k: int = 5, paper_id: str | None = None) -> dict:
    """
    Tool: semantic search over the paper.
    Returns ChromaDB query result.
    """
    collection_name = get_collection_name_for_paper(paper_id)
    return search(query, k=k, collection_name=collection_name)