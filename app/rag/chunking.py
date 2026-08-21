import re
from app.config import CHUNK_SIZE, CHUNK_OVERLAP


def detect_section(text: str, current_section: str = "Unknown") -> str:
    """
    Very simple section detector.
    Looks for common heading patterns:
    - 1. Introduction
    - 2 Related Work
    - Abstract
    - References
    """
    lines = text.strip().splitlines()
    for line in lines[:5]:
        line = line.strip()
        if not line:
            continue

        # Numbered section: "1.", "2.1"
        if re.match(r"^\d+(\.\d+)*\s+\w+", line):
            return line

        # Common headings
        if line.lower() in {
            "abstract",
            "introduction",
            "related work",
            "methodology",
            "experiments",
            "results",
            "discussion",
            "conclusion",
            "references",
        }:
            return line

    return current_section


def chunk_pages(pages: list[dict], chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[dict]:
    chunks = []
    chunk_id = 0
    current_section = "Unknown"

    for page in pages:
        page_number = page["page"]
        text = page["text"]

        # Clean whitespace
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            continue

        # Try to update section based on the page text
        current_section = detect_section(text, current_section)

        # Split into paragraphs
        paragraphs = [p.strip() for p in text.split(". ") if p.strip()]

        current_chunk = ""

        for para in paragraphs:
            # If adding this paragraph exceeds the chunk size,
            # save the current chunk and start a new one.
            if len(current_chunk) + len(para) + 2 > chunk_size:
                if current_chunk:
                    chunks.append({
                        "chunk_id": f"chunk_{chunk_id:04d}",
                        "page": page_number,
                        "section": current_section,
                        "text": current_chunk.strip(),
                    })
                    chunk_id += 1

                    # Overlap: keep the last part of the current chunk
                    if overlap > 0:
                        current_chunk = current_chunk[-overlap:]
                    else:
                        current_chunk = ""

            current_chunk += para + ". "

        # Add the last chunk from this page
        if current_chunk.strip():
            chunks.append({
                "chunk_id": f"chunk_{chunk_id:04d}",
                "page": page_number,
                "section": current_section,
                "text": current_chunk.strip(),
            })
            chunk_id += 1

    return chunks