import sqlite3
import os
import datetime
import logging
import config

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - DB_MANAGER - %(message)s')

class DatabaseManager:
    def __init__(self, db_path=config.DB_PATH):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

import sqlite3
import os
import datetime
import logging
import config
import glob

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - DB_MANAGER - %(message)s')

class DatabaseManager:
    def __init__(self, db_path=config.DB_PATH):
        self.db_path = db_path
        self._apply_migrations()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def _apply_migrations(self):
        """Aplica migraciones SQL en orden desde /migrations"""
        migration_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'migrations') # Ajustar path si module
        # Si estamos en root K:/.../migrations es directo
        migration_dir = "migrations"
        if not os.path.exists(migration_dir):
            logging.warning("⚠️ No migrations folder found. Creating tables manually might be needed.")
            return

        conn = self.get_connection()
        c = conn.cursor()
        
        # Tabla de control de migraciones
        c.execute('''
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at TEXT
            )
        ''')
        
        # Leer archivos .sql ordenados
        sql_files = sorted(glob.glob(os.path.join(migration_dir, "*.sql")))
        
        for sql_file in sql_files:
            try:
                version = int(os.path.basename(sql_file).split('_')[0])
                c.execute("SELECT 1 FROM schema_migrations WHERE version=?", (version,))
                if c.fetchone():
                    continue # Ya aplicada
                
                logging.info(f"🔄 Applying migration: {os.path.basename(sql_file)}")
                with open(sql_file, 'r', encoding='utf-8') as f:
                    script = f.read()
                    c.executescript(script)
                
                c.execute("INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)", 
                          (version, datetime.datetime.now().isoformat()))
                conn.commit()
                
            except Exception as e:
                logging.error(f"❌ Migration failed {sql_file}: {e}")
                conn.rollback()
                raise e
                
        conn.close()

    def init_db(self):
        """Deprecated: Use migrations instead. Kept for logic compat if called manually."""
        pass


    # --- PIPELINE STATE METHODS ---
    
    def check_artifact_exists(self, file_hash):
        """Idempotencia: Retorna True si ya procesamos este hash."""
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("SELECT 1 FROM artifacts WHERE file_hash = ?", (file_hash,))
        exists = c.fetchone() is not None
        conn.close()
        return exists

    def register_artifact(self, url, filename, status="NEW"):
        now = datetime.datetime.now().isoformat()
        conn = self.get_connection()
        c = conn.cursor()
        try:
            c.execute('''
                INSERT INTO artifacts (source_url, filename, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (url, filename, status, now, now))
            art_id = c.lastrowid
            conn.commit()
            return art_id
        except Exception as e:
            logging.error(f"Error registering artifact: {e}")
            return None
        finally:
            conn.close()

    def update_artifact_status(self, art_id, status, path=None, file_hash=None, size=None, error=None):
        now = datetime.datetime.now().isoformat()
        conn = self.get_connection()
        c = conn.cursor()
        
        query = "UPDATE artifacts SET status=?, updated_at=?"
        params = [status, now]
        
        if path: 
            query += ", download_path=?"
            params.append(path)
        if file_hash:
            query += ", file_hash=?"
            params.append(file_hash)
        if size:
            query += ", size_bytes=?"
            params.append(size)
        if error:
            query += ", last_error=?"
            params.append(str(error))
            
        query += " WHERE id=?"
        params.append(art_id)
        
        try:
            c.execute(query, params)
            conn.commit()
        except sqlite3.IntegrityError:
             logging.warning(f"Hash collision or logic error update art_id {art_id}")
        finally:
            conn.close()

    def log_radio_event(self, art_id, data):
        """Data dict con keys fch1, snr, etc"""
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO events_radio (
                artifact_id, timestamp, fch1, foff, snr, drift_rate, score, label, notes,
                path_waterfall, path_audio_raw, path_audio_clean
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            art_id, datetime.datetime.now().isoformat(),
            data.get('fch1'), data.get('foff'), data.get('snr'), data.get('drift'),
            data.get('score'), data.get('label'), data.get('notes'),
            data.get('waterfall_path'), data.get('audio_raw'), data.get('audio_clean')
        ))
        conn.commit()
        
        # Legacy support: Insert into hallazgos for Dashboard v1 (Temporal)
        c.execute('''
             INSERT INTO hallazgos (timestamp, tipo, nombre_objeto, frecuencia, snr, drift_rate, clasificacion, ruta_audio, ruta_audio_clean, notas)
             VALUES (?, 'RADIO', ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.datetime.now().isoformat(),
            f"Artifact_{art_id}",
            data.get('fch1'), data.get('snr'), data.get('drift'),
            data.get('label'), data.get('audio_raw'), data.get('audio_clean'),
            data.get('notes')
        ))
        conn.commit()
        conn.close()
        
    def log_image_event(self, art_id, data):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO events_image (
                artifact_id, timestamp, score, label, notes,
                path_annotated
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            art_id, datetime.datetime.now().isoformat(),
            data.get('score'), data.get('label'), data.get('notes'),
            data.get('annotated_path')
        ))
        conn.commit()
        
        # Legacy
        c.execute('''
             INSERT INTO hallazgos (timestamp, tipo, nombre_objeto, clasificacion, ruta_imagen, notas)
             VALUES (?, 'VISUAL', ?, ?, ?, ?)
        ''', (
            datetime.datetime.now().isoformat(),
            f"Artifact_{art_id}",
            data.get('label'), data.get('annotated_path'), data.get('notes')
        ))
        
        conn.commit()
        conn.close()
    # --- SESSION MANAGEMENT (PRO) ---
    def create_session(self, config_snapshot=None):
        import uuid
        import json
        session_id = str(uuid.uuid4())
        start_time = datetime.datetime.now().isoformat()
        if config_snapshot is None: config_snapshot = {}
        
        conn = self.get_connection()
        try:
            conn.execute(
                "INSERT INTO sessions (id, start_time, config_snapshot, status) VALUES (?, ?, ?, ?)",
                (session_id, start_time, json.dumps(config_snapshot), "ACTIVE")
            )
            conn.commit()
            logging.info(f"🟢 Session Started: {session_id}")
            return session_id
        except Exception as e:
            logging.error(f"Failed to start session: {e}")
            return None
        finally:
            conn.close()

    def end_session(self, session_id):
        end_time = datetime.datetime.now().isoformat()
        conn = self.get_connection()
        try:
            conn.execute(
                "UPDATE sessions SET end_time = ?, status = ? WHERE id = ?",
                (end_time, "COMPLETED", session_id)
            )
            conn.commit()
            logging.info(f"🔴 Session Ended: {session_id}")
        except Exception as e:
            logging.error(f"Failed to end session: {e}")
        finally:
            conn.close()

    def get_or_create_family(self, signature_hash, representative_event_id=None):
        import uuid
        conn = self.get_connection()
        c = conn.cursor()
        try:
            # Check existing
            c.execute("SELECT id FROM event_families WHERE signature_hash = ?", (signature_hash,))
            row = c.fetchone()
            if row:
                return row[0]
            
            # Create new
            fam_id = str(uuid.uuid4())
            ts = datetime.datetime.now().isoformat()
            c.execute(
                "INSERT INTO event_families (id, signature_hash, first_seen_at, representative_event_id) VALUES (?, ?, ?, ?)",
                (fam_id, signature_hash, ts, representative_event_id)
            )
            conn.commit()
            return fam_id
        except Exception as e:
            logging.error(f"Family Error: {e}")
            return None
        finally:
            conn.close()
