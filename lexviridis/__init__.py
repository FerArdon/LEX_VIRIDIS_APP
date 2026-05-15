"""
LEX VIRIDIS - Buscador Jurídico Ambiental de Honduras

Un sistema completo de búsqueda y análisis de documentos legales ambientales.
"""

__version__ = "3.0.0"
__author__ = "LEX VIRIDIS Team"

from .config import config
from .search_engine import SearchEngine
from .ai_assistant import LegalAIAssistant, GeminiClient
from .security import AuthManager, EncryptionManager

__all__ = [
    'config',
    'SearchEngine',
    'LegalAIAssistant',
    'GeminiClient',
    'AuthManager',
    'EncryptionManager'
]
