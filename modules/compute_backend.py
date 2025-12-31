import logging
import numpy as np
import config

# Global backend reference
xp = np
_backend_name = "numpy"

def init_backend():
    """
    Initializes the compute backend based on config.py.
    Tries to load CuPy if configured; falls back to NumPy.
    """
    global xp, _backend_name
    
    if not config.USE_GPU:
        logging.info("🖥️ Compute Backend: Forced CPU (NumPy).")
        return

    if config.GPU_BACKEND == "cupy":
        try:
            import cupy as cp
            # Simple check to see if CUDA device is accessible
            cp.cuda.Device(0).compute_capability
            xp = cp
            _backend_name = "cupy"
            logging.info(f"🚀 Compute Backend: GPU Activated ({xp.__name__})")
        except ImportError:
            logging.warning("⚠️ Compute Backend: CuPy not found. Installing 'cupy-cuda12x' is recommended for RTX 4060. Falling back to CPU.")
            xp = np
        except Exception as e:
            logging.warning(f"⚠️ Compute Backend: GPU Init failed ({e}). Falling back to CPU.")
            xp = np
    
    else:
        logging.info(f"Compute Backend: Unknown backend '{config.GPU_BACKEND}'. Using NumPy.")

def get_xp():
    """Returns the active array module (numpy or cupy)."""
    return xp

def to_cpu(array):
    """Safely converts array/tensor to NumPy (CPU)."""
    if _backend_name == "cupy" and hasattr(array, 'device'):
        return xp.asnumpy(array)
    return array

def to_gpu(array):
    """Moves array to GPU if backend is active."""
    if _backend_name == "cupy":
        return xp.asarray(array)
    return array

def is_gpu_enabled():
    return _backend_name == "cupy"

# Auto-init on module import
init_backend()
