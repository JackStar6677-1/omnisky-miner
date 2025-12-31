import sys
import os
import time
import logging
import signal

# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import config
from modules.discovery import DiscoveryAgent
from modules.pipeline import PipelineManager
from modules.daemon_control import DaemonControl
from modules.database_manager import DatabaseManager

# Setup Logging to file for Daemon
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - DAEMON - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(config.OMNISKY_DATA, "OBS", "daemon.log")),
        logging.StreamHandler()
    ]
)

class OmniSkyDaemon:
    def __init__(self):
        self.running = True
        self.control = DaemonControl()
        self.db = DatabaseManager() # Ensure schema
        self.pipeline = PipelineManager()
        self.discovery = DiscoveryAgent()
        
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

    def shutdown(self, signum, frame):
        logging.info("🛑 Daemon stopping...")
        self.running = False

    def run(self):
        logging.info("🚀 OmniSky Daemon Started (Background Mode)")
        
        while self.running:
            try:
                # 1. Check Control Plane (Local Resource Monitor)
                is_paused, reason = self.control.update_state(
                    current_status="WORKING" if self.pipeline.has_work() else "WAITING"
                )
                
                # 2. Check External Control (API control.json)
                control_file = os.path.join(config.OMNISKY_DATA, "OBS", "control.json")
                if os.path.exists(control_file):
                    try:
                        with open(control_file, 'r') as f:
                            ext_ctrl = json.load(f)
                        if ext_ctrl.get("desired_state") == "PAUSED":
                            is_paused = True
                            reason = f"API: {ext_ctrl.get('reason', 'USER')}"
                    except: pass
                
                if is_paused:
                    # Optional: Shutdown pipeline workers to save perfectly 0 CPU?
                    # For now we just don't feed it new work.
                    time.sleep(config.CHECK_INTERVAL_SECONDS)
                    continue

                # 2. Do Work
                # a) Pipeline maintenance (process queues) is async in threads.
                #    We keep the main loop alive to feed Discovery.
                
                # Check if we need more targets
                # Only discover if queue is low
                if self.pipeline.q_download.qsize() < 10:
                    new_targets = self.discovery.find_new_targets()
                    for t in new_targets:
                        self.pipeline.submit_task(t)
                        
                # b) Check queues
                if not self.pipeline.has_work() and self.pipeline.q_download.empty():
                     # Idle sleep
                     self.control.update_state("IDLE")
                     time.sleep(5)
                else:
                    time.sleep(1)
                    
            except Exception as e:
                logging.error(f"Daemon Loop Error: {e}")
                time.sleep(5)

if __name__ == "__main__":
    daemon = OmniSkyDaemon()
    daemon.run()
