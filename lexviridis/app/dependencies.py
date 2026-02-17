import logging
import threading

from ..analytics import AnalyticsTracker
from ..config import config
from ..ia_gemini import GeminiClient
from ..notifications import NotificationManager
from ..search_engine import SearchEngine
from ..security import AuthManager

# Import services and repositories
from ..services.library_repository import LibraryRepository
from ..services.stats_repository import StatsRepository
from ..repositories.casos_repository import CasosRepository


class DependencyContainer:
    """
    DI Container to manage shared services and repositories.
    Singleton-like behavior for the application lifecycle.
    Thread-safe initialization.
    """
    def __init__(self, page=None):
        self.page = page
        self._lock = threading.Lock()
        self._initialized = False
        self.db_manager = None
        self.library_repo = None
        self.stats_repo = None
        self.casos_repo = None
        self.search_engine = None
        self.auth_manager = None
        self.gemini_client = None
        self.analytics = None
        self.notifications = None

    def initialize(self):
        """Initializes all dependencies in a thread-safe manner."""
        with self._lock:
            if self._initialized:
                logging.info("Dependencies already initialized, skipping...")
                return

            logging.info("Initializing DependencyContainer...")

        # 1. Search Engine & DB (Core)
        self.search_engine = SearchEngine()
        self.db_manager = self.search_engine.db_manager

        # 2. Repositories
        self.library_repo = LibraryRepository(self.db_manager)
        self.stats_repo = StatsRepository(self.db_manager)
        db_casos_path = config.BASE_DIR / "LEX_VIRIDIS_DB" / "legislacion_ambiental.db"
        self.casos_repo = CasosRepository(db_casos_path)


        # 3. Services
        from ..accessibility import AccessibilityManager
        from ..ai_assistant import LegalAIAssistant
        from ..backup_manager import BackupManager
        from ..cloud_sync import CloudSync
        from ..proactive_assistant import ProactiveSuggestions, UserBehaviorAnalyzer
        from ..theme_manager import ThemeManager

        self.auth_manager = AuthManager(self.db_manager)
        self.gemini_client = GeminiClient()
        self.ai_assistant = LegalAIAssistant(self.search_engine, self.gemini_client)
        self.analytics = AnalyticsTracker(self.db_manager)
        self.notifications = NotificationManager(self.db_manager)

        # Additional Services for Settings & UI
        db_path = config.BASE_DIR / "LEX_VIRIDIS_DB" / "legislacion_ambiental.db"
        self.backup_manager = BackupManager(db_path)
        self.cloud_sync = CloudSync(self.db_manager)

        # UI Services (require page)
        if self.page:
            self.theme_manager = ThemeManager(self.page)
            self.accessibility = AccessibilityManager(self.page)
        else:
            self.theme_manager = None
            self.accessibility = None

        # Proactive Assistant
        self.analyzer = UserBehaviorAnalyzer(self.db_manager)
        self.proactive = ProactiveSuggestions(self.analyzer)

        # Study System
        from ..study_system import StudyManager
        self.study_manager = StudyManager(self.db_manager)

        self._initialized = True
        logging.info("Dependencies initialized successfully.")

    def get_library_repository(self) -> LibraryRepository:
        if not self.library_repo: self.initialize()
        return self.library_repo

    def get_stats_repository(self) -> StatsRepository:
        if not self.stats_repo: self.initialize()
        return self.stats_repo
