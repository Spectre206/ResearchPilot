from app.rag.vector_store import search
from app.llm.client import generate

QA_SYSTEM_PROMPT = """You are a research assistant answering questions about an academic paper.
Use ONLY the provided evidence chunks to answer.
If the evidence does not contain the answer, say: "The paper does not provide enough evidence to answer this question."
Always cite the evidence by including chunk IDs or page numbers.

Answer format:
- Answer: ...
- Evidence:
  - [page X | section Y]: "..."
"""

def format_evidence(chunks) -> str:
    lines = []
    for idx, chunk in enumerate(chunks, start=1):
        meta = chunk.get("metadata", {})
        lines.append(
            f"[{idx}] page {meta.get('page', '?')} | section {meta.get('section', '?')}\n"
            f"{chunk['document']}"
        )
    return "\n\n".join(lines)

def ask(question: str, k: int = 5) -> str:
    results = search(question, k=k)
    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({
            "document": doc,
            "metadata": meta,
            "distance": dist,
        })

    evidence = format_evidence(chunks)
    prompt = f"""Question:
{question}

Evidence:
{evidence}

Answer:"""
    return generate(prompt=prompt, system=QA_SYSTEM_PROMPT)