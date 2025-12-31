import queue
import threading
import time
import logging
import concurrent.futures
import config
from .database_manager import DatabaseManager
from modules.obs import Observability
from modules.triage import TriageEngine
from modules.deduplication import DeduplicationEngine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - PIPELINE - %(message)s')


class PipelineManager:
    def __init__(self, heavy_harvester, image_harvester):
        self.db = DatabaseManager()
        self.heavy = heavy_harvester
        self.image = image_harvester
        self.triage = TriageEngine()
        
        # Queues
        self.q_download = queue.Queue(maxsize=config.QUEUE_SIZE * 2)
        self.q_analyze = queue.Queue(maxsize=config.QUEUE_SIZE)
        self.q_persist = queue.Queue(maxsize=config.QUEUE_SIZE)
        
        # ThreadPools
        self.pool_download = concurrent.futures.ThreadPoolExecutor(max_workers=config.MAX_DOWNLOAD_WORKERS, thread_name_prefix="DL")
        self.pool_analyze = concurrent.futures.ThreadPoolExecutor(max_workers=config.MAX_ANALYZE_WORKERS, thread_name_prefix="AN")
        
        self.running = True
        
        # Start consumers
        threading.Thread(target=self._worker_dispatcher, daemon=True).start()

    def submit_job(self, url, job_type="RADIO"):
        """
        Entry point: Add URL to Download Queue.
        BLOCKS if queue is full (Backpressure).
        Returns True if queued, False if timeout/error.
        """
        try:
            # Blocking PUT with timeout to allow checking shutdown flag
            # 5 second timeout to allow main loop to check other things if block persists
            self.q_download.put((url, job_type), block=True, timeout=5)
            # logging.info(f"Job queued: {url}")
            return True
        except queue.Full:
            # Backpressure hit
            # logging.warning("⚠️ Backpressure: Queue Full. Waiting...")
            return False
            
    def _worker_dispatcher(self):
        """Standard Worker Pool Logic is handled by Consumers below."""
        pass

    def start(self):
        # Start Consumers dedicated threads that feed the pools
        threading.Thread(target=self._consume_download, daemon=True).start()
        threading.Thread(target=self._consume_analyze, daemon=True).start()
        threading.Thread(target=self._consume_persist, daemon=True).start()
        logging.info("🚀 Pipeline Started: Download -> Analyze -> Persist")

    def _consume_download(self):
        while self.running:
            url, jtype = self.q_download.get()
            self.pool_download.submit(self._task_download, url, jtype)
            self.q_download.task_done()

    def _consume_analyze(self):
        while self.running:
            artifact_id, jtype = self.q_analyze.get()
            self.pool_analyze.submit(self._task_analyze, artifact_id, jtype)
            self.q_analyze.task_done()
            
    def _consume_persist(self):
        while self.running:
            # Persist is fast (DB write), maybe single thread is enough or small pool
            # For now, simply execute inline
            data = self.q_persist.get()
            self._task_persist(data)
            self.q_persist.task_done()

    # --- TASKS ---

    def _task_download(self, url, jtype):
        """Executed in DL Pool"""
        filename = url.split('/')[-1] if '?' not in url else "unknown.dat"
        
        # 1. Register NEW
        art_id = self.db.register_artifact(url, filename, status="NEW")
        if not art_id: return

        # 2. Download
        try:
            self.db.update_artifact_status(art_id, "DOWNLOADING")
            if jtype == "RADIO":
                path, fhash, size = self.heavy.download_granular(url)
            else:
                path, fhash, size = self.image.download_granular(url)
                
            if path:
                # 3. Check Idempotency (Hash)
                if self.db.check_artifact_exists(fhash):
                    logging.info(f"♻️ Duplicate Hash {fhash[:8]}. Skipping.")
                    self.db.update_artifact_status(art_id, "DUPLICATE", path, fhash, size)
                    # Cleanup
                    self.db.update_artifact_status(art_id, "DUPLICATE", path, fhash, size)
                    
                    # FORENSIC: Only cleanup if not flagged for retention (duplicates usually trash)
                    self.heavy.cleanup(path)
                    return
                
                # 4. Success -> Queue Analyze
                self.db.update_artifact_status(art_id, "DOWNLOADED", path, fhash, size)
                self.q_analyze.put((art_id, jtype))
                Observability.log_event("DOWNLOAD_DONE", artifact_id=art_id, size=size)
            else:
                self.db.update_artifact_status(art_id, "FAILED", error="Download returned None")
                Observability.log_event("DOWNLOAD_FAIL", artifact_id=art_id, reason="Empty Path")
                
        except Exception as e:
            self.db.update_artifact_status(art_id, "FAILED", error=str(e))
            logging.error(f"DL Task Error: {e}")

    def _task_analyze(self, art_id, jtype):
        """Executed in AN Pool"""
        # Fetch path from DB
        conn = self.db.get_connection()
        c = conn.cursor()
        c.execute("SELECT download_path, source_url FROM artifacts WHERE id=?", (art_id,))
        row = c.fetchone()
        conn.close()
        
        if not row: return
        path, url = row
        
        try:
            self.db.update_artifact_status(art_id, "ANALYZING")
            Observability.log_event("ANALYZE_START", artifact_id=art_id, path=path)
            Observability.update_status({"stage": "ANALYZING", "current": {"artifact_id": art_id}})
            
            result_data = None
            if jtype == "RADIO":
                result_data = self.heavy.analyze_granular(path)
            else:
                result_data = self.image.analyze_granular(path)
                
            # Queue Persist
            if result_data:
                self.q_persist.put((art_id, jtype, result_data, path))
            else:
                 self.db.update_artifact_status(art_id, "FAILED_ANALYSIS")
                 self.heavy.cleanup(path) # Cleanup on fail

        except Exception as e:
            self.db.update_artifact_status(art_id, "ERROR_ANALYZING", error=str(e))
            self.heavy.cleanup(path) # Ensure cleanup

    def _task_persist(self, data):
        """Executed in Persist Thread"""
        art_id, jtype, result, path = data
        
        try:
            if jtype == "RADIO":
                self.db.log_radio_event(art_id, result)
            else:
                self.db.log_image_event(art_id, result)
                
            self.db.update_artifact_status(art_id, "CLEANED") # Mark as finally processed
            
            # Zero Waste: Nuke original
            self.heavy.cleanup(path)
            logging.info(f"✨ Artifact {art_id} processed & cleaned.")
            
        except Exception as e:
            logging.error(f"Persist Error: {e}")
