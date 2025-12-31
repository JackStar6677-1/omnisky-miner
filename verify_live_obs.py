from modules.obs import Observability
import time
import os
import json

def verify():
    print("Testing Live Observability...")
    
    # 1. Update Status
    Observability.update_status({"stage": "TESTING", "current": {"url": "http://test.com/data.fits"}})
    
    # 2. Log Events
    Observability.log_event("TEST_START", user="Admin")
    time.sleep(0.1)
    Observability.log_event("DOWNLOAD_DONE", url="http://test.com", size=1024)
    
    # 3. Read Back
    status = Observability.get_status()
    events = Observability.get_recent_events(5)
    
    print("\n✅ Status Readback:")
    print(json.dumps(status, indent=2))
    
    print("\n✅ Event Log Readback:")
    for e in events:
        print(f" - {e['ts']} | {e['event']} | {e}")

    if len(events) >= 2 and status['stage'] == 'TESTING':
        print("\n🎉 Verification SUCCESS")
    else:
        print("\n❌ Verification FAILED")

if __name__ == "__main__":
    verify()
