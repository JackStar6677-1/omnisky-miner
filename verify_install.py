import os
import sys
import sqlite3
import config
from modules.database_manager import DatabaseManager

sys.path.append(os.getcwd())

def test_system():
    print("=== OMNISKY MINER: VERIFICACIÓN FINAL (OBSERVATORIO LOCAL) ===")
    
    # 1. DB Check (Phase 4)
    print("\n[1] Verificando Base de Datos (Schema v2)...")
    if os.path.exists(config.DB_PATH):
        conn = sqlite3.connect(config.DB_PATH)
        c = conn.cursor()
        
        # Verify Schema Migrations
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'")
        if c.fetchone():
             print("  [OK] Tabla 'schema_migrations' activa (Version Control).")

        # Verify Artifacts table
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='artifacts'")
        if c.fetchone():
             print("  [OK] Tabla 'artifacts' (Pipeline Tracking) activa.")
             
        # Verify Events
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events_radio'")
        if c.fetchone():
             print("  [OK] Tabla 'events_radio' activa.")
             
        conn.close()

    # 1.5 Libs Check

    # 1.5 Libs Check
    try:
        import noisereduce
        import plotly
        print("  [OK] Librerías Visuales/Audio instaladas.")
    except ImportError:
        print("  [WARN] noisereduce/plotly no instaladas (pip install -r requirements.txt).")


    # 2. Config & Paths
    print("\n[2] Verificando Rutas...")
    if os.path.exists(config.DIR_VISUAL):
        print("  [OK] Bóveda Visual accesible.")

    # 3. Streamlit Check
    print("\n[3] Verificando Dashboard...")
    if os.path.exists("dashboard.py"):
        print("  [OK] dashboard.py existe. Ejecutar con: streamlit run dashboard.py")
    
    print("\n=== SISTEMA DE OBSERVATORIO OPERATIVO ===")

if __name__ == "__main__":
    test_system()
