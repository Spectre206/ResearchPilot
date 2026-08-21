import pymupdf
from pathlib import Path

def extract_pdf(pdf_path: Path) -> list[dict]:
    doc = pymupdf.open(pdf_path)   # instead of fitz.open
    pages = []
    for page_number, page in enumerate(doc):
        text = page.get_text()
        pages.append({
            "page": page_number,
            "text": text
        })
    return pages