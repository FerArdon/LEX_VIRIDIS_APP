"""
Constantes centralizadas para LEX VIRIDIS.
Evita números mágicos dispersos en el código.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class UIConstants:
    """Constantes de interfaz de usuario."""

    # Window dimensions
    MIN_WINDOW_WIDTH: int = 900
    MIN_WINDOW_HEIGHT: int = 650
    LOGIN_WINDOW_WIDTH: int = 450
    LOGIN_WINDOW_HEIGHT: int = 600

    # Timeouts (milliseconds)
    SNACKBAR_DURATION: int = 3000
    DEBOUNCE_SEARCH: int = 500
    AUTO_SAVE_INTERVAL: int = 30000

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # Cache
    MAX_CACHE_SIZE: int = 100
    MAX_HISTORY_SIZE: int = 50
    MAX_BACKUPS: int = 10

    # Search
    MIN_QUERY_LENGTH: int = 2
    MAX_QUERY_LENGTH: int = 500

    # PDF
    PDF_DPI: int = 150
    PDF_MAX_PAGES_PREVIEW: int = 5

    # Study System
    FLASHCARD_MIN_INTERVAL_DAYS: int = 1
    FLASHCARD_MAX_INTERVAL_DAYS: int = 365
    QUIZ_DEFAULT_QUESTIONS: int = 10


@dataclass(frozen=True)
class APIConstants:
    """Constantes para APIs y servicios externos."""

    # Gemini API
    GEMINI_MODEL: str = "gemini-1.5-flash"
    GEMINI_TEMPERATURE: float = 0.7
    GEMINI_MAX_TOKENS: int = 2048
    GEMINI_TIMEOUT: int = 30

    # Database
    DB_TIMEOUT: int = 10
    DB_POOL_SIZE: int = 5

    # Security
    PBKDF2_ITERATIONS: int = 600_000
    SESSION_EXPIRY_DAYS: int = 30
    PASSWORD_MIN_LENGTH: int = 8

    # File handling
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_PDF_EXTENSIONS: tuple = (".pdf",)
    ALLOWED_IMAGE_EXTENSIONS: tuple = (".png", ".jpg", ".jpeg", ".gif")


@dataclass(frozen=True)
class AppMetadata:
    """Metadatos de la aplicación."""

    APP_NAME: str = "LEX VIRIDIS"
    APP_VERSION: str = "2.0.0"
    APP_AUTHOR: str = "FEMA - Fiscalía Especial del Medio Ambiente"
    APP_DESCRIPTION: str = "Compendio Legal Ambiental de Honduras"
    APP_LICENSE: str = "Proprietary"

    # Support
    SUPPORT_EMAIL: str = "soporte@lexviridis.hn"
    DOCS_URL: str = "https://lexviridis.hn/docs"


# Instancias globales (singleton pattern)
UI = UIConstants()
API = APIConstants()
META = AppMetadata()
