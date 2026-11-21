from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime, timezone
import json
import time
from fastapi import APIRouter, Depends, Query, HTTPException, Body
from pydantic import BaseModel

from ..config import settings
from ..db import db_manager
from ..models.scheme import Scheme
from ..models.enums import TierType, SchemeStatus
from ..engine.validator import SchemeValidator, SchemeValidationError
from ..engine.loader import scheme_loader
from ..pipeline.extractor import IngestionPipeline
from ..pipeline.rejection_manager import RejectionManager
from ..auth import (
    UserRegisterPayload,
    UserLoginPayload,
    hash_password,
    verify_password,
    generate_session_token,
    validate_session_token,
)

auth_router = APIRouter(prefix="/api/admin/auth", tags=["admin-auth"])
citizen_auth_router = APIRouter(prefix="/api/auth", tags=["auth"])
router = APIRouter(prefix="/api/admin", tags=["admin"])

@auth_router.get("/users-count")
def get_users_count():
    """Returns number of registered users."""
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        return {"count": cursor.fetchone()[0]}

@auth_router.post("/register")
def register_user(payload: UserRegisterPayload, role: str = "user"):
    """Registers a new user into the users table with PBKDF2 hashed password."""
    contact = payload.contact.strip()
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE contact = ?", (contact,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=400,
                detail=f"User with contact '{contact}' is already registered. Please login instead."
            )

        hashed = hash_password(payload.password)
        now_iso = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
            INSERT INTO users (name, contact, dob, password_hash, role, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (payload.name.strip(), contact, payload.dob.strip(), hashed, role, now_iso))
        conn.commit()
        user_id = cursor.lastrowid

    token = generate_session_token(user_id, contact)
    return {
        "status": "success",
        "message": "User registered successfully.",
        "token": token,
        "user": {
            "id": user_id,
            "name": payload.name.strip(),
            "contact": contact,
            "dob": payload.dob.strip(),
            "role": role
        }
    }

@auth_router.post("/login")
def login_user(payload: UserLoginPayload):
    """Authenticates registered user and issues a fresh session token."""
    contact = payload.contact.strip()
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, contact, dob, password_hash, role FROM users WHERE contact = ?", (contact,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(
                status_code=401,
                detail=f"User with contact '{contact}' is not registered. Please register first."
            )

        if not verify_password(payload.password, row["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid password.")

        user_id = row["id"]
        user_data = {
            "id": user_id,
            "name": row["name"],
            "contact": row["contact"],
            "dob": row["dob"],
            "role": row["role"]
        }

    token = generate_session_token(user_id, contact)
    return {
        "status": "success",
        "message": "Login successful.",
        "token": token,
        "user": user_data
    }

@auth_router.get("/me")
def get_current_user_profile(
    x_admin_token: Optional[str] = Query(default=None),
):
    """Returns current user details from session token."""
    if not x_admin_token:
        return {"name": "Administrator", "contact": "admin@local", "role": "admin"}
    info = validate_session_token(x_admin_token)
    if not info:
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, contact, dob, role, created_at FROM users WHERE id = ?", (info["user_id"],))
        row = cursor.fetchone()
        if not row:
            return {"name": "Administrator", "contact": info["contact"], "role": "admin"}
        return dict(zip([d[0] for d in cursor.description], row))

@citizen_auth_router.post("/register")
def citizen_register(payload: UserRegisterPayload):
    """Citizen registration endpoint for Adhikar Saathi."""
    return register_user(payload)

@citizen_auth_router.post("/login")
def citizen_login(payload: UserLoginPayload):
    """Citizen login endpoint for Adhikar Saathi."""
    return login_user(payload)

@citizen_auth_router.get("/me")
def citizen_me(token: Optional[str] = Query(default=None)):
    """Get current logged-in citizen profile."""
    return get_current_user_profile(x_admin_token=token)

class ChangePasswordPayload(BaseModel):
    contact: str
    current_password: str
    new_password: str

@citizen_auth_router.post("/change-password")
@auth_router.post("/change-password")
def change_user_password(payload: ChangePasswordPayload):
    """Changes password for a registered user after verifying current password."""
    contact = payload.contact.strip()
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, password_hash FROM users WHERE contact = ?", (contact,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User account not found.")

        if not verify_password(payload.current_password, row["password_hash"]):
            raise HTTPException(status_code=400, detail="Current password is incorrect.")

        if len(payload.new_password) < 4:
            raise HTTPException(status_code=400, detail="New password must be at least 4 characters long.")

        new_hash = hash_password(payload.new_password)
        cursor.execute("UPDATE users SET password_hash = ? WHERE contact = ?", (new_hash, contact))
        conn.commit()

    return {"status": "success", "message": "Password updated successfully."}

class ReviewActionPayload(BaseModel):
    action: str  # 'promote' | 'reject' | 'update'
    reviewer: Optional[str] = "admin"
    notes: Optional[str] = ""
    updated_data: Optional[Dict[str, Any]] = None

class SqlQueryPayload(BaseModel):
    query: str

@router.post("/db/query")
def execute_sql_query(payload: SqlQueryPayload):
    """Executes a SQL query against data/adhikar_saathi.db for admin analysis."""
    q = payload.query.strip()
    if not q:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(q)
            if q.lower().startswith("select") or q.lower().startswith("pragma") or q.lower().startswith("explain"):
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                return {
                    "status": "success",
                    "type": "select",
                    "columns": columns,
                    "rows": [dict(zip(columns, r)) for r in rows],
                    "row_count": len(rows),
                }
            else:
                conn.commit()
                return {
                    "status": "success",
                    "type": "mutation",
                    "rows_affected": cursor.rowcount,
                }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

@router.get("/db/tables")
def get_database_tables():
    """Returns row counts and metadata for all SQLite tables."""
    return db_manager.get_summary_stats()

@router.get("/db/tables-summary")
def get_tables_summary():
    """Returns phpMyAdmin-style comprehensive table summary list."""
    return db_manager.get_all_tables_info()

@router.get("/db/table/{table_name}/structure")
def get_table_structure(table_name: str):
    """Returns column schema metadata for phpMyAdmin Structure tab."""
    schema = db_manager.get_table_schema(table_name)
    if not schema:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' has no columns or does not exist")
    return schema

@router.get("/db/table/{table_name}")
def get_table_rows(
    table_name: str,
    limit: int = 50,
    offset: int = 0,
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_dir: Optional[str] = "ASC"
):
    """Returns rows from any table for the visual frontend table explorer with query timing."""
    start_time = time.perf_counter()
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name = ?", (table_name,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"Table '{table_name}' does not exist")

        schema = db_manager.get_table_schema(table_name)
        columns = [c["name"] for c in schema]
        pk_cols = [c["name"] for c in schema if c["pk"]]
        primary_key = pk_cols[0] if pk_cols else (columns[0] if columns else "rowid")

        base_query = f"FROM {table_name}"
        params = []
        if search:
            search_clauses = [f"{col} LIKE ?" for col in columns]
            base_query += " WHERE (" + " OR ".join(search_clauses) + ")"
            params.extend([f"%{search}%"] * len(columns))

        cursor.execute(f"SELECT COUNT(*) {base_query}", params)
        total_rows = cursor.fetchone()[0]

        order_clause = ""
        if sort_by and sort_by in columns:
            direction = "DESC" if sort_dir and sort_dir.upper() == "DESC" else "ASC"
            order_clause = f" ORDER BY {sort_by} {direction}"
        elif pk_cols:
            order_clause = f" ORDER BY {pk_cols[0]} ASC"

        select_sql = f"SELECT * {base_query}{order_clause} LIMIT ? OFFSET ?"
        exec_params = list(params) + [limit, offset]
        cursor.execute(select_sql, exec_params)
        rows = cursor.fetchall()
        elapsed_sec = round(time.perf_counter() - start_time, 4)

        return {
            "table": table_name,
            "total_rows": total_rows,
            "limit": limit,
            "offset": offset,
            "columns": columns,
            "primary_key": primary_key,
            "schema": schema,
            "rows": [dict(zip(columns, r)) for r in rows],
            "query_sql": f"SELECT * FROM `{table_name}`" + (f" WHERE search='{search}'" if search else "") + f" LIMIT {limit} OFFSET {offset};",
            "query_time_seconds": elapsed_sec,
        }

@router.post("/db/table/{table_name}/row")
def insert_table_row(table_name: str, payload: Dict[str, Any] = Body(...)):
    """Inserts a new row into table_name with column-value mapping."""
    schema = db_manager.get_table_schema(table_name)
    valid_cols = [c["name"] for c in schema if not (c["pk"] and c["type"].upper() == "INTEGER" and payload.get(c["name"]) in (None, ""))]
    data = {k: v for k, v in payload.items() if k in valid_cols and v is not None}
    if not data:
        raise HTTPException(status_code=400, detail="No valid column data provided")

    cols = list(data.keys())
    placeholders = ["?"] * len(cols)
    vals = [data[c] for c in cols]

    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                f"INSERT INTO {table_name} ({', '.join(cols)}) VALUES ({', '.join(placeholders)})",
                vals
            )
            conn.commit()
            last_id = cursor.lastrowid
            return {"status": "success", "inserted_id": last_id, "message": "Row inserted successfully"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

@router.put("/db/table/{table_name}/row")
def update_table_row(table_name: str, payload: Dict[str, Any] = Body(...)):
    """Updates an existing row in table_name by primary key."""
    pk_col = payload.get("pk_col")
    pk_val = payload.get("pk_val")
    data = payload.get("data", {})
    if not pk_col or pk_val is None or not data:
        raise HTTPException(status_code=400, detail="Missing pk_col, pk_val, or data dictionary")

    schema = db_manager.get_table_schema(table_name)
    valid_cols = [c["name"] for c in schema]
    update_data = {k: v for k, v in data.items() if k in valid_cols and k != pk_col}
    if not update_data:
        raise HTTPException(status_code=400, detail="No modifiable column data provided")

    set_clauses = [f"{col} = ?" for col in update_data.keys()]
    vals = list(update_data.values()) + [pk_val]

    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE {pk_col} = ?", vals)
            conn.commit()
            return {"status": "success", "updated": True, "message": "Row updated successfully"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

@router.delete("/db/table/{table_name}/row")
def delete_table_row(table_name: str, pk_col: str = Query(...), pk_val: str = Query(...)):
    """Deletes a specific row by primary key."""
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(f"DELETE FROM {table_name} WHERE {pk_col} = ?", (pk_val,))
            conn.commit()
            return {"status": "success", "deleted": True, "message": f"Row where {pk_col}={pk_val} deleted"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

@router.post("/db/table/{table_name}/empty")
def empty_table(table_name: str):
    """Truncates/empties all rows from table_name."""
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {table_name}")
        conn.commit()
    return {"status": "success", "table": table_name, "message": "All rows deleted"}

@router.post("/db/table/{table_name}/drop")
def drop_table(table_name: str):
    """Drops table_name from SQLite (protected against core tables)."""
    if table_name in ("schemes", "users"):
        raise HTTPException(status_code=400, detail=f"Cannot drop protected core table '{table_name}'")
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        conn.commit()
    return {"status": "success", "table": table_name, "message": f"Table '{table_name}' dropped successfully"}

@router.post("/db/sync")
def trigger_sync():
    """Syncs JSON files into SQLite."""
    res = db_manager.sync_from_json()
    scheme_loader.load_all()
    return {"status": "success", "synced": res}

@router.get("/review")
def list_review_queue(
    status: Optional[str] = Query(default=None, description="Filter: unverified | verified | rejected"),
    tier: Optional[str] = Query(default=None, description="Filter: extracted | verified")
):
    """Returns schemes list for admin review and curation."""
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT s.*, r.reviewed_by, r.review_notes, r.reviewed_at FROM schemes s LEFT JOIN review_status r ON s.id = r.scheme_id WHERE 1=1"
        params = []
        if status:
            query += " AND s.status = ?"
            params.append(status)
        if tier:
            query += " AND s.tier = ?"
            params.append(tier)

        query += " ORDER BY s.created_at DESC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, r)) for r in rows]

@router.get("/review/{scheme_id}")
def get_scheme_for_review(scheme_id: str):
    """Returns full scheme record including raw_json and criteria."""
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM schemes WHERE id = ?", (scheme_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Scheme '{scheme_id}' not found")

        columns = [desc[0] for desc in cursor.description]
        data = dict(zip(columns, row))
        data["parsed_json"] = json.loads(data["raw_json"])
        return data

@router.post("/review/{scheme_id}")
def process_review_action(scheme_id: str, payload: ReviewActionPayload):
    """
    Promotes extracted scheme to Tier 1 verified, updates rules, or marks rejected.
    Updates SQLite DB and syncs data/schemes_verified.json / data/schemes_extracted.json.
    """
    now_iso = datetime.now(timezone.utc).isoformat()

    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT raw_json, tier, status FROM schemes WHERE id = ?", (scheme_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Scheme '{scheme_id}' not found")

        scheme_dict = json.loads(row["raw_json"])

        # If updated data is passed, merge it
        if payload.updated_data:
            scheme_dict.update(payload.updated_data)

        if payload.action == "promote":
            # Promotion from Tier 2 (Extracted) to Tier 1 (Verified)
            scheme_dict["tier"] = TierType.VERIFIED.value
            scheme_dict["status"] = SchemeStatus.VERIFIED.value
            scheme_dict["confidence"] = 1.0
            scheme_dict["reviewed_by"] = payload.reviewer
            scheme_dict["last_verified"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        elif payload.action == "reject":
            scheme_dict["status"] = SchemeStatus.REJECTED.value
            scheme_dict["reviewed_by"] = payload.reviewer

        elif payload.action == "update":
            # Just updating fields or criteria
            pass
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported action '{payload.action}'")

        # Validate before persisting
        try:
            validated = SchemeValidator.validate_or_raise(scheme_dict)
        except SchemeValidationError as e:
            raise HTTPException(status_code=422, detail={"errors": e.errors})

        # Update SQLite
        cursor.execute("""
            UPDATE schemes SET
                tier = ?,
                status = ?,
                confidence = ?,
                name_en = ?,
                name_kn = ?,
                name_hi = ?,
                level = ?,
                state = ?,
                department = ?,
                raw_json = ?,
                official_url = ?,
                source_name = ?,
                last_verified = ?,
                updated_at = ?
            WHERE id = ?
        """, (
            validated.tier.value,
            validated.status.value,
            validated.confidence,
            validated.names.get("en", scheme_id),
            validated.names.get("kn", ""),
            validated.names.get("hi", ""),
            validated.level.value,
            validated.state,
            validated.department,
            json.dumps(validated.model_dump()),
            validated.official_url,
            validated.source_name,
            validated.last_verified,
            now_iso,
            scheme_id,
        ))

        cursor.execute("""
            UPDATE review_status SET
                status = ?,
                reviewed_by = ?,
                review_notes = ?,
                reviewed_at = ?
            WHERE scheme_id = ?
        """, (
            validated.status.value,
            payload.reviewer,
            payload.notes,
            now_iso,
            scheme_id,
        ))

        # Audit log
        cursor.execute("""
            INSERT INTO audit_logs (event_type, details_json, created_at)
            VALUES (?, ?, ?)
        """, (
            f"scheme_{payload.action}",
            json.dumps({"scheme_id": scheme_id, "reviewer": payload.reviewer, "action": payload.action}),
            now_iso
        ))

        conn.commit()

    # Sync JSON files on disk
    _persist_scheme_to_json_files(validated, payload.action)
    scheme_loader.load_all()

    return {
        "status": "success",
        "action": payload.action,
        "scheme_id": scheme_id,
        "tier": validated.tier.value,
        "scheme_status": validated.status.value,
    }

def _persist_scheme_to_json_files(scheme: Scheme, action: str):
    """Maintains consistency between SQLite and /data JSON files."""
    verified_file = settings.VERIFIED_SCHEMES_PATH
    extracted_file = settings.EXTRACTED_SCHEMES_PATH

    v_items = []
    if verified_file.exists():
        with open(verified_file, "r", encoding="utf-8") as f:
            v_items = json.load(f)

    e_items = []
    if extracted_file.exists():
        with open(extracted_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                e_items = json.loads(content)

    scheme_dict = scheme.model_dump()

    if scheme.tier == TierType.VERIFIED:
        # Remove from extracted if present
        e_items = [it for it in e_items if it.get("id") != scheme.id]
        # Upsert into verified
        v_idx = next((i for i, it in enumerate(v_items) if it.get("id") == scheme.id), -1)
        if v_idx >= 0:
            v_items[v_idx] = scheme_dict
        else:
            v_items.append(scheme_dict)

    else:
        # Tier 2 Extracted
        e_idx = next((i for i, it in enumerate(e_items) if it.get("id") == scheme.id), -1)
        if e_idx >= 0:
            e_items[e_idx] = scheme_dict
        else:
            e_items.append(scheme_dict)

    with open(verified_file, "w", encoding="utf-8") as f:
        json.dump(v_items, f, indent=2, ensure_ascii=False)

    with open(extracted_file, "w", encoding="utf-8") as f:
        json.dump(e_items, f, indent=2, ensure_ascii=False)

@router.delete("/db/scheme/{scheme_id}")
def delete_scheme(scheme_id: str):
    """Deletes a scheme from the database and disk files."""
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM schemes WHERE id = ?", (scheme_id,))
        cursor.execute("DELETE FROM review_status WHERE scheme_id = ?", (scheme_id,))
        conn.commit()

    # Remove from JSON files
    for p in (settings.VERIFIED_SCHEMES_PATH, settings.EXTRACTED_SCHEMES_PATH):
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                content = f.read().strip()
                items = json.loads(content) if content else []
            filtered = [it for it in items if it.get("id") != scheme_id]
            with open(p, "w", encoding="utf-8") as f:
                json.dump(filtered, f, indent=2, ensure_ascii=False)

    scheme_loader.load_all()
    return {"status": "deleted", "scheme_id": scheme_id}

@router.post("/ingest")
async def trigger_ingestion(
    dry_run: bool = Query(default=False, description="Dry run without writing to extracted json"),
    reprocess: bool = Query(default=False, description="Force re-extraction for unchanged files"),
    file_path: Optional[str] = Query(default=None, description="Specific file in data/raw to ingest"),
):
    pipeline = IngestionPipeline()
    if file_path:
        target = Path(file_path)
        if not target.is_absolute():
            target = settings.BASE_DIR / target
        if not target.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
        result = await pipeline.process_file(target, dry_run=dry_run, reprocess=reprocess)
        return {"total": 1, "results": [result.to_dict()]}
    else:
        results = await pipeline.process_directory(settings.RAW_DIR, dry_run=dry_run, reprocess=reprocess)
        return {"total": len(results), "results": [r.to_dict() for r in results]}

@router.get("/rejections")
def get_rejections():
    rejection_mgr = RejectionManager()
    return rejection_mgr.list_rejections()
