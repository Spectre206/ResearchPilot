import unittest
from app.rag.chunking import (
    is_heuristic_table,
    chunk_table,
    detect_section_heuristic,
    chunk_pages,
)


class TestPhase4TableAwareChunking(unittest.TestCase):

    def test_heuristic_table_detection(self):
        # Markdown table
        md_table = "| Metric | Accuracy | Latency |\n| --- | --- | --- |\n| RAG | 85% | 120ms |\n| Agent | 94% | 350ms |"
        self.assertTrue(is_heuristic_table(md_table))

        # Numeric matrix table
        num_grid = "Layer 1   0.245   0.812   0.110\nLayer 2   0.551   0.920   0.340\nLayer 3   0.120   0.450   0.780"
        self.assertTrue(is_heuristic_table(num_grid))

        # Normal text paragraph
        narrative = "Self-healing architectures continuously monitor system health metrics and trigger automated failovers when errors exceed thresholds."
        self.assertFalse(is_heuristic_table(narrative))

    def test_table_chunking_header_preservation(self):
        large_table = """| Component | Strategy | Error Threshold | Recovery Time |
| --- | --- | --- | --- |
| Kafka Broker | Auto-rebalance | > 5% dropped | < 2.5s |
| Vector Store | Index rebuild | > 10% lag | < 5.0s |
| LLM Gateway | Model fallback | HTTP 5xx | < 1.0s |
| Pipeline Engine | Retry & Circuit | Rate limit | < 0.5s |
| Database | Replica switch | Disconnect | < 3.0s |"""

        chunks, next_id = chunk_table(
            table_md=large_table,
            page_number=2,
            section="Experimental Results",
            chunk_id_start=0,
            max_size=160,  # Force splitting into multiple chunks
        )

        self.assertGreater(len(chunks), 1)
        self.assertEqual(next_id, len(chunks))

        for chunk in chunks:
            self.assertTrue(chunk.get("is_table"))
            # Crucial requirement: header row must be preserved in all split table chunks!
            self.assertIn("Component", chunk["text"])
            self.assertIn("Strategy", chunk["text"])

    def test_font_and_pattern_section_detection(self):
        font_headings = ["3. SYSTEM ARCHITECTURE & RESILIENCE"]
        detected = detect_section_heuristic(
            text="Some narrative text on architecture...",
            current_section="Unknown",
            font_headings=font_headings,
        )
        self.assertEqual(detected, "3. SYSTEM ARCHITECTURE & RESILIENCE")

    def test_chunk_pages_with_mixed_content(self):
        pages = [{
            "page": 0,
            "text": "1. INTRODUCTION\n\nSelf-healing AI systems improve service reliability.\n\n| Component | Status |\n| --- | --- |\n| DB | Healthy |\n| Agent | Running |",
            "tables": ["| Model | Precision |\n| --- | --- |\n| RAG | 0.88 |\n| Pipeline | 0.94 |"],
            "detected_headings": ["1. INTRODUCTION"],
        }]

        chunks = chunk_pages(pages)
        self.assertGreater(len(chunks), 0)

        # Check section assignment and table detection
        sections = [c["section"] for c in chunks]
        self.assertTrue(any("INTRODUCTION" in s for s in sections))

        # Check tagged table presence
        table_chunks = [c for c in chunks if c.get("is_table")]
        self.assertGreater(len(table_chunks), 0)


if __name__ == "__main__":
    unittest.main()
