import json
from typing import Dict, Any, List
from groq import Groq
from app.config import GROQ_API_KEY, GROQ_MODEL_NAME
from app.tools.retrieval import search_paper
from app.observability.tracing import trace_execution

AGENT_SYSTEM_PROMPT = """You are an evidence-grounded AI research assistant.
You answer user questions about an academic paper by using the provided `search_paper` tool.

Instructions:
1. Whenever you need to answer a question or verify details, call `search_paper` with a focused search query.
2. You may make multiple tool calls if needed to gather complete evidence.
3. Rely ONLY on the evidence retrieved from the tool calls.
4. Always format your final response with explicit citations (e.g. [Page X | Section Y]).
5. If the paper does not contain sufficient evidence after searching, state that clearly.
"""

SEARCH_TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "search_paper",
        "description": "Searches the paper for relevant text chunks, returning matches with text, page number, section, and distance.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Semantic search query to retrieve relevant paragraphs or sections from the paper."
                },
                "k": {
                    "type": "integer",
                    "description": "Number of chunks to retrieve (default: 5).",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    }
}


@trace_execution("run_agent")
def run_agent(question: str, paper_id: str | None = None, max_turns: int = 6) -> Dict[str, Any]:
    """
    Synchronous Groq agent using native tool/function calling loop.
    """
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set. Please set it in your .env file.")

    client = Groq(api_key=GROQ_API_KEY)
    messages = [
        {"role": "system", "content": AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": question}
    ]
    tools = [SEARCH_TOOL_DEFINITION]
    steps: List[Dict[str, Any]] = []

    for turn in range(max_turns):
        response = client.chat.completions.create(
            model=GROQ_MODEL_NAME,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.1,
        )

        response_message = response.choices[0].message
        messages.append(response_message)

        # Handle function tool calls
        if response_message.tool_calls:
            for tool_call in response_message.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)

                if fn_name == "search_paper":
                    query = fn_args.get("query", "")
                    k = fn_args.get("k", 5)

                    # Run search_paper tool with paper_id context
                    results = search_paper(query=query, k=k, paper_id=paper_id)

                    # Format retrieved chunks
                    evidence_chunks = []
                    if results and results.get("documents") and len(results["documents"]) > 0:
                        for doc, meta, dist in zip(
                            results["documents"][0],
                            results["metadatas"][0],
                            results["distances"][0],
                        ):
                            evidence_chunks.append({
                                "page": meta.get("page", "?"),
                                "section": meta.get("section", "Unknown"),
                                "chunk_id": meta.get("chunk_id", ""),
                                "text": doc,
                                "distance": dist,
                            })

                    tool_result_str = json.dumps(evidence_chunks)
                    steps.append({
                        "turn": turn + 1,
                        "tool": fn_name,
                        "args": fn_args,
                        "results_count": len(evidence_chunks),
                        "evidence": evidence_chunks,
                    })

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result_str,
                    })
        else:
            # Final answer produced
            final_answer = response_message.content or ""
            if "</think>" in final_answer:
                final_answer = final_answer.split("</think>")[-1].strip()

            return {
                "question": question,
                "paper_id": paper_id,
                "answer": final_answer,
                "steps": steps,
            }

    # Fallback if max turns reached
    last_content = response_message.content if response_message else "Agent max turns reached."
    return {
        "question": question,
        "paper_id": paper_id,
        "answer": last_content,
        "steps": steps,
    }
