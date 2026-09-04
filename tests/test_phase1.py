import unittest
import uuid
from pathlib import Path
from fastapi.testclient import TestClient

from app.api.main import app
from app.db import init_db, register_paper, get_paper, list_papers
from app.rag.vector_store import get_collection_name_for_paper


class TestPhase1(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)

    def test_db_paper_registration(self):
        test_id = str(uuid.uuid4())
        paper = register_paper(
            paper_id=test_id,
            filename="test_paper.pdf",
            title="Test Paper Title",
            chunk_count=10,
        )
        self.assertIsNotNone(paper)
        self.assertEqual(paper["id"], test_id)
        self.assertEqual(paper["filename"], "test_paper.pdf")
        self.assertEqual(paper["title"], "Test Paper Title")
        self.assertEqual(paper["chunk_count"], 10)

        # Retrieve paper
        fetched = get_paper(test_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["id"], test_id)

        # List papers
        papers = list_papers()
        self.assertTrue(len(papers) > 0)
        self.assertTrue(any(p["id"] == test_id for p in papers))

    def test_vector_store_collection_naming(self):
        test_id = "550e8400-e29b-41d4-a716-446655440000"
        col_name = get_collection_name_for_paper(test_id)
        self.assertEqual(col_name, "paper_550e8400_e29b_41d4_a716_446655440000")

        default_col = get_collection_name_for_paper(None)
        self.assertEqual(default_col, "papers")

    def test_api_root(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "online")

    def test_api_get_papers(self):
        response = self.client.get("/papers")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_api_ask_invalid_paper(self):
        response = self.client.post(
            "/ask",
            json={
                "paper_id": "nonexistent-id",
                "question": "What is this?",
                "mode": "rag",
            },
        )
        self.assertEqual(response.status_code, 404)

    def test_api_ask_agent_stub(self):
        # Register dummy paper first
        dummy_id = str(uuid.uuid4())
        register_paper(dummy_id, "dummy.pdf", "Dummy", 5)

        response = self.client.post(
            "/ask-agent",
            json={
                "paper_id": dummy_id,
                "question": "What is this?",
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["mode"], "agent")
        self.assertEqual(data["status"], "not_implemented")


if __name__ == "__main__":
    unittest.main()
