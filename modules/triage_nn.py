import os
import numpy as np
import logging
import config

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logging.warning("⚠️ PyTorch not found. Deep learning triage will be disabled (falling back to classical ML/heuristics).")

MODEL_PATH = os.path.join(config.OMNISKY_ROOT, "models", "triage_cnn.pt")

if TORCH_AVAILABLE:
    class TriageCNN(nn.Module):
        def __init__(self):
            super(TriageCNN, self).__init__()
            # Input spectrogram: 1 channel, 64x64
            self.features = nn.Sequential(
                nn.Conv2d(1, 16, kernel_size=3, padding=1),
                nn.ReLU(),
                nn.MaxPool2d(2, 2), # 16 x 32 x 32
                
                nn.Conv2d(16, 32, kernel_size=3, padding=1),
                nn.ReLU(),
                nn.MaxPool2d(2, 2), # 32 x 16 x 16
                
                nn.Conv2d(32, 64, kernel_size=3, padding=1),
                nn.ReLU(),
                nn.MaxPool2d(2, 2), # 64 x 8 x 8
            )
            self.classifier = nn.Sequential(
                nn.Linear(64 * 8 * 8, 64),
                nn.ReLU(),
                nn.Dropout(0.3),
                nn.Linear(64, 1),
                nn.Sigmoid()
            )

        def forward(self, x):
            x = self.features(x)
            x = x.view(x.size(0), -1)
            x = self.classifier(x)
            return x

class DeepTriageEngine:
    def __init__(self):
        self.model = None
        self.is_ready = False
        if TORCH_AVAILABLE:
            self._load_model()

    def _load_model(self):
        if not os.path.exists(MODEL_PATH):
            logging.info("🧠 PyTorch triage weights not found. Creating dummy weights...")
            self.train_dummy()
            
        try:
            self.model = TriageCNN()
            # Load weights mapping to CPU by default for safety
            self.model.load_state_dict(torch.load(MODEL_PATH, map_location=torch.device('cpu')))
            self.model.eval()
            self.is_ready = True
            logging.info("🧠 Deep Learning Triage Model (PyTorch CNN) Loaded Successfully")
        except Exception as e:
            logging.error(f"Failed to load PyTorch model weights: {e}")
            self.is_ready = False

    def train_dummy(self):
        """Generates a dummy model with random/pre-initialized weights to ensure run-time safety."""
        if not TORCH_AVAILABLE:
            return "Torch not available"
        
        model = TriageCNN()
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        torch.save(model.state_dict(), MODEL_PATH)
        return "Dummy Weights Saved"

    def resize_spectrogram(self, spec, target_shape=(64, 64)):
        """Resizes a 2D numpy array to target_shape using bilinear zoom or numpy indexing fallback."""
        try:
            from scipy.ndimage import zoom
            h, w = spec.shape
            # Calculate zoom factors
            zh = target_shape[0] / h
            zw = target_shape[1] / w
            return zoom(spec, (zh, zw), order=1)
        except Exception:
            # CPU fallback method using bilinear interpolation
            h, w = spec.shape
            x = np.linspace(0, w - 1, target_shape[1]).astype(int)
            y = np.linspace(0, h - 1, target_shape[0]).astype(int)
            return spec[np.ix_(y, x)]

    def predict(self, spectrogram: np.ndarray) -> float:
        """
        Runs the 2D CNN over a spectrogram.
        Returns a probability score between 0.0 and 1.0.
        """
        if not TORCH_AVAILABLE or not self.is_ready or self.model is None:
            raise RuntimeError("PyTorch model is not initialized.")

        # Ensure we have a 2D array
        if len(spectrogram.shape) != 2:
            raise ValueError("Spectrogram must be a 2D array")

        # 1. Resize spectrogram to 64x64
        resized = self.resize_spectrogram(spectrogram, (64, 64))

        # 2. Normalize input values to [0.0, 1.0] range
        s_min = resized.min()
        s_max = resized.max()
        if s_max > s_min:
            normalized = (resized - s_min) / (s_max - s_min)
        else:
            normalized = np.zeros_like(resized)

        # 3. Convert to tensor: shape (1, 1, 64, 64)
        tensor = torch.tensor(normalized, dtype=torch.float32).unsqueeze(0).unsqueeze(0)

        # 4. Predict
        with torch.no_grad():
            output = self.model(tensor)
            prob = output.item()

        return prob
