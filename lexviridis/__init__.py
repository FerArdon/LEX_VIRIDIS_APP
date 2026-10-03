"""
LEX VIRIDIS - Buscador Jurídico Ambiental de Honduras

Un sistema completo de búsqueda y análisis de documentos legales ambientales.
"""

__version__ = "3.0.0"
__author__ = "LEX VIRIDIS Team"

# Restaura la API antigua de Flet (dialog, snack_bar, FilePicker.on_result) sobre Flet >= 0.80
from . import flet_compat  # noqa: F401
from .config import config
from .ia_gemini import GeminiClient
from .indexer import Indexer
from .persistence import AutoBackup, FavoritesManager, SearchCache, SearchHistory
from .search_engine import SearchEngine

__all__ = [
    "GeminiClient",
    "Indexer",
    "SearchEngine",
    "SearchCache",
    "SearchHistory",
    "FavoritesManager",
    "AutoBackup",
    "config",
]
