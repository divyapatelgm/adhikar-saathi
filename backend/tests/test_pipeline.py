import json
import pytest
from pathlib import Path
import tempfile
import sqlite3

from backend.app.config import settings
from backend.app.models.scheme import Scheme, SchemeBenefit, HowToApply, EligibilityContainer
from backend.app.models.enums import TierType, SchemeStatus, LevelType
from backend.app.pipeline.document_reader import DocumentReader
from backend.app.pipeline.db_tracker import PipelineDBTracker
from backend.app.pipeline.llm_client import MockLLMClient, GeminiLLMClient
from backend.app.pipeline.deduplicator import SchemeDeduplicator
from backend.app.pipeline.rejection_manager import RejectionManager
from backend.app.pipeline.embeddings import SchemeVectorStore
from backend.app.pipeline.extractor import IngestionPipeline

@pytest.fixture
def temp_dirs():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        base = Path(tmp_dir)
        db_path = base / "test_pipeline.db"
        rejected_dir = base / "rejected"
        extracted_path = base / "schemes_extracted.json"
        vector_path = base / "test_vectors.json"
        extracted_path.write_text("[]", encoding="utf-8")
        yield {
            "db_path": db_path,
            "rejected_dir": rejected_dir,
            "extracted_path": extracted_path,
            "vector_path": vector_path,
            "base": base,
        }

def test_document_reader_txt_and_pdf():
    # Test reading sample text document
    sample_txt = Path("data/samples/sample_test_scheme.txt")
    text, h = DocumentReader.read_document(sample_txt)
    assert "SAMPLE - NOT A REAL DOCUMENT" in text
    assert len(h) == 64

    # Test reading sample PDF document
    sample_pdf = Path("data/samples/sample_test_scheme.pdf")
    pdf_text, pdf_h = DocumentReader.read_document(sample_pdf)
    assert "SAMPLE - NOT A REAL DOCUMENT" in pdf_text
    assert len(pdf_h) == 64

def test_document_reader_unsupported_format(temp_dirs):
    unsupported = temp_dirs["base"] / "file.xyz"
    unsupported.write_text("content", encoding="utf-8")
    with pytest.raises(ValueError) as exc:
        DocumentReader.read_document(unsupported)
    assert "Unsupported file format" in str(exc.value)

def test_db_tracker_file_and_llm_caching(temp_dirs):
    tracker = PipelineDBTracker(db_path=temp_dirs["db_path"])

    file_p = "/path/to/test.txt"
    h1 = "hash_12345"

    assert not tracker.is_file_unchanged(file_p, h1)

    tracker.record_file_status(file_p, h1, status="success", scheme_ids=["test-scheme"])
    assert tracker.is_file_unchanged(file_p, h1)

    # Different hash means changed file
    assert not tracker.is_file_unchanged(file_p, "new_hash")

    # LLM response caching
    assert tracker.get_cached_llm(h1, "v1") is None
    tracker.save_cached_llm(h1, "v1", '{"mock": "response"}')
    cached = tracker.get_cached_llm(h1, "v1")
    assert cached == '{"mock": "response"}'

def test_deduplicator_exact_and_fuzzy():
    base_scheme = Scheme(
        id="karnataka-dairy-grant",
        tier=TierType.VERIFIED,
        status=SchemeStatus.VERIFIED,
        confidence=1.0,
        names={"en": "Karnataka Dairy Farmer Grant"},
        level=LevelType.STATE,
        state="Karnataka",
        department="Agri",
        summary_en="Summary",
        benefit=SchemeBenefit(type="cash", description="Benefit"),
        eligibility=EligibilityContainer(criteria=[]),
        how_to_apply=HowToApply(steps=["Step 1"]),
        official_url="https://karnataka.gov.in",
        source_name="Gov of Karnataka"
    )

    # 1. Exact ID
    cand_exact_id = base_scheme.model_copy(update={"names": {"en": "Different Name"}})
    is_dup, mid, score, _ = SchemeDeduplicator.check_duplicate(cand_exact_id, [base_scheme])
    assert is_dup is True
    assert mid == "karnataka-dairy-grant"

    # 2. Very similar name (> 85%)
    cand_similar = base_scheme.model_copy(update={"id": "new-id", "names": {"en": "Karnataka Dairy Farmers Grant"}})
    is_dup, mid, score, _ = SchemeDeduplicator.check_duplicate(cand_similar, [base_scheme])
    assert is_dup is True
    assert score >= 0.85

    # 3. Completely distinct scheme
    cand_distinct = base_scheme.model_copy(update={"id": "student-scholarship", "names": {"en": "Higher Education Student Aid"}})
    is_dup, _, score, _ = SchemeDeduplicator.check_duplicate(cand_distinct, [base_scheme])
    assert is_dup is False
    assert score < 0.50

def test_rejection_manager(temp_dirs):
    mgr = RejectionManager(rejected_dir=temp_dirs["rejected_dir"])
    rejection_path = mgr.record_rejection(
        source_file="bad_scheme.pdf",
        content_hash="bad_hash",
        reasons=["Missing official URL", "Negative age"],
        raw_content_preview="Document snippet"
    )
    assert rejection_path.exists()
    rejections = mgr.list_rejections()
    assert len(rejections) == 1
    assert rejections[0]["source_file"] == "bad_scheme.pdf"
    assert "Missing official URL" in rejections[0]["reasons"]

def test_vector_store_indexing_and_search(temp_dirs):
    store = SchemeVectorStore(index_path=temp_dirs["vector_path"])
    scheme = Scheme(
        id="organic-farming-subsidy",
        tier=TierType.VERIFIED,
        status=SchemeStatus.VERIFIED,
        confidence=1.0,
        names={"en": "Organic Farming Fertilizer Subsidy"},
        level=LevelType.STATE,
        state="Karnataka",
        department="Agriculture",
        category=["agriculture"],
        target_groups=["farmer"],
        summary_en="Subsidy for bio-fertilizers and compost to smallholder farmers.",
        benefit=SchemeBenefit(type="subsidy", description="Bio fertilizer grant"),
        eligibility=EligibilityContainer(criteria=[]),
        how_to_apply=HowToApply(steps=["Step 1"]),
        official_url="https://karnataka.gov.in",
        source_name="Gov of Karnataka"
    )
    store.add_scheme(scheme)
    store.save()

    results = store.search("bio fertilizer compost subsidy", top_k=3)
    assert len(results) >= 1
    assert results[0][0] == "organic-farming-subsidy"

@pytest.mark.asyncio
async def test_ingestion_pipeline_end_to_end(temp_dirs):
    tracker = PipelineDBTracker(db_path=temp_dirs["db_path"])
    rejection_mgr = RejectionManager(rejected_dir=temp_dirs["rejected_dir"])
    vector_store = SchemeVectorStore(index_path=temp_dirs["vector_path"])
    mock_llm = MockLLMClient()

    pipeline = IngestionPipeline(
        llm_client=mock_llm,
        db_tracker=tracker,
        rejection_mgr=rejection_mgr,
        vector_store=vector_store,
        extracted_path=temp_dirs["extracted_path"]
    )

    sample_file = Path("data/samples/sample_test_scheme.txt")

    # 1. First run with dry_run=True: should validate but not write to disk
    dry_res = await pipeline.process_file(sample_file, dry_run=True)
    assert dry_res.status == "dry_run_success"
    assert dry_res.scheme is not None
    assert dry_res.scheme.tier == TierType.EXTRACTED
    assert dry_res.scheme.status == SchemeStatus.UNVERIFIED
    # Extracted json file should still be empty []
    assert json.loads(temp_dirs["extracted_path"].read_text(encoding="utf-8")) == []

    # 2. Run with dry_run=False: should extract and write to schemes_extracted.json
    res1 = await pipeline.process_file(sample_file, dry_run=False)
    assert res1.status == "success"
    assert res1.scheme.id == "synthetic-dairy-farmer-incentive-grant"
    items = json.loads(temp_dirs["extracted_path"].read_text(encoding="utf-8"))
    assert len(items) == 1
    assert items[0]["id"] == "synthetic-dairy-farmer-incentive-grant"

    # 3. Second run without reprocess: should be skipped (unchanged hash)
    res2 = await pipeline.process_file(sample_file, dry_run=False, reprocess=False)
    assert res2.status == "skipped"

    # 4. Third run with reprocess=True: forces re-extraction
    res3 = await pipeline.process_file(sample_file, dry_run=False, reprocess=True)
    assert res3.status == "success"

@pytest.mark.asyncio
async def test_ingestion_pipeline_rejection_on_invalid_data(temp_dirs):
    tracker = PipelineDBTracker(db_path=temp_dirs["db_path"])
    rejection_mgr = RejectionManager(rejected_dir=temp_dirs["rejected_dir"])

    # Mock client returns invalid scheme (missing official_url and negative age)
    bad_json = json.dumps({
        "id": "bad-scheme",
        "names": {"en": "Bad Scheme"},
        "tier": "extracted",
        "status": "unverified",
        "confidence": 0.5,
        "level": "state",
        "department": "None",
        "summary_en": "Bad",
        "benefit": {"type": "cash", "description": "None"},
        "eligibility": {
            "criteria": [{"field": "age", "op": "gte", "value": -10, "text_en": "Age >= -10"}]
        },
        "official_url": "",  # Missing
        "source_name": ""   # Missing
    })

    bad_llm = MockLLMClient(predefined_response=bad_json)
    pipeline = IngestionPipeline(
        llm_client=bad_llm,
        db_tracker=tracker,
        rejection_mgr=rejection_mgr,
        extracted_path=temp_dirs["extracted_path"]
    )

    sample_file = Path("data/samples/sample_test_scheme.txt")
    res = await pipeline.process_file(sample_file, reprocess=True)
    assert res.status == "rejected"
    assert len(res.errors) >= 1

    # Check rejection was logged
    rejections = rejection_mgr.list_rejections()
    assert len(rejections) >= 1
    assert any("official_url" in err for err in rejections[0]["reasons"])
