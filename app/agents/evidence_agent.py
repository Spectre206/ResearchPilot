import json
from app.tools.retrieval import search_paper

def retrieve_evidence_for_claims(draft_answer: str, top_k: int = 2, paper_id: str | None = None) -> list[dict]:
    """
    Given a draft answer, split it into sentences and retrieve supporting evidence
    for each sentence. Returns a list of unique evidence dicts with text, page, section.
    """
    # Simple sentence splitter (by period, keeping it basic)
    sentences = [s.strip() for s in draft_answer.split('.') if s.strip()]
    evidence_map = {}  # key: chunk_id, value: dict

    for sentence in sentences:
        # Use the sentence as a search query
        results = search_paper(sentence, k=top_k, paper_id=paper_id)
        # results is ChromaDB format
        if results and results.get("documents") and len(results["documents"]) > 0:
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            ):
                chunk_id = meta.get("chunk_id", "")
                if chunk_id and chunk_id not in evidence_map:
                    evidence_map[chunk_id] = {
                        "chunk_id": chunk_id,
                        "text": doc,
                        "page": meta.get("page", "?"),
                        "section": meta.get("section", "Unknown"),
                        "distance": dist,
                    }

    # Return list sorted by distance (closest first)
    return sorted(evidence_map.values(), key=lambda x: x["distance"])