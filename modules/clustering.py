import pandas as pd
import sqlite3
import config
from sklearn.cluster import DBSCAN
import numpy as np

class ClusteringEngine:
    """
    Identifies 'Active Zones' using DBSCAN.
    """
    
    def compute_clusters(self):
        conn = sqlite3.connect(config.DB_PATH)
        df = pd.read_sql_query("SELECT id, ra, dec FROM events_image WHERE ra IS NOT NULL", conn)
        conn.close()
        
        if len(df) < 5: return [] # Not enough data
        
        # Features: RA, DEC
        X = df[['ra', 'dec']].values
        
        # DBSCAN (eps=1.0 degree approx, min_samples=3)
        db = DBSCAN(eps=1.0, min_samples=3).fit(X)
        labels = db.labels_
        
        # Return summary
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        return {"n_clusters": n_clusters, "noise_points": list(labels).count(-1)}
