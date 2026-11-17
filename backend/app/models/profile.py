from typing import Optional
from pydantic import BaseModel, Field

class UserProfile(BaseModel):
    """
    Citizen profile for eligibility evaluation.
    IMPORTANT: Every field defaults to None.
    A missing answer is unknown and must NEVER be treated as a known or defaulted value.
    """
    age: Optional[int] = Field(default=None, description="Citizen age in years")
    gender: Optional[str] = Field(default=None, description="Citizen gender e.g., male, female, other")
    state: Optional[str] = Field(default=None, description="State of residence e.g., Karnataka")
    district: Optional[str] = Field(default=None, description="District within state")
    occupation: Optional[str] = Field(default=None, description="Occupation e.g., farmer, student, worker")
    annual_income: Optional[float] = Field(default=None, description="Annual household income in Rupees")
    category: Optional[str] = Field(default=None, description="Social category e.g., GEN, OBC, SC, ST, minority")
    owns_land: Optional[bool] = Field(default=None, description="Whether citizen or family owns agricultural land")
    land_acres: Optional[float] = Field(default=None, description="Agricultural land holding in acres")
    is_student: Optional[bool] = Field(default=None, description="Whether currently enrolled as student")
    education_level: Optional[str] = Field(default=None, description="Current education qualification/level")
    disability: Optional[bool] = Field(default=None, description="Whether citizen has recognized disability")
    marital_status: Optional[str] = Field(default=None, description="Marital status e.g., single, married, widowed, divorced")
    bpl: Optional[bool] = Field(default=None, description="Whether citizen holds BPL / Antyodaya ration card")
