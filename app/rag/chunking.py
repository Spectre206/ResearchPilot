import re
from app.config import CHUNK_SIZE, CHUNK_OVERLAP

def is_boilerplate(line: str) -> bool:
    """
    Return True if the line looks like a page header/footer or journal boilerplate.
    """
    line = line.strip()
    if not line:
        return True

    # Common journal/author lines
    boilerplate_patterns = [
        r"JOURNAL OF INTERNATIONAL",
        r"ISSN:",
        r"VOL\s*\d+",
        r"Yogesh Pugazhendhi",
        r"Independent researcher",
        r"Self-Healing AI-Native Real-Time Data Pipelines:",
        r"Autonomous Resilience For Large-Scale Streaming Systems",
        r"^\d{1,3}$",   # page number only
    ]

    for pattern in boilerplate_patterns:
        if re.search(pattern, line, re.IGNORECASE):
            return True
    return False

def get_section_from_toc(page_number: int, toc: list[dict]) -> str:
    """Return section title for a page, based on TOC."""
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
    Scans for headings like "IV.", "4.1", "Introduction", etc.
    """
    lines = text.strip().splitlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Roman numeral heading
        if re.match(r"^[IVXLCDM]+\.\s+\w+", line):
            return line
        # Decimal heading
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
    """
    Paragraph-aware chunking:
    - Split text into paragraphs by double newlines.
    - Filter out page headers/footers and journal boilerplate.
    - Merge paragraphs until reaching chunk_size.
    - Keep section metadata.
    """
    chunks = []
    chunk_id = 0
    current_section = "Unknown"

    for page in pages:
        page_number = page["page"]
        original_text = page["text"]

        if not original_text.strip():
            continue

        # Determine section
        if toc:
            current_section = get_section_from_toc(page_number, toc)
        else:
            current_section = detect_section_heuristic(original_text, current_section)

        # Split into paragraphs by blank lines
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", original_text) if p.strip()]

        # If no blank lines, fallback to splitting by newlines
        if len(paragraphs) == 1:
            paragraphs = [p.strip() for p in original_text.splitlines() if p.strip()]

        # --- Filter out boilerplate lines from each paragraph ---
        clean_paragraphs = []
        for para in paragraphs:
            lines = [l for l in para.splitlines() if not is_boilerplate(l)]
            clean_para = " ".join(lines).strip()
            if clean_para:
                clean_paragraphs.append(clean_para)

        # If everything was boilerplate, skip this page
        if not clean_paragraphs:
            continue

        current_chunk = ""
        for para in clean_paragraphs:
            # Normalise spaces (but keep structure)
            para_clean = re.sub(r"[ \t]+", " ", para).strip()

            # If paragraph alone is larger than chunk_size, split it into sentences
            if len(para_clean) > chunk_size:
                # First save current chunk if any
                if current_chunk:
                    chunks.append({
                        "chunk_id": f"chunk_{chunk_id:04d}",
                        "page": page_number,
                        "section": current_section,
                        "text": current_chunk.strip(),
                    })
                    chunk_id += 1
                    current_chunk = ""

                # Split long paragraph by sentences
                sentences = re.split(r'(?<=[.!?]) +', para_clean)
                temp_chunk = ""
                for sent in sentences:
                    if len(temp_chunk) + len(sent) + 1 > chunk_size:
                        if temp_chunk:
                            chunks.append({
                                "chunk_id": f"chunk_{chunk_id:04d}",
                                "page": page_number,
                                "section": current_section,
                                "text": temp_chunk.strip(),
                            })
                            chunk_id += 1
                            # overlap
                            if overlap > 0:
                                temp_chunk = temp_chunk[-overlap:] + " " + sent
                            else:
                                temp_chunk = ""
                        else:
                            # Single sentence longer than chunk_size, add as is
                            chunks.append({
                                "chunk_id": f"chunk_{chunk_id:04d}",
                                "page": page_number,
                                "section": current_section,
                                "text": sent.strip(),
                            })
                            chunk_id += 1
                    else:
                        temp_chunk += (" " + sent) if temp_chunk else sent

                if temp_chunk.strip():
                    chunks.append({
                        "chunk_id": f"chunk_{chunk_id:04d}",
                        "page": page_number,
                        "section": current_section,
                        "text": temp_chunk.strip(),
                    })
                    chunk_id += 1

            # Normal paragraph: merge until size reached
            else:
                if len(current_chunk) + len(para_clean) + 1 > chunk_size:
                    if current_chunk:
                        chunks.append({
                            "chunk_id": f"chunk_{chunk_id:04d}",
                            "page": page_number,
                            "section": current_section,
                            "text": current_chunk.strip(),
                        })
                        chunk_id += 1
                        # overlap
                        if overlap > 0:
                            current_chunk = current_chunk[-overlap:] + " " + para_clean
                        else:
                            current_chunk = ""
                    else:
                        current_chunk = para_clean
                else:
                    current_chunk += ("\n\n" + para_clean) if current_chunk else para_clean

        # Add remaining chunk for this page
        if current_chunk.strip():
            chunks.append({
                "chunk_id": f"chunk_{chunk_id:04d}",
                "page": page_number,
                "section": current_section,
                "text": current_chunk.strip(),
            })
            chunk_id += 1

    return chunks