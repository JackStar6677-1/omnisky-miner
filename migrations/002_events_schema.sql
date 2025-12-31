-- Migration 002: Event Driven Schema (Phase 4)
-- Introduce Artifact tracking y Tablas de Eventos Científicos

-- 1. Sources: Control de fuentes y crawling
CREATE TABLE IF NOT EXISTS sources (
    url TEXT PRIMARY KEY,
    type TEXT, -- RADIO, IMAGE, METADATA
    last_visited TEXT,
    status TEXT DEFAULT 'ACTIVE', -- ACTIVE, DEAD, PAUSED
    error_count INTEGER DEFAULT 0
);

-- 2. Artifacts: Ciclo de vida del archivo (Idempotencia)
-- Controla el pipeline: NEW -> DOWNLOADING -> ANALYZED -> CLEANED
CREATE TABLE IF NOT EXISTS artifacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_url TEXT,
    filename TEXT,
    file_hash TEXT, -- SHA256 para evitar procesar lo mismo 2 veces
    size_bytes INTEGER,
    download_path TEXT, -- Ruta temporal
    status TEXT, -- NEW, QUEUED, DOWNLOADING, DOWNLOADED, ANALYZING, ANALYZED, FAILED, CLEANED
    created_at TEXT,
    updated_at TEXT,
    last_error TEXT,
    retry_count INTEGER DEFAULT 0,
    job_id TEXT, -- ID de ejecución para trazabilidad
    CONSTRAINT uniq_hash UNIQUE(file_hash)
);

CREATE INDEX IF NOT EXISTS idx_art_status ON artifacts(status);
CREATE INDEX IF NOT EXISTS idx_art_hash ON artifacts(file_hash);
CREATE INDEX IF NOT EXISTS idx_art_url ON artifacts(source_url);

-- 3. Events Radio: Resultados científicos de radioastronomía
CREATE TABLE IF NOT EXISTS events_radio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    artifact_id INTEGER,
    timestamp TEXT,
    fch1 REAL,
    foff REAL,
    snr REAL,
    drift_rate REAL,
    score REAL,
    label TEXT, -- RFI, CANDIDATE, NOISE
    notes TEXT,
    path_waterfall TEXT, -- Evidence PNG
    path_npz TEXT, -- Evidence Data (Time-Freq snippet)
    path_audio_raw TEXT,
    path_audio_clean TEXT,
    FOREIGN KEY(artifact_id) REFERENCES artifacts(id)
);

CREATE INDEX IF NOT EXISTS idx_rad_label ON events_radio(label);
CREATE INDEX IF NOT EXISTS idx_rad_score ON events_radio(score);

-- 4. Events Image: Resultados visuales (FITS)
CREATE TABLE IF NOT EXISTS events_image (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    artifact_id INTEGER,
    timestamp TEXT,
    ra REAL,
    dec REAL,
    score REAL,
    label TEXT, -- VISUAL_SOURCE, NOISE, ARTIFACT
    notes TEXT,
    path_cutout TEXT, -- Evidence NPZ/FITS small
    path_annotated TEXT, -- Evidence PNG
    FOREIGN KEY(artifact_id) REFERENCES artifacts(id)
);

CREATE INDEX IF NOT EXISTS idx_img_label ON events_image(label);
