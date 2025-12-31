import time
import threading
import psutil
import sqlite3
import logging
import datetime
import config

class TelemetryMonitor:
    def __init__(self, pipeline_manager=None, db_path=None):
        self.pipeline = pipeline_manager
        self.db_path = db_path or config.DB_PATH
        self.running = False
        self.thread = None
        
        # Network State
        self.last_net = psutil.net_io_counters()
        self.last_time = time.time()
        
        self.peak_mbps_session = 0.0
        self.metrics_history = [] # Ring buffer for p95 calc (last 60s)
        
    def start(self):
        if self.running: return
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        logging.info("📡 Telemetry Monitor Started (Background)")
        
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
            
    def _monitor_loop(self):
        # Init DB table if needed (handled by migrations usually, but just in case)
        pass 
        
        while self.running:
            try:
                self._tick()
            except Exception as e:
                logging.error(f"Telemetry Error: {e}")
            time.sleep(config.TELEMETRY_INTERVAL_SEC)
            
    def _tick(self):
        now = time.time()
        current_net = psutil.net_io_counters()
        
        # Delta calculation
        dt = now - self.last_time
        if dt <= 0: return # Too fast
        
        bytes_recv = current_net.bytes_recv - self.last_net.bytes_recv
        bytes_sent = current_net.bytes_sent - self.last_net.bytes_sent
        
        # Convert to Mbps
        # (bytes * 8) / 1,000,000 / seconds
        mbps_down = (bytes_recv * 8) / 1_000_000 / dt
        mbps_up = (bytes_sent * 8) / 1_000_000 / dt
        
        # Update metrics
        if mbps_down > self.peak_mbps_session:
            self.peak_mbps_session = mbps_down
            
        # Plan Usage
        plan_pct = (mbps_down / config.PLAN_MBPS) * 100.0 if config.PLAN_MBPS else 0
        
        # Pipeline State
        q_dl, q_an, q_pe = 0, 0, 0
        act_dl, act_an = 0, 0
        ok_total, fail_total = 0, 0
        
        if self.pipeline:
            q_dl = self.pipeline.q_download.qsize()
            q_an = self.pipeline.q_analyze.qsize()
            q_pe = self.pipeline.q_persist.qsize()
            # Approximation of active workers (TODO: precise tracking require worker hooks)
            # For now we assume if queue is moving, workers are active? 
            # Better: PipelineManager should expose 'active_count'
            pass

        # Update State
        self.last_net = current_net
        self.last_time = now
        
        # Write to DB
        self._write_db(mbps_down, mbps_up, plan_pct, q_dl, q_an, q_pe)
        
    def _write_db(self, down, up, plan, q_dl, q_an, q_pe):
        ts = datetime.datetime.now().isoformat()
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("""
                INSERT INTO telemetry (
                    timestamp, mbps_down, mbps_up, mbps_peak_session, plan_usage_pct,
                    q_download_size, q_analyze_size, q_persist_size
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (ts, down, up, self.peak_mbps_session, plan, q_dl, q_an, q_pe))
            
            # Retention Policy: Delete older than 1 hour to keep DB light?
            # Or just keep it. SQLite can handle it.
            
            conn.commit()
            conn.close()
        except Exception:
            pass # Don't crash monitoring on DB lock
