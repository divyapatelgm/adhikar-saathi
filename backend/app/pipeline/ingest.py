import argparse
import asyncio
from pathlib import Path
import sys
import logging

from ..config import settings
from .extractor import IngestionPipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ingest")

async def main_async(args):
    from .llm_client import MockLLMClient, get_llm_client
    llm = MockLLMClient() if args.mock else get_llm_client()
    pipeline = IngestionPipeline(llm_client=llm)

    if args.file:
        target_file = Path(args.file)
        if not target_file.is_absolute():
            target_file = settings.BASE_DIR / target_file
        print(f"\n🚀 Ingesting single document: {target_file.name}")
        print(f"Flags: dry_run={args.dry_run}, reprocess={args.reprocess}\n")

        res = await pipeline.process_file(
            file_path=target_file,
            dry_run=args.dry_run,
            reprocess=args.reprocess
        )
        results = [res]
    else:
        target_dir = Path(args.dir)
        if not target_dir.is_absolute():
            target_dir = settings.BASE_DIR / target_dir
        print(f"\n🚀 Ingesting documents from directory: {target_dir}")
        print(f"Flags: dry_run={args.dry_run}, reprocess={args.reprocess}, concurrency={args.concurrency}\n")

        results = await pipeline.process_directory(
            directory_path=target_dir,
            dry_run=args.dry_run,
            reprocess=args.reprocess,
            concurrency=args.concurrency
        )

    # Print Summary Report
    print("=" * 60)
    print("INGESTION PIPELINE EXECUTION SUMMARY")
    print("=" * 60)

    success_cnt = sum(1 for r in results if r.status in ("success", "dry_run_success"))
    skipped_cnt = sum(1 for r in results if r.status == "skipped")
    rejected_cnt = sum(1 for r in results if r.status == "rejected")

    for r in results:
        status_icon = "✅" if r.status in ("success", "dry_run_success") else ("⏭️" if r.status == "skipped" else "❌")
        cached_badge = " (Cached)" if r.from_cache else ""
        scheme_info = f" -> {r.scheme.names.get('en')}" if r.scheme else ""
        print(f"{status_icon} [{r.status.upper()}]{cached_badge} {Path(r.file_path).name}{scheme_info}")
        if r.errors:
            for err in r.errors:
                print(f"    ⚠️ {err}")

    print("-" * 60)
    print(f"Total: {len(results)} | Success: {success_cnt} | Skipped: {skipped_cnt} | Rejected: {rejected_cnt}")
    print("=" * 60)

def main():
    parser = argparse.ArgumentParser(description="Adhikar Saathi Document Ingestion Pipeline")
    parser.add_argument("--dir", default="data/raw", help="Directory containing source documents (default: data/raw)")
    parser.add_argument("--file", default=None, help="Process a specific single file")
    parser.add_argument("--dry-run", action="store_true", help="Extract and validate without writing to schemes_extracted.json")
    parser.add_argument("--reprocess", action="store_true", help="Force re-extraction even if content hash matches")
    parser.add_argument("--concurrency", type=int, default=3, help="Max concurrent extraction workers (default: 3)")
    parser.add_argument("--mock", action="store_true", help="Use deterministic mock LLM for offline extraction testing")

    args = parser.parse_args()
    asyncio.run(main_async(args))

if __name__ == "__main__":
    main()
