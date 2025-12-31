import json
import os
import time
import threading
import logging
import config

# Paths
OBS_DIR = os.path.join(config.OMNISKY_ROOT, "OBS")
STATUS_FILE = os.path.join(OBS_DIR, "status.json")
EVENT_LOG_FILE = os.path.join(OBS_DIR, "event_log.jsonl")

# Ensure dir
if not os.path.exists(OBS_DIR):
    os.makedirs(OBS_DIR)

class Observability:
    """
    Handles Live Observability via atomic JSON files.
    """
    _status_lock = threading.Lock()
    _log_lock = threading.Lock()
    
    # Defaults
    current_status = {
        "ts": None,
        "stage": "IDLE",
        "queues": {"download": 0, "analyze": 0, "persist": 0},
        "net": {"mbps_down": 0},
        "counters": {}
    }

    @staticmethod
    def update_status(updates):
        """
        Updates the in-memory status and writes to disk atomically.
        updates: dict with keys to merge into current_status
        """
        with Observability._status_lock:
            # Merge
            for k, v in updates.items():
                if isinstance(v, dict) and k in Observability.current_status and isinstance(Observability.current_status[k], dict):
                     Observability.current_status[k].update(v)
                else:
                    Observability.current_status[k] = v
            
            Observability.current_status["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            
            # Atomic Write (Write temp -> Rename)
            tmp_file = STATUS_FILE + ".tmp"
            try:
                with open(tmp_file, 'w') as f:
                    json.dump(Observability.current_status, f)
                os.replace(tmp_file, STATUS_FILE)
            except Exception as e:
                logging.error(f"OBS Status Write Error: {e}")

    @staticmethod
    def log_event(event_type, **kwargs):
        """
        Appends an event to the JSONL log.
        """
        entry = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "event": event_type,
            **kwargs
        }
        
        # Console output for debugging
        # logging.info(f"OBS: {event_type} - {kwargs}")
        
        with Observability._log_lock:
            try:
                with open(EVENT_LOG_FILE, 'a') as f:
                    f.write(json.dumps(entry) + "\n")
            except Exception as e:
                logging.error(f"OBS Log Write Error: {e}")

    @staticmethod
    def get_status():
        """Reads status.json safely."""
        if not os.path.exists(STATUS_FILE): return {}
        try:
            with open(STATUS_FILE, 'r') as f:
                return json.load(f)
        except: return {}

    @staticmethod
    def get_recent_events(limit=50):
        """Reads start of event_log.jsonl (or tail if implemented efficiently, here simple readlines)"""
        if not os.path.exists(EVENT_LOG_FILE): return []
        events = []
        try:
            # Read last N lines involves seeking, but for simplicity read all and slice logic
            # OR better: read line by line storing generic ring buffer
            # Since files might be big, we use 'tail' logic
            with open(EVENT_LOG_FILE, 'rb') as f:
                f.seek(0, os.SEEK_END)
                pos = f.tell()
                lines = []
                # Simple tail logic: read blocks backwards
                # For MVP just read lines if small, or use `deque`
                pass
            
            # Simple fallback for MVP usage
            with open(EVENT_LOG_FILE, 'r') as f:
                lines = f.readlines()
                return [json.loads(l) for l in lines[-limit:]][::-1]
        except: return []
