import sys
import json
from pathlib import Path

from app.rag.ingestion import extract_pdf
from app.rag.chunking import chunk_pages
from app.rag.vector_store import add_chunks
from app.rag.rag_qa import ask as rag_ask
from app.agents.research_agent import run_agent, run_full_pipeline


def ingest_pdf(pdf_path: str):
    pages = extract_pdf(Path(pdf_path))
    chunks = chunk_pages(pages)
    add_chunks(chunks)
    print(f"Ingested {len(chunks)} chunks from {Path(pdf_path).name}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py path/to/paper.pdf [--mode rag|agent|pipeline]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    mode = "rag"  # default

    # Parse optional --mode argument
    if "--mode" in sys.argv:
        idx = sys.argv.index("--mode")
        if idx + 1 < len(sys.argv):
            mode = sys.argv[idx + 1]
            if mode not in {"rag", "agent", "pipeline"}:
                print(f"Invalid mode '{mode}'. Falling back to 'rag'.")
                mode = "rag"

    print(f"Running in {mode} mode\n")

    ingest_pdf(pdf_path)

    while True:
        question = input("\nAsk a question (or 'exit'): ")
        if question.lower() in {"exit", "quit"}:
            break

        if mode == "agent":
            result = run_agent(question)
            print("\nAgent final answer (JSON):")
            print(json.dumps(result, indent=2))

        elif mode == "pipeline":
            result = run_full_pipeline(question)
            print("\nPipeline result (JSON):")
            print(json.dumps(result, indent=2))

        else:  # rag mode
            answer = rag_ask(question)
            print("\n" + answer + "\n")


if __name__ == "__main__":
    main()