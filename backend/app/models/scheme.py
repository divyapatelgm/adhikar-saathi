from typing import List, Dict, Optional
from pydantic import BaseModel, Field, HttpUrl
from .enums import TierType, SchemeStatus, LevelType, ApplicationMode
from .rule import EligibilityRule

class SchemeBenefit(BaseModel):
    type: str = Field(..., description="cash | subsidy | loan | insurance | service | scholarship | other")
    description: str
    amount_text: Optional[str] = ""

class EligibilityContainer(BaseModel):
    criteria: List[EligibilityRule] = Field(default_factory=list)
    exclusions: List[EligibilityRule] = Field(default_factory=list)
    notes: Optional[str] = ""

class HowToApply(BaseModel):
    steps: List[str] = Field(default_factory=list)
    mode: str = Field(default="both", description="online | offline | both")
    portal_url: Optional[str] = ""

class Scheme(BaseModel):
    id: str = Field(..., description="Unique slug identifier")
    tier: TierType = Field(..., description="verified | extracted")
    status: SchemeStatus = Field(default=SchemeStatus.UNVERIFIED, description="verified | unverified | rejected")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    is_placeholder: bool = Field(default=False, description="True for synthetic/placeholder records excluded in production")
    names: Dict[str, str] = Field(..., description="Localized names {'en': ..., 'kn': ..., 'hi': ...}")
    level: LevelType = Field(..., description="central | state")
    state: Optional[str] = Field(default=None, description="State name for state-level schemes; None for central")
    department: str
    category: List[str] = Field(default_factory=list)
    target_groups: List[str] = Field(default_factory=list)
    summary_en: str
    benefit: SchemeBenefit
    eligibility: EligibilityContainer
    documents_required: List[str] = Field(default_factory=list)
    how_to_apply: HowToApply
    deadline_text: Optional[str] = "Ongoing"
    official_url: str = Field(..., description="Official government scheme portal URL")
    source_name: str = Field(..., description="Name of official issuing department or authority")
    source_document: Optional[str] = Field(default=None, description="Filename in /data/raw or null")
    last_verified: Optional[str] = Field(default=None, description="YYYY-MM-DD or null")
    extracted_at: Optional[str] = Field(default=None, description="ISO datetime or null")
    reviewed_by: Optional[str] = Field(default=None, description="Reviewer identifier or null")
