import os
import hmac
import hashlib
import time
import json
from typing import Optional, Dict, Any
from pathlib import Path
from pydantic import BaseModel, field_validator
from .config import settings
from .db import db_manager

SECRET_KEY = settings.ADMIN_PASSWORD + "_adhikar_auth_secret_salt_2026"

class UserRegisterPayload(BaseModel):
    name: str
    contact: str
    dob: str
    password: str

    @field_validator("name", "contact", "dob", "password")
    @classmethod
    def not_empty(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Field cannot be empty")
        return s

class UserLoginPayload(BaseModel):
    contact: str
    password: str

def hash_password(password: str) -> str:
    """Hashes password using PBKDF2 HMAC SHA-256 with a unique random 16-byte salt."""
    salt = os.urandom(16).hex()
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 100000).hex()
    return f"{salt}${key}"

def verify_password(password: str, stored_hash: str) -> bool:
    """Verifies plaintext password against stored PBKDF2 hash."""
    try:
        parts = stored_hash.split("$")
        if len(parts) != 2:
            return False
        salt, key = parts
        check_key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 100000).hex()
        return hmac.compare_digest(check_key, key)
    except Exception:
        return False

def generate_session_token(user_id: int, contact: str) -> str:
    """Generates a tamper-proof session token with expiry."""
    timestamp = int(time.time())
    payload = f"{user_id}:{contact}:{timestamp}"
    signature = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}:{signature}"

def validate_session_token(token: str, max_age_seconds: int = 86400 * 7) -> Optional[Dict[str, Any]]:
    """Validates session token signature and freshness."""
    try:
        parts = token.split(":")
        if len(parts) != 4:
            return None
        user_id_str, contact, timestamp_str, sig = parts
        payload = f"{user_id_str}:{contact}:{timestamp_str}"
        expected_sig = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return None
        created_at = int(timestamp_str)
        if time.time() - created_at > max_age_seconds:
            return None
        return {"user_id": int(user_id_str), "contact": contact}
    except Exception:
        return None
