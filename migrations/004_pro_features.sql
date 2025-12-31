-- Migration 004: OmniSky Pro Features
-- Includes: Sessions, Event Families (Dedupe), ML Model Tracking, Alerts

-- 1. Sessions: Track execution runs and config
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    start_time TEXT,
    end_time TEXT,
    config_snapshot TEXT,
    status TEXT
);

-- 2. Event Families: For advanced deduplication grouping
CREATE TABLE IF NOT EXISTS event_families (
    id TEXT PRIMARY KEY,
    signature_hash TEXT UNIQUE,
    first_seen_at TEXT,
    representative_event_id INTEGER
);

-- 3. Model Runs: Track ML Triage versions
CREATE TABLE IF NOT EXISTS model_runs (
    version TEXT PRIMARY KEY,
    trained_at TEXT,
    algorithm TEXT,
    metrics_json TEXT,
    is_active BOOLEAN
);

-- 4. Alerts: System notifications
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    level TEXT,
    message TEXT,
    context_json TEXT,
    is_read BOOLEAN DEFAULT 0
);

-- 5. Update existing event tables with new Pro columns
-- Note: SQLite does not support IF NOT EXISTS for columns easily.
-- We assume this runs once. If it fails due to existing column, the migration system catches it.

ALTER TABLE events_radio ADD COLUMN session_id TEXT REFERENCES sessions(id);
ALTER TABLE events_radio ADD COLUMN family_id TEXT REFERENCES event_families(id);
ALTER TABLE events_radio ADD COLUMN ml_score REAL;
ALTER TABLE events_radio ADD COLUMN ml_label TEXT;

ALTER TABLE events_image ADD COLUMN session_id TEXT REFERENCES sessions(id);
ALTER TABLE events_image ADD COLUMN family_id TEXT REFERENCES event_families(id);
ALTER TABLE events_image ADD COLUMN ml_score REAL;
ALTER TABLE events_image ADD COLUMN ml_label TEXT;
