from app.tools.retrieval import search_paper
from app.agents.evidence_agent import retrieve_evidence_for_claims
from app.agents.critic_agent import critic_review
from app.agents.report_agent import create_report
from app.agents.analyst_agent import analyze_evidence


def run_full_pipeline(question: str, paper_id: str | None = None) -> dict:
    """
    Deterministic multi-agent pipeline:
    1. Retrieve initial evidence using the question.
    2. Analyst Agent drafts an answer from the evidence.
    3. Evidence Agent retrieves supporting passages for the draft.
    4. Critic Agent reviews the answer against evidence.
    5. Report Agent formats the final output.
    """
    # Step 1: Retrieve initial evidence
    results = search_paper(question, k=5, paper_id=paper_id)

    evidence_list = []
    if results and results.get("documents") and len(results["documents"]) > 0:
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            evidence_list.append({
                "text": doc,
                "page": meta.get("page", "?"),
                "section": meta.get("section", "Unknown"),
                "chunk_id": meta.get("chunk_id", ""),
                "distance": dist,
            })

    # Step 2: Analyst Agent drafts an answer from the evidence
    if evidence_list:
        analyst_draft = analyze_evidence(question, evidence_list)
    else:
        analyst_draft = "No evidence retrieved to answer the question."

    # Step 3: Evidence Agent retrieves supporting evidence for the draft answer
    evidence_for_answer = retrieve_evidence_for_claims(analyst_draft, top_k=3, paper_id=paper_id)

    # Fallback to initial evidence if nothing found
    if not evidence_for_answer:
        evidence_for_answer = evidence_list

    # Step 4: Critic reviews the analyst's draft
    critic_result = critic_review(analyst_draft, evidence_for_answer)

    # Step 5: Report Agent formats final output
    report = create_report(question, critic_result, evidence_for_answer)
    return report