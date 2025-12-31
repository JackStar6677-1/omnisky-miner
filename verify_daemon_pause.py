import sys
import os
import time
import json
import logging
# Mock config for test if needed, or rely on real
# We just want to instantiate DaemonControl and simulate a process name match

from modules.daemon_control import DaemonControl
import config

def verify_daemon():
    print(">> Testing Daemon Control Logic...")
    
    # 1. Force a "Heavy Process" into the config list for testing
    print("[1/3] Injecting test process 'python.exe' as HEAVY...")
    original_heavy = config.HEAVY_PROCESS_NAMES
    config.HEAVY_PROCESS_NAMES = ["python.exe", "pythonw.exe"] # Self-match
    
    dc = DaemonControl()
    should_pause, reason = dc.check_should_pause()
    
    if should_pause:
        print(f"   [OK] Pause detected correctly: {reason}")
    else:
        print(f"   [FAIL] Did not detect heavy process. Reason: {reason}")
        
    # 2. Reset and check Idle
    print("\n[2/3] Checking IDLE state (Restoring config)...")
    config.HEAVY_PROCESS_NAMES = ["NonExistentGame.exe"]
    should_pause, reason = dc.check_should_pause()
    
    if not should_pause:
        print(f"   [OK] System IDLE (Running). Reason: {reason}")
    else:
        print(f"   [WARN] System busy ({reason}). Could not verify IDLE.")
        
    # 3. Write State
    print("\n[3/3] Writing State File...")
    dc.update_state("RUNNING")
    if os.path.exists(dc.state_file):
        with open(dc.state_file, 'r') as f:
            data = json.load(f)
            print(f"   [OK] State file written: {json.dumps(data)}")
    else:
        print("   [FAIL] State file not found.")

    print("\n>> DAEMON TEST COMPLETE")

if __name__ == "__main__":
    verify_daemon()
