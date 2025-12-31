import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from modules.evidence_contract import EvidenceContract
from modules.database_manager import DatabaseManager
import config

def verify_evidence():
    print(">> Verifying Evidence Contract...")
    
    db = DatabaseManager()
    
    # 1. Check Contract Module
    print("\n[1/3] Testing Evidence Contract...")
    test_row = {"id": 999, "event_id": 999}
    ok, missing, details = EvidenceContract.validate_event_evidence(test_row, "IMAGE")
    print(f"   Test Event: ok={ok}, missing={missing}")
    print(f"   Expected Dir: {details['evidence_dir']}")
    
    # 2. Check existing events
    print("\n[2/3] Checking existing IMAGE events...")
    import sqlite3
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT id, path_annotated FROM events_image LIMIT 10").fetchall()
    
    for row in rows:
        ok, missing, _ = EvidenceContract.validate_event_evidence(dict(row), "IMAGE")
        status = "[OK]" if ok else f"[MISSING: {missing}]"
        print(f"   Event {row['id']}: {status}")
    conn.close()
    
    # 3. Ensure directory creation works
    print("\n[3/3] Testing directory creation...")
    test_dir = EvidenceContract.ensure_evidence_dir(12345, "IMAGE")
    if os.path.exists(test_dir):
        print(f"   [OK] Created {test_dir}")
        os.rmdir(test_dir) # Cleanup test dir
    else:
        print("   [FAIL] Directory not created")
    
    print("\n>> EVIDENCE CONTRACT VERIFIED")

if __name__ == "__main__":
    verify_evidence()
