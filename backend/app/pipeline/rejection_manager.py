import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import logging

from ..config import settings

logger = logging.getLogger(__name__)

class RejectionManager:
    """Logs and stores rejected document extractions with detailed error reasons."""

    def __init__(self, rejected_dir: Optional[Path] = None):
        self.rejected_dir = rejected_dir or settings.REJECTED_DIR
        self.rejected_dir.mkdir(parents=True, exist_ok=True)

    def record_rejection(
        self,
        source_file: str,
        content_hash: str,
        reasons: List[str],
        raw_content_preview: str,
        raw_response: Optional[str] = None
    ) -> Path:
        """Writes rejection details to a JSON file in data/rejected/."""
        timestamp = datetime.now(timezone.utc)
        ts_str = timestamp.strftime("%Y%m%d_%H%M%S")
        safe_name = Path(source_file).stem.replace(" ", "_")
        rejection_file = self.rejected_dir / f"{safe_name}_{ts_str}_rejection.json"

        data = {
            "source_file": source_file,
            "content_hash": content_hash,
            "rejected_at": timestamp.isoformat(),
            "reasons": reasons,
            "raw_content_preview": raw_content_preview[:800],
            "raw_llm_response": raw_response[:800] if raw_response else None,
        }

        with open(rejection_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info("Recorded rejection for %s in %s", source_file, rejection_file)
        return rejection_file

    def list_rejections(self) -> List[Dict[str, Any]]:
        """Returns all rejection records in the rejected folder."""
        results = []
        for file in sorted(self.rejected_dir.glob("*.json"), reverse=True):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    results.append(json.load(f))
            except Exception as e:
                logger.warning("Could not read rejection file %s: %s", file, e)
        return results
