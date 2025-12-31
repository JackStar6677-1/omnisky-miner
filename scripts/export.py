import sqlite3
import pandas as pd
import os
import sys
import shutil
import json
import logging

# Add project root to path if running isolated
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import config

EXPORT_DIR = os.path.join(config.OMNISKY_ROOT, "EXPORTS")

def export_events(format='csv'):
    """Exports all events to CSV or Parquet."""
    conn = sqlite3.connect(config.DB_PATH)
    
    # Unified Query (using our UI View logic ideally, but raw for now)
    # We export separate tables for cleanliness
    
    tables = ['events_radio', 'events_image', 'telemetry', 'sessions']
    
    if not os.path.exists(EXPORT_DIR):
        os.makedirs(EXPORT_DIR)
        
    res_files = []
    
    for tbl in tables:
        try:
            df = pd.read_sql_query(f"SELECT * FROM {tbl}", conn)
            path_base = os.path.join(EXPORT_DIR, f"{tbl}_export")
            
            if format == 'parquet':
                fname = path_base + ".parquet"
                df.to_parquet(fname)
            else:
                fname = path_base + ".csv"
                df.to_csv(fname, index=False)
            
            logging.info(f"Exported {tbl} -> {fname}")
            res_files.append(fname)
        except Exception as e:
            logging.error(f"Skip {tbl}: {e}")
            
    conn.close()
    return res_files

def export_case(event_id):
    """
    Creates a 'Case Folder' for a specific event with all artifacts + report.
    """
    # 1. Fetch Event Metadata
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Try radio
    c.execute("SELECT * FROM events_radio WHERE id = ?", (event_id,))
    row = c.fetchone()
    etype = "RADIO"
    if not row:
         c.execute("SELECT * FROM events_image WHERE id = ?", (event_id,))
         row = c.fetchone()
         etype = "IMAGE"
    
    if not row:
        logging.error("Event not found")
        return None
        
    # 2. Create Case Dir
    obj_name = row['artifact_id'] # Use art ID or object name if joined
    # Join with artifacts to get filename? Simplified here.
    case_dir = os.path.join(EXPORT_DIR, f"CASE_{event_id}_{etype}")
    if not os.path.exists(case_dir):
        os.makedirs(case_dir)
        
    # 3. Copy Assets
    # Radio: video, audio_raw, audio_clean, npz
    # Image: path_annotated, path_cutout
    
    assets = []
    if etype == "RADIO":
        assets = [row['path_waterfall'], row['path_npz'], row['path_audio_raw'], row['path_audio_clean']]
    else:
        assets = [row['path_annotated'], row['path_cutout']]
        
    for p in assets:
        if p and os.path.exists(p):
            try:
                shutil.copy(p, case_dir)
            except: pass
            
    # 4. Generate Report
    report_path = os.path.join(case_dir, "REPORT.json")
    with open(report_path, 'w') as f:
        # Convert Row to dict
        d = dict(row)
        json.dump(d, f, indent=2, default=str)
        
    logging.info(f"Case exported to {case_dir}")
    return case_dir

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) > 1 and sys.argv[1] == "case":
        export_case(sys.argv[2])
    else:
        export_events()
