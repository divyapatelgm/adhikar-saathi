from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from .profile import UserProfile
from .verdict import EligibilityEvaluation, NextQuestionResponse
from .scheme import Scheme

class EligibilityRequest(BaseModel):
    profile: UserProfile
    language: str = Field(default="en", description="Target language: en, kn, hi")
    category_filter: Optional[str] = None
    target_group_filter: Optional[str] = None

class EligibilityResponse(BaseModel):
    total_evaluated: int
    ranked_schemes: List[EligibilityEvaluation]
    next_recommended_question: Optional[NextQuestionResponse] = None

class ChatRequest(BaseModel):
    message: str
    language: str = Field(default="en", description="en | kn | hi")
    profile: Optional[UserProfile] = None
    conversation_id: Optional[str] = None

class SourceCitation(BaseModel):
    source_name: str
    official_url: str
    last_verified: Optional[str] = None
    tier: str

class ChatResponse(BaseModel):
    reply_text: str
    language: str
    sources: List[SourceCitation] = Field(default_factory=list)
    is_link_out: bool = False
    disclaimer: str = "Information only, not legal advice. Please verify at the official office/portal."

class StatsResponse(BaseModel):
    verified_schemes_count: int
    extracted_schemes_count: int
    total_schemes_count: int
    demo_mode: bool
