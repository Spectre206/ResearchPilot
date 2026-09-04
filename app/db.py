import sqlite3
from typing import Optional, List, Dict, Any
from app.config import SQLITE_DB_PATH, DATA_DIR


def get_db_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(SQLITE_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize SQLite database tables."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS papers (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            title TEXT NOT NULL,
            chunk_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


def register_paper(paper_id: str, filename: str, title: str, chunk_count: int) -> Dict[str, Any]:
    """Register a new paper in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO papers (id, filename, title, chunk_count)
        VALUES (?, ?, ?, ?)
        """,
        (paper_id, filename, title, chunk_count),
    )
    conn.commit()
    conn.close()
    return get_paper(paper_id)  # type: ignore


def get_paper(paper_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve metadata for a specific paper."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, filename, title, chunk_count, created_at FROM papers WHERE id = ?", (paper_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def list_papers() -> List[Dict[str, Any]]:
    """List all registered papers ordered by creation time descending."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, filename, title, chunk_count, created_at FROM papers ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
