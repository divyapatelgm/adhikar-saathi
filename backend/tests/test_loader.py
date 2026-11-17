import pytest
from backend.app.engine.loader import SchemeLoader
from backend.app.models.enums import TierType

def test_loader_excludes_placeholders_when_demo_mode_false():
    loader = SchemeLoader(demo_mode=False)
    counts = loader.get_counts()
    # In production mode without demo_mode, placeholders must be hidden
    assert counts["verified"] == 0
    assert counts["total"] == 0
    assert loader.get_scheme("placeholder-karnataka-farmer-grant") is None

def test_loader_includes_placeholders_when_demo_mode_true():
    loader = SchemeLoader(demo_mode=True)
    counts = loader.get_counts()
    assert counts["verified"] >= 5
    assert counts["total"] >= 5

    scheme = loader.get_scheme("placeholder-karnataka-farmer-grant")
    assert scheme is not None
    assert scheme.is_placeholder is True
    assert scheme.tier == TierType.VERIFIED
    assert "Karnataka" in scheme.names["en"]

def test_loader_filter_by_category():
    loader = SchemeLoader(demo_mode=True)
    agri_schemes = loader.filter_schemes(category="agriculture")
    assert len(agri_schemes) >= 1
    assert all("agriculture" in s.category for s in agri_schemes)
