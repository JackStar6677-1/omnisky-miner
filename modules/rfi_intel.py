import pandas as pd
import sqlite3
import config

class RFIIntelligence:
    """
    Analyzes RFI patterns to generate exclusion zones and heatmaps.
    """
    
    @staticmethod
    def get_frequency_heatmap():
        """
        Returns a DataFrame of frequency ranges and their RFI density.
        """
        conn = sqlite3.connect(config.DB_PATH)
        # Query known RFI events
        q = """
            SELECT fch1 as freq, bandwidth 
            FROM events_radio 
            WHERE label IN ('RFI', 'INTERFERENCIA_TERRESTRE', 'NOISE')
        """
        try:
            df = pd.read_sql_query(q, conn)
            if df.empty: return None
            
            # Simple histogram for heatmap
            # bin freq into 1MHz buckets
            df['freq_bin'] = df['freq'].round(0)
            counts = df.groupby('freq_bin').size().reset_index(name='count')
            return counts
        except:
            return None
        finally:
            conn.close()

    @staticmethod
    def check_zone(freq_mhz):
        """
        Returns True if freq is in a known heavy RFI zone.
        """
        # Heuristic / Lookup DB
        # E.g. FM Band 88-108
        if 88 <= freq_mhz <= 108: return True
        return False
