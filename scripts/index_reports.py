import sqlite3
import config
from modules.search import SearchEngine
import logging

logging.basicConfig(level=logging.INFO)

def index_reports():
    print("🔎 Indexing Reports for FTS5...")
    
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    search = SearchEngine()
    
    # Index Radio Events
    c = conn.cursor()
    c.execute("SELECT id, label, ml_score, ml_label FROM events_radio")
    count = 0
    for row in c.fetchall():
        # Construct a "virtual document" content
        content = f"Radio event classified as {row['label']}. ML says {row['ml_label']} with score {row['ml_score']}."
        tags = f"radio {row['label']} {row['ml_label']}"
        title = f"Radio Event {row['id']}"
        
        search.index_item(row['id'], title, content, tags)
        count += 1
        
    # Index Images
    c.execute("SELECT id, label, ml_score, ml_label, object_name FROM events_image")
    for row in c.fetchall():
        content = f"Visual survey object {row['object_name']}. Classified as {row['label']}."
        tags = f"image {row['label']} {row['object_name']}"
        title = f"Image {row['object_name']}"
        
        search.index_item(row['id'], title, content, tags)
        count += 1
        
    conn.close()
    print(f"✅ Indexed {count} generated reports.")

if __name__ == "__main__":
    index_reports()
