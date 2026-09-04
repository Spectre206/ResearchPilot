import pymupdf
from pathlib import Path
from typing import Tuple, Optional
from app.rag.chunking import chunk_pages
from app.rag.vector_store import add_chunks, get_collection_name_for_paper
from app.db import register_paper


def extract_pdf(pdf_path: Path) -> Tuple[list[dict], list[dict]]:
    """
    Extract text page by page and table of contents.
    Returns:
        pages: list of dicts with page number and text
        toc: list of dicts with level, title, page (1-indexed)
    """
    doc = pymupdf.open(str(pdf_path))

    pages = []
    for page_number, page in enumerate(doc):
        text = page.get_text()
        pages.append({
            "page": page_number,
            "text": text
        })

    # Extract TOC: list of [level, title, page_number]
    raw_toc = doc.get_toc()
    toc = []
    for level, title, page_num in raw_toc:
        toc.append({
            "level": level,
            "title": title.strip(),
            "page": page_num - 1  # convert to 0-indexed
        })

    return pages, toc


def ingest_pdf_paper(pdf_path: Path, paper_id: str, title: Optional[str] = None) -> Tuple[str, int]:
    """
    Extract PDF text, chunk, store in Chroma collection for paper_id,
    and register paper in SQLite database.
    """
    pages, toc = extract_pdf(pdf_path)
    chunks = chunk_pages(pages, toc)

    collection_name = get_collection_name_for_paper(paper_id)
    add_chunks(chunks, collection_name=collection_name)

    paper_title = title or pdf_path.stem.replace("_", " ").replace("-", " ").title()
    register_paper(
        paper_id=paper_id,
        filename=pdf_path.name,
        title=paper_title,
        chunk_count=len(chunks)
    )

    return paper_id, len(chunks)