import sqlite3
import config
import logging
import json

class MissionControl:
    """
    Gamification Engine: Tracks user progress on research missions.
    """
    
    def __init__(self):
        self.db_path = config.DB_PATH
        self._seed_missions()

    def _seed_missions(self):
        """Creates default missions if they don't exist."""
        default_missions = [
            ("M001", "Radio Novice", "Analyze 10 Radio Signals", {"type": "RADIO", "count": 10}, {"xp": 100}),
            ("M002", "Deep Field", "Find an object above DEC 80", {"min_dec": 80, "count": 1}, {"xp": 250}),
            ("M003", "RFI Hunter", "Classify 50 RFI events", {"label": "RFI", "count": 50}, {"badge": "JAMMER"})
        ]
        
        conn = sqlite3.connect(self.db_path)
        try:
            for mid, name, desc, cond, reward in default_missions:
                conn.execute(
                    "INSERT OR IGNORE INTO missions (id, name, description, conditions_json, reward_json, created_at) VALUES (?, ?, ?, ?, ?, datetime('now'))",
                    (mid, name, desc, json.dumps(cond), json.dumps(reward))
                )
            conn.commit()
        except Exception as e:
            logging.error(f"Mission Seed Error: {e}")
        finally:
            conn.close()

    def update_progress(self, event_data):
        """
        Evaluates event against active missions.
        Returns list of newly completed mission names.
        """
        completed = []
        # Logic stub: Read active missions, check condition, increment progress in DB.
        # This requires reading and writing `mission_progress` table.
        return completed
