import json
from app.llm.client import generate
from app.tools.retrieval import search_paper
from app.agents.analyst_agent import analyze_evidence
from app.agents.evidence_agent import retrieve_evidence_for_claims
from app.agents.critic_agent import critic_review
from app.agents.report_agent import create_report

AGENT_SYSTEM_PROMPT = """You are a research agent assisting with questions about an academic paper.

You have access to the following tool:
- search_paper(query: str) -> dict
  Searches the paper for relevant passages and returns the top results.

You must always respond with JSON in one of these two formats:

1. To call a tool:
{"action": "tool_call", "tool": "search_paper", "input": "your search query"}

2. To give the final answer:
{"action": "final_answer", "answer": "your answer", "evidence": ["chunk_id or page refs"]}

Rules:
- If you need information from the paper, call search_paper first.
- Do not answer from memory; use the evidence returned by the tool.
- If the evidence does not contain the answer, say: "The paper does not provide enough evidence to answer this question."
- Include evidence references in the final answer.
"""

def run_agent(question: str, max_steps: int = 4) -> dict:
    conversation = [
        {"role": "system", "content": AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    for step in range(max_steps):
        # Build prompt from conversation history
        prompt = ""
        for msg in conversation:
            role = msg["role"].upper()
            prompt += f"{role}: {msg['content']}\n\n"
        prompt += "ASSISTANT:"

        response = generate(
            prompt=prompt,
            system=AGENT_SYSTEM_PROMPT,
            format="json",
        )

        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            conversation.append({"role": "assistant", "content": response})
            conversation.append({"role": "user", "content": "Return valid JSON only."})
            continue

        if data.get("action") == "tool_call":
            tool_name = data.get("tool")
            tool_input = data.get("input", "")

            if tool_name == "search_paper":
                result = search_paper(tool_input)
                # Add assistant's tool call and tool result to conversation
                conversation.append({"role": "assistant", "content": response})
                conversation.append({
                    "role": "user",
                    "content": f"Tool result:\n{json.dumps(result)}",
                })
            else:
                conversation.append({
                    "role": "user",
                    "content": f"Unknown tool: {tool_name}",
                })

        elif data.get("action") == "final_answer":
            return data

    return {"answer": "Agent did not complete.", "evidence": []}

def run_full_pipeline(question: str) -> dict:
    """
    Full agentic pipeline:
    1. Research Agent -> retrieves evidence (and produces initial answer)
    2. Analyst Agent -> drafts a detailed answer from evidence
    3. Evidence Agent -> retrieves supporting evidence for the draft
    4. Critic Agent -> reviews draft against evidence
    5. Report Agent -> formats final output
    """
    # Step 1: Research Agent produces draft answer and evidence chunk IDs
    research_result = run_agent(question)
    draft_answer_initial = research_result.get("answer", "")
    initial_evidence_ids = research_result.get("evidence", [])

    # Step 1b: Get the actual evidence text using the chunk IDs
    # We'll retrieve full evidence based on the initial answer (or using IDs)
    # For simplicity, we'll use the Evidence Agent's retrieval function,
    # but pass the draft_answer_initial as the text to search for.
    # Later we can map IDs directly.
    evidence_list = retrieve_evidence_for_claims(draft_answer_initial, top_k=3)

    # Step 2: Use Analyst Agent to produce a better draft answer from the evidence
    # Convert evidence list to format expected by analyst
    if evidence_list:
        analyst_draft = analyze_evidence(question, evidence_list)
    else:
        # Fallback to initial answer
        analyst_draft = draft_answer_initial

    # Step 3: Critic reviews the analyst's draft
    critic_result = critic_review(analyst_draft, evidence_list)

    # Step 4: Report Agent formats final output
    report = create_report(question, critic_result, evidence_list)
    return report