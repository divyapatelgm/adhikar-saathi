import sqlite3
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from contextlib import contextmanager
import logging
import argparse

from .config import settings

logger = logging.getLogger(__name__)

DB_PATH = settings.DATA_DIR / "adhikar_saathi.db"

class DatabaseManager:
    """
    Unified SQLite Database Manager for Adhikar Saathi.
    Houses:
    1. schemes (structured scheme records)
    2. review_status (admin curation and promotion workflow for Phase 5)
    3. response_cache (LLM explanation and translation cache)
    4. file_tracker (ingestion pipeline document hashes)
    5. llm_cache (raw document extraction outputs)
    6. audit_logs (system and query activity logs)
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def init_db(self) -> None:
        """Creates all necessary database tables with proper indexing."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Schemes Table (Mirrors & indexes structured schemes for rapid querying)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schemes (
                    id TEXT PRIMARY KEY,
                    tier TEXT NOT NULL,           -- 'verified' | 'extracted'
                    status TEXT NOT NULL,         -- 'verified' | 'unverified' | 'rejected'
                    confidence REAL NOT NULL,     -- 0.0 to 1.0
                    is_placeholder INTEGER NOT NULL DEFAULT 0,
                    name_en TEXT NOT NULL,
                    name_kn TEXT,
                    name_hi TEXT,
                    level TEXT NOT NULL,          -- 'central' | 'state'
                    state TEXT,                   -- 'Karnataka' | null
                    department TEXT,
                    category TEXT,                -- JSON list
                    target_groups TEXT,           -- JSON list
                    raw_json TEXT NOT NULL,       -- Complete Scheme JSON
                    official_url TEXT NOT NULL,
                    source_name TEXT NOT NULL,
                    last_verified TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # 2. Review Status Table (Tracks human reviewer workflow for Phase 5)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS review_status (
                    scheme_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,         -- 'unverified' | 'verified' | 'rejected'
                    reviewed_by TEXT,
                    review_notes TEXT,
                    reviewed_at TEXT,
                    FOREIGN KEY (scheme_id) REFERENCES schemes(id) ON DELETE CASCADE
                )
            """)

            # 3. Response Cache Table (Pre-generated and cached LLM responses)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS response_cache (
                    cache_key TEXT PRIMARY KEY,
                    query_text TEXT NOT NULL,
                    language TEXT NOT NULL,       -- 'kn' | 'hi' | 'en'
                    prompt_version TEXT NOT NULL,
                    reply_text TEXT NOT NULL,
                    sources_json TEXT NOT NULL,
                    is_link_out INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)

            # 4. Ingestion File Tracker Table (SHA-256 hash idempotency)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS file_tracker (
                    file_path TEXT PRIMARY KEY,
                    content_hash TEXT NOT NULL,
                    processed_at TEXT NOT NULL,
                    status TEXT NOT NULL,         -- 'success' | 'rejected' | 'skipped'
                    scheme_ids TEXT,              -- JSON list
                    error_message TEXT
                )
            """)

            # 5. Ingestion LLM Cache Table (Extracted raw LLM responses)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS llm_cache (
                    cache_key TEXT PRIMARY KEY,
                    content_hash TEXT NOT NULL,
                    prompt_version TEXT NOT NULL,
                    raw_response TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

            # 6. Audit & Usage Logs Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,     -- 'chat_query', 'eligibility_eval', 'admin_review', 'ingestion'
                    details_json TEXT,
                    ip_address TEXT,
                    created_at TEXT NOT NULL
                )
            """)

            # 7. Registered Users / Admin Credentials Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    contact TEXT NOT NULL UNIQUE,
                    dob TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT DEFAULT 'admin',
                    created_at TEXT NOT NULL
                )
            """)

            # Indexes for high performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_schemes_tier_status ON schemes(tier, status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_response_cache_query ON response_cache(language, prompt_version)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_file_tracker_hash ON file_tracker(content_hash)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_contact ON users(contact)")

            conn.commit()

    def sync_from_json(self) -> Dict[str, int]:
        """
        Synchronizes JSON records from /data/schemes_verified.json and /data/schemes_extracted.json
        into the SQLite `schemes` and `review_status` tables.
        """
        verified_path = settings.VERIFIED_SCHEMES_PATH
        extracted_path = settings.EXTRACTED_SCHEMES_PATH

        synced_verified = 0
        synced_extracted = 0

        now_iso = datetime.now(timezone.utc).isoformat()

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Sync Verified Schemes
            if verified_path.exists():
                with open(verified_path, "r", encoding="utf-8") as f:
                    v_items = json.load(f)
                    for item in v_items:
                        self._upsert_scheme(cursor, item, now_iso)
                        synced_verified += 1

            # Sync Extracted Schemes
            if extracted_path.exists():
                with open(extracted_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        e_items = json.loads(content)
                        for item in e_items:
                            self._upsert_scheme(cursor, item, now_iso)
                            synced_extracted += 1

            conn.commit()

        return {
            "synced_verified": synced_verified,
            "synced_extracted": synced_extracted,
            "total_synced": synced_verified + synced_extracted,
        }

    def _upsert_scheme(self, cursor: sqlite3.Cursor, item: Dict[str, Any], now_iso: str) -> None:
        scheme_id = item["id"]
        names = item.get("names", {})
        cursor.execute("""
            INSERT INTO schemes (
                id, tier, status, confidence, is_placeholder,
                name_en, name_kn, name_hi,
                level, state, department, category, target_groups,
                raw_json, official_url, source_name, last_verified,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                tier = excluded.tier,
                status = excluded.status,
                confidence = excluded.confidence,
                is_placeholder = excluded.is_placeholder,
                name_en = excluded.name_en,
                name_kn = excluded.name_kn,
                name_hi = excluded.name_hi,
                level = excluded.level,
                state = excluded.state,
                department = excluded.department,
                category = excluded.category,
                target_groups = excluded.target_groups,
                raw_json = excluded.raw_json,
                official_url = excluded.official_url,
                source_name = excluded.source_name,
                last_verified = excluded.last_verified,
                updated_at = excluded.updated_at
        """, (
            scheme_id,
            item.get("tier", "extracted"),
            item.get("status", "unverified"),
            item.get("confidence", 1.0),
            int(item.get("is_placeholder", False)),
            names.get("en", scheme_id),
            names.get("kn", ""),
            names.get("hi", ""),
            item.get("level", "state"),
            item.get("state"),
            item.get("department", ""),
            json.dumps(item.get("category", [])),
            json.dumps(item.get("target_groups", [])),
            json.dumps(item),
            item.get("official_url", ""),
            item.get("source_name", ""),
            item.get("last_verified"),
            item.get("extracted_at") or now_iso,
            now_iso
        ))

        # Ensure review_status entry exists
        cursor.execute("""
            INSERT INTO review_status (scheme_id, status, reviewed_by, review_notes, reviewed_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(scheme_id) DO UPDATE SET
                status = excluded.status
        """, (
            scheme_id,
            item.get("status", "unverified"),
            item.get("reviewed_by"),
            None,
            now_iso if item.get("status") == "verified" else None
        ))

    def get_summary_stats(self) -> Dict[str, Any]:
        """Returns row counts across all database tables."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            tables = ["users", "schemes", "review_status", "response_cache", "file_tracker", "llm_cache", "audit_logs"]
            stats = {}
            for t in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {t}")
                stats[t] = cursor.fetchone()[0]

            cursor.execute("SELECT tier, status, COUNT(*) FROM schemes GROUP BY tier, status")
            breakdown = [f"{row[0]}/{row[1]}: {row[2]}" for row in cursor.fetchall()]
            stats["breakdown"] = breakdown

        return stats

    def get_all_tables_info(self) -> List[Dict[str, Any]]:
        """Returns phpMyAdmin-style detailed table summary list."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
            tables = [r[0] for r in cursor.fetchall()]

            summary = []
            for t in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {t}")
                row_count = cursor.fetchone()[0]

                cursor.execute(f"PRAGMA table_info({t})")
                cols = cursor.fetchall()
                col_names = [c[1] for c in cols]

                summary.append({
                    "name": t,
                    "rows": row_count,
                    "columns_count": len(cols),
                    "columns": col_names,
                    "type": "SQLite / Table",
                    "collation": "utf8_general_ci",
                    "size_kb": round((row_count * 0.4) + 4.0, 1)  # Estimated KB size
                })
            return summary

    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Returns column schema metadata for table_name."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            cols = cursor.fetchall()
            return [
                {
                    "cid": c[0],
                    "name": c[1],
                    "type": c[2] or "TEXT",
                    "notnull": bool(c[3]),
                    "dflt_value": c[4],
                    "pk": bool(c[5])
                }
                for c in cols
            ]

    def view_table(self, table_name: str, limit: int = 20) -> None:
        """Prints formatted table contents to terminal using tabulate."""
        from tabulate import tabulate

        valid_tables = ["schemes", "review_status", "response_cache", "file_tracker", "llm_cache", "audit_logs"]
        if table_name not in valid_tables:
            print(f"❌ Unknown table '{table_name}'. Valid tables: {', '.join(valid_tables)}")
            return

        with self.get_connection() as conn:
            cursor = conn.cursor()

            if table_name == "schemes":
                cursor.execute("""
                    SELECT id, tier, status, round(confidence, 2) as conf,
                           substr(name_en, 1, 32) as title, level, department, last_verified
                    FROM schemes LIMIT ?
                """, (limit,))
                rows = cursor.fetchall()
                headers = ["ID", "Tier", "Status", "Conf", "Scheme Title (en)", "Level", "Department", "Last Verified"]
            elif table_name == "review_status":
                cursor.execute("SELECT scheme_id, status, reviewed_by, review_notes, reviewed_at FROM review_status LIMIT ?", (limit,))
                rows = cursor.fetchall()
                headers = ["Scheme ID", "Review Status", "Reviewer", "Notes", "Reviewed At"]
            elif table_name == "response_cache":
                cursor.execute("SELECT substr(cache_key, 1, 10) as key, substr(query_text, 1, 35) as query, language, prompt_version, substr(reply_text, 1, 45) as reply, created_at FROM response_cache LIMIT ?", (limit,))
                rows = cursor.fetchall()
                headers = ["Key", "Query Preview", "Lang", "Prompt Ver", "Reply Preview", "Cached At"]
            elif table_name == "file_tracker":
                cursor.execute("SELECT file_path, substr(content_hash, 1, 10) as hash, status, scheme_ids, processed_at FROM file_tracker LIMIT ?", (limit,))
                rows = cursor.fetchall()
                headers = ["File Path", "SHA256", "Status", "Extracted Schemes", "Processed At"]
            else:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT ?", (limit,))
                rows = cursor.fetchall()
                headers = [desc[0] for desc in cursor.description]

            if not rows:
                print(f"\n📂 Table '{table_name}' is currently empty (0 rows).\n")
                return

            print(f"\n📋 TABLE: {table_name} (Showing top {len(rows)} rows)")
            print(tabulate([list(r) for r in rows], headers=headers, tablefmt="rounded_grid"))
            print()

    def view_scheme_details(self, scheme_id: str) -> None:
        """Displays full formatted details for a specific scheme."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT raw_json FROM schemes WHERE id = ?", (scheme_id,))
            row = cursor.fetchone()
            if not row:
                print(f"❌ Scheme with ID '{scheme_id}' not found.")
                return

            data = json.loads(row["raw_json"])
            print("\n" + "=" * 60)
            print(f"SCHEME DETAILS: {data.get('id')}")
            print("=" * 60)
            print(f"  • Title (en)      : {data.get('names', {}).get('en')}")
            print(f"  • Title (kn)      : {data.get('names', {}).get('kn')}")
            print(f"  • Tier / Status   : {data.get('tier')} / {data.get('status')} (Confidence: {data.get('confidence', 1.0):.0%})")
            print(f"  • Level / State   : {data.get('level')} ({data.get('state')})")
            print(f"  • Department      : {data.get('department')}")
            print(f"  • Official URL    : {data.get('official_url')}")
            print(f"  • Key Benefit     : {data.get('benefit', {}).get('description')} ({data.get('benefit', {}).get('amount_text')})")
            print(f"  • Criteria Count  : {len(data.get('eligibility', {}).get('criteria', []))} criteria, {len(data.get('eligibility', {}).get('exclusions', []))} exclusions")
            for i, c in enumerate(data.get('eligibility', {}).get('criteria', [])):
                print(f"      [{i+1}] {c.get('field')} {c.get('op')} {c.get('value')} -> {c.get('text_en')}")
            print(f"  • Documents       : {', '.join(data.get('documents_required', []))}")
            print(f"  • Apply Process   : {data.get('how_to_apply', {}).get('mode')} -> {data.get('how_to_apply', {}).get('portal_url')}")
            print("=" * 60 + "\n")

# Global database manager instance
db_manager = DatabaseManager()

def init_db():
    return db_manager.init_db()

def sync_files_to_db():
    return db_manager.sync_from_json()

def cli():
    parser = argparse.ArgumentParser(description="Adhikar Saathi SQLite Database Manager")
    parser.add_argument("--init", action="store_true", help="Initialize all database tables and indexes")
    parser.add_argument("--sync", action="store_true", help="Sync schemes from verified & extracted JSON files into SQLite")
    parser.add_argument("--status", action="store_true", help="Display current database row counts and status")
    parser.add_argument("--view", type=str, default=None, help="View formatted table rows (e.g. --view schemes, --view review_status)")
    parser.add_argument("--view-scheme", type=str, default=None, help="View detailed rules and metadata for a specific scheme ID")
    args = parser.parse_args()

    mgr = DatabaseManager()

    if args.init:
        mgr.init_db()
        print(f"✅ Initialized SQLite database tables at: {mgr.db_path}")

    if args.sync:
        res = mgr.sync_from_json()
        print(f"✅ Synced schemes into SQLite: {res}")

    if args.view:
        mgr.view_table(args.view)
        return

    if args.view_scheme:
        mgr.view_scheme_details(args.view_scheme)
        return

    if args.status or (not args.init and not args.sync):
        stats = mgr.get_summary_stats()
        print("\n" + "=" * 50)
        print(f"DATABASE LOCATION: {mgr.db_path}")
        print("=" * 50)
        for tbl, count in stats.items():
            if tbl != "breakdown":
                print(f"  • {tbl.ljust(18)}: {count} row(s)")
        print("-" * 50)
        print(f"  Breakdown: {', '.join(stats.get('breakdown', [])) or 'None'}")
        print("=" * 50 + "\n")

if __name__ == "__main__":
    cli()
