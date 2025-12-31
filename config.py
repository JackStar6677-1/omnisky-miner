# Configuración de OmniSky Miner - Versión Observatorio Local (Phase 4: Robust Pipeline)
import os

# MODO DE PRUEBA
TEST_MODE = True

# --- PIPELINE SETTINGS ---
MAX_DOWNLOAD_WORKERS = 10 # Turbo Mode
MAX_ANALYZE_WORKERS = 5
QUEUE_SIZE = 50          
RETRY_ATTEMPTS = 1
BACKOFF_FACTOR = 0.5     # Aggressive retries

# --- FUENTES DE DATOS REALES (Hardcoded) ---
RADIO_SOURCES = [
    "http://blpd1.ssl.berkeley.edu/voyager_2020/sample_data/", 
    "http://blpd0.ssl.berkeley.edu/sample_data/"
]

IMAGE_SOURCES = [ 
    "https://archive-new.nrao.edu/vlass/quicklook/VLASS1.2/" 
]

# --- USER AGENTS PARA ROTACIÓN (Evita bloqueos) ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 10; SM-G960U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Mobile Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/91.0.4472.77 Mobile/15E148 Safari/604.1"
]

# --- RANGOS DE FRECUENCIA IGNORADOS (RFI Conocida) ---
# Formato: (Min MHz, Max MHz, "Descripción")
RFI_RANGES = [
    (88, 108, "FM Radio Broadcast"),
    (870, 960, "GSM Mobile"),
    (1559, 1610, "GPS L1"),
    (2400, 2483.5, "WiFi / Bluetooth")
]

# === LA BÓVEDA (FileSystem) ===
OMNISKY_ROOT = "OMNISKY_DATA"

DIR_TEMP = os.path.join(OMNISKY_ROOT, "TEMP_CACHE")
DIR_NOISE = os.path.join(OMNISKY_ROOT, "HALLAZGOS", "0_RUIDO_FONDO")
DIR_RFI = os.path.join(OMNISKY_ROOT, "HALLAZGOS", "1_INTERFERENCIA_TERRESTRE")
DIR_SAT = os.path.join(OMNISKY_ROOT, "HALLAZGOS", "2_SATELITES_Y_GPS")
DIR_CANDIDATES = os.path.join(OMNISKY_ROOT, "HALLAZGOS", "3_CANDIDATOS_ANOMALOS")
DIR_AUDIO = os.path.join(OMNISKY_ROOT, "HALLAZGOS", "4_AUDIO_DESTACADO")
DIR_VISUAL = os.path.join(OMNISKY_ROOT, "HALLAZGOS", "5_IMAGENES_VISUALES")

# Alias legacy
DIR_OUTPUT = DIR_CANDIDATES

# Base de Datos
DB_PATH = "omnisky.db"
