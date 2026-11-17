from typing import Dict, List, Optional
from ..models.api import ChatResponse, SourceCitation

DEFAULT_PORTALS: Dict[str, str] = {
    "karnataka": "https://sevasindhu.karnataka.gov.in",
    "central": "https://www.myscheme.gov.in",
    "general": "https://www.india.gov.in",
}

class Tier3LinkOutService:
    """
    Tier 3 Link-Out and Anti-Hallucination Guardrail.
    When a requested scheme or rights query is not found in verified or extracted datasets,
    this service generates a factual redirection response with official portal links,
    strictly refusing to invent scheme figures, deadlines, or criteria.
    """

    RESPONSES_BY_LANG = {
        "en": (
            "We do not have a verified or extracted record for '{query}' in our local database. "
            "To prevent misinformation, we do not invent scheme criteria or benefits. "
            "Please check the official government portal directly or visit your nearest Grama One / Seva Sindhu center."
        ),
        "kn": (
            "ನಮ್ಮ ಸ್ಥಳೀಯ ಡೇಟಾಬೇಸ್‌ನಲ್ಲಿ '{query}' ಬಗ್ಗೆ ಪರಿಶೀಲಿಸಿದ ಯಾವುದೇ ದಾಖಲೆ ಲಭ್ಯವಿಲ್ಲ. "
            "ತಪ್ಪುದಾರಿಗೆಳೆಯುವಿಕೆಯನ್ನು ತಡೆಯಲು, ನಾವು ಯಾವುದೇ ಕಲ್ಪಿತ ವಿವರಗಳನ್ನು ನೀಡುವುದಿಲ್ಲ. "
            "ದಯವಿಟ್ಟು ನೇರವಾಗಿ ಅಧಿಕೃತ ಸರ್ಕಾರಿ ಪೋರ್ಟಲ್‌ನಲ್ಲಿ ಪರಿಶೀಲಿಸಿ ಅಥವಾ ನಿಮ್ಮ ಸಮೀಪದ ಗ್ರಾಮ ಒನ್ / ಸೇವಾ ಸಿಂಧು ಕೇಂದ್ರಕ್ಕೆ ಭೇಟಿ ನೀಡಿ."
        ),
        "hi": (
            "हमारे स्थानीय डेटाबेस में '{query}' के संबंध में कोई सत्यापित रिकॉर्ड उपलब्ध नहीं है। "
            "भ्रामक जानकारी से बचने के लिए, हम मनगढ़ंत विवरण प्रदान नहीं करते हैं। "
            "कृपया सीधे आधिकारिक सरकारी पोर्टल पर जांचें या अपने निकटतम नागरिक सेवा केंद्र पर जाएं।"
        ),
    }

    @classmethod
    def generate_linkout_response(
        cls,
        query: str,
        language: str = "en",
        region: str = "karnataka"
    ) -> ChatResponse:
        portal_url = DEFAULT_PORTALS.get(region.lower(), DEFAULT_PORTALS["general"])
        lang = language if language in cls.RESPONSES_BY_LANG else "en"

        clean_query = query.strip()
        msg_template = cls.RESPONSES_BY_LANG[lang]
        reply_text = msg_template.format(query=clean_query)

        sources = [
            SourceCitation(
                source_name="Official Karnataka Seva Sindhu Portal" if region == "karnataka" else "National myScheme Portal",
                official_url=portal_url,
                last_verified=None,
                tier="tier-3-link-out"
            )
        ]

        return ChatResponse(
            reply_text=reply_text,
            language=lang,
            sources=sources,
            is_link_out=True,
            disclaimer="Information only, not legal advice. Please verify at the official office/portal."
        )
