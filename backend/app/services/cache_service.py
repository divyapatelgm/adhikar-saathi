import sqlite3
import hashlib
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from contextlib import contextmanager
import logging

from ..config import settings
from ..models.api import ChatResponse, SourceCitation

logger = logging.getLogger(__name__)

class ResponseCacheService:
    """
    SQLite response cache for multilingual chat explanations and translations.
    Keyed by (query_hash, language, prompt_version).
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or settings.SQLITE_DB_PATH
        self._init_db()

    @contextmanager
    def _connection(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_cache (
                    cache_key TEXT PRIMARY KEY,
                    query_text TEXT NOT NULL,
                    language TEXT NOT NULL,
                    prompt_version TEXT NOT NULL,
                    reply_text TEXT NOT NULL,
                    sources_json TEXT NOT NULL,
                    is_link_out INTEGER NOT NULL,
                    audio_summary TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            try:
                cursor.execute("ALTER TABLE chat_cache ADD COLUMN audio_summary TEXT")
            except sqlite3.OperationalError:
                pass
            conn.commit()

    @staticmethod
    def _make_key(query: str, language: str, prompt_version: str) -> str:
        norm_query = query.strip().lower()
        content = f"{norm_query}:{language.strip().lower()}:{prompt_version}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def get_cached_chat(self, query: str, language: str, prompt_version: str = "v1") -> Optional[ChatResponse]:
        """Retrieves cached response if present."""
        key = self._make_key(query, language, prompt_version)
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT reply_text, language, sources_json, is_link_out, audio_summary FROM chat_cache WHERE cache_key = ?",
                (key,)
            )
            row = cursor.fetchone()
            if row:
                sources_raw = json.loads(row["sources_json"])
                sources = [SourceCitation(**s) for s in sources_raw]
                audio_sum = row["audio_summary"] if "audio_summary" in row.keys() else None
                return ChatResponse(
                    reply_text=row["reply_text"],
                    language=row["language"],
                    audio_summary=audio_sum,
                    sources=sources,
                    is_link_out=bool(row["is_link_out"]),
                    disclaimer="Information only, not legal advice. Please verify at the official office/portal."
                )
        return None

    def save_cached_chat(
        self,
        query: str,
        language: str,
        response: ChatResponse,
        prompt_version: str = "v1"
    ) -> None:
        """Stores chat response in SQLite cache."""
        key = self._make_key(query, language, prompt_version)
        sources_json = json.dumps([s.model_dump() for s in response.sources])
        now_iso = datetime.now(timezone.utc).isoformat()

        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO chat_cache (cache_key, query_text, language, prompt_version, reply_text, sources_json, is_link_out, audio_summary, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET
                    reply_text = excluded.reply_text,
                    sources_json = excluded.sources_json,
                    is_link_out = excluded.is_link_out,
                    audio_summary = excluded.audio_summary,
                    created_at = excluded.created_at
            """, (key, query, language, prompt_version, response.reply_text, sources_json, int(response.is_link_out), response.audio_summary, now_iso))
            conn.commit()

    def clear(self) -> None:
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chat_cache")
            conn.commit()

# Global cache instance
response_cache = ResponseCacheService()
