-- Migration 001: Initial Legacy Schema
-- Crea las tablas base legacy para compatibilidad con Dashboard v1 y Gamification

CREATE TABLE IF NOT EXISTS usuario_stats (
    id INTEGER PRIMARY KEY,
    mb_procesados REAL DEFAULT 0,
    hallazgos_total INTEGER DEFAULT 0,
    xp_total REAL DEFAULT 0
);

-- Inicializa usuario_stats si está vacía
INSERT OR IGNORE INTO usuario_stats (id, mb_procesados, hallazgos_total, xp_total) 
VALUES (1, 0, 0, 0);

-- Tabla Legacy Hallazgos (para Dashboard v1)
-- En el futuro Dashboard v2 leerá de events_radio/image
CREATE TABLE IF NOT EXISTS hallazgos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT, 
    tipo TEXT, 
    nombre_objeto TEXT, 
    frecuencia REAL, 
    snr REAL, 
    drift_rate REAL, 
    coordenadas TEXT, 
    clasificacion TEXT, 
    ruta_reporte TEXT, 
    ruta_audio TEXT, 
    ruta_audio_clean TEXT, 
    ruta_imagen TEXT, 
    notas TEXT
);
