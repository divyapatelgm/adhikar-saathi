from typing import List
from pydantic import BaseModel, Field

class RightsEntry(BaseModel):
    id: str = Field(..., description="Unique slug for the rights entry")
    topic: str = Field(..., description="Legal topic or civic category e.g., Unpaid Wages, RTI, Consumer Rights")
    question_variants: List[str] = Field(default_factory=list, description="Common phrasing variants of the citizen's question")
    answer_en: str = Field(..., description="Plain-language explanation of legal rights in English")
    steps: List[str] = Field(default_factory=list, description="Step-by-step procedure for grievance/redressal")
    helpline_or_authority: str = Field(..., description="Designated grievance officer, authority, or helpline number")
    source_name: str = Field(..., description="Official act, legal authority, or statutory body name")
    source_url: str = Field(..., description="Official government portal URL for rights filing")
    last_verified: str = Field(..., description="YYYY-MM-DD verification date")
