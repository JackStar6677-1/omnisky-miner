import sys
import os
import sqlite3
import requests
import json
import logging

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import config
from modules.evidence_contract import EvidenceContract

logging.basicConfig(level=logging.INFO, format='%(asctime)s - BACKFILL - %(message)s')

def backfill_image_event(event_id, source_url, conn):
    """Re-downloads FITS and generates evidence for an IMAGE event."""
    logging.info(f"Backfilling IMAGE event {event_id}...")
    
    # 1. Create evidence directory
    evidence_dir = EvidenceContract.ensure_evidence_dir(event_id, "IMAGE")
    
    # 2. Download source file
    try:
        resp = requests.get(source_url, timeout=60)
        resp.raise_for_status()
        
        # Save temporarily
        temp_fits = os.path.join(evidence_dir, "source.fits")
        with open(temp_fits, 'wb') as f:
            f.write(resp.content)
        logging.info(f"  Downloaded {len(resp.content)} bytes")
    except Exception as e:
        logging.error(f"  Download failed: {e}")
        return False

    # 3. Generate annotated PNG
    try:
        from astropy.io import fits
        import numpy as np
        from PIL import Image
        
        with fits.open(temp_fits) as hdul:
            data = hdul[0].data
            if data is None and len(hdul) > 1:
                data = hdul[1].data
        
        if data is None:
            logging.error("  No image data in FITS")
            return False
        
        # Handle 3D/4D data
        while data.ndim > 2:
            data = data[0]
        
        # Normalize to 0-255
        data = np.nan_to_num(data)
        vmin, vmax = np.percentile(data, [1, 99])
        scaled = np.clip((data - vmin) / (vmax - vmin + 1e-10) * 255, 0, 255).astype(np.uint8)
        
        img = Image.fromarray(scaled)
        png_path = os.path.join(evidence_dir, "annotated.png")
        img.save(png_path)
        logging.info(f"  Created annotated.png")
        
    except Exception as e:
        logging.error(f"  PNG generation failed: {e}")
        return False

    # 4. Generate evidence.json
    evidence = {
        "event_id": event_id,
        "source_url": source_url,
        "generated_at": str(os.popen('date /t').read().strip()),
        "backfilled": True
    }
    evidence_path = os.path.join(evidence_dir, "evidence.json")
    with open(evidence_path, 'w') as f:
        json.dump(evidence, f, indent=2)
    
    # 5. Generate report.md
    report = f"""# Reporte de Evento {event_id}

## Origen
- URL: {source_url}

## Evidencia
- PNG Anotado: annotated.png
- Backfill automático realizado.

## Notas
Este reporte fue generado automáticamente por el sistema de Backfill.
"""
    report_path = os.path.join(evidence_dir, "report.md")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    # 6. Update DB with paths
    try:
        conn.execute("""
            UPDATE events_image 
            SET path_annotated = ?, path_cutout = ?, updated_at = datetime('now')
            WHERE id = ?
        """, (png_path, evidence_path, event_id))
        conn.commit()
        logging.info(f"  DB updated with paths")
    except Exception as e:
        logging.error(f"  DB update failed: {e}")
        return False
    
    # 7. Cleanup temp FITS (Zero Waste)
    try:
        os.remove(temp_fits)
    except: pass
    
    logging.info(f"  Backfill COMPLETE for event {event_id}")
    return True

def backfill_all():
    """Backfills all IMAGE events missing evidence."""
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # Find events with missing paths - JOIN with artifacts for source_url
    rows = conn.execute("""
        SELECT e.id, a.source_url 
        FROM events_image e
        JOIN artifacts a ON e.artifact_id = a.id
        WHERE e.path_annotated IS NULL OR e.path_annotated = ''
    """).fetchall()
    
    logging.info(f"Found {len(rows)} events to backfill")
    
    ok = 0
    fail = 0
    for row in rows:
        if backfill_image_event(row['id'], row['source_url'], conn):
            ok += 1
        else:
            fail += 1
    
    conn.close()
    logging.info(f"Backfill complete: {ok} OK, {fail} FAILED")

def backfill_single(event_id):
    """Backfills a single event by ID."""
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # JOIN with artifacts table to get source_url
    row = conn.execute("""
        SELECT e.id, a.source_url 
        FROM events_image e
        JOIN artifacts a ON e.artifact_id = a.id
        WHERE e.id = ?
    """, (event_id,)).fetchone()
    
    if not row:
        logging.error(f"Event {event_id} not found in events_image")
        return
    
    backfill_image_event(row['id'], row['source_url'], conn)
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--event-id":
        backfill_single(int(sys.argv[2]))
    else:
        backfill_all()
