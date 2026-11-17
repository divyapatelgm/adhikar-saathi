import pytest
from backend.app.services.tier3_linkout import Tier3LinkOutService

def test_tier3_linkout_karnataka_portal():
    res = Tier3LinkOutService.generate_linkout_response(
        query="Non-existent Space Farmer Rocket Grant",
        language="en",
        region="karnataka"
    )
    assert res.is_link_out is True
    assert "Non-existent Space Farmer Rocket Grant" in res.reply_text
    assert "https://sevasindhu.karnataka.gov.in" in res.sources[0].official_url
    assert res.sources[0].tier == "tier-3-link-out"
    # Anti-hallucination guarantee: disclaimer is present
    assert "Information only, not legal advice" in res.disclaimer

def test_tier3_linkout_kannada():
    res = Tier3LinkOutService.generate_linkout_response(
        query="ಕಲ್ಪಿತ ಯೋಜನೆ",
        language="kn",
        region="karnataka"
    )
    assert res.is_link_out is True
    assert res.language == "kn"
    assert "ದಾಖಲೆ ಲಭ್ಯವಿಲ್ಲ" in res.reply_text
    assert "https://sevasindhu.karnataka.gov.in" in res.sources[0].official_url

def test_tier3_linkout_hindi():
    res = Tier3LinkOutService.generate_linkout_response(
        query="काल्पनिक योजना",
        language="hi",
        region="central"
    )
    assert res.is_link_out is True
    assert res.language == "hi"
    assert "सत्यापित रिकॉर्ड उपलब्ध नहीं है" in res.reply_text
    assert "myscheme.gov.in" in res.sources[0].official_url
