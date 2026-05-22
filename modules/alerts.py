import sqlite3
import datetime
import logging
import json
import config

class AlertManager:
    """
    Manages system alerts.
    Logs to DB and optionally sends to external hooks (Discord/Telegram).
    Also triggers closed-loop telescope follow-up slewing when a high-priority
    candidate signal is found.
    """
    
    def __init__(self, db_manager=None):
        self.db_path = config.DB_PATH
        # Lazy loading of ObsBridge to avoid circular dependencies
        self._bridge = None
        
    def send_alert(self, level, message, context=None):
        """
        level: INFO, WARNING, CRITICAL
        """
        ts = datetime.datetime.now().isoformat()
        if context:
            clean_ctx = {}
            for k, v in context.items():
                if hasattr(v, 'tolist'):
                    clean_ctx[k] = f"<numpy.ndarray of shape {v.shape}>"
                else:
                    clean_ctx[k] = v
            ctx_json = json.dumps(clean_ctx)
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

        # 2. Trigger Closed-loop Slew Follow-up via Obs-Bridge if we find a Candidate
        if level == "CRITICAL" or "CANDIDATE" in message.upper() or (context and context.get("label") == "CANDIDATE"):
            try:
                if self._bridge is None:
                    from modules.obs_bridge import ObservationBridge
                    self._bridge = ObservationBridge()
                
                # Slew the array to target candidate's coordinates
                self._bridge.trigger_candidate_followup(context or {})
            except Exception as e:
                logging.warning(f"Failed to trigger automatic telescope follow-up: {e}")

        # 3. Dispatch External (Optional stub)
        if level == "CRITICAL" and hasattr(config, "DISCORD_WEBHOOK_URL") and config.DISCORD_WEBHOOK_URL:
            # self._dispatch_webhook(message, config.DISCORD_WEBHOOK_URL)
            pass
