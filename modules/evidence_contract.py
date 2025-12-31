import os
import json
import config

class EvidenceContract:
    """
    Enforces mandatory evidence requirements for events.
    """
    
    REQUIRED_IMAGE = ['annotated_png', 'evidence_json', 'report_md']
    REQUIRED_RADIO = ['waterfall_png', 'evidence_json', 'report_md']
    
    @staticmethod
    def get_event_dir(event_id, event_type):
        """Returns the expected directory for an event's evidence."""
        if event_type == "IMAGE":
            return os.path.join(config.OMNISKY_ROOT, "HALLAZGOS", "5_IMAGENES_VISUALES", str(event_id))
        else:
            return os.path.join(config.OMNISKY_ROOT, "HALLAZGOS", "3_CANDIDATOS_ANOMALOS", str(event_id))

    @staticmethod
    def validate_event_evidence(event_row, event_type="IMAGE"):
        """
        Validates that all required evidence exists for an event.
        Returns (ok: bool, missing: list, details: dict)
        """
        event_id = event_row.get('id') or event_row.get('event_id')
        evidence_dir = EvidenceContract.get_event_dir(event_id, event_type)
        
        if event_type == "IMAGE":
            required_files = {
                'annotated_png': 'annotated.png',
                'evidence_json': 'evidence.json',
                'report_md': 'report.md'
            }
        else:
            required_files = {
                'waterfall_png': 'waterfall.png',
                'evidence_json': 'evidence.json',
                'report_md': 'report.md'
            }
        
        missing = []
        details = {"evidence_dir": evidence_dir, "files": {}}
        
        for key, filename in required_files.items():
            path = os.path.join(evidence_dir, filename)
            exists = os.path.exists(path)
            details["files"][key] = {"path": path, "exists": exists}
            if not exists:
                missing.append(key)
        
        ok = len(missing) == 0
        return ok, missing, details

    @staticmethod
    def ensure_evidence_dir(event_id, event_type):
        """Creates the evidence directory if it doesn't exist."""
        path = EvidenceContract.get_event_dir(event_id, event_type)
        os.makedirs(path, exist_ok=True)
        return path
