import psutil
import time
import json
import os
import shutil
import logging
import subprocess
import config

class DaemonControl:
    """
    Monitors system resources and heavy processes to control Daemon state.
    """
    
    def __init__(self):
        self.state_file = config.DAEMON_STATE_FILE
        self.last_pause = 0
        self.last_resume = 0
        self.is_paused = False
        
        # Ensure OBS dir exists
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)

    def check_should_pause(self):
        """
        Returns (should_pause: bool, reason: str)
        """
        # 1. Check Heavy Processes
        try:
            # Iterating processes can be slow, might want to optimize or cache PIDs logic
            # For robustness, we check names.
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] in config.HEAVY_PROCESS_NAMES:
                    return True, f"HEAVY_PROCESS: {proc.info['name']}"
        except Exception:
            pass # Access denied etc.

        # 2. Check Resources
        cpu = psutil.cpu_percent(interval=0.1)
        if cpu > config.PAUSE_CPU_PCT:
            return True, f"CPU_HIGH: {cpu}%"

        ram = psutil.virtual_memory().percent
        if ram > config.PAUSE_RAM_PCT:
            return True, f"RAM_HIGH: {ram}%"

        # 3. Check GPU (NVIDIA only stub)
        # shutil.which("nvidia-smi") could check presence
        # For now, minimal overhead check or skip
        
        return False, "IDLE"

    def update_state(self, current_status="IDLE", metrics=None):
        """Writes state to JSON for Dashboard."""
        should_pause, reason = self.check_should_pause()
        
        # Hysteresis / Cooldown Logic
        now = time.time()
        
        if should_pause:
            if not self.is_paused:
                self.is_paused = True
                self.last_pause = now
                logging.info(f"⏸️ PAUSING DAEMON: {reason}")
            state_str = "PAUSED"
        else:
            # Only resume if cooldown passed
            if self.is_paused:
                if (now - self.last_pause) > config.RESUME_COOLDOWN_SECONDS:
                    self.is_paused = False
                    self.last_resume = now
                    logging.info("▶️ RESUMING DAEMON: System Free")
                    state_str = "RUNNING"
                else:
                    state_str = "PAUSED" # Keep paused during cooldown
                    reason = "COOLDOWN"
            else:
                state_str = "RUNNING"
                reason = "SYSTEM_OK"

        # If pipeline is idle despite running, we mark IDLE
        if state_str == "RUNNING" and current_status == "WAITING":
            state_str = "IDLE"

        state_data = {
            "daemon_state": state_str,
            "pause_reason": reason,
            "updated_at": now,
            "metrics": {
                "cpu": psutil.cpu_percent(interval=None),
                "ram": psutil.virtual_memory().percent,
                "gpu": "N/A"
            }
        }
        
        # Write Atomic
        try:
            with open(self.state_file + ".tmp", 'w') as f:
                json.dump(state_data, f)
            shutil.move(self.state_file + ".tmp", self.state_file)
        except: pass
        
        return self.is_paused, reason
