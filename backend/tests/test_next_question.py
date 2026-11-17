import pytest
from backend.app.models.profile import UserProfile
from backend.app.models.scheme import Scheme, SchemeBenefit, HowToApply, EligibilityContainer
from backend.app.models.rule import EligibilityRule
from backend.app.models.enums import RuleField, RuleOperator, TierType, SchemeStatus, LevelType
from backend.app.engine.question_selector import next_question

def make_scheme(scheme_id: str, criteria: list) -> Scheme:
    return Scheme(
        id=scheme_id,
        tier=TierType.VERIFIED,
        status=SchemeStatus.VERIFIED,
        confidence=1.0,
        names={"en": f"Scheme {scheme_id}"},
        level=LevelType.STATE,
        state="Karnataka",
        department="Test",
        summary_en="Test",
        benefit=SchemeBenefit(type="cash", description="Benefit"),
        eligibility=EligibilityContainer(criteria=criteria),
        how_to_apply=HowToApply(steps=["Step 1"]),
        official_url="https://karnataka.gov.in/test",
        source_name="Gov of Karnataka"
    )

def test_next_question_selects_most_frequent_missing_field():
    """Field needed by 3 schemes beats field needed by 1 scheme."""
    # 3 schemes need 'annual_income', only 1 needs 'bpl'
    s1 = make_scheme("s1", [EligibilityRule(field=RuleField.ANNUAL_INCOME, op=RuleOperator.LTE, value=100000.0, text_en="Income <= 1L")])
    s2 = make_scheme("s2", [EligibilityRule(field=RuleField.ANNUAL_INCOME, op=RuleOperator.LTE, value=200000.0, text_en="Income <= 2L")])
    s3 = make_scheme("s3", [EligibilityRule(field=RuleField.ANNUAL_INCOME, op=RuleOperator.LTE, value=300000.0, text_en="Income <= 3L")])
    s4 = make_scheme("s4", [EligibilityRule(field=RuleField.BPL, op=RuleOperator.IS_TRUE, value=True, text_en="Must have BPL")])

    profile = UserProfile(state="Karnataka")  # annual_income and bpl are None
    q = next_question(profile, [s1, s2, s3, s4])

    assert q is not None
    assert q.field == RuleField.ANNUAL_INCOME
    assert q.resolves_maybe_count == 3
    assert "en" in q.question
    assert "kn" in q.question
    assert "hi" in q.question

def test_next_question_tie_breaking():
    """When two fields have the same frequency, higher priority field wins."""
    # 1 scheme needs 'occupation' (priority 90), 1 needs 'category' (priority 75)
    s1 = make_scheme("s1", [EligibilityRule(field=RuleField.OCCUPATION, op=RuleOperator.EQ, value="farmer", text_en="Farmer")])
    s2 = make_scheme("s2", [EligibilityRule(field=RuleField.CATEGORY, op=RuleOperator.EQ, value="SC", text_en="SC")])

    profile = UserProfile(state="Karnataka")
    q = next_question(profile, [s1, s2])

    assert q is not None
    assert q.field == RuleField.OCCUPATION
    assert q.resolves_maybe_count == 1

def test_next_question_returns_none_when_no_maybe():
    """When all schemes are already ELIGIBLE or NOT_ELIGIBLE, returns None."""
    s1 = make_scheme("s1", [EligibilityRule(field=RuleField.AGE, op=RuleOperator.GTE, value=18, text_en="Age >= 18")])
    profile = UserProfile(age=25, state="Karnataka")

    q = next_question(profile, [s1])
    assert q is None
