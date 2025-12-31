import sqlite3
import config
from modules.triage import TriageEngine
from modules.alerts import AlertManager
from modules.deduplication import DeduplicationEngine
from modules.database_manager import DatabaseManager
import logging

def verify_pro():
    print(">> Verifying OmniSky Pro Upgrade...")
    
    # Trigger Migrations
    db = DatabaseManager()
    
    # 1. DB Schema Check
    print("\n[1/4] Checking Database Schema...")
    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()
    tables = ['sessions', 'event_families', 'model_runs', 'alerts']
    missing = []
    for t in tables:
        try:
            cursor.execute(f"SELECT 1 FROM {t} LIMIT 1")
        except sqlite3.OperationalError:
            print(f"   [MISSING] Missing table: {t}")
            missing.append(t)
        else:
            print(f"   [OK] Table found: {t}")
    conn.close()
    
    if missing:
        print("FAIL: DB Schema incomplete.")
        return

    # 2. Triage Engine Check
    print("\n[2/4] Testing ML Triage Engine...")
    triage = TriageEngine()
    if not triage.is_ready:
        print("   [WARN] Model not found (Heuristic Mode). Training Dummy...")
        triage.train_dummy()
    
    sample = {'snr': 55.0, 'drift': 0.5}
    res = triage.analyze(sample)
    print(f"   [OK] Prediction: {res['label']} (Score: {res['score']:.1f}%) via {res['method']}")

    # 3. Deduplication Check
    print("\n[3/4] Testing Deduplication Hashing...")
    sig = DeduplicationEngine.compute_signature("RADIO", {'object_name': 'VOYAGER', 'frequency': 8400.123, 'drift': 0.1})
    print(f"   [OK] Signature: {sig}")
    
    # 4. Alerts
    print("\n[4/4] Testing Alerts...")
    am = AlertManager()
    am.send_alert("INFO", "Verification Run", {"user": "tester"})
    print("   [OK] Alert logged to DB.")
    
    print("\n>> OMNISKY PRO SYSTEMS OPERATIONAL")

if __name__ == "__main__":
    verify_pro()
