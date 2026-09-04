from app.rag.hybrid_retrieval import hybrid_search
from app.llm.client import generate
from app.observability.tracing import trace_execution

QA_SYSTEM_PROMPT = """You are an expert research assistant answering questions about an academic paper.
Use the provided evidence chunks to provide a comprehensive, accurate, evidence-grounded answer.
Always cite your evidence using page numbers and sections (e.g. [Page X | Section Y]).
If the evidence does not directly answer the question, summarize what the provided passages state regarding the topic.

Answer format:
- Answer: ...
- Evidence Citations:
  - [Page X | Section Y]: "..."
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


@trace_execution("rag_ask")
def ask(question: str, k: int = 8, paper_id: str | None = None) -> str:
    results = hybrid_search(question, k=k, paper_id=paper_id)
    chunks = []
    if results and results.get("documents") and len(results["documents"]) > 0:
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