import pytest
from pydantic import ValidationError

from backend.app.models.profile import UserProfile
from backend.app.models.rule import EligibilityRule
from backend.app.models.scheme import Scheme, SchemeBenefit, HowToApply, EligibilityContainer
from backend.app.models.enums import RuleField, RuleOperator, LevelType, TierType, SchemeStatus, VerdictType

def test_user_profile_all_defaults_none():
    """Verify that UserProfile has NO default values; every field is None."""
    p = UserProfile()
    assert p.age is None
    assert p.gender is None
    assert p.state is None
    assert p.district is None
    assert p.occupation is None
    assert p.annual_income is None
    assert p.category is None
    assert p.owns_land is None
    assert p.land_acres is None
    assert p.is_student is None
    assert p.education_level is None
    assert p.disability is None
    assert p.marital_status is None
    assert p.bpl is None

def test_scheme_state_default_none_and_is_placeholder_default_false():
    """Verify Scheme.state defaults to None and is_placeholder defaults to False."""
    s = Scheme(
        id="test-central-scheme",
        tier=TierType.VERIFIED,
        status=SchemeStatus.VERIFIED,
        confidence=1.0,
        names={"en": "Test Central Scheme"},
        level=LevelType.CENTRAL,
        department="Central Dept",
        summary_en="Test summary",
        benefit=SchemeBenefit(type="cash", description="Test cash benefit"),
        eligibility=EligibilityContainer(criteria=[]),
        how_to_apply=HowToApply(steps=["Step 1"]),
        official_url="https://example.gov.in/test",
        source_name="Gov of India",
    )
    assert s.state is None
    assert s.is_placeholder is False

def test_eligibility_rule_valid_fields():
    """Verify EligibilityRule accepts valid RuleField enum values."""
    rule = EligibilityRule(
        field=RuleField.AGE,
        op=RuleOperator.GTE,
        value=18,
        text_en="Age must be 18 or above"
    )
    assert rule.field == RuleField.AGE
    assert rule.op == RuleOperator.GTE
    assert rule.value == 18

def test_eligibility_rule_rejects_invalid_field():
    """Verify EligibilityRule rejects unknown field strings."""
    with pytest.raises(ValidationError):
        EligibilityRule(
            field="astrological_sign",  # Invalid field
            op=RuleOperator.EQ,
            value="Aries",
            text_en="Invalid"
        )

def test_eligibility_rule_between_requires_two_elements():
    """Operator 'between' requires a list of exactly 2 numbers."""
    with pytest.raises(ValidationError):
        EligibilityRule(
            field=RuleField.AGE,
            op=RuleOperator.BETWEEN,
            value=[18],  # Only 1 element
            text_en="Invalid between"
        )

def test_eligibility_rule_between_rejects_min_greater_than_max():
    """Operator 'between' rejects min > max."""
    with pytest.raises(ValidationError):
        EligibilityRule(
            field=RuleField.AGE,
            op=RuleOperator.BETWEEN,
            value=[60, 18],  # 60 > 18
            text_en="Invalid between inverted"
        )

def test_eligibility_rule_in_requires_non_empty_list():
    """Operator 'in' requires non-empty list."""
    with pytest.raises(ValidationError):
        EligibilityRule(
            field=RuleField.CATEGORY,
            op=RuleOperator.IN,
            value=[],  # Empty list
            text_en="Invalid in"
        )

def test_verdict_type_contains_likely():
    """Verify VerdictType contains LIKELY."""
    assert VerdictType.LIKELY.value == "Likely"
    assert VerdictType.ELIGIBLE.value == "Eligible"
    assert VerdictType.MAYBE.value == "Maybe"
    assert VerdictType.NOT_ELIGIBLE.value == "Not eligible"
