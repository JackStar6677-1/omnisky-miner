import time
import numpy as np
import os
import sys

# Ensure modules in path
sys.path.append(os.getcwd())
import config

def benchmark():
    print("🚀 OmniSky Compute Benchmark")
    print("----------------------------")
    
    # 1. Force CPU Run
    print("1. Testing CPU (NumPy)...")
    config.USE_GPU = False
    from modules import compute_backend as cb
    cb.init_backend()
    
    start = time.time()
    cpu_res = run_heavy_op(cb.get_xp())
    cpu_time = time.time() - start
    print(f"   ⏱️ CPU Time: {cpu_time:.4f}s")
    
    # 2. Force GPU Run
    print("\n2. Testing GPU (CuPy)...")
    config.USE_GPU = True
    config.GPU_BACKEND = "cupy"
    
    # Reload backend
    import importlib
    importlib.reload(cb)
    cb.init_backend()
    
    if not cb.is_gpu_enabled():
        print("   ❌ GPU Not Available (CuPy not installed or no CUDA). Skipping.")
        return

    start = time.time()
    gpu_res = run_heavy_op(cb.get_xp())
    
    # Synchronization for fair timing
    cb.get_xp().cuda.Device(0).synchronize()
    gpu_time = time.time() - start
    print(f"   ⏱️ GPU Time: {gpu_time:.4f}s")
    
    speedup = cpu_time / gpu_time
    print(f"\n⚡ Speedup Factor: {speedup:.2f}x")
    if speedup > 1.0:
        print("✅ GPU Acceleration is WORKING.")
    else:
        print("⚠️ GPU was slower (overhead?) or dataset too small.")

def run_heavy_op(xp):
    """
    Simulates a heavy pipeline op:
    3x Large Matrix Mul + FFT + Thresholding
    """
    # 4000x4000 float32 matrix (~64MB)
    size = 4000 
    a = xp.random.rand(size, size).astype(xp.float32)
    b = xp.random.rand(size, size).astype(xp.float32)
    
    # Heavy Ops
    c = xp.matmul(a, b) # Matrix Mul
    d = xp.fft.fft2(c[:1000, :1000]) # FFT on subset
    thresh = xp.mean(xp.abs(d))
    
    return thresh

if __name__ == "__main__":
    benchmark()
