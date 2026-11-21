import asyncio
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import logging

from ..config import settings
from ..models.scheme import Scheme
from ..models.enums import TierType, SchemeStatus
from ..engine.validator import SchemeValidator, SchemeValidationError
from ..engine.loader import scheme_loader
from .document_reader import DocumentReader
from .db_tracker import PipelineDBTracker
from .llm_client import LLMClient, get_llm_client
from .deduplicator import SchemeDeduplicator
from .rejection_manager import RejectionManager
from .embeddings import SchemeVectorStore

logger = logging.getLogger(__name__)

PROMPT_VERSION = "v1"

class ExtractionResult:
    def __init__(
        self,
        file_path: str,
        status: str,  # 'success' | 'skipped' | 'rejected' | 'dry_run_success'
        scheme: Optional[Scheme] = None,
        errors: Optional[List[str]] = None,
        from_cache: bool = False,
    ):
        self.file_path = file_path
        self.status = status
        self.scheme = scheme
        self.errors = errors or []
        self.from_cache = from_cache

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "status": self.status,
            "scheme_id": self.scheme.id if self.scheme else None,
            "scheme_name": self.scheme.names.get("en") if self.scheme else None,
            "errors": self.errors,
            "from_cache": self.from_cache,
        }

class IngestionPipeline:
    """
    Orchestrates the ingestion of raw documents into structured Tier 2 scheme records:
    Document reading -> Hash check -> LLM extraction -> Caching -> Validation -> Deduplication -> Vector Indexing.
    """

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        db_tracker: Optional[PipelineDBTracker] = None,
        rejection_mgr: Optional[RejectionManager] = None,
        vector_store: Optional[SchemeVectorStore] = None,
        extracted_path: Optional[Path] = None,
    ):
        self.llm_client = llm_client or get_llm_client()
        self.db_tracker = db_tracker or PipelineDBTracker()
        self.rejection_mgr = rejection_mgr or RejectionManager()
        self.vector_store = vector_store or SchemeVectorStore()
        self.extracted_path = extracted_path or settings.EXTRACTED_SCHEMES_PATH
        self.prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> str:
        prompt_file = settings.BASE_DIR / "backend" / "app" / "prompts" / PROMPT_VERSION / "extract_scheme.txt"
        if prompt_file.exists():
            return prompt_file.read_text(encoding="utf-8")
        return (
            "Extract structured welfare scheme record from this document in JSON conforming strictly "
            "to the Scheme schema:\n\n{DOCUMENT_TEXT}\n\nSource: {FILENAME}"
        )

    async def process_file(
        self,
        file_path: Path,
        dry_run: bool = False,
        reprocess: bool = False,
    ) -> ExtractionResult:
        """Processes a single document file."""
        file_str = str(file_path.resolve())

        # 1. Read document text and hash
        try:
            doc_text, content_hash = DocumentReader.read_document(file_path)
        except Exception as e:
            err = f"Failed to read file: {e}"
            logger.error("%s: %s", file_path, err)
            self.rejection_mgr.record_rejection(
                source_file=file_str,
                content_hash="unknown",
                reasons=[err],
                raw_content_preview=""
            )
            return ExtractionResult(file_str, status="rejected", errors=[err])

        # 2. Check tracker for unchanged file
        if not reprocess and self.db_tracker.is_file_unchanged(file_str, content_hash):
            logger.info("Skipping unchanged file: %s (hash: %s...)", file_path.name, content_hash[:8])
            return ExtractionResult(file_str, status="skipped", from_cache=True)

        # 3. Check SQLite LLM Cache
        from_cache = False
        raw_json_str = self.db_tracker.get_cached_llm(content_hash, PROMPT_VERSION)
        if raw_json_str and not reprocess:
            from_cache = True
            logger.info("Using cached LLM response for %s", file_path.name)
        else:
            # 4. Generate extraction via LLM
            prompt = self.prompt_template.replace("{DOCUMENT_TEXT}", doc_text).replace("{FILENAME}", file_path.name)
            try:
                raw_json_str = await self.llm_client.generate_json(prompt)
                self.db_tracker.save_cached_llm(content_hash, PROMPT_VERSION, raw_json_str)
            except Exception as e:
                err = f"LLM extraction failure: {e}"
                logger.error("%s: %s", file_path, err)
                self.rejection_mgr.record_rejection(
                    source_file=file_str,
                    content_hash=content_hash,
                    reasons=[err],
                    raw_content_preview=doc_text[:500]
                )
                self.db_tracker.record_file_status(file_str, content_hash, status="rejected", error_message=err)
                return ExtractionResult(file_str, status="rejected", errors=[err])

        # 5. Parse JSON
        try:
            parsed_data = json.loads(raw_json_str)
        except json.JSONDecodeError as e:
            err = f"Invalid JSON generated by LLM: {e}"
            logger.error("%s: %s", file_path, err)
            self.rejection_mgr.record_rejection(
                source_file=file_str,
                content_hash=content_hash,
                reasons=[err],
                raw_content_preview=doc_text[:500],
                raw_response=raw_json_str
            )
            self.db_tracker.record_file_status(file_str, content_hash, status="rejected", error_message=err)
            return ExtractionResult(file_str, status="rejected", errors=[err])

        # Ensure tier and metadata fields are normalized
        parsed_data["tier"] = TierType.EXTRACTED.value
        parsed_data["status"] = SchemeStatus.UNVERIFIED.value
        parsed_data["source_document"] = file_path.name
        parsed_data["extracted_at"] = datetime.now(timezone.utc).isoformat()
        if "is_placeholder" not in parsed_data:
            parsed_data["is_placeholder"] = False

        # 6. Validate Scheme
        try:
            validated_scheme = SchemeValidator.validate_or_raise(parsed_data)
        except SchemeValidationError as e:
            errs = e.errors
            logger.warning("%s validation failed with %d errors: %s", file_path.name, len(errs), errs)
            self.rejection_mgr.record_rejection(
                source_file=file_str,
                content_hash=content_hash,
                reasons=errs,
                raw_content_preview=doc_text[:500],
                raw_response=raw_json_str
            )
            self.db_tracker.record_file_status(file_str, content_hash, status="rejected", error_message="; ".join(errs))
            return ExtractionResult(file_str, status="rejected", errors=errs, from_cache=from_cache)

        # 7. Deduplication check against verified schemes and other extracted schemes
        verified_existing = scheme_loader.filter_schemes(tier=TierType.VERIFIED, include_placeholders=True)
        is_dup, dup_id, score, dup_reason = SchemeDeduplicator.check_duplicate(validated_scheme, verified_existing)
        if is_dup:
            err = f"Conflicts with verified scheme ({score:.1%}): {dup_reason}"
            logger.warning("%s rejected: %s", file_path.name, err)
            self.rejection_mgr.record_rejection(
                source_file=file_str,
                content_hash=content_hash,
                reasons=[err],
                raw_content_preview=doc_text[:500],
                raw_response=raw_json_str
            )
            self.db_tracker.record_file_status(file_str, content_hash, status="rejected", error_message=err)
            return ExtractionResult(file_str, status="rejected", errors=[err], from_cache=from_cache)

        other_extracted = [s for s in scheme_loader.filter_schemes(tier=TierType.EXTRACTED) if s.id != validated_scheme.id]
        is_dup_ext, dup_id, score, dup_reason = SchemeDeduplicator.check_duplicate(validated_scheme, other_extracted)
        if is_dup_ext:
            err = f"Duplicate of existing extracted scheme ({score:.1%}): {dup_reason}"
            logger.warning("%s rejected: %s", file_path.name, err)
            self.rejection_mgr.record_rejection(
                source_file=file_str,
                content_hash=content_hash,
                reasons=[err],
                raw_content_preview=doc_text[:500],
                raw_response=raw_json_str
            )
            self.db_tracker.record_file_status(file_str, content_hash, status="rejected", error_message=err)
            return ExtractionResult(file_str, status="rejected", errors=[err], from_cache=from_cache)

        # 8. Success handling
        if dry_run:
            logger.info("[DRY RUN] Validated scheme: %s (confidence: %.2f)", validated_scheme.id, validated_scheme.confidence)
            return ExtractionResult(file_str, status="dry_run_success", scheme=validated_scheme, from_cache=from_cache)

        # Save to schemes_extracted.json
        self._append_extracted_scheme(validated_scheme)
        self.vector_store.add_scheme(validated_scheme)
        self.vector_store.save()

        # Update tracker
        self.db_tracker.record_file_status(
            file_str,
            content_hash,
            status="success",
            scheme_ids=[validated_scheme.id]
        )

        # Reload in-memory loader
        scheme_loader.load_all()

        return ExtractionResult(file_str, status="success", scheme=validated_scheme, from_cache=from_cache)

    def _append_extracted_scheme(self, scheme: Scheme) -> None:
        """Loads schemes_extracted.json, appends or updates record, and writes back."""
        items: List[Dict[str, Any]] = []
        if self.extracted_path.exists():
            try:
                with open(self.extracted_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        items = json.loads(content)
            except Exception as e:
                logger.error("Could not read %s: %s", self.extracted_path, e)

        # Replace existing with same ID if present, else append
        new_dict = scheme.model_dump()
        replaced = False
        for idx, it in enumerate(items):
            if it.get("id") == scheme.id:
                items[idx] = new_dict
                replaced = True
                break

        if not replaced:
            items.append(new_dict)

        with open(self.extracted_path, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2, ensure_ascii=False)

    async def process_directory(
        self,
        directory_path: Path,
        dry_run: bool = False,
        reprocess: bool = False,
        concurrency: int = 3,
    ) -> List[ExtractionResult]:
        """Processes all supported documents in a directory with controlled concurrency."""
        if not directory_path.exists():
            logger.warning("Directory not found: %s", directory_path)
            return []

        all_files = [
            f for f in directory_path.iterdir()
            if f.is_file() and f.suffix.lower() in DocumentReader.SUPPORTED_EXTENSIONS
        ]

        if not all_files:
            logger.info("No supported files found in %s", directory_path)
            return []

        semaphore = asyncio.Semaphore(concurrency)

        async def worker(f: Path) -> ExtractionResult:
            async with semaphore:
                return await self.process_file(f, dry_run=dry_run, reprocess=reprocess)

        tasks = [worker(f) for f in all_files]
        results = await asyncio.gather(*tasks)
        return list(results)
