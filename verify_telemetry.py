from modules.telemetry import TelemetryMonitor
import time
import sqlite3
import pandas as pd
import os
import config

def verify():
    print("📡 Testing Telemetry Monitor...")
    
    # 1. Start Monitor
    # Pass None for pipeline (it handles valid None check)
    mon = TelemetryMonitor(pipeline_manager=None)
    mon.start()
    
    print("   Running for 5 seconds...")
    time.sleep(5)
    
    mon.stop()
    print("   Stopped.")
    
    # 2. Check DB
    try:
        conn = sqlite3.connect(config.DB_PATH)
        df = pd.read_sql_query("SELECT * FROM telemetry ORDER BY timestamp DESC LIMIT 10", conn)
        conn.close()
        
        if not df.empty:
            print("\n✅ Data intercepted in DB:")
            print(df[['timestamp', 'mbps_down', 'plan_usage_pct']].to_string(index=False))
            print(f"   Peak Session: {df.iloc[0]['mbps_peak_session']:.2f} Mbps")
        else:
            print("❌ DB is empty!")
            
    except Exception as e:
        print(f"❌ Verification Failed: {e}")

if __name__ == "__main__":
    verify()
