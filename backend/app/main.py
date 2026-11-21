from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, Security, status, Header
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader

from .config import settings
from .engine.loader import scheme_loader
from .engine.rules_engine import RulesEngine
from .engine.question_selector import next_question
from .models.api import (
    EligibilityRequest,
    EligibilityResponse,
    StatsResponse,
)
from .models.scheme import Scheme
from .models.enums import TierType
from .routes.admin import router as admin_router, auth_router, citizen_auth_router
from .routes.chat import router as chat_router
from .routes.notice import router as notice_router
from .routes.speech import router as speech_router
from .auth import validate_session_token

app = FastAPI(
    title="Adhikar Saathi API",
    description="Multilingual Policy, Rights & Scheme Explainer for Karnataka & India",
    version="1.0.0",
)

# CORS Configuration
origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Admin Security Dependency (Supports both master password and registered user session tokens)
def verify_admin_access(
    x_admin_password: Optional[str] = Header(None, alias="X-Admin-Password"),
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    # 1. Master Admin Password check
    if x_admin_password and x_admin_password == settings.ADMIN_PASSWORD:
        return True

    # 2. Check X-Admin-Token
    if x_admin_token:
        user_info = validate_session_token(x_admin_token)
        if user_info:
            return True

    # 3. Check Bearer Authorization Header
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
        user_info = validate_session_token(token)
        if user_info:
            return True

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing admin credentials. Please login or register."
    )

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Adhikar Saathi API",
        "demo_mode": settings.DEMO_MODE,
    }

@app.get("/api/stats", response_model=StatsResponse)
def get_stats():
    counts = scheme_loader.get_counts()
    return StatsResponse(
        verified_schemes_count=counts["verified"],
        extracted_schemes_count=counts["extracted"],
        total_schemes_count=counts["total"],
        demo_mode=settings.DEMO_MODE,
    )

@app.get("/api/schemes", response_model=List[Scheme])
def get_schemes(
    tier: Optional[TierType] = None,
    category: Optional[str] = None,
    target_group: Optional[str] = None,
    state: Optional[str] = None,
):
    return scheme_loader.filter_schemes(
        tier=tier,
        category=category,
        target_group=target_group,
        state=state,
    )

@app.post("/api/eligibility", response_model=EligibilityResponse)
def evaluate_eligibility(payload: EligibilityRequest):
    schemes = scheme_loader.filter_schemes(
        category=payload.category_filter,
        target_group=payload.target_group_filter,
        include_placeholders=True if settings.DEMO_MODE else None,
    )

    ranked_results = RulesEngine.evaluate_all(
        profile=payload.profile,
        schemes=schemes,
        language=payload.language,
    )

    recommended_q = next_question(payload.profile, schemes)

    return EligibilityResponse(
        total_evaluated=len(schemes),
        ranked_schemes=ranked_results,
        next_recommended_question=recommended_q,
    )

@app.get("/api/admin/verify-auth")
def check_admin_auth(authorized: bool = Depends(verify_admin_access)):
    return {"authenticated": True, "message": "Admin credentials valid."}

# Public Auth Endpoints (Register & Login)
app.include_router(auth_router)
app.include_router(citizen_auth_router)

# Protected Admin Endpoints
app.include_router(admin_router, dependencies=[Depends(verify_admin_access)])

# Conversational Chat Endpoints
app.include_router(chat_router)

# Government Notice Scanner Endpoints
app.include_router(notice_router)

# Speech & Voice Endpoints
app.include_router(speech_router)

# Serve static DBControl dashboard at /admin
db_control_dir = settings.BASE_DIR / "DBControl"
if db_control_dir.exists():
    from fastapi.staticfiles import StaticFiles

    @app.get("/admin", include_in_schema=False)
    def redirect_admin_trailing_slash():
        return RedirectResponse(url="/admin/")

    app.mount("/admin", StaticFiles(directory=str(db_control_dir), html=True), name="dbcontrol")

# Serve static frontend build if present
frontend_dist = settings.BASE_DIR / "frontend" / "dist"
if frontend_dist.exists():
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
