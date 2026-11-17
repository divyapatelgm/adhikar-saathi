import pytest
from backend.app.models.profile import UserProfile
from backend.app.models.scheme import Scheme, SchemeBenefit, HowToApply, EligibilityContainer
from backend.app.models.rule import EligibilityRule
from backend.app.models.enums import (
    RuleField, RuleOperator, TierType, SchemeStatus, LevelType, VerdictType
)
from backend.app.engine.rules_engine import RulesEngine

def make_scheme(
    scheme_id: str = "test-scheme",
    tier: TierType = TierType.VERIFIED,
    confidence: float = 1.0,
    criteria: list = None,
    exclusions: list = None,
    level: LevelType = LevelType.STATE,
    state: str = "Karnataka"
) -> Scheme:
    return Scheme(
        id=scheme_id,
        tier=tier,
        status=SchemeStatus.VERIFIED if tier == TierType.VERIFIED else SchemeStatus.UNVERIFIED,
        confidence=confidence,
        names={"en": f"Scheme {scheme_id}"},
        level=level,
        state=state if level == LevelType.STATE else None,
        department="Test Dept",
        category=["agriculture"],
        target_groups=["farmer"],
        summary_en="Test summary",
        benefit=SchemeBenefit(type="cash", description="Test benefit"),
        eligibility=EligibilityContainer(
            criteria=criteria or [],
            exclusions=exclusions or []
        ),
        how_to_apply=HowToApply(steps=["Step 1"]),
        official_url="https://karnataka.gov.in/test",
        source_name="Gov of Karnataka"
    )

# --- 1. Boundary tests for numeric criteria ---

def test_boundary_age_exact_min():
    """Citizen age exactly equals min bound (18) of between [18, 65]."""
    scheme = make_scheme(criteria=[
        EligibilityRule(field=RuleField.AGE, op=RuleOperator.BETWEEN, value=[18, 65], text_en="Age 18-65")
    ])
    profile = UserProfile(age=18, state="Karnataka")
    res = RulesEngine.evaluate_scheme(profile, scheme)
    assert res.verdict == VerdictType.ELIGIBLE

def test_boundary_age_exact_max():
    """Citizen age exactly equals max bound (65) of between [18, 65]."""
    scheme = make_scheme(criteria=[
        EligibilityRule(field=RuleField.AGE, op=RuleOperator.BETWEEN, value=[18, 65], text_en="Age 18-65")
    ])
    profile = UserProfile(age=65, state="Karnataka")
    res = RulesEngine.evaluate_scheme(profile, scheme)
    assert res.verdict == VerdictType.ELIGIBLE

def test_boundary_age_one_below_min():
    """Citizen age 17 is below min bound 18."""
    scheme = make_scheme(criteria=[
        EligibilityRule(field=RuleField.AGE, op=RuleOperator.BETWEEN, value=[18, 65], text_en="Age 18-65")
    ])
    profile = UserProfile(age=17, state="Karnataka")
    res = RulesEngine.evaluate_scheme(profile, scheme)
    assert res.verdict == VerdictType.NOT_ELIGIBLE

def test_boundary_age_one_above_max():
    """Citizen age 66 is above max bound 65."""
    scheme = make_scheme(criteria=[
        EligibilityRule(field=RuleField.AGE, op=RuleOperator.BETWEEN, value=[18, 65], text_en="Age 18-65")
    ])
    profile = UserProfile(age=66, state="Karnataka")
    res = RulesEngine.evaluate_scheme(profile, scheme)
    assert res.verdict == VerdictType.NOT_ELIGIBLE

def test_boundary_income_exact_limit():
    """Income equals exact maximum ceiling."""
    scheme = make_scheme(criteria=[
        EligibilityRule(field=RuleField.ANNUAL_INCOME, op=RuleOperator.LTE, value=150000.0, text_en="Income <= 150000")
    ])
    profile = UserProfile(annual_income=150000.0, state="Karnataka")
    res = RulesEngine.evaluate_scheme(profile, scheme)
    assert res.verdict == VerdictType.ELIGIBLE

def test_boundary_income_exceeded():
    """Income 150001 exceeds ceiling of 150000."""
    scheme = make_scheme(criteria=[
        EligibilityRule(field=RuleField.ANNUAL_INCOME, op=RuleOperator.LTE, value=150000.0, text_en="Income <= 150000")
    ])
    profile = UserProfile(annual_income=150001.0, state="Karnataka")
    res = RulesEngine.evaluate_scheme(profile, scheme)
    assert res.verdict == VerdictType.NOT_ELIGIBLE

# --- 2. Missing fields tests (MAYBE verdicts) ---

def test_missing_single_field_returns_maybe():
    """Missing age in profile yields MAYBE verdict with age in missing_info."""
    scheme = make_scheme(criteria=[
        EligibilityRule(field=RuleField.AGE, op=RuleOperator.GTE, value=18, text_en="Age >= 18")
    ])
    profile = UserProfile(state="Karnataka")  # age is None
    res = RulesEngine.evaluate_scheme(profile, scheme)
    assert res.verdict == VerdictType.MAYBE
    assert "age" in res.missing_info
    assert res.missing_question is not None

def test_missing_multiple_fields():
    """Missing multiple fields tracks all required unknown fields."""
    scheme = make_scheme(criteria=[
        EligibilityRule(field=RuleField.OCCUPATION, op=RuleOperator.EQ, value="farmer", text_en="Must be farmer"),
        EligibilityRule(field=RuleField.ANNUAL_INCOME, op=RuleOperator.LTE, value=200000.0, text_en="Income <= 2L"),
        EligibilityRule(field=RuleField.OWNS_LAND, op=RuleOperator.IS_TRUE, value=True, text_en="Owns land")
    ])
    profile = UserProfile(state="Karnataka")
    res = RulesEngine.evaluate_scheme(profile, scheme)
    assert res.verdict == VerdictType.MAYBE
    assert set(res.missing_info) == {"occupation", "annual_income", "owns_land"}

# --- 3. Exclusion Rules ---

def test_exclusion_rule_triggers_disqualification():
    """Even if all criteria pass, an exclusion match results in NOT_ELIGIBLE."""
    scheme = make_scheme(
        criteria=[
            EligibilityRule(field=RuleField.OCCUPATION, op=RuleOperator.EQ, value="farmer", text_en="Farmer")
        ],
        exclusions=[
            EligibilityRule(field=RuleField.LAND_ACRES, op=RuleOperator.GTE, value=10.0, text_en="Land >= 10 acres excludes")
        ]
    )
    profile = UserProfile(occupation="farmer", land_acres=12.0, state="Karnataka")
    res = RulesEngine.evaluate_scheme(profile, scheme)
    assert res.verdict == VerdictType.NOT_ELIGIBLE
    assert any("Excluded" in f for f in res.failed_criteria)

def test_exclusion_rule_not_triggered():
    """Farmer with land below exclusion limit is eligible."""
    scheme = make_scheme(
        criteria=[
            EligibilityRule(field=RuleField.OCCUPATION, op=RuleOperator.EQ, value="farmer", text_en="Farmer")
        ],
        exclusions=[
            EligibilityRule(field=RuleField.LAND_ACRES, op=RuleOperator.GTE, value=10.0, text_en="Land >= 10 acres excludes")
        ]
    )
    profile = UserProfile(occupation="farmer", land_acres=4.0, state="Karnataka")
    res = RulesEngine.evaluate_scheme(profile, scheme)
    assert res.verdict == VerdictType.ELIGIBLE

def test_exclusion_field_missing_returns_maybe():
    """If candidate matches criteria but exclusion field is unknown, returns MAYBE."""
    scheme = make_scheme(
        criteria=[
            EligibilityRule(field=RuleField.OCCUPATION, op=RuleOperator.EQ, value="farmer", text_en="Farmer")
        ],
        exclusions=[
            EligibilityRule(field=RuleField.LAND_ACRES, op=RuleOperator.GTE, value=10.0, text_en="Land >= 10 acres excludes")
        ]
    )
    profile = UserProfile(occupation="farmer", land_acres=None, state="Karnataka")
    res = RulesEngine.evaluate_scheme(profile, scheme)
    assert res.verdict == VerdictType.MAYBE
    assert "land_acres" in res.missing_info

# --- 4. Tier 2 (Extracted) Record Caps ---

def test_tier2_high_confidence_returns_likely_never_eligible():
    """Tier 2 records can return only LIKELY or MAYBE (never ELIGIBLE)."""
    scheme = make_scheme(
        tier=TierType.EXTRACTED,
        confidence=0.85,
        criteria=[
            EligibilityRule(field=RuleField.OCCUPATION, op=RuleOperator.EQ, value="farmer", text_en="Farmer")
        ]
    )
    profile = UserProfile(occupation="farmer", state="Karnataka")
    res = RulesEngine.evaluate_scheme(profile, scheme)
    assert res.verdict == VerdictType.LIKELY
    assert res.verdict != VerdictType.ELIGIBLE

def test_tier2_low_confidence_capped_at_maybe():
    """Tier 2 with confidence < 0.7 is capped at MAYBE even when criteria all match."""
    scheme = make_scheme(
        tier=TierType.EXTRACTED,
        confidence=0.65,  # < 0.7
        criteria=[
            EligibilityRule(field=RuleField.OCCUPATION, op=RuleOperator.EQ, value="farmer", text_en="Farmer")
        ]
    )
    profile = UserProfile(occupation="farmer", state="Karnataka")
    res = RulesEngine.evaluate_scheme(profile, scheme)
    assert res.verdict == VerdictType.MAYBE
    assert "low" in res.reason_en.lower()

def test_tier2_failed_criterion_returns_not_eligible():
    """Tier 2 record with failed criterion returns NOT_ELIGIBLE."""
    scheme = make_scheme(
        tier=TierType.EXTRACTED,
        confidence=0.9,
        criteria=[
            EligibilityRule(field=RuleField.OCCUPATION, op=RuleOperator.EQ, value="farmer", text_en="Farmer")
        ]
    )
    profile = UserProfile(occupation="student", state="Karnataka")
    res = RulesEngine.evaluate_scheme(profile, scheme)
    assert res.verdict == VerdictType.NOT_ELIGIBLE

# --- 5. Operators tests ---

def test_operator_eq_case_insensitive():
    scheme = make_scheme(criteria=[
        EligibilityRule(field=RuleField.OCCUPATION, op=RuleOperator.EQ, value="farmer", text_en="Farmer")
    ])
    profile = UserProfile(occupation="FaRmEr", state="Karnataka")
    res = RulesEngine.evaluate_scheme(profile, scheme)
    assert res.verdict == VerdictType.ELIGIBLE

def test_operator_ne():
    scheme = make_scheme(criteria=[
        EligibilityRule(field=RuleField.CATEGORY, op=RuleOperator.NE, value="GEN", text_en="Non-general")
    ])
    profile1 = UserProfile(category="SC", state="Karnataka")
    profile2 = UserProfile(category="GEN", state="Karnataka")
    assert RulesEngine.evaluate_scheme(profile1, scheme).verdict == VerdictType.ELIGIBLE
    assert RulesEngine.evaluate_scheme(profile2, scheme).verdict == VerdictType.NOT_ELIGIBLE

def test_operator_in():
    scheme = make_scheme(criteria=[
        EligibilityRule(field=RuleField.CATEGORY, op=RuleOperator.IN, value=["SC", "ST"], text_en="SC or ST")
    ])
    assert RulesEngine.evaluate_scheme(UserProfile(category="sc", state="Karnataka"), scheme).verdict == VerdictType.ELIGIBLE
    assert RulesEngine.evaluate_scheme(UserProfile(category="OBC", state="Karnataka"), scheme).verdict == VerdictType.NOT_ELIGIBLE

def test_operator_not_in():
    scheme = make_scheme(criteria=[
        EligibilityRule(field=RuleField.MARITAL_STATUS, op=RuleOperator.NOT_IN, value=["married"], text_en="Unmarried")
    ])
    assert RulesEngine.evaluate_scheme(UserProfile(marital_status="single", state="Karnataka"), scheme).verdict == VerdictType.ELIGIBLE
    assert RulesEngine.evaluate_scheme(UserProfile(marital_status="married", state="Karnataka"), scheme).verdict == VerdictType.NOT_ELIGIBLE

def test_operator_is_true():
    scheme = make_scheme(criteria=[
        EligibilityRule(field=RuleField.BPL, op=RuleOperator.IS_TRUE, value=True, text_en="BPL card holder")
    ])
    assert RulesEngine.evaluate_scheme(UserProfile(bpl=True, state="Karnataka"), scheme).verdict == VerdictType.ELIGIBLE
    assert RulesEngine.evaluate_scheme(UserProfile(bpl=False, state="Karnataka"), scheme).verdict == VerdictType.NOT_ELIGIBLE

def test_operator_is_false():
    scheme = make_scheme(criteria=[
        EligibilityRule(field=RuleField.DISABILITY, op=RuleOperator.IS_FALSE, value=False, text_en="No disability")
    ])
    assert RulesEngine.evaluate_scheme(UserProfile(disability=False, state="Karnataka"), scheme).verdict == VerdictType.ELIGIBLE
    assert RulesEngine.evaluate_scheme(UserProfile(disability=True, state="Karnataka"), scheme).verdict == VerdictType.NOT_ELIGIBLE

# --- 6. State Residency & Central Schemes ---

def test_state_scheme_residence_check():
    scheme = make_scheme(level=LevelType.STATE, state="Karnataka")
    # Matching state
    res_ka = RulesEngine.evaluate_scheme(UserProfile(state="Karnataka"), scheme)
    assert res_ka.verdict == VerdictType.ELIGIBLE
    # Other state
    res_tn = RulesEngine.evaluate_scheme(UserProfile(state="Tamil Nadu"), scheme)
    assert res_tn.verdict == VerdictType.NOT_ELIGIBLE

def test_central_scheme_accepts_any_state():
    scheme = make_scheme(level=LevelType.CENTRAL, state=None)
    res_dl = RulesEngine.evaluate_scheme(UserProfile(state="Delhi"), scheme)
    assert res_dl.verdict == VerdictType.ELIGIBLE

# --- 7. Ranking Order ---

def test_ranking_order_eligible_likely_maybe_not_eligible():
    """Verifies that evaluate_all ranks schemes strictly: ELIGIBLE > LIKELY > MAYBE > NOT_ELIGIBLE."""
    s_eligible = make_scheme(scheme_id="s1", tier=TierType.VERIFIED, criteria=[
        EligibilityRule(field=RuleField.AGE, op=RuleOperator.GTE, value=18, text_en="Age >= 18")
    ])
    s_likely = make_scheme(scheme_id="s2", tier=TierType.EXTRACTED, confidence=0.85, criteria=[
        EligibilityRule(field=RuleField.AGE, op=RuleOperator.GTE, value=18, text_en="Age >= 18")
    ])
    s_maybe = make_scheme(scheme_id="s3", tier=TierType.VERIFIED, criteria=[
        EligibilityRule(field=RuleField.OWNS_LAND, op=RuleOperator.IS_TRUE, value=True, text_en="Owns land")
    ])
    s_not_eligible = make_scheme(scheme_id="s4", tier=TierType.VERIFIED, criteria=[
        EligibilityRule(field=RuleField.AGE, op=RuleOperator.LTE, value=15, text_en="Age <= 15")
    ])

    profile = UserProfile(age=25, state="Karnataka")  # owns_land is None -> s3 is Maybe; age 25 fails s4
    results = RulesEngine.evaluate_all(profile, [s_not_eligible, s_maybe, s_likely, s_eligible])

    verdicts = [r.verdict for r in results]
    assert verdicts == [VerdictType.ELIGIBLE, VerdictType.LIKELY, VerdictType.MAYBE, VerdictType.NOT_ELIGIBLE]
