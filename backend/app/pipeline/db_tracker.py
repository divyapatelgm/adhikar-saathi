import sqlite3
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import logging

from ..config import settings

logger = logging.getLogger(__name__)

class PipelineDBTracker:
    """
    SQLite tracker for processed document content hashes and LLM output caching.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or settings.SQLITE_DB_PATH
        self._init_db()

    from contextlib import contextmanager

    @contextmanager
    def _connection(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        """Initializes tables if they do not exist."""
        with self._connection() as conn:
            cursor = conn.cursor()
            # Table 1: Processed files tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processed_files (
                    file_path TEXT PRIMARY KEY,
                    content_hash TEXT NOT NULL,
                    processed_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    scheme_ids TEXT,
                    error_message TEXT
                )
            """)
            # Table 2: LLM output cache
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS llm_cache (
                    cache_key TEXT PRIMARY KEY,
                    content_hash TEXT NOT NULL,
                    prompt_version TEXT NOT NULL,
                    raw_response TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def is_file_unchanged(self, file_path: str, current_hash: str) -> bool:
        """Returns True if the file was previously processed with the exact same hash and succeeded."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT content_hash, status FROM processed_files WHERE file_path = ?",
                (file_path,)
            )
            row = cursor.fetchone()
            if row and row["content_hash"] == current_hash and row["status"] == "success":
                return True
        return False

    def record_file_status(
        self,
        file_path: str,
        content_hash: str,
        status: str,  # 'success' | 'rejected' | 'skipped'
        scheme_ids: Optional[List[str]] = None,
        error_message: Optional[str] = None
    ) -> None:
        """Records or updates processed file status."""
        now_iso = datetime.now(timezone.utc).isoformat()
        ids_json = json.dumps(scheme_ids or [])
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO processed_files (file_path, content_hash, processed_at, status, scheme_ids, error_message)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(file_path) DO UPDATE SET
                    content_hash = excluded.content_hash,
                    processed_at = excluded.processed_at,
                    status = excluded.status,
                    scheme_ids = excluded.scheme_ids,
                    error_message = excluded.error_message
            """, (file_path, content_hash, now_iso, status, ids_json, error_message))
            conn.commit()

    def get_cached_llm(self, content_hash: str, prompt_version: str) -> Optional[str]:
        """Retrieves cached LLM response for content_hash + prompt_version."""
        cache_key = f"{content_hash}:{prompt_version}"
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT raw_response FROM llm_cache WHERE cache_key = ?",
                (cache_key,)
            )
            row = cursor.fetchone()
            if row:
                return row["raw_response"]
        return None

    def save_cached_llm(self, content_hash: str, prompt_version: str, raw_response: str) -> None:
        """Caches LLM raw response."""
        cache_key = f"{content_hash}:{prompt_version}"
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO llm_cache (cache_key, content_hash, prompt_version, raw_response, created_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET
                    raw_response = excluded.raw_response,
                    created_at = excluded.created_at
            """, (cache_key, content_hash, prompt_version, raw_response, now_iso))
            conn.commit()

    def clear_cache(self) -> None:
        """Clears all records for testing."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM processed_files")
            cursor.execute("DELETE FROM llm_cache")
            conn.commit()
