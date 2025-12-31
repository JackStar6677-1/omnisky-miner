import sqlite3
import pandas as pd
import os
import config
import logging

# --- CONSTANTS ---
DB_PATH = config.DB_PATH
OMNISKY_ROOT = config.OMNISKY_ROOT

class UIDataLoader:
    """
    Handles data fetching, normalization, and 'Real vs Test' logic for the Dashboard.
    Adapts between New Schema (Events/Artifacts) and Legacy Schema (Hallazgos).
    """
    
    @staticmethod
    def get_connection():
        return sqlite3.connect(DB_PATH, check_same_thread=False)

    @staticmethod
    def classify_origin(row):
        """
        Determines if an event is REAL or TEST.
        """
        # 1. Explicit Flags
        if str(row.get('type', '')).upper() in ['LEGACY', 'TEST']:
            return 'TEST'
        if str(row.get('classification', '')).upper() == 'TEST':
            return 'TEST'
            
        # 2. Source/Metadata Checks
        source = str(row.get('source_url', ''))
        obj_name = str(row.get('object_name', ''))
        
        if not source or source.lower() in ['n/a', 'none', '']:
            # If no source and looks like a mock artifact
            if "artifact" in obj_name.lower() or "test" in obj_name.lower() or "mock" in obj_name.lower():
                return 'TEST'
        
        # 3. Validation for REAL
        # Needs at least a valid source URL or a substantial file size/hash (if available)
        # For now, if it came from the new pipeline (RADIO/IMAGE types) and didn't fail the above, assume REAL.
        if row.get('type') in ['RADIO', 'IMAGE']:
            return 'REAL'
            
        return 'TEST' # Fallback

    @staticmethod
    def fetch_all_events(limit=1000):
        conn = UIDataLoader.get_connection()
        
        # --- 1. Radio Events (New) ---
        q_radio = """
            SELECT 
                r.id as event_id,
                r.timestamp, 
                a.filename as object_name, 
                r.label as classification, 
                r.snr as data_value, -- Renamed for generic usage
                'SNR' as value_unit,
                r.fch1 as frequency,
                r.path_audio_raw, 
                r.path_audio_clean,
                r.path_waterfall as path_visual_main, -- PNG
                r.path_npz as path_data_aux, -- NPZ
                'RADIO' as type,
                a.source_url,
                a.file_hash,
                a.size_bytes,
                a.id as artifact_id
            FROM events_radio r
            JOIN artifacts a ON r.artifact_id = a.id
        """
        
        # --- 2. Image Events (New) ---
        q_image = """
            SELECT 
                i.id as event_id,
                i.timestamp, 
                a.filename as object_name, 
                i.label as classification, 
                i.score as data_value, -- Sigma/Score
                'SIGMA' as value_unit,
                0 as frequency,
                NULL as path_audio_raw, 
                NULL as path_audio_clean,
                i.path_annotated as path_visual_main,
                i.path_cutout as path_data_aux,
                'IMAGE' as type,
                a.source_url,
                a.file_hash,
                a.size_bytes,
                a.id as artifact_id,
                i.ra,
                i.dec
            FROM events_image i
            JOIN artifacts a ON i.artifact_id = a.id
        """
        
        # --- 3. Legacy (Hallazgos) ---
        # Robust check if table exists
        has_legacy = False
        try:
            pd.read_sql_query("SELECT 1 FROM hallazgos LIMIT 1", conn)
            has_legacy = True
        except:
            pass

        dfs = []
        
        try:
            dfs.append(pd.read_sql_query(q_radio, conn))
        except Exception: pass # Maybe table doesn't exist yet
        
        try:
            dfs.append(pd.read_sql_query(q_image, conn))
        except Exception: pass
        
        if has_legacy:
            q_legacy = """
            SELECT
                id as event_id,
                timestamp,
                nombre_objeto as object_name,
                clasificacion as classification,
                snr as data_value,
                'SNR' as value_unit,
                frecuencia as frequency,
                ruta_audio as path_audio_raw,
                NULL as path_audio_clean,
                NULL as path_visual_main,
                NULL as path_data_aux,
                'LEGACY' as type,
                'N/A' as source_url,
                NULL as file_hash,
                0 as size_bytes,
                NULL as artifact_id
            FROM hallazgos
            """
            try:
                dfs.append(pd.read_sql_query(q_legacy, conn))
            except Exception: pass

        conn.close()
        
        if not dfs:
            return pd.DataFrame(columns=['event_id', 'timestamp', 'object_name', 'classification', 'data_origin', 'type'])

        # Merge
        df = pd.concat(dfs, ignore_index=True)
        
        # Normalize
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df['data_value'] = pd.to_numeric(df['data_value'], errors='coerce').fillna(0)
        df['classification'] = df['classification'].fillna('UNKNOWN')
        
        # Apply Origin Logic
        df['data_origin'] = df.apply(UIDataLoader.classify_origin, axis=1)
        
        # Sort
        df.sort_values(by='timestamp', ascending=False, inplace=True)
        
        # Limit
        return df.head(limit)

    @staticmethod
    def resolve_path(path_str):
        """
        Resolves a path to (absolute_path, exists_bool, details_str).
        Handles relative, absolute, and legacy paths.
        """
        if not path_str or str(path_str).lower() in ['none', 'nan', '', 'null']:
            return None, False, "Path is Empty/None"

        # 1. Absolute
        if os.path.exists(path_str):
            return os.path.abspath(path_str), True, "OK (Absolute)"

        # 2. Relative to Project Root (CWD)
        abs_cwd = os.path.abspath(path_str)
        if os.path.exists(abs_cwd):
            return abs_cwd, True, "OK (Relative CWD)"

        # 3. Relative to OMNISKY_ROOT (Data Dir)
        abs_data = os.path.join(OMNISKY_ROOT, path_str)
        if os.path.exists(abs_data):
            return os.path.abspath(abs_data), True, f"OK ({OMNISKY_ROOT})"
            
        return abs_cwd, False, "File Not Found"
