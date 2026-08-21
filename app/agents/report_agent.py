def create_report(question: str, critic_result: dict, evidence: list[dict]) -> dict:
    """
    Combine the question, revised answer, and evidence into a final report dict.
    """
    final_answer = critic_result.get("revised_answer", "")
    supported = critic_result.get("supported", False)
    issues = critic_result.get("issues", [])

    # Format evidence nicely
    formatted_evidence = []
    for item in evidence:
        formatted_evidence.append({
            "chunk_id": item.get("chunk_id", ""),
            "page": item.get("page", "?"),
            "section": item.get("section", "Unknown"),
            "text": item.get("text", ""),
            "relevance": round(1 - item.get("distance", 0), 3) if item.get("distance") is not None else None,
        })

    return {
        "question": question,
        "answer": final_answer,
        "supported": supported,
        "issues": issues,
        "evidence": formatted_evidence,
    }