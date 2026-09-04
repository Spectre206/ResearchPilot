import pymupdf
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any
from app.rag.chunking import chunk_pages
from app.rag.vector_store import add_chunks, get_collection_name_for_paper
from app.db import register_paper


def extract_font_headings(page) -> List[str]:
    """Detect section headings from font sizes and bold text in PyMuPDF dict output."""
    headings = []
    try:
        blocks = page.get_text("dict").get("blocks", [])
        font_sizes = []
        for b in blocks:
            if b.get("type") == 0:  # text block
                for line in b.get("lines", []):
                    for span in line.get("spans", []):
                        font_sizes.append(span.get("size", 0))

        if not font_sizes:
            return headings

        avg_size = sum(font_sizes) / len(font_sizes)

        for b in blocks:
            if b.get("type") == 0:
                for line in b.get("lines", []):
                    line_text = "".join([span.get("text", "") for span in line.get("spans", [])]).strip()
                    if not line_text or len(line_text) < 3 or len(line_text) > 80:
                        continue
                    if line_text.endswith("."):
                        continue

                    # Check span features (size > avg + 1.2 or bold)
                    is_heading = False
                    for span in line.get("spans", []):
                        size = span.get("size", 0)
                        flags = span.get("flags", 0)
                        font_name = span.get("font", "").lower()

                        if size > avg_size + 1.2 or (flags & 2) or "bold" in font_name:
                            is_heading = True
                            break

                    if is_heading:
                        headings.append(line_text)
    except Exception:
        pass
    return headings


def extract_tables_from_page(page) -> List[str]:
    """Extract markdown representation of tables using PyMuPDF if available."""
    tables_md = []
    try:
        tabs = page.find_tables()
        if tabs and hasattr(tabs, "tables"):
            for tab in tabs.tables:
                df = tab.to_pandas()
                md = df.to_markdown(index=False)
                if md and md.strip():
                    tables_md.append(md.strip())
    except Exception:
        pass
    return tables_md


def extract_pdf(pdf_path: Path) -> Tuple[list[dict], list[dict]]:
    """
    Extract text page by page, detected tables, font-based headings, and TOC.
    Returns:
        pages: list of dicts with page number, text, tables, and detected_headings
        toc: list of dicts with level, title, page (0-indexed)
    """
    doc = pymupdf.open(str(pdf_path))

    pages = []
    for page_number, page in enumerate(doc):
        text = page.get_text()
        tables = extract_tables_from_page(page)
        headings = extract_font_headings(page)

        pages.append({
            "page": page_number,
            "text": text,
            "tables": tables,
            "detected_headings": headings,
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
    Extract PDF text & tables, chunk, store in Chroma collection for paper_id,
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