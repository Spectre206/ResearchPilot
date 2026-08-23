import re
from app.config import CHUNK_SIZE, CHUNK_OVERLAP


def get_section_from_toc(page_number: int, toc: list[dict]) -> str:
    """
    Return the section title based on the page number.
    toc is a list of dicts with keys: level, title, page (0-indexed).
    """
    current_section = "Unknown"
    for entry in toc:
        if page_number >= entry["page"]:
            current_section = entry["title"]
        else:
            break
    return current_section


def detect_section_heuristic(text: str, current_section: str) -> str:
    """
    Heuristic section detector using raw text with newlines.
    """
    lines = text.strip().splitlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Roman numeral heading: "IV. AI-Native Components"
        if re.match(r"^[IVXLCDM]+\.\s+\w+", line):
            return line

        # Decimal heading: "4.1 Anomaly Detection Engine"
        if re.match(r"^\d+(\.\d+)*\s+\w+", line):
            return line

        # Common unnumbered section names
        lower = line.lower()
        if lower in {
            "abstract", "introduction", "related work",
            "methodology", "experiments", "results",
            "discussion", "conclusion", "references",
        }:
            return line

    return current_section

def chunk_pages(pages: list[dict], toc: list[dict] | None = None,
                chunk_size: int = CHUNK_SIZE,
                overlap: int = CHUNK_OVERLAP) -> list[dict]:
    chunks = []
    chunk_id = 0
    current_section = "Unknown"

    for page in pages:
        page_number = page["page"]
        original_text = page["text"]

        if not original_text.strip():
            continue

        # ----- Section detection on original text (newlines preserved) -----
        if toc:
            current_section = get_section_from_toc(page_number, toc)
        else:
            current_section = detect_section_heuristic(original_text, current_section)

        # ----- Clean text for chunking -----
        text = re.sub(r"\s+", " ", original_text).strip()

        # Split into paragraphs (simple: by sentence endings)
        paragraphs = [p.strip() for p in text.split(". ") if p.strip()]

        current_chunk = ""
        for para in paragraphs:
            if len(current_chunk) + len(para) + 2 > chunk_size:
                if current_chunk:
                    chunks.append({
                        "chunk_id": f"chunk_{chunk_id:04d}",
                        "page": page_number,
                        "section": current_section,
                        "text": current_chunk.strip(),
                    })
                    chunk_id += 1
                    if overlap > 0:
                        current_chunk = current_chunk[-overlap:]
                    else:
                        current_chunk = ""
            current_chunk += para + ". "

        if current_chunk.strip():
            chunks.append({
                "chunk_id": f"chunk_{chunk_id:04d}",
                "page": page_number,
                "section": current_section,
                "text": current_chunk.strip(),
            })
            chunk_id += 1

    return chunks