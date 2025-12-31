import sqlite3
import config
import logging
from modules.search import SearchEngine
from modules.quality import QualityManager
from modules.missions import MissionControl
from modules.clustering import ClusteringEngine
from modules.collections import CollectionManager
from modules.detectors.consensus import ConsensusEngine
from modules.database_manager import DatabaseManager

def verify_research():
    print(">> Verifying OmniSky Research Station...")
    
    # 0. Migrations
    db = DatabaseManager() # triggers schema
    
    # 1. Search
    print("\n[1/6] Testing Semantic Search...")
    data = {"id": "TEST_EVT_1", "title": "Test Event", "content": "Evidence of technosignature", "tags": "radio candidate"}
    se = SearchEngine()
    se.index_item(data['id'], data['title'], data['content'], data['tags'])
    res = se.search("technosignature")
    if res:
        print(f"   [OK] Search returned {len(res)} result(s).")
    else:
        print("   [FAIL] Search returned nothing.")

    # 2. Quality
    print("\n[2/6] Testing Quality Manager...")
    qm = QualityManager()
    flags = qm.validate_artifact({"id": "TEST_EVT_1"}, {"visual": "missing.png"})
    if flags:
        print(f"   [OK] Generated {len(flags)} quality flags (Expected MISSING).")
    
    # 3. Missions
    print("\n[3/6] Testing Missions...")
    mc = MissionControl()
    # Just seed check
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.execute("SELECT count(*) FROM missions")
    print(f"   [OK] {c.fetchone()[0]} missions active.")
    conn.close()
    
    # 4. Clustering
    print("\n[4/6] Testing Clustering...")
    ce = ClusteringEngine()
    res = ce.compute_clusters()
    print(f"   [OK] Cluster Result: {res}")
    
    # 5. Collections
    print("\n[5/6] Testing Collections...")
    cm = CollectionManager()
    cid = cm.create_collection("My Favorites")
    if cid:
        print(f"   [OK] Created Collection {cid}")
        
    # 6. Consensus
    print("\n[6/6] Testing Detector Consensus...")
    con = ConsensusEngine()
    dummy_input = {"snr": 100, "drift": 0.5}
    res = con.run_all(dummy_input)
    print(f"   [OK] Consensus: {res['label']} ({res['score']}%)")
    
    print("\n>> RESEARCH STATION OPERATIONAL")

if __name__ == "__main__":
    verify_research()
