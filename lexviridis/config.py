"""
Configuration module for LEX VIRIDIS application.

This module provides centralized configuration management with:
- Type safety and validation
- Security best practices
- Environment-aware settings
- Immutable configuration objects
- Comprehensive logging setup
"""

import os
import sys
import platform
from pathlib import Path
from datetime import datetime
from typing import Final, Optional, Dict, Any
import logging
import logging.handlers
import json
from dataclasses import dataclass, field
from enum import Enum
import warnings

# Suppress warnings in production
if not os.getenv('DEBUG'):
    warnings.filterwarnings('ignore')


class LogLevel(Enum):
    """Standard logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class SecurityConfig:
    """Security-related configuration."""
    enable_file_permissions: bool = True
    max_log_file_size_mb: int = 10
    max_log_backup_count: int = 5
    sanitize_paths: bool = True


@dataclass(frozen=True)
class DatabaseConfig:
    """Database and storage configuration."""
    index_version: str = "1.1"
    cache_ttl_seconds: int = 3600
    backup_retention_days: int = 30
    compression_enabled: bool = True


@dataclass(frozen=True)
class LocaleConfig:
    """Configuración de localización y formato (Reglas de Fer)."""
    THOUSANDS_SEPARATOR: str = ","
    DECIMAL_SEPARATOR: str = "."
    CURRENCY_DECIMALS: int = 2
    DATE_FORMAT: str = "%d/%m/%Y"


@dataclass(frozen=True)
class AppConfig:
    """Main application configuration with immutability and validation."""
    
    # Application metadata
    APP_NAME: Final[str] = "LEX VIRIDIS"
    APP_VERSION: Final[str] = "3.2.0.2026"
    
    # Security, database and locale configs
    security: SecurityConfig = field(default_factory=SecurityConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    locale: LocaleConfig = field(default_factory=LocaleConfig)
    
    # Environment detection
    IS_FROZEN: Final[bool] = getattr(sys, 'frozen', False)
    IS_WINDOWS: Final[bool] = platform.system() == "Windows"
    IS_MACOS: Final[bool] = platform.system() == "Darwin"
    IS_LINUX: Final[bool] = platform.system() == "Linux"
    
    # Base directories with validation
    @property
    def BASE_DIR(self) -> Path:
        """Get base directory with validation and logging."""
        base = Path(
            sys._MEIPASS if self.IS_FROZEN
            else Path(__file__).parent.parent
        ).resolve()

        if not base.exists():
            raise RuntimeError(f"Base directory does not exist: {base}")

        return base

    @property
    def INSTALL_DIR(self) -> Path:
        """Directorio de instalación: junto al .exe cuando frozen, o BASE_DIR en dev.
        Inno Setup instala la BD y los PDFs aquí, no dentro de _internal."""
        if self.IS_FROZEN:
            return Path(sys.executable).parent.resolve()
        return self.BASE_DIR
    
    @property
    def RESOURCE_DIR(self) -> Path:
        """Resource directory for assets."""
        return self._ensure_dir(self.BASE_DIR / "assets")
    
    @property
    def DATA_DIR(self) -> Path:
        """Data directory for application data. Uses %APPDATA% in frozen Windows mode."""
        if self.IS_WINDOWS and self.IS_FROZEN:
            # Use %APPDATA% for persistence when installed to avoid Disk I/O errors in read-only locations
            appdata = os.environ.get('APPDATA')
            if appdata:
                return self._ensure_dir(Path(appdata) / "LEX VIRIDIS" / "data")
        
        return self._ensure_dir(self.BASE_DIR / "data")
    
    @property
    def PDF_DIR(self) -> Path:
        """Directory containing PDF documents. PRIORITY: COMPENDIO LEYES FEMA"""
        # Los PDFs los instala Inno Setup junto al exe (INSTALL_DIR)
        pdf_dir = self.INSTALL_DIR / "COMPENDIO LEYES FEMA"

        if not pdf_dir.exists():
            pdf_dir = self.INSTALL_DIR / "COMPENDIO_LEYES_FEMA"

        return self._ensure_dir(pdf_dir)
    
    def get_pdf_absolute_path(self, filename: str) -> Optional[Path]:
        """Obtiene la ruta absoluta de un PDF con fallback inteligente de 4 niveles."""
        if not filename or filename == "Desconocido":
            return None

        # 1. Ruta exacta (nombre base, por si viene con prefijo de carpeta)
        base_name = Path(filename).name
        full_path = self.PDF_DIR / base_name
        if full_path.exists():
            return full_path

        if not self.PDF_DIR.exists():
            return None

        files_in_dir = [f.name for f in self.PDF_DIR.iterdir()
                        if f.is_file() and f.suffix.lower() == '.pdf']

        # 2. Coincidencia exacta ignorando mayúsculas
        base_lower = base_name.lower()
        for f in files_in_dir:
            if f.lower() == base_lower:
                return self.PDF_DIR / f

        # 3. Fuzzy match con cutoff reducido (0.55) para cubrir renombrados con prefijos numéricos
        import difflib
        matches = difflib.get_close_matches(base_name, files_in_dir, n=1, cutoff=0.55)
        if matches:
            return self.PDF_DIR / matches[0]

        # 4. Búsqueda por palabras clave: todas las palabras significativas del nombre deben estar
        #    presentes en el nombre del archivo real (insensible a mayúsculas/tildes)
        import unicodedata
        def _norm(s):
            return unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode().lower()

        # Extraer palabras de ≥4 letras del nombre buscado
        import re
        keywords = [w for w in re.split(r'[\s\-_\.]+', _norm(base_name)) if len(w) >= 4]
        if keywords:
            best_match = None
            best_score = 0
            for f in files_in_dir:
                f_norm = _norm(f)
                hits = sum(1 for kw in keywords if kw in f_norm)
                score = hits / len(keywords)
                if score > best_score:
                    best_score = score
                    best_match = f
            # Aceptar si al menos 60% de las palabras clave coinciden
            if best_match and best_score >= 0.6:
                return self.PDF_DIR / best_match

        return None
    
    @property
    def LOG_DIR(self) -> Path:
        """Log directory outside OneDrive to avoid sync-blocking."""
        import tempfile
        log_dir = Path(tempfile.gettempdir()) / "LEX_VIRIDIS" / "logs"
        return self._ensure_dir(log_dir)
    
    # Subdirectories
    @property
    def INDEX_DIR(self) -> Path:
        """Search index directory."""
        return self._ensure_dir(self.DATA_DIR / "index")
    
    @property
    def CACHE_DIR(self) -> Path:
        """Cache directory for temporary data."""
        return self._ensure_dir(self.DATA_DIR / "cache")
    
    @property
    def BACKUP_DIR(self) -> Path:
        """Backup directory for data protection."""
        return self._ensure_dir(self.DATA_DIR / "backups")

    @property
    def EXPORT_DIR(self) -> Path:
        """Directory for user-generated exports (PDF, Excel, TXT).
        Uses Documents folder on frozen Windows builds; BASE_DIR/exports in dev."""
        if self.IS_WINDOWS and self.IS_FROZEN:
            docs = Path.home() / "Documents" / "LEX VIRIDIS" / "Exportaciones"
        else:
            docs = self.BASE_DIR / "exports"
        return self._ensure_dir(docs)

    @property
    def SEED_DB_DIR(self) -> Path:
        """BD semilla instalada junto al .exe (puede ser de solo lectura en Program Files)."""
        return self.INSTALL_DIR / "LEX_VIRIDIS_DB"

    @property
    def DB_DIR(self) -> Path:
        """Directorio operativo de la BD SQLite — AppData cuando instalado (writable), BASE_DIR en dev."""
        if self.IS_WINDOWS and self.IS_FROZEN:
            appdata = os.environ.get('APPDATA')
            if appdata:
                return self._ensure_dir(Path(appdata) / "LEX VIRIDIS" / "db")
        return self.INSTALL_DIR / "LEX_VIRIDIS_DB"

    @property
    def API_KEY_FILE(self) -> Path:
        """File to persist the Gemini API key."""
        return self.DATA_DIR / "api_key.json"
    
    # File paths
    @property
    def INDEX_FILE(self) -> Path:
        """Search index file path."""
        return self.INDEX_DIR / f"text_index_v{self.database.index_version}.pkl"
    
    @property
    def CACHE_FILE(self) -> Path:
        """Cache file path."""
        return self.CACHE_DIR / f"search_cache_v{self.database.index_version}.json"
    
    @property
    def HISTORY_FILE(self) -> Path:
        """Search history file path."""
        return self.DATA_DIR / f"search_history_v{self.database.index_version}.json"
    
    @property
    def FAVORITES_FILE(self) -> Path:
        """Favorites file path."""
        return self.DATA_DIR / f"favorites_v{self.database.index_version}.json"
    
    @property
    def ICON_PATH(self) -> Optional[Path]:
        """Application icon path."""
        try:
            return self._validate_resource(self.RESOURCE_DIR / "LEXVIRIDIS_WHITE_BG.ico")
        except FileNotFoundError:
            try:
                # Fallback to PNG
                return self._validate_resource(self.RESOURCE_DIR / "LEXVIRIDIS_WHITE_BG.png")
            except FileNotFoundError:
                return None
    
    @property
    def LOGO_PATH(self) -> Path:
        """Application logo path."""
        return self._validate_resource(self.RESOURCE_DIR / "LEXVIRIDIS_WHITE_BG.png")
    
    def _ensure_dir(self, path: Path) -> Path:
        """Ensure directory exists with proper permissions."""
        try:
            path.mkdir(parents=True, exist_ok=True)
            if self.security.enable_file_permissions and self.IS_WINDOWS:
                # Set appropriate permissions on Windows
                try:
                    os.chmod(path, 0o755)
                except (OSError, AttributeError):
                    pass  # Ignore permission errors on Windows
            return path
        except Exception as e:
            raise RuntimeError(f"Cannot create directory {path}: {e}")
    
    def _validate_resource(self, path: Path) -> Path:
        """Validate resource file exists."""
        if not path.exists():
            # Try alternative extensions
            for ext in ['.png', '.jpg', '.jpeg', '.ico']:
                alt_path = path.with_suffix(ext)
                if alt_path.exists():
                    return alt_path
            raise FileNotFoundError(f"Required resource not found: {path}")
        return path
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for debugging."""
        return {
            "app_name": self.APP_NAME,
            "app_version": self.APP_VERSION,
            "base_dir": str(self.BASE_DIR),
            "data_dir": str(self.DATA_DIR),
            "pdf_dir": str(self.PDF_DIR),
            "log_dir": str(self.LOG_DIR),
            "frozen": self.IS_FROZEN,
            "platform": platform.system(),
            "index_version": self.database.index_version,
        }


class LoggingManager:
    """Advanced logging manager with rotation and security."""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.logger = None
    
    def setup_logging(self, level: LogLevel = LogLevel.INFO) -> logging.Logger:
        """Configure comprehensive logging with rotation."""
        log_level = getattr(logging, level.value)
        
        # Ensure log directory
        self.config.LOG_DIR.mkdir(parents=True, exist_ok=True)
        
        # Configurar el logger raíz de la jerarquía "lexviridis.*"
        # para que search, ai, security, pdf, etc. propaguen aquí.
        root_lv = logging.getLogger("lexviridis")
        root_lv.setLevel(log_level)

        # Logger principal de la app (para compatibilidad con código existente)
        logger = logging.getLogger(self.config.APP_NAME)
        logger.setLevel(log_level)

        # Clear existing handlers
        logger.handlers.clear()
        root_lv.handlers.clear()
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handler with rotation
        log_file = self.config.LOG_DIR / f"lexviridis_{datetime.now():%Y%m%d}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self.config.security.max_log_file_size_mb * 1024 * 1024,
            backupCount=self.config.security.max_log_backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(detailed_formatter)
        
        # Console handler — forzar UTF-8 para que emojis no rompan en Windows (cp1252)
        import io
        safe_stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace') \
            if hasattr(sys.stdout, 'buffer') else sys.stdout
        console_handler = logging.StreamHandler(safe_stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(simple_formatter)
        
        # Add handlers al logger principal y al raíz "lexviridis"
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        root_lv.addHandler(file_handler)
        root_lv.addHandler(console_handler)
        
        # Log startup
        logger.info("=" * 60)
        logger.info(f"{self.config.APP_NAME} v{self.config.APP_VERSION} Started")
        logger.info(f"Platform: {platform.system()} {platform.release()}")
        logger.info(f"Python: {platform.python_version()}")
        logger.info(f"Base Directory: {self.config.BASE_DIR}")
        logger.info("=" * 60)
        
        self.logger = logger
        return logger
    
    def get_logger(self, name: str = None) -> logging.Logger:
        """Get a named logger."""
        if name:
            return logging.getLogger(f"{self.config.APP_NAME}.{name}")
        return self.logger or logging.getLogger(self.config.APP_NAME)


# Global configuration instance
config = AppConfig()

# Initialize logging
logging_manager = LoggingManager(config)
logger = logging_manager.setup_logging()

# Export commonly used items
__all__ = [
    'config',
    'logger',
    'logging_manager',
    'AppConfig',
    'SecurityConfig',
    'DatabaseConfig',
    'LogLevel',
    'LoggingManager'
]


# Validation on import
if __name__ == "__main__":
    print(json.dumps(config.to_dict(), indent=2))
    logger.info("Configuration loaded successfully")
