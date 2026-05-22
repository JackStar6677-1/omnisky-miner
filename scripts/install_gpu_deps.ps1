# install_gpu_deps.ps1
# Auto-detect CUDA capability and install appropriate CuPy package in the virtual environment.

$ErrorActionPreference = "Stop"

Write-Host "🕵️ Detecting GPU and CUDA details..." -ForegroundColor Cyan

# Determine pip path (use active venv if present, otherwise look in local venv folder)
$pipPath = "pip"
if (Test-Path "../venv/Scripts/pip.exe") {
    $pipPath = "../venv/Scripts/pip.exe"
} elseif (Test-Path "venv/Scripts/pip.exe") {
    $pipPath = "venv/Scripts/pip.exe"
}

Write-Host "Using pip path: $pipPath" -ForegroundColor Gray

# 1. Try to find nvidia-smi
$nvismi = $null
if (Get-Command "nvidia-smi" -ErrorAction SilentlyContinue) {
    $nvismi = "nvidia-smi"
} elseif (Test-Path "C:\Program Files\NVIDIA Corporation\NVSMI\nvidia-smi.exe") {
    $nvismi = "C:\Program Files\NVIDIA Corporation\NVSMI\nvidia-smi.exe"
}

$cudaVersion = $null

if ($nvismi) {
    Write-Host "NVIDIA System Management Interface found." -ForegroundColor Gray
    # Run nvidia-smi and extract CUDA Version line
    $smiOut = & $nvismi
    # Match pattern: "CUDA Version: XX.X"
    if ($smiOut -match "CUDA Version:\s+(\d+\.\d+)") {
        $cudaVersion = $Matches[1]
        Write-Host "Detected CUDA Version (from driver): $cudaVersion" -ForegroundColor Green
    }
}

# 2. Try to check nvcc as fallback
if (-not $cudaVersion) {
    if (Get-Command "nvcc" -ErrorAction SilentlyContinue) {
        $nvccOut = nvcc --version
        if ($nvccOut -match "release (\d+\.\d+)") {
            $cudaVersion = $Matches[1]
            Write-Host "Detected CUDA Version (from nvcc): $cudaVersion" -ForegroundColor Green
        }
    }
}

# 3. Check environment variable CUDA_PATH as another fallback
if (-not $cudaVersion -and $env:CUDA_PATH) {
    # CUDA_PATH is usually like C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.1
    if ($env:CUDA_PATH -match "v(\d+\.\d+)") {
        $cudaVersion = $Matches[1]
        Write-Host "Detected CUDA Version (from CUDA_PATH): $cudaVersion" -ForegroundColor Green
    }
}

if (-not $cudaVersion) {
    Write-Warning "No NVIDIA GPU / CUDA driver detected. Skipping CuPy installation."
    Write-Host "System will operate on CPU-only fallback mode using NumPy." -ForegroundColor Yellow
    exit 0
}

# Map CUDA version to CuPy packages
# Modern CuPy supports cupy-cuda12x (for 12.x) and cupy-cuda11x (for 11.x)
$majorVersion = $cudaVersion.Split('.')[0]
$cupyPkg = ""

if ($majorVersion -eq "12") {
    $cupyPkg = "cupy-cuda12x"
} elseif ($majorVersion -eq "11") {
    $cupyPkg = "cupy-cuda11x"
} else {
    # Fallback to standard source/binary wheel
    $cupyPkg = "cupy"
}

Write-Host "Installing $cupyPkg..." -ForegroundColor Cyan
try {
    & $pipPath install $cupyPkg
    Write-Host "✅ Successfully installed $cupyPkg." -ForegroundColor Green
} catch {
    Write-Error "Failed to install $cupyPkg: $_"
}
