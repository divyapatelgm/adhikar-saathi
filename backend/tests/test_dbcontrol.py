import json
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.config import settings
from backend.app.db import init_db, sync_files_to_db

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_db()
    sync_files_to_db()

@pytest.fixture
def client():
    return TestClient(app)

def test_dbcontrol_static_files(client):
    # Test index.html
    res_index = client.get("/admin/")
    assert res_index.status_code == 200
    assert "DBControl" in res_index.text
    assert "schemes" in res_index.text

    # Test style.css
    res_css = client.get("/admin/style.css")
    assert res_css.status_code == 200
    assert "auth-overlay" in res_css.text

    # Test app.js
    res_js = client.get("/admin/app.js")
    assert res_js.status_code == 200
    assert "checkAuthValidity" in res_js.text

def test_admin_auth_endpoints(client):
    # Missing auth
    res_unauth = client.get("/api/admin/verify-auth")
    assert res_unauth.status_code == 401

    # Valid auth
    headers = {"X-Admin-Password": settings.ADMIN_PASSWORD}
    res_auth = client.get("/api/admin/verify-auth", headers=headers)
    assert res_auth.status_code == 200
    assert res_auth.json()["authenticated"] is True

def test_admin_db_tables(client):
    headers = {"X-Admin-Password": settings.ADMIN_PASSWORD}
    res = client.get("/api/admin/db/tables", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "schemes" in data
    assert "review_status" in data
    assert "file_tracker" in data

def test_admin_db_table_data(client):
    headers = {"X-Admin-Password": settings.ADMIN_PASSWORD}
    res = client.get("/api/admin/db/table/schemes?limit=5", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["table"] == "schemes"
    assert "columns" in data
    assert "rows" in data
    assert len(data["rows"]) > 0

def test_admin_db_query_select(client):
    headers = {"X-Admin-Password": settings.ADMIN_PASSWORD}
    query_payload = {"query": "SELECT id, name_en, tier FROM schemes LIMIT 2;"}
    res = client.post("/api/admin/db/query", json=query_payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["type"] == "select"
    assert len(data["rows"]) <= 2

def test_admin_scheme_review_and_alter(client):
    headers = {"X-Admin-Password": settings.ADMIN_PASSWORD}
    
    # 1. Fetch a scheme
    res = client.get("/api/admin/db/table/schemes?limit=1", headers=headers)
    rows = res.json()["rows"]
    if not rows:
        pytest.skip("No schemes to review")
    
    scheme_id = rows[0]["id"]
    
    # Review details
    res_detail = client.get(f"/api/admin/review/{scheme_id}", headers=headers)
    assert res_detail.status_code == 200
    detail = res_detail.json()
    assert detail["id"] == scheme_id
    assert "parsed_json" in detail

    # Update scheme notes
    update_payload = {
        "action": "update",
        "reviewer": "test_admin",
        "notes": "Automated test update",
        "updated_data": detail["parsed_json"]
    }
    res_update = client.post(f"/api/admin/review/{scheme_id}", json=update_payload, headers=headers)
    assert res_update.status_code == 200
    assert res_update.json()["status"] == "success"
    assert res_update.json()["action"] == "update"

def test_user_registration_and_hash_storage(client):
    unique_contact = f"99887766{int(pytest.importorskip('time').time()) % 10000}"
    payload = {
        "name": "Super Admin User",
        "contact": unique_contact,
        "dob": "1990-05-15",
        "password": "SecurePassword123!"
    }
    
    # 1. Register User
    res = client.post("/api/admin/auth/register", json=payload)
    assert res.status_code == 200
    reg_data = res.json()
    assert reg_data["status"] == "success"
    assert "token" in reg_data
    assert reg_data["user"]["contact"] == unique_contact
    assert reg_data["user"]["name"] == "Super Admin User"

    # 2. Verify password stored in hash form (not plaintext!)
    res_user = client.get(f"/api/admin/db/table/users?search={unique_contact}", headers={"X-Admin-Password": settings.ADMIN_PASSWORD})
    assert res_user.status_code == 200
    user_rows = res_user.json()["rows"]
    assert len(user_rows) >= 1
    stored_hash = user_rows[0]["password_hash"]
    assert stored_hash != "SecurePassword123!"
    assert "$" in stored_hash  # PBKDF2 salt$key format

    # 3. Duplicate Registration Prevention
    res_dup = client.post("/api/admin/auth/register", json=payload)
    assert res_dup.status_code == 400
    assert "already registered" in res_dup.json()["detail"].lower()

    # 4. Login with registered user credentials
    login_payload = {
        "contact": unique_contact,
        "password": "SecurePassword123!"
    }
    res_login = client.post("/api/admin/auth/login", json=login_payload)
    assert res_login.status_code == 200
    login_data = res_login.json()
    assert login_data["status"] == "success"
    user_token = login_data["token"]
    assert user_token

    # 5. Access protected DB endpoint using the user session token!
    res_protected = client.get("/api/admin/db/tables-summary", headers={"X-Admin-Token": user_token})
    assert res_protected.status_code == 200
    tables = res_protected.json()
    assert any(t["name"] == "users" for t in tables)

    # Clean up test user so DB stays clean
    client.delete(f"/api/admin/db/table/users/row?pk_col=contact&pk_val={unique_contact}", headers={"X-Admin-Password": settings.ADMIN_PASSWORD})

def test_phpmyadmin_style_table_crud(client):
    headers = {"X-Admin-Password": settings.ADMIN_PASSWORD}

    # 1. Table Summary (Img 3)
    res_sum = client.get("/api/admin/db/tables-summary", headers=headers)
    assert res_sum.status_code == 200
    tables = res_sum.json()
    assert len(tables) >= 5

    # 2. Table Structure (Img 3)
    res_struct = client.get("/api/admin/db/table/users/structure", headers=headers)
    assert res_struct.status_code == 200
    cols = res_struct.json()
    col_names = [c["name"] for c in cols]
    assert "id" in col_names
    assert "name" in col_names
    assert "contact" in col_names
    assert "password_hash" in col_names

    # 3. Browse Table (Img 4)
    res_browse = client.get("/api/admin/db/table/users?limit=10", headers=headers)
    assert res_browse.status_code == 200
    browse_data = res_browse.json()
    assert "query_sql" in browse_data
    assert "query_time_seconds" in browse_data
    assert "rows" in browse_data

def test_change_password_endpoint(client):
    contact = "pwd_test_user_99"
    # 1. Register user
    reg_payload = {
        "name": "Password Test User",
        "contact": contact,
        "dob": "1992-08-20",
        "password": "OldPassword123"
    }
    res_reg = client.post("/api/auth/register", json=reg_payload)
    assert res_reg.status_code == 200

    # 2. Try wrong current password
    change_payload_bad = {
        "contact": contact,
        "current_password": "WrongPassword",
        "new_password": "NewSecretPassword456"
    }
    res_bad = client.post("/api/auth/change-password", json=change_payload_bad)
    assert res_bad.status_code == 400
    assert "incorrect" in res_bad.json()["detail"].lower()

    # 3. Change with correct password
    change_payload_ok = {
        "contact": contact,
        "current_password": "OldPassword123",
        "new_password": "NewSecretPassword456"
    }
    res_ok = client.post("/api/auth/change-password", json=change_payload_ok)
    assert res_ok.status_code == 200
    assert res_ok.json()["status"] == "success"

    # 4. Verify login with new password
    login_ok = client.post("/api/auth/login", json={"contact": contact, "password": "NewSecretPassword456"})
    assert login_ok.status_code == 200

    # Clean up test user
    client.delete(f"/api/admin/db/table/users/row?pk_col=contact&pk_val={contact}", headers={"X-Admin-Password": settings.ADMIN_PASSWORD})

def test_admin_scheme_promote_and_reject(client):
    import time
    headers = {"X-Admin-Password": settings.ADMIN_PASSWORD}
    
    # 1. Insert a temporary extracted scheme matching Scheme schema
    temp_id = f"test-phase5-{int(time.time())}"
    with open("data/schemes_verified.json", "r", encoding="utf-8") as f:
        sample_scheme = json.load(f)[0].copy()
    sample_scheme["id"] = temp_id
    sample_scheme["tier"] = "extracted"
    sample_scheme["status"] = "unverified"
    sample_scheme["confidence"] = 0.88
    sample_scheme["names"]["en"] = "Phase 5 Temp Scheme"

    row_data = {
        "id": temp_id,
        "tier": "extracted",
        "status": "unverified",
        "confidence": 0.88,
        "is_placeholder": 0,
        "name_en": "Phase 5 Temp Scheme",
        "level": sample_scheme.get("level", "state"),
        "official_url": sample_scheme.get("official_url", "https://karnataka.gov.in"),
        "source_name": sample_scheme.get("source_name", "Government of Karnataka"),
        "created_at": "2026-11-17T22:00:00Z",
        "updated_at": "2026-11-17T22:00:00Z",
        "raw_json": json.dumps(sample_scheme)
    }

    try:
        ins_res = client.post("/api/admin/db/table/schemes/row", json=row_data, headers=headers)
        assert ins_res.status_code == 200

        # 2. Test promotion to Tier 1 verified
        promote_res = client.post(
            f"/api/admin/review/{temp_id}",
            json={"action": "promote", "reviewer": "Phase5_Reviewer", "notes": "Approved for Tier 1 verified"},
            headers=headers
        )
        assert promote_res.status_code == 200
        assert promote_res.json()["status"] == "success"
        assert promote_res.json()["action"] == "promote"

        # Verify status in database
        chk = client.get(f"/api/admin/review/{temp_id}", headers=headers)
        assert chk.status_code == 200
        chk_data = chk.json()
        assert chk_data["tier"] == "verified"
        assert chk_data["status"] == "verified"
        assert chk_data["parsed_json"]["reviewed_by"] == "Phase5_Reviewer"

        # 3. Test rejection action
        reject_res = client.post(
            f"/api/admin/review/{temp_id}",
            json={"action": "reject", "reviewer": "Phase5_Reviewer", "notes": "Marked rejected during test"},
            headers=headers
        )
        assert reject_res.status_code == 200
        assert reject_res.json()["action"] == "reject"

        chk_reject = client.get(f"/api/admin/review/{temp_id}", headers=headers)
        assert chk_reject.json()["status"] == "rejected"
    finally:
        # Clean up temporary test scheme
        client.delete(f"/api/admin/db/table/schemes/row?pk_col=id&pk_val={temp_id}", headers=headers)
        client.delete(f"/api/admin/db/table/review_status/row?pk_col=scheme_id&pk_val={temp_id}", headers=headers)

def test_admin_ingest_and_rejections_endpoints(client):
    headers = {"X-Admin-Password": settings.ADMIN_PASSWORD}

    # 1. Test GET /api/admin/rejections
    rej_res = client.get("/api/admin/rejections", headers=headers)
    assert rej_res.status_code == 200
    assert isinstance(rej_res.json(), list)

    # 2. Test POST /api/admin/ingest with dry_run=True (safe test)
    ingest_res = client.post("/api/admin/ingest?dry_run=true", headers=headers)
    assert ingest_res.status_code == 200
    data = ingest_res.json()
    assert "total" in data
    assert "results" in data



