from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, Security, status, Header
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

# Admin Security Dependency
admin_key_header = APIKeyHeader(name="X-Admin-Password", auto_error=False)

def verify_admin_access(x_admin_password: Optional[str] = Security(admin_key_header)):
    if not x_admin_password or x_admin_password != settings.ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin credentials."
        )
    return True

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
