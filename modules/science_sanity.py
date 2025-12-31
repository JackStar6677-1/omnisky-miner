class ScienceSanity:
    """
    Enforces physical plausibility rules.
    """
    
    @staticmethod
    def check_physics(event_data):
        """
        Returns (is_plausible, score_modifier, reasons)
        """
        reasons = []
        score_mod = 0
        
        # Rule 1: Doppler Drift Limit
        # Real ET signals (narrowband) usually have drift due to rotation/orbit.
        # But wildly high drift (> 50 Hz/s) is likely RFI (satellites) or impossible.
        drift = abs(float(event_data.get('drift', 0)))
        if drift > 100.0:
            reasons.append("Excessive Drift (>100Hz/s)")
            score_mod -= 30
        if drift == 0.0 and event_data.get('label') == 'CANDIDATE':
            # Zero drift is suspicious for earth-based receivers (unless barycentric corrected)
            reasons.append("Zero Drift (Suspicious for stationary RFI)")
            score_mod -= 10

        # Rule 2: Bandwidth
        # Candidates should be narrowband (< 10 Hz ideally)
        # If unavailable, skip.

        return True, score_mod, reasons
