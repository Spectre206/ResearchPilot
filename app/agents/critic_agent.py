import json
from app.llm.client import generate

CRITIC_SYSTEM_PROMPT = """You are a critical reviewer for a research assistant.

Given a draft answer and a list of evidence (each with text, page, section), evaluate whether every important claim in the answer is supported by the evidence.

Return JSON in this format:
{
  "supported": true or false,
  "issues": ["list of issues, if any"],
  "revised_answer": "a revised answer that only contains supported claims, or the original if all supported"
}

Rules:
- Be strict: if a claim cannot be found in the evidence, mark it as unsupported.
- Do not invent new information.
- If the answer is fully supported, set "supported" to true and "issues" to an empty list.
- If not supported, explain the issues and provide a revised answer that removes unsupported claims.
"""

def critic_review(draft_answer: str, evidence: list[dict]) -> dict:
    """
    Use the LLM to review the answer against the evidence.
    """
    evidence_str = json.dumps(evidence, indent=2)
    prompt = f"""Draft answer:
{draft_answer}

Evidence:
{evidence_str}

Evaluate the answer and return your JSON verdict."""

    response = generate(
        prompt=prompt,
        system=CRITIC_SYSTEM_PROMPT,
        format="json",
    )

    try:
        result = json.loads(response)
    except json.JSONDecodeError:
        # If JSON parsing fails, return a safe fallback
        result = {
            "supported": False,
            "issues": ["Critic could not parse model response."],
            "revised_answer": draft_answer,
        }
    return result