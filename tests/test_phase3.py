import unittest
from unittest.mock import patch, MagicMock
from app.rag.hybrid_retrieval import BM25Okapi, hybrid_search
from app.tools.retrieval import search_paper


class TestPhase3HybridRetrieval(unittest.TestCase):

    def test_bm25_okapi_scoring(self):
        corpus = [
            "Self-healing data pipelines handle automatic recovery in distributed systems.",
            "Deep learning transformer models require large scale GPU cluster training.",
            "Real-time streaming architectures process event streams with low latency.",
        ]
        bm25 = BM25Okapi(corpus)
        scores = bm25.get_scores("self-healing data pipelines")

        self.assertEqual(len(scores), 3)
        # First document should have highest score
        self.assertGreater(scores[0], scores[1])
        self.assertGreater(scores[0], scores[2])

    @patch("app.rag.hybrid_retrieval.get_collection")
    @patch("app.rag.hybrid_retrieval.get_collection_name_for_paper")
    def test_hybrid_search_fusion(self, mock_get_col_name, mock_get_collection):
        mock_get_col_name.return_value = "paper_dummy"

        mock_collection = MagicMock()
        mock_get_collection.return_value = mock_collection

        # Mock collection.get (all documents for BM25)
        mock_collection.get.return_value = {
            "ids": ["c1", "c2", "c3"],
            "documents": [
                "Self-healing mechanisms in data engineering.",
                "Vector database indexing with cosine distance.",
                "Automated anomaly detection in pipeline architectures.",
            ],
            "metadatas": [
                {"page": 1, "section": "Intro"},
                {"page": 2, "section": "Methods"},
                {"page": 3, "section": "Results"},
            ],
        }

        # Mock collection.query (dense vector search)
        mock_collection.query.return_value = {
            "ids": [["c2", "c1"]],
            "documents": [["Vector database indexing with cosine distance.", "Self-healing mechanisms in data engineering."]],
            "metadatas": [[{"page": 2, "section": "Methods"}, {"page": 1, "section": "Intro"}]],
            "distances": [[0.1, 0.2]],
        }

        # Query hybrid search
        results = hybrid_search(query="self-healing data pipeline", k=2, paper_id="dummy_paper")

        self.assertIn("documents", results)
        self.assertIn("metadatas", results)
        self.assertIn("distances", results)
        self.assertIn("rrf_scores", results)

        docs = results["documents"][0]
        self.assertEqual(len(docs), 2)
        # Document c1 matches both BM25 and vector search, so should be top ranked
        self.assertIn("Self-healing mechanisms", docs[0])

    @patch("app.tools.retrieval.hybrid_search")
    def test_search_paper_tool_integration(self, mock_hybrid_search):
        mock_hybrid_search.return_value = {
            "documents": [["Sample doc"]],
            "metadatas": [[{"page": 1, "section": "Main"}]],
            "distances": [[0.05]],
            "rrf_scores": [[0.032]],
        }

        res = search_paper(query="test query", k=3, paper_id="paper_123")
        mock_hybrid_search.assert_called_once_with(query="test query", k=3, paper_id="paper_123")
        self.assertEqual(res, mock_hybrid_search.return_value)


if __name__ == "__main__":
    unittest.main()
