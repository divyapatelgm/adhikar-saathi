from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class UrgencyLevel(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    INFORMATIONAL = "Informational"

class NoticeScanResult(BaseModel):
    """Structured citizen breakdown of a government notice or order."""
    issuing_authority: str = Field(..., description="Issuing department or government authority")
    purpose: str = Field(..., description="Plain-language description of what this notice announces or demands")
    summary: str = Field(..., description="Plain-language summary at ~6th-grade reading level in chosen language")
    citizen_obligations: List[str] = Field(default_factory=list, description="Specific things the citizen is required to do")
    deadline: str = Field(
        default="No deadline mentioned in the document",
        description="Explicit date/deadline, or 'No deadline mentioned in the document'"
    )
    urgency: UrgencyLevel = Field(default=UrgencyLevel.INFORMATIONAL, description="Urgency rating")
    next_steps: List[str] = Field(default_factory=list, description="Step-by-step ordered citizen action items")
    official_portal: Optional[str] = Field(default=None, description="Official portal or website mentioned")
    disclaimer: str = Field(
        default="Information only, not legal advice. Please verify at the official office/portal.",
        description="Mandatory legal disclaimer"
    )
    language: str = Field(default="en", description="Target language: en | kn | hi")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Extraction confidence score")
    source_filename: Optional[str] = Field(default=None, description="Uploaded file name if applicable")
