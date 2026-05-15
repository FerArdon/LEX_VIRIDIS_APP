"""
Configuración de LEX VIRIDIS
"""
from pathlib import Path
import os

# === PATHS ===
BASE_DIR = Path(__file__).parent
DB_DIR = BASE_DIR / "LEX_VIRIDIS_DB"
DB_PATH = DB_DIR / "legislacion_ambiental.db"
LOGS_DIR = BASE_DIR / "logs"
ASSETS_DIR = BASE_DIR / "assets"

# Crear directorios
DB_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# === APP ===
APP_NAME = "LEX VIRIDIS"
APP_VERSION = "3.0.0"
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900

# === THEME ===
PRIMARY_COLOR = "#1B5E20"  # Verde legal
SECONDARY_COLOR = "#0D47A1"  # Azul institucional
ACCENT_COLOR = "#F9A825"  # Dorado

# === SEARCH ===
MIN_QUERY_LENGTH = 2
MAX_QUERY_LENGTH = 200
DEFAULT_PAGE_SIZE = 20
CACHE_SIZE = 100

# === LOGGING ===
LOG_LEVEL = "INFO"
LOG_FILE = LOGS_DIR / "lexviridis.log"
