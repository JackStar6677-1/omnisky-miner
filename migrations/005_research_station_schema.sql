-- Migration 005: Research Station Extensions
-- Includes: FTS5 Search, Missions, Quality, Clusters, Collections, Change Detection, Detectors

-- 1. Semantic Search (FTS5 Virtual Table)
-- Note: Requires SQLite with FTS5 enabled (Standard in Python 3.9+)
-- We store searchable text here.
CREATE VIRTUAL TABLE IF NOT EXISTS reports_fts USING fts5(
    content, 
    title, 
    tags,
    event_id UNINDEXED, 
    session_id UNINDEXED,
    tokenize='porter unicode61'
);

-- 2. Missions & Gamification
CREATE TABLE IF NOT EXISTS missions (
    id TEXT PRIMARY KEY,
    name TEXT,
    description TEXT,
    conditions_json TEXT, -- e.g. {"min_ra": 0, "max_ra": 30, "count": 5}
    reward_json TEXT,     -- e.g. {"xp": 100, "badge": "EXPLORER"}
    active BOOLEAN DEFAULT 1,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS mission_progress (
    mission_id TEXT,
    session_id TEXT, -- Progress might be session-bound or global (user UUID?)
    progress_json TEXT, -- e.g. {"count": 2}
    completed_at TEXT,
    PRIMARY KEY (mission_id, session_id),
    FOREIGN KEY (mission_id) REFERENCES missions(id)
);

CREATE TABLE IF NOT EXISTS achievements (
    id TEXT PRIMARY KEY,
    name TEXT,
    icon TEXT,
    unlocked_at TEXT,
    details_json TEXT
);

-- 3. Quality & Flags
CREATE TABLE IF NOT EXISTS quality_flags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    artifact_id TEXT,
    event_id INTEGER, -- Optional link to event
    flag TEXT,        -- e.g. 'CORRUPT_FILE'
    severity TEXT,    -- 'WARNING', 'CRITICAL'
    details_json TEXT,
    created_at TEXT
);

-- 4. Clustering (Hotspots)
CREATE TABLE IF NOT EXISTS clusters (
    id TEXT PRIMARY KEY,
    kind TEXT,        -- 'RADIO', 'IMAGE'
    centroid_ra REAL,
    centroid_dec REAL,
    centroid_freq REAL,
    count INTEGER,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS event_cluster_map (
    event_id INTEGER,
    cluster_id TEXT,
    distance_from_centroid REAL,
    PRIMARY KEY (event_id, cluster_id),
    FOREIGN KEY (cluster_id) REFERENCES clusters(id)
);

-- 5. Collections (Playlists)
CREATE TABLE IF NOT EXISTS collections (
    id TEXT PRIMARY KEY,
    name TEXT,
    description TEXT,
    kind TEXT, -- 'PLAYLIST', 'GALLERY'
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS collection_items (
    collection_id TEXT,
    event_id INTEGER,
    item_order INTEGER,
    note TEXT,
    added_at TEXT,
    PRIMARY KEY (collection_id, event_id),
    FOREIGN KEY (collection_id) REFERENCES collections(id)
);

-- 6. Change Detection (Pairs)
CREATE TABLE IF NOT EXISTS image_pairs (
    id TEXT PRIMARY KEY,
    event_a_id INTEGER,
    event_b_id INTEGER,
    delta_metrics_json TEXT, -- {delta_flux: 0.5, ssim: 0.9}
    label TEXT,              -- 'STABLE', 'VARIABLE'
    created_at TEXT
);

-- 7. Multi-Detector Runs
CREATE TABLE IF NOT EXISTS detector_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT,       -- Correlation ID for processing batch
    detector_name TEXT, 
    event_id INTEGER,
    score REAL,
    label TEXT,
    details_json TEXT,
    created_at TEXT
);
