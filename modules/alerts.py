import sqlite3
import datetime
import logging
import json
import config

class AlertManager:
    """
    Manages system alerts.
    Logs to DB and optionally sends to external hooks (Discord/Telegram).
    """
    
    def __init__(self, db_manager=None):
        self.db_path = config.DB_PATH
        # In a real scenario, we might inject db_manager instance
        
    def send_alert(self, level, message, context=None):
        """
        level: INFO, WARNING, CRITICAL
        """
        ts = datetime.datetime.now().isoformat()
        if context:
            ctx_json = json.dumps(context)
        else:
            ctx_json = "{}"
            
        # 1. Log to DB
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                "INSERT INTO alerts (timestamp, level, message, context_json, is_read) VALUES (?, ?, ?, ?, 0)",
                (ts, level, message, ctx_json)
            )
            conn.commit()
            conn.close()
            logging.info(f"🔔 ALERT [{level}]: {message}")
        except Exception as e:
            logging.error(f"Failed to log alert: {e}")

        # 2. Dispatch External (Optional stub)
        if level == "CRITICAL" and hasattr(config, "DISCORD_WEBHOOK_URL") and config.DISCORD_WEBHOOK_URL:
            # self._dispatch_webhook(message, config.DISCORD_WEBHOOK_URL)
            pass
