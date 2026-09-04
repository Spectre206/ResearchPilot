import unittest
from fastapi.testclient import TestClient
from app.api.main import app
from app.observability.tracing import (
    init_trace_db,
    log_trace,
    get_recent_traces,
    trace_execution,
)


class TestPhase5Observability(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_trace_db()
        cls.client = TestClient(app)

    def test_trace_db_logging_and_retrieval(self):
        trace_id = log_trace(
            name="manual_test_span",
            duration_ms=45.67,
            status="success",
            inputs={"query": "test query"},
            outputs={"result": "success"},
        )
        self.assertIsNotNone(trace_id)

        recent = get_recent_traces(limit=10)
        self.assertTrue(len(recent) > 0)
        match = next((t for t in recent if t["id"] == trace_id), None)
        self.assertIsNotNone(match)
        self.assertEqual(match["name"], "manual_test_span")
        self.assertEqual(match["duration_ms"], 45.67)
        self.assertEqual(match["status"], "success")

    def test_trace_execution_decorator_success(self):
        @trace_execution("sample_math_add")
        def add_numbers(a: int, b: int) -> int:
            return a + b

        result = add_numbers(5, 7)
        self.assertEqual(result, 12)

        recent = get_recent_traces(limit=5)
        span = next((t for t in recent if t["name"] == "sample_math_add"), None)
        self.assertIsNotNone(span)
        self.assertEqual(span["status"], "success")

    def test_trace_execution_decorator_error(self):
        @trace_execution("failing_span")
        def raise_error():
            raise ValueError("Deliberate trace test failure")

        with self.assertRaises(ValueError):
            raise_error()

        recent = get_recent_traces(limit=5)
        span = next((t for t in recent if t["name"] == "failing_span"), None)
        self.assertIsNotNone(span)
        self.assertEqual(span["status"], "error")
        self.assertEqual(span["error_message"], "Deliberate trace test failure")

    def test_api_get_traces_endpoint(self):
        response = self.client.get("/traces")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)


if __name__ == "__main__":
    unittest.main()
