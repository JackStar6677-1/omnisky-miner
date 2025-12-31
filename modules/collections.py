import sqlite3
import config
import uuid

class CollectionManager:
    """
    Manages Playlists and Galleries.
    """
    
    def __init__(self):
        self.db_path = config.DB_PATH

    def create_collection(self, name, kind="PLAYLIST"):
        cid = str(uuid.uuid4())
        conn = sqlite3.connect(self.db_path)
        conn.execute("INSERT INTO collections (id, name, kind, created_at) VALUES (?, ?, ?, datetime('now'))", (cid, name, kind))
        conn.commit()
        conn.close()
        return cid

    def add_to_collection(self, collection_id, event_id):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                "INSERT INTO collection_items (collection_id, event_id, added_at) VALUES (?, ?, datetime('now'))",
                (collection_id, event_id)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False # Already in collection
        finally:
            conn.close()
