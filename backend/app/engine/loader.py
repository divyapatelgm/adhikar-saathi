import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from ..config import settings
from ..models.scheme import Scheme
from ..models.enums import TierType, SchemeStatus
from .validator import SchemeValidator

logger = logging.getLogger(__name__)

class SchemeLoader:
    """
    Manages loading, validating, caching, and querying of schemes from Tier 1 (verified)
    and Tier 2 (extracted) JSON datasets.
    """

    def __init__(self, verified_path: Optional[Path] = None, extracted_path: Optional[Path] = None, demo_mode: Optional[bool] = None):
        self.verified_path = verified_path or settings.VERIFIED_SCHEMES_PATH
        self.extracted_path = extracted_path or settings.EXTRACTED_SCHEMES_PATH
        self.demo_mode = settings.DEMO_MODE if demo_mode is None else demo_mode
        self._schemes: Dict[str, Scheme] = {}
        self.load_all()

    def load_all(self) -> None:
        """Loads and validates schemes from disk."""
        self._schemes.clear()
        self._load_file(self.verified_path, TierType.VERIFIED)
        self._load_file(self.extracted_path, TierType.EXTRACTED)
        logger.info("Loaded %d total schemes (demo_mode=%s)", len(self._schemes), self.demo_mode)

    def _load_file(self, file_path: Path, expected_tier: TierType) -> None:
        if not file_path.exists():
            logger.warning("Data file does not exist: %s", file_path)
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_items = json.load(f)
        except Exception as e:
            logger.error("Error reading JSON from %s: %s", file_path, e)
            return

        if not isinstance(raw_items, list):
            logger.error("Root element in %s must be a JSON array", file_path)
            return

        for idx, item in enumerate(raw_items):
            try:
                scheme = SchemeValidator.validate_or_raise(item)
                # Store by ID
                self._schemes[scheme.id] = scheme
            except Exception as e:
                logger.error("Skipping invalid record #%d in %s: %s", idx, file_path, e)

    def get_scheme(self, scheme_id: str, allow_placeholder: Optional[bool] = None) -> Optional[Scheme]:
        """Returns scheme by id, respecting placeholder and demo_mode filtering."""
        scheme = self._schemes.get(scheme_id)
        if not scheme:
            return None

        allow_ph = self.demo_mode if allow_placeholder is None else allow_placeholder
        if scheme.is_placeholder and not allow_ph:
            return None

        return scheme

    def filter_schemes(
        self,
        tier: Optional[TierType] = None,
        category: Optional[str] = None,
        target_group: Optional[str] = None,
        state: Optional[str] = None,
        include_placeholders: Optional[bool] = None,
    ) -> List[Scheme]:
        """Filters active schemes according to tier, category, target groups, and state."""
        allow_ph = self.demo_mode if include_placeholders is None else include_placeholders
        results: List[Scheme] = []

        for scheme in self._schemes.values():
            if scheme.is_placeholder and not allow_ph:
                continue
            if tier and scheme.tier != tier:
                continue
            if category and category not in scheme.category:
                continue
            if target_group and target_group not in scheme.target_groups:
                continue
            if state and scheme.level == "state" and scheme.state and scheme.state.lower() != state.lower():
                continue

            results.append(scheme)

        return results

    def get_all_active(self, include_placeholders: Optional[bool] = None) -> List[Scheme]:
        """Returns all schemes available under the current demo/production configuration."""
        return self.filter_schemes(include_placeholders=include_placeholders)

    def get_counts(self, include_placeholders: Optional[bool] = None) -> Dict[str, int]:
        """Returns scheme counts per tier."""
        allow_ph = self.demo_mode if include_placeholders is None else include_placeholders
        verified_cnt = 0
        extracted_cnt = 0

        for scheme in self._schemes.values():
            if scheme.is_placeholder and not allow_ph:
                continue
            if scheme.tier == TierType.VERIFIED:
                verified_cnt += 1
            elif scheme.tier == TierType.EXTRACTED:
                extracted_cnt += 1

        return {
            "verified": verified_cnt,
            "extracted": extracted_cnt,
            "total": verified_cnt + extracted_cnt,
        }

# Global singleton instance for application use
scheme_loader = SchemeLoader()
