import os
import sqlite3
import json
import logging
import config

class QualityManager:
    """
    Validates artifacts and manages quality flags.
    """
    
    def __init__(self):
        self.db_path = config.DB_PATH

    def validate_artifact(self, artifact_metadata, paths):
        """
        Checks file integrity, header presence, etc.
        Returns list of flag dicts.
        """
        flags = []
        art_id = artifact_metadata.get('id')
        
        # 1. Check File Existence & Size
        for label, path in paths.items():
            if not path: continue
            
            if not os.path.exists(path):
                flags.append(self._create_flag(art_id, f"MISSING_FILE_{label}", "CRITICAL", f"{label} path not found"))
            elif os.path.getsize(path) == 0:
                flags.append(self._create_flag(art_id, f"EMPTY_FILE_{label}", "CRITICAL", f"{label} size is 0 bytes"))
                
        # 2. Check Valid Headers (Stub)
        # In real impl, open FITS/WAV and check magic bytes.
        
        if flags:
            self._persist_flags(flags)
            
        return flags

    def _create_flag(self, art_id, flag_name, severity, details):
        return {
            "artifact_id": art_id,
            "flag": flag_name,
            "severity": severity,
            "details": details
        }

    def _persist_flags(self, flags):
        if not flags: return
        conn = sqlite3.connect(self.db_path)
        ts = "N/A" # Should use datetime
        try:
            data = [(f['artifact_id'], None, f['flag'], f['severity'], f['details'], ts) for f in flags]
            conn.executemany(
                "INSERT INTO quality_flags (artifact_id, event_id, flag, severity, details_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                data
            )
            conn.commit()
        except Exception as e:
            logging.error(f"Failed to log quality flags: {e}")
        finally:
            conn.close()
