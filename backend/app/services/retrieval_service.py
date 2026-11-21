import json
import difflib
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any, Union
import logging

from ..config import settings
from ..models.scheme import Scheme
from ..models.rights import RightsEntry
from ..engine.loader import scheme_loader
from ..pipeline.embeddings import SchemeVectorStore

logger = logging.getLogger(__name__)

class RetrievalService:
    """
    Multilingual retrieval service searching across:
    - Tier 1: Hand-verified schemes
    - Tier 2: Ingestion-pipeline extracted schemes
    - Rights Knowledge Base: Common civic issues & statutory remedies
    """

    def __init__(self, rights_path: Optional[Path] = None, vector_store: Optional[SchemeVectorStore] = None):
        self.rights_path = rights_path or settings.RIGHTS_KB_PATH
        self.vector_store = vector_store or SchemeVectorStore()
        self._rights_entries: List[RightsEntry] = []
        self._load_rights()

    def _load_rights(self) -> None:
        if not self.rights_path.exists():
            logger.warning("Rights KB file not found at %s", self.rights_path)
            return
        try:
            with open(self.rights_path, "r", encoding="utf-8") as f:
                raw_list = json.load(f)
                self._rights_entries = [RightsEntry(**it) for it in raw_list]
        except Exception as e:
            logger.error("Failed to load rights KB: %s", e)

    def retrieve(self, query: str) -> Tuple[str, Optional[Union[RightsEntry, Scheme]], float]:
        """
        Retrieves top candidate.
        Returns:
            (match_type, item, score)
            match_type is one of: "rights", "scheme", "none"
        """
        norm_query = query.strip().lower()
        if not norm_query:
            return "none", None, 0.0

        # 1. Search Rights Knowledge Base
        best_rights = None
        best_rights_score = 0.0

        for r in self._rights_entries:
            # Check topic similarity
            topic_score = difflib.SequenceMatcher(None, norm_query, r.topic.lower()).ratio()
            if topic_score > best_rights_score:
                best_rights_score = topic_score
                best_rights = r

            # Check question variants
            for variant in r.question_variants:
                v_score = difflib.SequenceMatcher(None, norm_query, variant.lower()).ratio()
                # Also check keyword inclusion
                words = [w for w in norm_query.split() if len(w) > 3]
                matched_words = sum(1 for w in words if w in variant.lower())
                overlap_ratio = matched_words / len(words) if words else 0.0
                combined_score = max(v_score, overlap_ratio)

                if combined_score > best_rights_score:
                    best_rights_score = combined_score
                    best_rights = r

        # 2. Search Schemes (Verified & Extracted)
        best_scheme = None
        best_scheme_score = 0.0

        schemes = scheme_loader.get_all_active(include_placeholders=True if settings.DEMO_MODE else None)

        # Keyword and sequence search
        for s in schemes:
            for lang in ("en", "kn", "hi"):
                name = s.names.get(lang, "").lower()
                if not name:
                    continue
                name_score = difflib.SequenceMatcher(None, norm_query, name).ratio()
                # Keyword containment (scheme title directly in query)
                if name in norm_query:
                    name_score = max(name_score, 0.75)
                if name_score > best_scheme_score:
                    best_scheme_score = name_score
                    best_scheme = s

        # Check vector store search
        vector_matches = self.vector_store.search(norm_query, top_k=1)
        if vector_matches:
            top_id, top_score = vector_matches[0]
            matched_s = scheme_loader.get_scheme(top_id)
            if matched_s and (top_score > best_scheme_score or best_scheme is None):
                # Normalize vector score roughly
                norm_vec_score = min(top_score / 2.0, 0.95)
                if norm_vec_score > best_scheme_score:
                    best_scheme_score = norm_vec_score
                    best_scheme = matched_s

        # 3. Decision threshold
        RELEVANCE_THRESHOLD = 0.45

        if best_rights_score >= RELEVANCE_THRESHOLD and best_rights_score >= best_scheme_score:
            return "rights", best_rights, best_rights_score
        elif best_scheme_score >= RELEVANCE_THRESHOLD:
            return "scheme", best_scheme, best_scheme_score

        return "none", None, 0.0

retrieval_service = RetrievalService()
