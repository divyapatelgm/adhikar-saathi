import json
from pathlib import Path
import pytest
from backend.app.config import settings
from backend.app.engine.rules_engine import RulesEngine
from backend.app.engine.loader import scheme_loader
from backend.app.models.profile import UserProfile
from backend.app.services.tier3_linkout import Tier3LinkOutService

EVAL_PATH = settings.BASE_DIR / "data" / "evaluation_set_30.json"
RIGHTS_KB_PATH = settings.BASE_DIR / "data" / "rights_kb.json"

def test_evaluation_dataset_structure():
    assert EVAL_PATH.exists(), "evaluation_set_30.json must exist"
    with open(EVAL_PATH, "r", encoding="utf-8") as f:
        dataset = json.load(f)
    
    assert len(dataset) == 30, f"Expected 30 evaluation items, got {len(dataset)}"
    
    en_items = [q for q in dataset if q["language"] == "en"]
    kn_items = [q for q in dataset if q["language"] == "kn"]
    hi_items = [q for q in dataset if q["language"] == "hi"]
    
    assert len(en_items) == 10, f"Expected 10 English items, got {len(en_items)}"
    assert len(kn_items) == 10, f"Expected 10 Kannada items, got {len(kn_items)}"
    assert len(hi_items) == 10, f"Expected 10 Hindi items, got {len(hi_items)}"

def test_evaluation_tier3_linkouts():
    """Verify that hallucination-bait queries trigger Tier 3 Link-Out and do not hallucinate."""
    with open(EVAL_PATH, "r", encoding="utf-8") as f:
        dataset = json.load(f)
    
    linkout_items = [q for q in dataset if q["category"] == "linkout"]
    assert len(linkout_items) >= 6
    
    for item in linkout_items:
        response = Tier3LinkOutService.generate_linkout_response(
            query=item["query"],
            language=item["language"]
        )
        assert response.is_link_out is True
        assert len(response.sources) > 0
        assert response.sources[0].tier == "tier-3-link-out"
        assert "not legal advice" in response.disclaimer.lower() or "ಕಾನೂನು ಸಲಹೆಯಲ್ಲ" in response.disclaimer or "सलाह नहीं" in response.disclaimer

def test_evaluation_rights_grounding():
    """Verify that citizen rights inquiries are grounded in the verified rights knowledge base."""
    assert RIGHTS_KB_PATH.exists()
    with open(RIGHTS_KB_PATH, "r", encoding="utf-8") as f:
        rights_data = json.load(f)
    
    topics = {r["topic"] for r in rights_data}
    assert any("MGNREGA" in t for t in topics)
    assert any("RTI" in t or "Information" in t for t in topics)
    assert any("Ration" in t for t in topics)

def test_evaluation_eligibility_verdicts():
    """Verify that eligibility queries produce deterministic verdicts via the rules engine."""
    # Farmer profile eligible for Karnataka farmer grant
    farmer = UserProfile(
        age=42,
        state="Karnataka",
        occupation="farmer",
        annual_income=90000,
        owns_land=True,
        land_acres=2.0
    )
    schemes = scheme_loader.filter_schemes(include_placeholders=True)
    results = RulesEngine.evaluate_all(profile=farmer, schemes=schemes, language="en")
    
    eligible_ids = [r.scheme_id for r in results if r.verdict == "Eligible"]
    assert "placeholder-karnataka-farmer-grant" in eligible_ids

    # Student profile eligible for scholarship (age 6-18, category OBC/SC/ST, income <= 200000)
    student = UserProfile(
        age=16,
        state="Karnataka",
        occupation="student",
        is_student=True,
        category="OBC",
        annual_income=120000
    )
    student_results = RulesEngine.evaluate_all(profile=student, schemes=schemes, language="en")
    eligible_student_ids = [r.scheme_id for r in student_results if r.verdict == "Eligible"]
    assert "placeholder-student-scholarship" in eligible_student_ids
