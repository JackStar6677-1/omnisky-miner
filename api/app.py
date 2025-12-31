from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
import json
import os
import time
import sqlite3
from pathlib import Path

# --- Configuration ---
# Adjust paths relative to this file or use env vars
BASE_DIR = Path(__file__).resolve().parent.parent # omnisky-miner root
OMNISKY_DATA = BASE_DIR / "OMNISKY_DATA"
OBS_DIR = OMNISKY_DATA / "OBS"
DB_PATH = OMNISKY_DATA / "omniskyminer.db"

STATUS_FILE = OBS_DIR / "daemon_state.json"
CONTROL_FILE = OBS_DIR / "control.json"
EVENT_LOG_FILE = OBS_DIR / "event_log.jsonl"

app = FastAPI(title="OmniSky Command Center API", version="1.0")

# --- Models ---
class PauseRequest(BaseModel):
    reason: str = "USER_REQUEST"
    finish_current_job: bool = True

# --- Helpers ---
def read_json(path, default=None):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except:
        return default or {}

def write_json(path, data):
    os.makedirs(path.parent, exist_ok=True)
    with open(str(path) + ".tmp", 'w') as f:
        json.dump(data, f, indent=2)
    os.replace(str(path) + ".tmp", path)

# --- Control Endpoints ---
@app.get("/status")
def get_status():
    """Returns current daemon state and telemetry."""
    status = read_json(STATUS_FILE, {"daemon_state": "UNKNOWN"})
    control = read_json(CONTROL_FILE, {"desired_state": "RUNNING"})
    
    # Compute stall time if last_progress_ts available
    last_ts = status.get("updated_at", time.time())
    stall_seconds = time.time() - last_ts
    
    return {
        "daemon_state": status.get("daemon_state", "UNKNOWN"),
        "pause_reason": status.get("pause_reason"),
        "desired_state": control.get("desired_state", "RUNNING"),
        "metrics": status.get("metrics", {}),
        "stall_seconds": round(stall_seconds, 1),
        "updated_at": status.get("updated_at")
    }

@app.post("/pause")
def pause_daemon(req: PauseRequest):
    """Request the daemon to pause."""
    control = {
        "desired_state": "PAUSED",
        "reason": req.reason,
        "finish_current_job": req.finish_current_job,
        "updated_at": time.time()
    }
    write_json(CONTROL_FILE, control)
    return {"status": "OK", "message": "Pause request sent"}

@app.post("/resume")
def resume_daemon():
    """Request the daemon to resume."""
    control = {
        "desired_state": "RUNNING",
        "reason": "USER_RESUME",
        "updated_at": time.time()
    }
    write_json(CONTROL_FILE, control)
    return {"status": "OK", "message": "Resume request sent"}

# --- Data Endpoints ---
@app.get("/events")
def get_events(
    type: str = Query(None),
    min_score: float = Query(0),
    limit: int = Query(50),
    offset: int = Query(0)
):
    """Query events from database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # Union query for both radio and image
    q = """
        SELECT 'RADIO' as type, id, label, ml_score, ml_label, created_at FROM events_radio
        UNION ALL
        SELECT 'IMAGE' as type, id, label, ml_score, ml_label, created_at FROM events_image
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """
    try:
        rows = conn.execute(q, (limit, offset)).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

@app.get("/logs/tail")
def tail_logs(lines: int = Query(100)):
    """Returns last N lines of event_log.jsonl."""
    if not EVENT_LOG_FILE.exists():
        return []
    
    with open(EVENT_LOG_FILE, 'r') as f:
        all_lines = f.readlines()
        
    recent = all_lines[-lines:]
    result = []
    for line in recent:
        try:
            result.append(json.loads(line))
        except:
            pass
    return result

@app.get("/telemetry/latest")
def get_telemetry():
    """Returns raw status.json snapshot."""
    return read_json(STATUS_FILE)

# --- Static UI Serving (Optional) ---
UI_DIST = BASE_DIR / "ui" / "dist"
if UI_DIST.exists():
    app.mount("/ui", StaticFiles(directory=UI_DIST, html=True), name="ui")

@app.get("/")
def root():
    if (UI_DIST / "index.html").exists():
        return FileResponse(UI_DIST / "index.html")
    return {"message": "OmniSky API Online. UI not built yet."}
