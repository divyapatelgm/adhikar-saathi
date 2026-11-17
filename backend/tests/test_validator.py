import pytest
from backend.app.engine.validator import SchemeValidator, SchemeValidationError

def get_base_scheme_dict():
    return {
        "id": "valid-test-scheme",
        "tier": "verified",
        "status": "verified",
        "confidence": 1.0,
        "is_placeholder": False,
        "names": {"en": "Valid Test Scheme"},
        "level": "state",
        "state": "Karnataka",
        "department": "Agriculture",
        "category": ["agriculture"],
        "target_groups": ["farmer"],
        "summary_en": "Summary",
        "benefit": {"type": "cash", "description": "Cash support"},
        "eligibility": {
            "criteria": [
                {
                    "field": "age",
                    "op": "between",
                    "value": [18, 65],
                    "text_en": "Age must be between 18 and 65"
                }
            ],
            "exclusions": []
        },
        "documents_required": ["Aadhaar"],
        "how_to_apply": {"steps": ["Apply online"], "mode": "online"},
        "official_url": "https://karnataka.gov.in/agri",
        "source_name": "Dept of Agriculture"
    }

def test_validator_accepts_valid_scheme():
    data = get_base_scheme_dict()
    scheme = SchemeValidator.validate_or_raise(data)
    assert scheme.id == "valid-test-scheme"
    assert scheme.names["en"] == "Valid Test Scheme"

def test_validator_rejects_missing_official_url():
    data = get_base_scheme_dict()
    data["official_url"] = ""
    with pytest.raises(SchemeValidationError) as exc:
        SchemeValidator.validate_or_raise(data)
    assert any("official_url" in err for err in exc.value.errors)

def test_validator_rejects_non_http_url():
    data = get_base_scheme_dict()
    data["official_url"] = "ftp://invalid-url.com"
    with pytest.raises(SchemeValidationError) as exc:
        SchemeValidator.validate_or_raise(data)
    assert any("http://" in err or "https://" in err for err in exc.value.errors)

def test_validator_rejects_missing_source_name():
    data = get_base_scheme_dict()
    data["source_name"] = " "
    with pytest.raises(SchemeValidationError) as exc:
        SchemeValidator.validate_or_raise(data)
    assert any("source_name" in err for err in exc.value.errors)

def test_validator_rejects_negative_age():
    data = get_base_scheme_dict()
    data["eligibility"]["criteria"] = [
        {
            "field": "age",
            "op": "gte",
            "value": -5,
            "text_en": "Age >= -5"
        }
    ]
    with pytest.raises(SchemeValidationError) as exc:
        SchemeValidator.validate_or_raise(data)
    assert any("negative" in err for err in exc.value.errors)

def test_validator_rejects_impossible_age_over_125():
    data = get_base_scheme_dict()
    data["eligibility"]["criteria"] = [
        {
            "field": "age",
            "op": "lte",
            "value": 200,
            "text_en": "Age <= 200"
        }
    ]
    with pytest.raises(SchemeValidationError) as exc:
        SchemeValidator.validate_or_raise(data)
    assert any("125" in err for err in exc.value.errors)

def test_validator_detects_lakh_confusion():
    data = get_base_scheme_dict()
    # Income entered as scalar 2.0 (meaning 2 Lakhs, but not multiplied by 100,000)
    data["eligibility"]["criteria"] = [
        {
            "field": "annual_income",
            "op": "lte",
            "value": 2.5,
            "text_en": "Annual income must be under 2.5 Lakh"
        }
    ]
    with pytest.raises(SchemeValidationError) as exc:
        SchemeValidator.validate_or_raise(data)
    assert any("Lakhs" in err or "Rupees" in err for err in exc.value.errors)

def test_validator_detects_crore_confusion():
    data = get_base_scheme_dict()
    data["eligibility"]["criteria"] = [
        {
            "field": "annual_income",
            "op": "lte",
            "value": 500000000.0,  # 50 Crores
            "text_en": "Annual income under 50 Crores"
        }
    ]
    with pytest.raises(SchemeValidationError) as exc:
        SchemeValidator.validate_or_raise(data)
    assert any("Crore" in err for err in exc.value.errors)
