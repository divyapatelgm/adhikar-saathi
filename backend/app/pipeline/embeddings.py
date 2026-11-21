import json
import math
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import logging

from ..config import settings
from ..models.scheme import Scheme

logger = logging.getLogger(__name__)

STOP_WORDS = {
    "scheme", "yojana", "yojane", "how", "what", "can", "get", "apply", "for",
    "the", "and", "from", "with", "this", "that", "tell", "about", "claim",
    "free", "give", "details", "help", "please", "government", "govt", "will", "are"
}

class SchemeVectorStore:
    """
    Local vector store and semantic search index for schemes.
    Supports local TF-IDF / vector search with seamless Gemini embedding extension.
    """

    def __init__(self, index_path: Optional[Path] = None):
        self.index_path = index_path or (settings.DATA_DIR / "scheme_embeddings.json")
        self._documents: Dict[str, str] = {}  # scheme_id -> searchable text
        self._term_frequencies: Dict[str, Dict[str, int]] = {}
        self._doc_frequencies: Dict[str, int] = {}
        self.load()

    def _tokenize(self, text: str) -> List[str]:
        words = re.findall(r"\w+", text.lower())
        return [w for w in words if len(w) > 2 and w not in STOP_WORDS]

    def add_scheme(self, scheme: Scheme) -> None:
        """Indexes a Scheme record into the searchable vector store."""
        searchable_text = self._build_searchable_text(scheme)
        self._documents[scheme.id] = searchable_text
        tokens = self._tokenize(searchable_text)

        tf: Dict[str, int] = {}
        for token in tokens:
            tf[token] = tf.get(token, 0) + 1

        self._term_frequencies[scheme.id] = tf

        # Update doc frequencies
        for token in set(tokens):
            self._doc_frequencies[token] = self._doc_frequencies.get(token, 0) + 1

    def _build_searchable_text(self, scheme: Scheme) -> str:
        parts = [
            scheme.names.get("en", ""),
            scheme.names.get("kn", ""),
            scheme.names.get("hi", ""),
            scheme.summary_en,
            " ".join(scheme.category),
            " ".join(scheme.target_groups),
            scheme.benefit.description,
            scheme.department,
        ]
        for crit in scheme.eligibility.criteria:
            parts.append(crit.text_en)
        return " ".join([p for p in parts if p])

    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Calculates cosine similarity / BM25-style relevance score between query and indexed schemes.
        Returns sorted list of (scheme_id, score).
        """
        query_tokens = self._tokenize(query)
        if not query_tokens or not self._documents:
            return []

        scores: Dict[str, float] = {}
        num_docs = len(self._documents)

        for scheme_id, tf_map in self._term_frequencies.items():
            doc_score = 0.0
            doc_len = sum(tf_map.values()) or 1

            for token in query_tokens:
                if token in tf_map:
                    tf = tf_map[token] / doc_len
                    df = self._doc_frequencies.get(token, 1)
                    idf = math.log((num_docs + 1) / (df + 1)) + 1.0
                    doc_score += tf * idf

            if doc_score > 0.0:
                scores[scheme_id] = doc_score

        sorted_results = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        return sorted_results[:top_k]

    def save(self) -> None:
        """Serializes document index to disk."""
        data = {
            "documents": self._documents,
            "term_frequencies": self._term_frequencies,
            "doc_frequencies": self._doc_frequencies,
        }
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

    def load(self) -> None:
        """Loads serialized document index from disk if present."""
        if not self.index_path.exists():
            return
        try:
            with open(self.index_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._documents = data.get("documents", {})
                self._term_frequencies = data.get("term_frequencies", {})
                self._doc_frequencies = data.get("doc_frequencies", {})
        except Exception as e:
            logger.warning("Could not load vector store from %s: %s", self.index_path, e)
