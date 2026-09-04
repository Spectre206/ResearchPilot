import re
from typing import List, Dict, Any, Optional, Tuple
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


def detect_section_heuristic(text: str, current_section: str, font_headings: Optional[List[str]] = None) -> str:
    """
    Font & pattern-aware section detector.
    Checks font headings first, then falls back to regex patterns.
    """
    if font_headings:
        for h in font_headings:
            h_clean = h.strip()
            if h_clean and len(h_clean) <= 80:
                return h_clean

    heading_regex = r"^(?:[IVXLCDM]+\.?|\d+(?:\.\d+)*\.?)\s+\w+"

    lines = text.strip().splitlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if re.match(heading_regex, line, re.IGNORECASE):
            return line
        lower = line.lower()
        if lower in {
            "abstract", "introduction", "related work",
            "methodology", "experiments", "results",
            "discussion", "conclusion", "references",
            "architecture", "system design",
        }:
            return line
    return current_section


def is_heuristic_table(paragraph: str) -> bool:
    """
    Detect if a paragraph is a heuristic table (e.g. multiple lines with columns/numbers/pipes).
    """
    lines = [l.strip() for l in paragraph.splitlines() if l.strip()]
    if len(lines) < 2:
        return False

    # Check for Markdown table pipes
    pipe_lines = sum(1 for l in lines if l.count("|") >= 2)
    if pipe_lines >= 2:
        return True

    # Check for numeric grid pattern (lines with >=3 numbers or tab-separated columns)
    num_grid_lines = 0
    for l in lines:
        numbers = re.findall(r"\d+(?:\.\d+)?", l)
        if len(numbers) >= 3 or "\t" in l or "  " in l:
            num_grid_lines += 1

    return num_grid_lines >= 2 and (num_grid_lines / len(lines)) >= 0.5


def chunk_table(table_md: str, page_number: int, section: str, chunk_id_start: int, max_size: int = CHUNK_SIZE * 2) -> Tuple[List[Dict[str, Any]], int]:
    """
    Chunk a table while preserving table header rows across splits.
    """
    chunks = []
    chunk_id = chunk_id_start
    lines = [l for l in table_md.strip().splitlines() if l.strip()]

    if not lines:
        return chunks, chunk_id

    # Identify header rows (markdown table structure usually has line 0 and line 1 as header & separator)
    has_md_sep = len(lines) > 1 and "---" in lines[1]
    header_lines = lines[:2] if has_md_sep else lines[:1]
    data_lines = lines[2:] if has_md_sep else lines[1:]

    header_text = "\n".join(header_lines)

    # If entire table fits within max_size, return as single chunk
    full_table = f"[TABLE]\n{table_md}"
    if len(full_table) <= max_size or not data_lines:
        chunks.append({
            "chunk_id": f"chunk_{chunk_id:04d}",
            "page": page_number,
            "section": section,
            "text": full_table,
            "is_table": True,
        })
        return chunks, chunk_id + 1

    # Split data rows preserving header
    current_rows = []
    current_len = len(header_text) + 10

    for row in data_lines:
        if current_len + len(row) + 1 > max_size and current_rows:
            chunk_text = f"[TABLE (Part)]\n{header_text}\n" + "\n".join(current_rows)
            chunks.append({
                "chunk_id": f"chunk_{chunk_id:04d}",
                "page": page_number,
                "section": section,
                "text": chunk_text,
                "is_table": True,
            })
            chunk_id += 1
            current_rows = [row]
            current_len = len(header_text) + len(row) + 10
        else:
            current_rows.append(row)
            current_len += len(row) + 1

    if current_rows:
        chunk_text = f"[TABLE (Part)]\n{header_text}\n" + "\n".join(current_rows)
        chunks.append({
            "chunk_id": f"chunk_{chunk_id:04d}",
            "page": page_number,
            "section": section,
            "text": chunk_text,
            "is_table": True,
        })
        chunk_id += 1

    return chunks, chunk_id


def chunk_pages(pages: list[dict], toc: list[dict] | None = None,
                chunk_size: int = CHUNK_SIZE,
                overlap: int = CHUNK_OVERLAP) -> list[dict]:
    """
    Table-aware and layout-aware paragraph chunking:
    - Preserves PyMuPDF extracted tables & heuristic tables intact with headers.
    - Uses font-detected headings and TOC for precise section tracking.
    - Filters boilerplate lines.
    - Paragraph and sentence merging up to chunk_size.
    """
    chunks = []
    chunk_id = 0
    current_section = "Unknown"

    for page in pages:
        page_number = page["page"]
        original_text = page.get("text", "")
        tables = page.get("tables", [])
        font_headings = page.get("detected_headings", [])

        # Determine section title
        if toc:
            current_section = get_section_from_toc(page_number, toc)
        else:
            current_section = detect_section_heuristic(original_text, current_section, font_headings)

        # 1. Process explicit PyMuPDF tables first
        for table_md in tables:
            tbl_chunks, chunk_id = chunk_table(table_md, page_number, current_section, chunk_id)
            chunks.extend(tbl_chunks)

        if not original_text.strip():
            continue

        # Split into paragraphs by double newlines
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", original_text) if p.strip()]
        if len(paragraphs) == 1:
            paragraphs = [p.strip() for p in original_text.splitlines() if p.strip()]

        clean_paragraphs = []
        for para in paragraphs:
            lines = [l for l in para.splitlines() if not is_boilerplate(l)]
            clean_para = "\n".join(lines).strip() if is_heuristic_table(para) else " ".join(lines).strip()
            if clean_para:
                clean_paragraphs.append(clean_para)

        if not clean_paragraphs:
            continue

        current_chunk = ""
        for para in clean_paragraphs:
            # Check if paragraph is a heuristic table
            if is_heuristic_table(para):
                # Save pending text chunk
                if current_chunk:
                    chunks.append({
                        "chunk_id": f"chunk_{chunk_id:04d}",
                        "page": page_number,
                        "section": current_section,
                        "text": current_chunk.strip(),
                    })
                    chunk_id += 1
                    current_chunk = ""

                # Chunk table atomically
                tbl_chunks, chunk_id = chunk_table(para, page_number, current_section, chunk_id)
                chunks.extend(tbl_chunks)
                continue

            para_clean = re.sub(r"[ \t]+", " ", para).strip()

            # Split long paragraphs by sentences if > chunk_size
            if len(para_clean) > chunk_size:
                if current_chunk:
                    chunks.append({
                        "chunk_id": f"chunk_{chunk_id:04d}",
                        "page": page_number,
                        "section": current_section,
                        "text": current_chunk.strip(),
                    })
                    chunk_id += 1
                    current_chunk = ""

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
                            if overlap > 0:
                                temp_chunk = temp_chunk[-overlap:] + " " + sent
                            else:
                                temp_chunk = ""
                        else:
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
                        if overlap > 0:
                            current_chunk = current_chunk[-overlap:] + " " + para_clean
                        else:
                            current_chunk = ""
                    else:
                        current_chunk = para_clean
                else:
                    current_chunk += ("\n\n" + para_clean) if current_chunk else para_clean

        if current_chunk.strip():
            chunks.append({
                "chunk_id": f"chunk_{chunk_id:04d}",
                "page": page_number,
                "section": current_section,
                "text": current_chunk.strip(),
            })
            chunk_id += 1

    return chunks