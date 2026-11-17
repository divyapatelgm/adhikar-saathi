import re
from typing import Dict, Any, List, Union, Optional
from pydantic import ValidationError

from ..models.enums import TierType, SchemeStatus, LevelType, RuleOperator, RuleField
from ..models.scheme import Scheme
from ..models.rule import EligibilityRule

class SchemeValidationError(ValueError):
    """Custom exception raised when scheme record fails validation."""
    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__("; ".join(errors))

class SchemeValidator:
    """
    Validates Scheme records and raw dictionaries against strict schema,
    boundary checks, and logical sanity rules.
    """

    @classmethod
    def validate_dict(cls, data: Dict[str, Any]) -> List[str]:
        errors: List[str] = []

        # 1. Check required base metadata
        official_url = data.get("official_url")
        if not official_url or not isinstance(official_url, str) or not official_url.strip():
            errors.append("official_url is required and cannot be empty")
        elif not (official_url.startswith("http://") or official_url.startswith("https://")):
            errors.append(f"official_url must start with http:// or https://: '{official_url}'")

        source_name = data.get("source_name")
        if not source_name or not isinstance(source_name, str) or len(source_name.strip()) < 2:
            errors.append("source_name is required and must have at least 2 characters")

        # 2. Check level & state consistency
        level = data.get("level")
        state = data.get("state")
        if level == "central" and state is not None:
            # state should be None for central level schemes
            pass  # Allowed but flagged if needed; per requirement state is None for central
        if level == "state" and not state:
            errors.append("state must be specified for state-level schemes")

        # 3. Check confidence boundaries
        confidence = data.get("confidence", 1.0)
        if not isinstance(confidence, (int, float)) or not (0.0 <= confidence <= 1.0):
            errors.append(f"confidence must be a float between 0.0 and 1.0; got {confidence}")

        # 4. Check eligibility rules
        eligibility = data.get("eligibility") or {}
        criteria = eligibility.get("criteria", [])
        exclusions = eligibility.get("exclusions", [])

        if not isinstance(criteria, list):
            errors.append("eligibility.criteria must be a list")
        else:
            for i, rule in enumerate(criteria):
                rule_errs = cls.validate_rule(rule, f"criteria[{i}]")
                errors.extend(rule_errs)

        if not isinstance(exclusions, list):
            errors.append("eligibility.exclusions must be a list")
        else:
            for i, rule in enumerate(exclusions):
                rule_errs = cls.validate_rule(rule, f"exclusions[{i}]")
                errors.extend(rule_errs)

        return errors

    @classmethod
    def validate_rule(cls, rule_data: Union[Dict[str, Any], EligibilityRule], prefix: str = "rule") -> List[str]:
        errors: List[str] = []
        if isinstance(rule_data, EligibilityRule):
            field_name = rule_data.field.value
            op_name = rule_data.op.value
            val = rule_data.value
            text_en = rule_data.text_en
        elif isinstance(rule_data, dict):
            field_name = rule_data.get("field")
            op_name = rule_data.get("op")
            val = rule_data.get("value")
            text_en = rule_data.get("text_en", "")
        else:
            return [f"{prefix}: must be a dictionary or EligibilityRule instance"]

        # Validate field enum
        valid_fields = {f.value for f in RuleField}
        if field_name not in valid_fields:
            errors.append(f"{prefix}.field '{field_name}' is invalid. Allowed fields: {sorted(valid_fields)}")
            return errors  # Cannot safely inspect further without valid field

        # Validate operator enum
        valid_ops = {o.value for o in RuleOperator}
        if op_name not in valid_ops:
            errors.append(f"{prefix}.op '{op_name}' is invalid. Allowed ops: {sorted(valid_ops)}")
            return errors

        # Validate operator-value compatibility
        if op_name == RuleOperator.BETWEEN.value:
            if not isinstance(val, (list, tuple)) or len(val) != 2:
                errors.append(f"{prefix}: operator 'between' requires a list [min, max]")
            else:
                min_val, max_val = val[0], val[1]
                if not isinstance(min_val, (int, float)) or not isinstance(max_val, (int, float)):
                    errors.append(f"{prefix}: operator 'between' [min, max] boundaries must be numeric")
                elif min_val > max_val:
                    errors.append(f"{prefix}: operator 'between' min ({min_val}) cannot be greater than max ({max_val})")

        elif op_name in (RuleOperator.IN.value, RuleOperator.NOT_IN.value):
            if not isinstance(val, (list, tuple, set)) or len(val) == 0:
                errors.append(f"{prefix}: operator '{op_name}' requires a non-empty list of values")

        elif op_name in (RuleOperator.GTE.value, RuleOperator.LTE.value):
            if not isinstance(val, (int, float)):
                errors.append(f"{prefix}: operator '{op_name}' requires a numeric comparison value")

        # Field-specific domain boundary validation
        if field_name == RuleField.AGE.value:
            cls._validate_age_boundaries(val, op_name, prefix, errors)

        elif field_name == RuleField.ANNUAL_INCOME.value:
            cls._validate_income_boundaries(val, op_name, text_en, prefix, errors)

        elif field_name == RuleField.LAND_ACRES.value:
            cls._validate_land_boundaries(val, op_name, prefix, errors)

        return errors

    @classmethod
    def _validate_age_boundaries(cls, val: Any, op: str, prefix: str, errors: List[str]):
        if op == RuleOperator.BETWEEN.value and isinstance(val, (list, tuple)) and len(val) == 2:
            min_age, max_age = val[0], val[1]
            if min_age < 0 or max_age < 0:
                errors.append(f"{prefix}: age values cannot be negative; got [{min_age}, {max_age}]")
            if min_age > 125 or max_age > 125:
                errors.append(f"{prefix}: impossible age value > 125; got [{min_age}, {max_age}]")
        elif isinstance(val, (int, float)):
            if val < 0:
                errors.append(f"{prefix}: age cannot be negative; got {val}")
            if val > 125:
                errors.append(f"{prefix}: impossible age > 125; got {val}")

    @classmethod
    def _validate_income_boundaries(cls, val: Any, op: str, text_en: str, prefix: str, errors: List[str]):
        # Check negative
        if op == RuleOperator.BETWEEN.value and isinstance(val, (list, tuple)) and len(val) == 2:
            min_inc, max_inc = val[0], val[1]
            if min_inc < 0 or max_inc < 0:
                errors.append(f"{prefix}: annual income cannot be negative; got [{min_inc}, {max_inc}]")
            cls._check_lakh_crore_confusion(min_inc, text_en, prefix, errors)
            cls._check_lakh_crore_confusion(max_inc, text_en, prefix, errors)
        elif isinstance(val, (int, float)):
            if val < 0:
                errors.append(f"{prefix}: annual income cannot be negative; got {val}")
            cls._check_lakh_crore_confusion(val, text_en, prefix, errors)

    @classmethod
    def _check_lakh_crore_confusion(cls, num_val: Union[int, float], text_en: str, prefix: str, errors: List[str]):
        # Flag 1: If value is small (e.g. 1 to 50), it is likely in Lakhs but stored as scalar units without multiplying by 100,000.
        if 0 < num_val <= 100:
            errors.append(
                f"{prefix}: annual income value {num_val} appears to be in Lakhs/thousands rather than raw Rupees. "
                f"Please specify full Rupee amount (e.g., 200000 instead of 2)."
            )
        # Flag 2: If value exceeds 10,00,00,000 (10 Crores), likely an unrealistic or confused welfare scheme figure.
        elif num_val > 100000000:
            errors.append(
                f"{prefix}: annual income {num_val} exceeds ₹10 Crore, indicating probable unit/crore confusion."
            )

        # Flag 3: Text mentions 'lakh' or 'crore' but figure doesn't match
        lower_text = text_en.lower() if text_en else ""
        if "lakh" in lower_text or "lac" in lower_text:
            match = re.search(r"(\d+(?:\.\d+)?)\s*(?:lakh|lac)", lower_text)
            if match:
                expected_approx = float(match.group(1)) * 100000
                if abs(num_val - expected_approx) > (expected_approx * 0.5) and num_val != float(match.group(1)):
                    errors.append(
                        f"{prefix}: text mentions '{match.group(0)}' (~₹{expected_approx:,.0f}) but rule value is {num_val}. Check for Lakh confusion."
                    )

    @classmethod
    def _validate_land_boundaries(cls, val: Any, op: str, prefix: str, errors: List[str]):
        if op == RuleOperator.BETWEEN.value and isinstance(val, (list, tuple)) and len(val) == 2:
            min_l, max_l = val[0], val[1]
            if min_l < 0 or max_l < 0:
                errors.append(f"{prefix}: land acres cannot be negative; got [{min_l}, {max_l}]")
            if max_l > 10000:
                errors.append(f"{prefix}: unrealistic land acres > 10,000; got {max_l}")
        elif isinstance(val, (int, float)):
            if val < 0:
                errors.append(f"{prefix}: land acres cannot be negative; got {val}")
            if val > 10000:
                errors.append(f"{prefix}: unrealistic land acres > 10,000; got {val}")

    @classmethod
    def validate_or_raise(cls, data: Union[Dict[str, Any], Scheme]) -> Scheme:
        """Validates dict or Scheme; raises SchemeValidationError if invalid, or returns parsed Scheme."""
        raw_dict = data.model_dump() if isinstance(data, Scheme) else data
        errors = cls.validate_dict(raw_dict)
        if errors:
            raise SchemeValidationError(errors)

        try:
            if isinstance(data, Scheme):
                return data
            return Scheme(**data)
        except ValidationError as e:
            pydantic_errors = [f"{err['loc']}: {err['msg']}" for err in e.errors()]
            raise SchemeValidationError(errors + pydantic_errors)
