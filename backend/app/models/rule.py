from typing import Any, List, Optional, Union
from pydantic import BaseModel, Field, model_validator
from .enums import RuleOperator, RuleField

class EligibilityRule(BaseModel):
    field: RuleField = Field(..., description="Field from user profile or 'other'")
    op: RuleOperator = Field(..., description="Comparison operator")
    value: Any = Field(default=None, description="Scalar, list, or [min, max]")
    text_en: str = Field(..., description="Human-readable explanation of rule in English")
    source_quote: Optional[str] = Field(default=None, description="Short supporting text from source document")

    @model_validator(mode="after")
    def validate_operator_value_pair(self) -> "EligibilityRule":
        op = self.op
        val = self.value

        if op == RuleOperator.BETWEEN:
            if not isinstance(val, (list, tuple)) or len(val) != 2:
                raise ValueError("Operator 'between' requires a list or tuple of exactly two numbers [min, max]")
            min_val, max_val = val[0], val[1]
            if not isinstance(min_val, (int, float)) or not isinstance(max_val, (int, float)):
                raise ValueError("Operator 'between' boundaries [min, max] must both be numeric")
            if min_val > max_val:
                raise ValueError(f"Operator 'between' min ({min_val}) cannot be greater than max ({max_val})")

        elif op in (RuleOperator.IN, RuleOperator.NOT_IN):
            if not isinstance(val, (list, tuple, set)):
                raise ValueError(f"Operator '{op.value}' requires a list or collection of values")
            if len(val) == 0:
                raise ValueError(f"Operator '{op.value}' requires a non-empty list of values")

        elif op in (RuleOperator.GTE, RuleOperator.LTE):
            if not isinstance(val, (int, float)):
                raise ValueError(f"Operator '{op.value}' requires a numeric comparison value")

        elif op in (RuleOperator.IS_TRUE, RuleOperator.IS_FALSE):
            # value can be True/False or None; if None we can default to matching the op
            if val is not None and not isinstance(val, bool):
                raise ValueError(f"Operator '{op.value}' requires a boolean value or None")

        return self
