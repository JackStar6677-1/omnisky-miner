-- Migration 003: Network Telemetry
CREATE TABLE IF NOT EXISTS telemetry (
    timestamp TEXT PRIMARY KEY, -- ISO8601
    mbps_down REAL,
    mbps_up REAL,
    mbps_peak_session REAL,
    plan_usage_pct REAL,
    
    -- Pipeline State
    active_downloads INTEGER,
    active_analysis INTEGER,
    q_download_size INTEGER,
    q_analyze_size INTEGER,
    q_persist_size INTEGER,
    
    -- Counters
    analyzed_ok_total INTEGER,
    analyzed_fail_total INTEGER
);

CREATE INDEX IF NOT EXISTS idx_telemetry_ts ON telemetry(timestamp);
