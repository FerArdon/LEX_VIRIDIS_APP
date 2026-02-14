"""
LEX VIRIDIS - Buscador Jurídico Ambiental de Honduras

Un sistema completo de búsqueda y análisis de documentos legales ambientales.
"""

__version__ = "3.0.0"
__author__ = "LEX VIRIDIS Team"

from .config import config
from .ia_gemini import GeminiClient
from .indexer import Indexer
from .search_engine import SearchEngine
from .persistence import SearchCache, SearchHistory, FavoritesManager, AutoBackup

__all__ = [
    'GeminiClient',
    'Indexer',
    'SearchEngine',
    'SearchCache',
    'SearchHistory',
    'FavoritesManager',
    'AutoBackup',
    'config'
]
