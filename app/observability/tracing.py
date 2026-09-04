import time
import json
import uuid
import sqlite3
import functools
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from app.config import SQLITE_DB_PATH, DATA_DIR


def get_db_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(SQLITE_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_trace_db() -> None:
    """Initialize SQLite traces table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS traces (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            name TEXT NOT NULL,
            duration_ms REAL NOT NULL,
            status TEXT NOT NULL,
            inputs_json TEXT,
            outputs_json TEXT,
            error_message TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def log_trace(
    name: str,
    duration_ms: float,
    status: str,
    inputs: Any = None,
    outputs: Any = None,
    error_message: Optional[str] = None,
) -> str:
    """Log a single execution trace to SQLite database."""
    init_trace_db()
    trace_id = str(uuid.uuid4())
    now_iso = datetime.utcnow().isoformat() + "Z"

    def _sanitize(obj):
        try:
            return json.dumps(obj)
        except Exception:
            return json.dumps(str(obj))

    inputs_str = _sanitize(inputs) if inputs is not None else None
    outputs_str = _sanitize(outputs) if outputs is not None else None

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO traces (id, timestamp, name, duration_ms, status, inputs_json, outputs_json, error_message)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (trace_id, now_iso, name, round(duration_ms, 2), status, inputs_str, outputs_str, error_message),
    )
    conn.commit()
    conn.close()
    return trace_id


def get_recent_traces(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve recent trace logs ordered by timestamp descending."""
    init_trace_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, timestamp, name, duration_ms, status, inputs_json, outputs_json, error_message FROM traces ORDER BY timestamp DESC LIMIT ?",
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()

    traces = []
    for r in rows:
        item = dict(r)
        if item["inputs_json"]:
            try:
                item["inputs"] = json.loads(item["inputs_json"])
            except Exception:
                item["inputs"] = item["inputs_json"]
        if item["outputs_json"]:
            try:
                item["outputs"] = json.loads(item["outputs_json"])
            except Exception:
                item["outputs"] = item["outputs_json"]
        traces.append(item)
    return traces


def trace_execution(name: Optional[str] = None):
    """
    Decorator to automatically trace execution duration, parameters,
    return values, and error status for functions.
    """
    def decorator(func: Callable):
        span_name = name or func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            inputs = {"args": [str(a) for a in args], "kwargs": kwargs}
            try:
                result = func(*args, **kwargs)
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0

                # Summary of result for clean trace storage
                res_summary = result
                if isinstance(result, dict) and "documents" in result:
                    res_summary = {
                        "returned_documents_count": len(result["documents"][0]) if result.get("documents") else 0,
                        "has_rrf_scores": "rrf_scores" in result,
                    }
                elif isinstance(result, str) and len(result) > 500:
                    res_summary = result[:500] + "... [truncated]"

                log_trace(
                    name=span_name,
                    duration_ms=elapsed_ms,
                    status="success",
                    inputs=inputs,
                    outputs=res_summary,
                )
                return result
            except Exception as e:
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                log_trace(
                    name=span_name,
                    duration_ms=elapsed_ms,
                    status="error",
                    inputs=inputs,
                    error_message=str(e),
                )
                raise e

        return wrapper
    return decorator
