import pymupdf
from pathlib import Path

def extract_pdf(pdf_path: Path) -> tuple[list[dict], list[dict]]:
    """
    Extract text page by page and table of contents.
    Returns:
        pages: list of dicts with page number and text
        toc: list of dicts with level, title, page (1-indexed)
    """
    doc = pymupdf.open(pdf_path)

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