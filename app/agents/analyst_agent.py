import json
from app.llm.client import generate

ANALYST_SYSTEM_PROMPT = """You are a research analyst.

Given a question and a set of evidence passages from an academic paper, write a clear, concise draft answer that directly addresses the question.

Rules:
- Use only the provided evidence.
- Do not add external knowledge.
- If the evidence is insufficient, say so.
- Structure the answer with:
  - Main finding(s)
  - Supporting details from the evidence
- Return JSON in this format:
{
  "draft_answer": "your draft answer text"
}
"""

def analyze_evidence(question: str, evidence: list[dict]) -> str:
    """
    Generate a draft answer from the question and evidence.
    `evidence` is a list of dicts with keys: text, page, section, chunk_id.
    Returns the draft answer as a string.
    """
    if not evidence:
        return "No evidence was retrieved to answer the question."

    # Format evidence for the prompt
    evidence_str = ""
    for i, item in enumerate(evidence, 1):
        evidence_str += (
            f"[{i}] page {item.get('page', '?')} | section {item.get('section', 'Unknown')}\n"
            f"{item.get('text', '')}\n\n"
        )

    prompt = f"""Question:
{question}

Evidence:
{evidence_str}

Analyze the evidence and produce a draft answer."""

    response = generate(
        prompt=prompt,
        system=ANALYST_SYSTEM_PROMPT,
        format="json",
    )

    try:
        data = json.loads(response)
        return data.get("draft_answer", response)
    except json.JSONDecodeError:
        # Fallback: return raw response if not JSON
        return response