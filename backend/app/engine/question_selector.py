from collections import Counter
from typing import List, Optional, Dict, Any

from ..models.enums import RuleField, VerdictType
from ..models.profile import UserProfile
from ..models.scheme import Scheme
from ..models.verdict import NextQuestionResponse, QuestionOption
from .rules_engine import RulesEngine

# Question metadata for all standard profile fields
QUESTION_METADATA: Dict[str, Dict[str, Any]] = {
    RuleField.STATE.value: {
        "question": {
            "en": "Which state do you permanently reside in?",
            "kn": "ನೀವು ಶಾಶ್ವತವಾಗಿ ವಾಸಿಸುವ ರಾಜ್ಯ ಯಾವುದು?",
            "hi": "आप स्थायी रूप से किस राज्य में रहते हैं?",
        },
        "input_type": "choice",
        "options": [
            {"value": "Karnataka", "labels": {"en": "Karnataka", "kn": "ಕರ್ನಾಟಕ", "hi": "कर्नाटक"}},
            {"value": "Other", "labels": {"en": "Other State", "kn": "ಇತರ ರಾಜ್ಯ", "hi": "अन्य राज्य"}},
        ],
        "tie_priority": 100,
    },
    RuleField.OCCUPATION.value: {
        "question": {
            "en": "What is your primary occupation?",
            "kn": "ನಿಮ್ಮ ಮುಖ್ಯ ಉದ್ಯೋಗ ಅಥವಾ ವೃತ್ತಿ ಯಾವುದು?",
            "hi": "आपका मुख्य व्यवसाय या कार्य क्या है?",
        },
        "input_type": "choice",
        "options": [
            {"value": "farmer", "labels": {"en": "Farmer / Agriculture", "kn": "ರೈತ / ಕೃಷಿ", "hi": "किसान / कृषि"}},
            {"value": "worker", "labels": {"en": "Daily Wage Worker", "kn": "ದೈನಂದಿನ ಕೂಲಿ ಕಾರ್ಮಿಕ", "hi": "दैनिक मजदूर"}},
            {"value": "student", "labels": {"en": "Student", "kn": "ವಿದ್ಯಾರ್ಥಿ", "hi": "छात्र"}},
            {"value": "artisan", "labels": {"en": "Artisan / Weaver", "kn": "ಕುಶಲಕರ್ಮಿ / ನೇಕಾರ", "hi": "कारीगर / बुनकर"}},
            {"value": "other", "labels": {"en": "Other / Homemaker", "kn": "ಇತರೆ / ಗೃಹಿಣಿ", "hi": "अन्य / गृहिणी"}},
        ],
        "tie_priority": 90,
    },
    RuleField.AGE.value: {
        "question": {
            "en": "What is your current age (in years)?",
            "kn": "ನಿಮ್ಮ ಪ್ರಸ್ತುತ ವಯಸ್ಸು ಎಷ್ಟು?",
            "hi": "आपकी वर्तमान आयु कितनी है?",
        },
        "input_type": "number",
        "options": None,
        "tie_priority": 85,
    },
    RuleField.ANNUAL_INCOME.value: {
        "question": {
            "en": "What is your approximate family annual income in Rupees?",
            "kn": "ನಿಮ್ಮ ಒಟ್ಟು ಕುಟುಂಬದ ಅಂದಾಜು ವಾರ್ಷಿಕ ಆದಾಯ ಎಷ್ಟು ರೂಪಾಯಿ?",
            "hi": "आपके परिवार की अनुमानित कुल वार्षिक आय कितनी है (रुपये)?",
        },
        "input_type": "number",
        "options": None,
        "tie_priority": 80,
    },
    RuleField.CATEGORY.value: {
        "question": {
            "en": "Which social category do you belong to?",
            "kn": "ನಿಮ್ಮ ಸಾಮಾಜಿಕ ವರ್ಗ ಯಾವುದು?",
            "hi": "आप किस सामाजिक श्रेणी से संबंधित हैं?",
        },
        "input_type": "choice",
        "options": [
            {"value": "SC", "labels": {"en": "Scheduled Caste (SC)", "kn": "ಪರಿಶಿಷ್ಟ ಜಾತಿ (SC)", "hi": "अनुसूचित जाति (SC)"}},
            {"value": "ST", "labels": {"en": "Scheduled Tribe (ST)", "kn": "ಪರಿಶಿಷ್ಟ ಪಂಗಡ (ST)", "hi": "अनुसूचित जनजाति (ST)"}},
            {"value": "OBC", "labels": {"en": "Other Backward Class (OBC)", "kn": "ಇತರ ಹಿಂದುಳಿದ ವರ್ಗ (OBC)", "hi": "अन्य पिछड़ा वर्ग (OBC)"}},
            {"value": "GEN", "labels": {"en": "General (GEN)", "kn": "ಸಾಮಾನ್ಯ ವರ್ಗ (GEN)", "hi": "सामान्य (GEN)"}},
        ],
        "tie_priority": 75,
    },
    RuleField.GENDER.value: {
        "question": {
            "en": "What is your gender?",
            "kn": "ನಿಮ್ಮ ಲಿಂಗ ಯಾವುದು?",
            "hi": "आपका लिंग क्या है?",
        },
        "input_type": "choice",
        "options": [
            {"value": "female", "labels": {"en": "Female", "kn": "ಮಹಿಳೆ", "hi": "महिला"}},
            {"value": "male", "labels": {"en": "Male", "kn": "ಪುರುಷ", "hi": "पुरुष"}},
            {"value": "other", "labels": {"en": "Other / Transgender", "kn": "ಇತರೆ / ತೃತೀಯ ಲಿಂಗ", "hi": "अन्य"}},
        ],
        "tie_priority": 70,
    },
    RuleField.BPL.value: {
        "question": {
            "en": "Does your family have a BPL or Antyodaya ration card?",
            "kn": "ನಿಮ್ಮ ಕುಟುಂಬವು ಬಿಪಿಎಲ್ ಅಥವಾ ಅಂತ್ಯೋದಯ ಪಡಿತರ ಚೀಟಿ ಹೊಂದಿದೆಯೇ?",
            "hi": "क्या आपके परिवार के पास बीपीएल या अंत्योदय राशन कार्ड है?",
        },
        "input_type": "boolean",
        "options": [
            {"value": True, "labels": {"en": "Yes, have BPL card", "kn": "ಹೌದು, ಬಿಪಿಎಲ್ ಕಾರ್ಡ್ ಇದೆ", "hi": "हाँ, बीपीएल कार्ड है"}},
            {"value": False, "labels": {"en": "No BPL card", "kn": "ಇಲ್ಲ, ಬಿಪಿಎಲ್ ಕಾರ್ಡ್ ಇಲ್ಲ", "hi": "नहीं, बीपीएल कार्ड नहीं है"}},
        ],
        "tie_priority": 65,
    },
    RuleField.OWNS_LAND.value: {
        "question": {
            "en": "Do you or your family own agricultural land?",
            "kn": "ನಿಮಗೆ ಅಥವಾ ನಿಮ್ಮ ಕುಟುಂಬಕ್ಕೆ ಕೃಷಿ ಭೂಮಿ ಇದೆಯೇ?",
            "hi": "क्या आपके या आपके परिवार के पास कृषि भूमि है?",
        },
        "input_type": "boolean",
        "options": [
            {"value": True, "labels": {"en": "Yes, own land", "kn": "ಹೌದು, ಕೃಷಿ ಭೂಮಿ ಇದೆ", "hi": "हाँ, जमीन है"}},
            {"value": False, "labels": {"en": "No agricultural land", "kn": "ಇಲ್ಲ, ಕೃಷಿ ಭೂಮಿ ಇಲ್ಲ", "hi": "नहीं, जमीन नहीं है"}},
        ],
        "tie_priority": 60,
    },
    RuleField.LAND_ACRES.value: {
        "question": {
            "en": "How many acres of agricultural land do you own?",
            "kn": "ನಿಮ್ಮ ಬಳಿ ಎಷ್ಟು ಎಕರೆ ಕೃಷಿ ಭೂಮಿ ಇದೆ?",
            "hi": "आपके पास कितने एकड़ कृषि भूमि है?",
        },
        "input_type": "number",
        "options": None,
        "tie_priority": 55,
    },
    RuleField.IS_STUDENT.value: {
        "question": {
            "en": "Are you currently enrolled as a student?",
            "kn": "ನೀವು ಪ್ರಸ್ತುತ ವಿದ್ಯಾರ್ಥಿಯಾಗಿದ್ದೀರಾ?",
            "hi": "क्या आप वर्तमान में छात्र हैं?",
        },
        "input_type": "boolean",
        "options": [
            {"value": True, "labels": {"en": "Yes, I am a student", "kn": "ಹೌದು, ನಾನು ವಿದ್ಯಾರ್ಥಿ", "hi": "हाँ, मैं छात्र हूँ"}},
            {"value": False, "labels": {"en": "No", "kn": "ಇಲ್ಲ", "hi": "नहीं"}},
        ],
        "tie_priority": 50,
    },
    RuleField.DISABILITY.value: {
        "question": {
            "en": "Do you have a recognized disability (UDID card or 40%+ disability certificate)?",
            "kn": "ನೀವು ಮಾನ್ಯತೆ ಪಡೆದ ವಿಕಲಚೇತನರೇ (UDID ಕಾರ್ಡ್ ಅಥವಾ 40%+ ಪ್ರಮಾಣಪತ್ರ)?",
            "hi": "क्या आप दिव्यांगजन हैं (यूडीआईडी कार्ड या 40%+ प्रमाण पत्र)?",
        },
        "input_type": "boolean",
        "options": [
            {"value": True, "labels": {"en": "Yes", "kn": "ಹೌದು", "hi": "हाँ"}},
            {"value": False, "labels": {"en": "No", "kn": "ಇಲ್ಲ", "hi": "नहीं"}},
        ],
        "tie_priority": 45,
    },
    RuleField.MARITAL_STATUS.value: {
        "question": {
            "en": "What is your marital status?",
            "kn": "ನಿಮ್ಮ ವೈವಾಹಿಕ ಸ್ಥಿತಿ ಯಾವುದು?",
            "hi": "आपकी वैवाहिक स्थिति क्या है?",
        },
        "input_type": "choice",
        "options": [
            {"value": "single", "labels": {"en": "Single / Unmarried", "kn": "ಅವಿವಾಹಿತ", "hi": "अविवाहित"}},
            {"value": "married", "labels": {"en": "Married", "kn": "ವಿವಾಹಿತ", "hi": "विवाहित"}},
            {"value": "widowed", "labels": {"en": "Widowed", "kn": "ವಿಧವೆ / ವಿಧುರ", "hi": "विधवा / विधुर"}},
            {"value": "divorced", "labels": {"en": "Divorced / Separated", "kn": "ವಿಚ್ಛೇದಿತ", "hi": "तलाकशुदा"}},
        ],
        "tie_priority": 40,
    },
}

def next_question(profile: UserProfile, candidate_schemes: List[Scheme]) -> Optional[NextQuestionResponse]:
    """
    Identifies the single missing field from candidate schemes that resolves
    the most 'Maybe' schemes.
    Returns NextQuestionResponse with trilingual text, options, and resolution count.
    """
    if not candidate_schemes:
        return None

    # 1. Evaluate candidate schemes to identify all 'Maybe' outcomes
    evaluations = [RulesEngine.evaluate_scheme(profile, s) for s in candidate_schemes]
    maybe_evals = [e for e in evaluations if e.verdict == VerdictType.MAYBE]

    if not maybe_evals:
        return None

    # 2. Count missing field occurrences across all MAYBE schemes
    field_counter = Counter()
    for ev in maybe_evals:
        # A scheme lists missing fields; each scheme contributes at most 1 count per field
        seen_in_scheme = set(ev.missing_info)
        for field in seen_in_scheme:
            # Only consider fields that are currently None in profile and not "other"
            if field != RuleField.OTHER.value and getattr(profile, field, None) is None:
                field_counter[field] += 1

    if not field_counter:
        return None

    # 3. Sort by:
    #    a) count of MAYBE schemes resolved (descending)
    #    b) tie_priority from metadata (descending)
    sorted_fields = sorted(
        field_counter.keys(),
        key=lambda f: (
            field_counter[f],
            QUESTION_METADATA.get(f, {}).get("tie_priority", 0)
        ),
        reverse=True
    )

    top_field_str = sorted_fields[0]
    meta = QUESTION_METADATA.get(top_field_str)

    if not meta:
        # Fallback question if field is custom
        return NextQuestionResponse(
            field=RuleField(top_field_str),
            question={
                "en": f"Please provide your {top_field_str.replace('_', ' ')}.",
                "kn": f"ದಯವಿಟ್ಟು ನಿಮ್ಮ {top_field_str} ವಿವರಗಳನ್ನು ತಿಳಿಸಿ.",
                "hi": f"कृपया अपने {top_field_str} का विवरण प्रदान करें।",
            },
            input_type="text",
            options=None,
            resolves_maybe_count=field_counter[top_field_str],
        )

    options_objs = None
    if meta.get("options"):
        options_objs = [
            QuestionOption(value=opt["value"], labels=opt["labels"])
            for opt in meta["options"]
        ]

    return NextQuestionResponse(
        field=RuleField(top_field_str),
        question=meta["question"],
        input_type=meta["input_type"],
        options=options_objs,
        resolves_maybe_count=field_counter[top_field_str],
    )
