from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from .enums import VerdictType, TierType, RuleField

class EvaluationCriterionResult(BaseModel):
    field: str
    text_en: str
    status: str  # "matched" | "failed" | "missing"
    citizen_value: Any = None
    required_value: Any = None
    reason: str = ""

class EligibilityEvaluation(BaseModel):
    scheme_id: str
    scheme_name: str
    verdict: VerdictType
    confidence: float
    tier: TierType
    matched_criteria: List[str] = Field(default_factory=list)
    failed_criteria: List[str] = Field(default_factory=list)
    missing_info: List[str] = Field(default_factory=list)
    detailed_criteria: List[EvaluationCriterionResult] = Field(default_factory=list)
    reason_en: str
    missing_question: Optional[str] = None
    official_url: str
    source_name: str
    last_verified: Optional[str] = None
    disclaimer: str = "Information only, not legal advice. Please verify at the official office/portal."

class QuestionOption(BaseModel):
    value: Any
    labels: Dict[str, str]  # {"en": "...", "kn": "...", "hi": "..."}

class NextQuestionResponse(BaseModel):
    field: RuleField
    question: Dict[str, str]  # {"en": "...", "kn": "...", "hi": "..."}
    input_type: str  # "choice" | "boolean" | "number" | "text"
    options: Optional[List[QuestionOption]] = None
    resolves_maybe_count: int = 0
