import sys
import json
from pathlib import Path

from app.rag.ingestion import extract_pdf
from app.rag.chunking import chunk_pages
from app.rag.vector_store import add_chunks, reset_collection
from app.rag.rag_qa import ask as rag_ask
from app.agents.research_agent import run_full_pipeline


def ingest_pdf(pdf_path: str):
    """Extract pages + TOC, chunk, reset collection, and add new chunks."""
    pages, toc = extract_pdf(Path(pdf_path))
    chunks = chunk_pages(pages, toc)
    reset_collection()
    add_chunks(chunks)
    print(f"Ingested {len(chunks)} chunks from {Path(pdf_path).name}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py path/to/paper.pdf [--mode rag|pipeline]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    mode = "rag"

    if "--mode" in sys.argv:
        idx = sys.argv.index("--mode")
        if idx + 1 < len(sys.argv):
            mode = sys.argv[idx + 1]
            if mode not in {"rag", "pipeline"}:
                print(f"Invalid mode '{mode}'. Falling back to 'rag'.")
                mode = "rag"

    print(f"Running in {mode} mode\n")

    ingest_pdf(pdf_path)

    while True:
        question = input("\nAsk a question (or 'exit'): ")
        if question.lower() in {"exit", "quit"}:
            break

        if mode == "pipeline":
            result = run_full_pipeline(question)
            print("\nPipeline result (JSON):")
            print(json.dumps(result, indent=2))
        else:
            answer = rag_ask(question)
            print("\n" + answer + "\n")


if __name__ == "__main__":
    main()