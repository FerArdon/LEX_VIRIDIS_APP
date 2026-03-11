"""
Configuration module for LEX VIRIDIS application.

This module provides centralized configuration management with:
- Type safety and validation
- Security best practices
- Environment-aware settings
- Immutable configuration objects
- Comprehensive logging setup
"""

import json
import logging
import logging.handlers
import os
import platform
import sys
import warnings
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Final

# Suppress warnings in production
if not os.getenv("DEBUG"):
    warnings.filterwarnings("ignore")


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
class AppConfig:
    """Main application configuration with immutability and validation."""

    # Application metadata
    APP_NAME: Final[str] = "LEX VIRIDIS"
    APP_VERSION: Final[str] = "3.0.0"

    # Security and database configs
    security: SecurityConfig = field(default_factory=SecurityConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)

    # Environment detection
    IS_FROZEN: Final[bool] = getattr(sys, "frozen", False)
    IS_WINDOWS: Final[bool] = platform.system() == "Windows"
    IS_MACOS: Final[bool] = platform.system() == "Darwin"
    IS_LINUX: Final[bool] = platform.system() == "Linux"

    # Base directories with validation
    @property
    def BASE_DIR(self) -> Path:
        """Get base directory with validation."""
        base = Path(getattr(sys, "_MEIPASS", None) or Path(__file__).parent.parent).resolve()

        if not base.exists():
            raise RuntimeError(f"Base directory does not exist: {base}")
        return base

    @property
    def RESOURCE_DIR(self) -> Path:
        """Resource directory for assets."""
        return self._ensure_dir(self.BASE_DIR / "assets")

    @property
    def DATA_DIR(self) -> Path:
        """Data directory for application data."""
        return self._ensure_dir(self.BASE_DIR / "data")

    @property
    def PDF_DIR(self) -> Path:
        """Directory containing PDF documents. PRIORITY: COMPENDIO LEYES FEMA"""
        # Prioritize exact "COMPENDIO LEYES FEMA" in base dir
        pdf_dir = self.BASE_DIR / "COMPENDIO LEYES FEMA"

        if not pdf_dir.exists():
            # Fallback to underscores if space version missing
            pdf_dir = self.BASE_DIR / "COMPENDIO_LEYES_FEMA"

        return self._ensure_dir(pdf_dir)

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
    def ICON_PATH(self) -> Path | None:
        """Application icon path."""
        # Fix: Icon might not exist, return None or try PNG
        try:
            return self._validate_resource(self.RESOURCE_DIR / "lux_viridis_2.ico")
        except FileNotFoundError:
            try:
                # Fallback to PNG
                return self._validate_resource(self.RESOURCE_DIR / "logo_luxviridis.png")
            except (FileNotFoundError, OSError, AttributeError):
                return None

    @property
    def LOGO_PATH(self) -> Path:
        """Application logo path."""
        return self._validate_resource(self.RESOURCE_DIR / "logo_luxviridis.png")

    def _ensure_dir(self, path: Path) -> Path:
        """Ensure directory exists with proper permissions."""
        try:
            path.mkdir(parents=True, exist_ok=True)
            if self.security.enable_file_permissions and self.IS_WINDOWS:
                # Set appropriate permissions on Windows
                try:
                    os.chmod(path, 0o755)  # nosec B103
                except (OSError, AttributeError):
                    pass  # Ignore permission errors on Windows
            return path
        except Exception as e:
            raise RuntimeError(f"Cannot create directory {path}: {e}") from e

    def _validate_resource(self, path: Path) -> Path:
        """Validate resource file exists."""
        if not path.exists():
            # Try alternative extensions
            for ext in [".png", ".jpg", ".jpeg", ".ico"]:
                alt_path = path.with_suffix(ext)
                if alt_path.exists():
                    return alt_path
            raise FileNotFoundError(f"Required resource not found: {path}")
        return path

    def to_dict(self) -> dict[str, Any]:
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
        self.logger: logging.Logger | None = None

    def setup_logging(self, level: LogLevel = LogLevel.INFO) -> logging.Logger:
        """Configure comprehensive logging with rotation."""
        log_level = getattr(logging, level.value)

        # Ensure log directory
        self.config.LOG_DIR.mkdir(parents=True, exist_ok=True)

        # Create logger
        logger = logging.getLogger(self.config.APP_NAME)
        logger.setLevel(log_level)

        # Clear existing handlers
        logger.handlers.clear()

        # Create formatters
        detailed_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        simple_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

        # File handler with rotation
        log_file = self.config.LOG_DIR / f"lexviridis_{datetime.now():%Y%m%d}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self.config.security.max_log_file_size_mb * 1024 * 1024,
            backupCount=self.config.security.max_log_backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(detailed_formatter)

        # Console handler (only if stdout is available, e.g., not in frozen windowed mode)
        if sys.stdout is not None:
            try:
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setLevel(log_level)
                console_handler.setFormatter(simple_formatter)
                logger.addHandler(console_handler)
            except Exception:
                pass  # Skip console handler in frozen windowed mode

        # Add handlers
        logger.addHandler(file_handler)

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
    "config",
    "logger",
    "logging_manager",
    "AppConfig",
    "SecurityConfig",
    "DatabaseConfig",
    "LogLevel",
    "LoggingManager",
]


# Validation on import
if __name__ == "__main__":
    print(json.dumps(config.to_dict(), indent=2))
    logger.info("Configuration loaded successfully")
