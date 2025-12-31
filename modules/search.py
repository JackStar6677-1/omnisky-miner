import sqlite3
import config
import logging

class SearchEngine:
    """
    Local Semantic Search using SQLite FTS5.
    """
    
    def __init__(self):
        self.db_path = config.DB_PATH

    def index_item(self, event_id, title, content, tags, session_id=None):
        """Adds or updates an item in the FTS index."""
        conn = sqlite3.connect(self.db_path)
        try:
            # Check existing (by event_id logic requires keeping ID mapping, but FTS ROWID is implicit)
            # We use DELETE + INSERT for simplicity or specific logic if needed.
            # FTS doesn't have a unique constraint on event_id column easily unless logic enforced.
            
            # Simple approach: append. Cleanups via rebuilding index periodically.
            conn.execute(
                "INSERT INTO reports_fts(content, title, tags, event_id, session_id) VALUES (?, ?, ?, ?, ?)",
                (content, title, tags, event_id, session_id)
            )
            conn.commit()
        except Exception as e:
            logging.error(f"Search Index Error: {e}")
        finally:
            conn.close()

    def search(self, query, limit=20):
        """
        Full-text search.
        Returns list of dicts.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        results = []
        try:
            # Use snippet() function for context if desired
            q = """
                SELECT event_id, title, snippet(reports_fts, 0, '<b>', '</b>', '...', 10) as snippet, rank 
                FROM reports_fts 
                WHERE reports_fts MATCH ? 
                ORDER BY rank 
                LIMIT ?
            """
            cursor = conn.execute(q, (query, limit))
            results = [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Search Query Error: {e}")
        finally:
            conn.close()
        return results
