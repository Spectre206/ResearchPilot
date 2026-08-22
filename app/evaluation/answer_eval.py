import json
from app.llm.client import generate

JUDGE_SYSTEM_PROMPT = """You are an evaluation assistant.

Given:
- A question
- An expected answer
- A generated answer

Score the generated answer's correctness and relevance to the expected answer.

Return JSON in this format:
{"score": integer between 1 and 5, "explanation": "brief reason"}

Score guide:
5 = completely correct and relevant
4 = mostly correct, minor omissions
3 = partially correct
2 = mostly incorrect
1 = completely incorrect or irrelevant
"""

def evaluate_answer(question: str, expected_answer: str, generated_answer: str) -> dict:
    """
    Use an LLM to judge the generated answer against the expected answer.
    Falls back to simple substring matching if JSON parsing fails.
    """
    prompt = f"""Question:
{question}

Expected answer:
{expected_answer}

Generated answer:
{generated_answer}

Evaluate."""
    response = generate(
        prompt=prompt,
        system=JUDGE_SYSTEM_PROMPT,
        format="json",
    )

    try:
        result = json.loads(response)
        score = int(result.get("score", 0))
        explanation = result.get("explanation", "")
    except (json.JSONDecodeError, ValueError, TypeError):
        # Fallback: keyword match
        gen_lower = generated_answer.lower()
        exp_lower = expected_answer.lower()
        score = 5 if exp_lower in gen_lower else 1
        explanation = "Fallback: substring match used."

    return {
        "score": score,
        "explanation": explanation,
        "generated_answer": generated_answer,
        "expected_answer": expected_answer,
    }