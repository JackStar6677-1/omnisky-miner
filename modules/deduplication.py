import hashlib
import logging

class DeduplicationEngine:
    """
    Computes fuzzy signatures for events to group them into 'Families'.
    """
    
    @staticmethod
    def compute_signature(event_type: str, metadata: dict) -> str:
        """
        Generates a deterministic hash for an event based on its physical properties.
        """
        try:
            if event_type == "RADIO":
                # Factors: Object Name, Approx Frequency, Drift
                obj = str(metadata.get("object_name", "UNKNOWN")).strip().upper()
                
                # Round frequency to nearest 0.1 MHz to group variances
                freq = float(metadata.get("frequency", 0))
                freq_bucket = round(freq, 1)
                
                # Drift bucket (if significant)
                drift = float(metadata.get("drift", 0))
                drift_bucket = round(drift, 1)
                
                raw_sig = f"{obj}|{freq_bucket}|{drift_bucket}"
                return hashlib.sha1(raw_sig.encode()).hexdigest()
                
            elif event_type == "IMAGE":
                # Factors: RA/DEC rounded (approx 1 arcmin?), Epoch
                ra = float(metadata.get("ra", 0))
                dec = float(metadata.get("dec", 0))
                
                # Round to 2 decimals (approx 0.01 deg)
                ra_bucket = round(ra, 2)
                dec_bucket = round(dec, 2)
                
                epoch = str(metadata.get("epoch", "UNKNOWN"))
                
                raw_sig = f"{ra_bucket}|{dec_bucket}|{epoch}"
                return hashlib.sha1(raw_sig.encode()).hexdigest()
                
            return hashlib.sha1(str(metadata).encode()).hexdigest()
            
        except Exception as e:
            logging.error(f"Dedupe Sig Error: {e}")
            return "UNKNOWN_SIG"
