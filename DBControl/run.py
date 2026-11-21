"""
DBControl Standalone Runner
Launches the Adhikar Saathi API & Database Console at http://localhost:8000/admin/
"""

import sys
import os
import webbrowser
import threading
import time
from pathlib import Path

# Add project root to sys.path so backend imports resolve from any cwd
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.config import settings
from backend.app.db import init_db, sync_files_to_db

def main():
    port = settings.PORT or 8000
    admin_url = f"http://localhost:{port}/admin/"

    print("=" * 64)
    print(" 🛡️  Adhikar Saathi — DBControl & Curation Console")
    print("=" * 64)
    print(f"Database Path : {settings.SQLITE_DB_PATH}")
    print(f"Admin Password: {settings.ADMIN_PASSWORD}")
    print(f"Console URL   : {admin_url}")
    print("=" * 64)

    # 1. Initialize SQLite Database & Tables if not present
    print("[1/3] Initializing SQLite tables...")
    init_db()

    # 2. Sync verified and extracted JSON files into DB
    print("[2/3] Synchronizing scheme files with SQLite...")
    synced = sync_files_to_db()
    print(f"      Verified Schemes : {synced.get('synced_verified', synced.get('verified', 0))}")
    print(f"      Extracted Schemes: {synced.get('synced_extracted', synced.get('extracted', 0))}")
    print(f"      Total Ingested   : {synced.get('total_synced', 0)}")

    # 3. Launch Server & Open Browser
    print(f"[3/3] Starting backend server on http://127.0.0.1:{port} ...")
    print(f"\n👉 Access DBControl Console at: {admin_url}")
    print("   Press Ctrl+C to stop.\n")

    try:
        import uvicorn
        from backend.app.main import app

        def open_browser():
            time.sleep(1.2)
            try:
                webbrowser.open(admin_url)
            except Exception:
                pass

        threading.Thread(target=open_browser, daemon=True).start()

        uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
    except KeyboardInterrupt:
        print("\nDBControl shut down gracefully.")

if __name__ == "__main__":
    main()
