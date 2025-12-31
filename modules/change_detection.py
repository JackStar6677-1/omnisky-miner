class ChangeDetector:
    """
    Compare two epochs of data for the same coordinate.
    """
    def compare(self, event_a, event_b):
        # Stub logic
        # Real logic: Load FITS A and B, subtract pixels, calculate std dev of residual.
        
        # Mock Metrics
        return {
            "delta_flux": 0.12,
            "structural_sim": 0.85,
            "label": "STABLE"
        }
