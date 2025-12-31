from .base import Detector

class HeuristicDetector(Detector):
    @property
    def name(self):
        return "HEURISTIC"

    def detect(self, event_data):
        score = 0
        snr = float(event_data.get('snr', 0) or event_data.get('sigma', 0))
        drift = abs(float(event_data.get('drift', 0)))
        
        if snr > 10: score += 50
        if snr > 50: score += 30
        if 0.1 < drift < 2.0: score += 20
        
        label = "CANDIDATE" if score > 60 else "NOISE"
        return {"score": score, "label": label, "metadata": {}}
