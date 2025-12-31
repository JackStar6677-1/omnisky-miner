import logging
import sqlite3
import config
from .heuristic import HeuristicDetector
# from .ml import MLDetector # Could wrap TriageEngine here

class ConsensusEngine:
    def __init__(self):
        self.detectors = [HeuristicDetector()]
        # Add ML wrapper if needed
        self.db_path = config.DB_PATH

    def run_all(self, event_data, event_id=None):
        results = []
        for d in self.detectors:
            try:
                res = d.detect(event_data)
                results.append({
                    "detector": d.name,
                    "score": res['score'],
                    "label": res['label']
                })
                
                # Persist run if event_id provided
                if event_id:
                   self._persist_run(event_id, d.name, res)
                   
            except Exception as e:
                logging.error(f"Detector {d.name} failed: {e}")
        
        # Determine Consensus
        # Simple Majority or Max Score
        if not results: return {"label": "UNKNOWN", "score": 0, "disputed": False}
        
        labels = [r['label'] for r in results]
        consensus = max(set(labels), key=labels.count)
        disputed = len(set(labels)) > 1
        avg_score = sum(r['score'] for r in results) / len(results)
        
        return {
            "label": consensus,
            "score": avg_score,
            "disputed": disputed,
            "details": results
        }

    def _persist_run(self, event_id, det_name, res):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                "INSERT INTO detector_runs (run_id, detector_name, event_id, score, label, created_at) VALUES (?, ?, ?, ?, ?, datetime('now'))",
                ("BATCH", det_name, event_id, res['score'], res['label'])
            )
            conn.commit()
        except: pass
        finally: conn.close()
