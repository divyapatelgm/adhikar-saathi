import difflib
from typing import List, Tuple, Optional, Dict
from ..models.scheme import Scheme

class SchemeDeduplicator:
    """
    Detects potential duplicate schemes by computing name and token similarity
    against existing verified and extracted schemes.
    """

    SIMILARITY_THRESHOLD = 0.85

    @classmethod
    def check_duplicate(
        cls,
        candidate: Scheme,
        existing_schemes: List[Scheme],
        threshold: float = SIMILARITY_THRESHOLD
    ) -> Tuple[bool, Optional[str], float, str]:
        """
        Compares candidate against a list of existing schemes.
        Returns:
            (is_duplicate, matching_scheme_id, similarity_score, reason)
        """
        # 1. Exact ID match check
        for existing in existing_schemes:
            if candidate.id.strip().lower() == existing.id.strip().lower():
                return True, existing.id, 1.0, f"Exact scheme ID match: '{candidate.id}'"

        # 2. Name similarity comparison across languages
        candidate_en = (candidate.names.get("en") or "").strip().lower()
        candidate_slug = candidate_en.replace("placeholder", "").replace("synthetic", "").strip()

        best_score = 0.0
        best_match_id = None
        best_match_name = ""

        for existing in existing_schemes:
            existing_en = (existing.names.get("en") or "").strip().lower()
            existing_slug = existing_en.replace("placeholder", "").replace("synthetic", "").strip()

            # Sequence similarity
            score = difflib.SequenceMatcher(None, candidate_slug, existing_slug).ratio()

            # Check localized names as well if available
            for lang in ("kn", "hi"):
                c_loc = candidate.names.get(lang, "").strip()
                e_loc = existing.names.get(lang, "").strip()
                if c_loc and e_loc:
                    loc_score = difflib.SequenceMatcher(None, c_loc, e_loc).ratio()
                    if loc_score > score:
                        score = loc_score

            if score > best_score:
                best_score = score
                best_match_id = existing.id
                best_match_name = existing_en

        if best_score >= threshold:
            reason = (
                f"Candidate name '{candidate.names.get('en')}' is {best_score:.1%} similar to "
                f"existing scheme '{best_match_name}' (ID: {best_match_id})"
            )
            return True, best_match_id, best_score, reason

        return False, None, best_score, ""
