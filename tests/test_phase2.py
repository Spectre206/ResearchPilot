import unittest
import uuid
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.api.main import app
from app.db import init_db, register_paper
from app.agents.agent_executor import SEARCH_TOOL_DEFINITION, run_agent


class TestPhase2(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)

    def test_search_tool_definition(self):
        self.assertEqual(SEARCH_TOOL_DEFINITION["type"], "function")
        self.assertEqual(SEARCH_TOOL_DEFINITION["function"]["name"], "search_paper")
        self.assertIn("query", SEARCH_TOOL_DEFINITION["function"]["parameters"]["properties"])

    @patch("app.agents.agent_executor.Groq")
    @patch("app.agents.agent_executor.search_paper")
    def test_run_agent_tool_loop(self, mock_search_paper, mock_groq_class):
        mock_client = MagicMock()
        mock_groq_class.return_value = mock_client

        # Turn 1 response: model requests search_paper tool call
        tool_call_mock = MagicMock()
        tool_call_mock.id = "call_123"
        tool_call_mock.function.name = "search_paper"
        tool_call_mock.function.arguments = '{"query": "self-healing architecture", "k": 3}'

        msg1 = MagicMock()
        msg1.tool_calls = [tool_call_mock]
        msg1.content = None

        resp1 = MagicMock()
        resp1.choices = [MagicMock(message=msg1)]

        # Turn 2 response: model produces final answer
        msg2 = MagicMock()
        msg2.tool_calls = None
        msg2.content = "Self-healing architectures automatically recover from failures."

        resp2 = MagicMock()
        resp2.choices = [MagicMock(message=msg2)]

        mock_client.chat.completions.create.side_effect = [resp1, resp2]

        # Mock vector store search
        mock_search_paper.return_value = {
            "documents": [["Self-healing is defined as..."]],
            "metadatas": [[{"page": 1, "section": "Intro", "chunk_id": "chunk_0001"}]],
            "distances": [[0.12]],
        }

        output = run_agent(question="What is self-healing architecture?", paper_id="dummy_id")

        self.assertEqual(output["answer"], "Self-healing architectures automatically recover from failures.")
        self.assertEqual(len(output["steps"]), 1)
        self.assertEqual(output["steps"][0]["tool"], "search_paper")

    @patch("app.api.main.run_agent")
    def test_ask_agent_endpoint(self, mock_run_agent):
        dummy_id = str(uuid.uuid4())
        register_paper(dummy_id, "test.pdf", "Test Paper", 10)

        mock_run_agent.return_value = {
            "answer": "Agent answer here.",
            "steps": [{"turn": 1, "tool": "search_paper", "args": {"query": "test"}, "results_count": 1}],
        }

        response = self.client.post(
            "/ask-agent",
            json={"paper_id": dummy_id, "question": "Explain test paper"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["mode"], "agent")
        self.assertEqual(data["answer"], "Agent answer here.")
        self.assertEqual(len(data["steps"]), 1)


if __name__ == "__main__":
    unittest.main()
