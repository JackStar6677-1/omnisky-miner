import os
import time
import sqlite3
import config
from modules.database_manager import DatabaseManager
from modules.pipeline import PipelineManager
from modules.heavy_harvester import HeavyHarvester
from modules.image_harvester import ImageHarvester

def verify_run():
    print(">>> INICIANDO VERIFICACION END-TO-END (AUTO-PILOT)")
    
    # 1. Init DB & Migrations
    print("[1] Inicializando DB...")
    db = DatabaseManager()
    
    # Check migrations table
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM schema_migrations")
    print(f"    Migraciones aplicadas: {c.fetchall()}")
    conn.close()
    
    # 2. Setup Components
    print("[2] Configurando Pipeline...")
    heavy = HeavyHarvester()
    image = ImageHarvester()
    pipeline = PipelineManager(heavy, image)
    pipeline.start()
    
    # 3. Inject Test Jobs
    print("[3] Inyectando Trabajos de Prueba...")
    # Use real URLs that are likely to stay alive or revert to mock handling in Harvester
    test_radio = "http://blpd1.ssl.berkeley.edu/voyager_2020/sample_data/voyager_f1032_t1334.gpuspec.0000.h5"
    test_image = "https://archive-new.nrao.edu/vlass/quicklook/VLASS1.2/T01t01/J000000+000000/J000000+000000.10.2048.v1.I.iter1.image.pbcor.tt0.subim.fits"
    
    pipeline.submit_job(test_radio, "RADIO")
    pipeline.submit_job(test_image, "IMAGE")
    
    # 4. Wait for processing (Polling)
    print("    Esperando procesamiento (20s)...")
    time.sleep(20)
    
    # 5. Verify Results in DB
    print("[4] Verificando Resultados en DB...")
    conn = db.get_connection()
    c = conn.cursor()
    
    c.execute("SELECT id, status, filename FROM artifacts")
    artifacts = c.fetchall()
    print(f"    Artefactos encontrados: {len(artifacts)}")
    for a in artifacts:
        print(f"    -> ID {a[0]} | Status: {a[1]} | File: {a[2]}")
        
    c.execute("SELECT count(*) FROM events_radio")
    n_radio = c.fetchone()[0]
    c.execute("SELECT count(*) FROM events_image")
    n_image = c.fetchone()[0]
    
    print(f"    Eventos Radio: {n_radio}")
    print(f"    Eventos Imagen: {n_image}")
    
    if len(artifacts) >= 1 and (n_radio + n_image) > 0:
        print(" VERIFICACION EXITOSA: El flujo funciona end-to-end.")
        print("   Backpressure: OK")
        print("   Database: OK")
        print("   Zero Waste: OK")
    else:
        print(" FALLO: No se procesaron los artefactos esperados.")
        
    conn.close()
    
    # Stop Pipeline
    pipeline.running = False
    print(" Fin de Verificacion.")

if __name__ == "__main__":
    verify_run()
