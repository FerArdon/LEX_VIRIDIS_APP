"""
Pruebas del modulo de configuracion (config.py).
Cubre: AppConfig, SecurityConfig, DatabaseConfig, LoggingManager.
"""

import pytest
from pathlib import Path
from dataclasses import FrozenInstanceError

from lexviridis.config import (
    AppConfig,
    SecurityConfig,
    DatabaseConfig,
    LogLevel,
    LoggingManager,
)


class TestSecurityConfig:

    def test_default_values(self):
        sc = SecurityConfig()
        assert sc.enable_file_permissions is True
        assert sc.max_log_file_size_mb == 10
        assert sc.max_log_backup_count == 5
        assert sc.sanitize_paths is True

    def test_is_frozen(self):
        sc = SecurityConfig()
        with pytest.raises(FrozenInstanceError):
            sc.max_log_file_size_mb = 999


class TestDatabaseConfig:

    def test_default_values(self):
        dc = DatabaseConfig()
        assert dc.index_version == "1.1"
        assert dc.cache_ttl_seconds == 3600
        assert dc.backup_retention_days == 30
        assert dc.compression_enabled is True

    def test_is_frozen(self):
        dc = DatabaseConfig()
        with pytest.raises(FrozenInstanceError):
            dc.index_version = "9.9"


class TestAppConfig:

    def test_app_metadata(self):
        cfg = AppConfig()
        assert cfg.APP_NAME == "LEX VIRIDIS"
        assert cfg.APP_VERSION == "3.0.0"

    def test_nested_configs(self):
        cfg = AppConfig()
        assert isinstance(cfg.security, SecurityConfig)
        assert isinstance(cfg.database, DatabaseConfig)

    def test_base_dir_exists(self):
        cfg = AppConfig()
        assert cfg.BASE_DIR.exists()
        assert cfg.BASE_DIR.is_dir()

    def test_data_dir_created(self):
        cfg = AppConfig()
        data_dir = cfg.DATA_DIR
        assert data_dir.exists()

    def test_log_dir_created(self):
        cfg = AppConfig()
        log_dir = cfg.LOG_DIR
        assert log_dir.exists()

    def test_to_dict_has_required_keys(self):
        cfg = AppConfig()
        d = cfg.to_dict()
        assert "app_name" in d
        assert "app_version" in d
        assert "base_dir" in d
        assert "platform" in d
        assert "index_version" in d

    def test_to_dict_values_are_strings(self):
        cfg = AppConfig()
        d = cfg.to_dict()
        for key, value in d.items():
            assert isinstance(value, (str, bool)), f"Clave '{key}' no es str/bool: {type(value)}"

    def test_index_file_path_includes_version(self):
        cfg = AppConfig()
        assert cfg.database.index_version in cfg.INDEX_FILE.name

    def test_cache_file_path_includes_version(self):
        cfg = AppConfig()
        assert cfg.database.index_version in cfg.CACHE_FILE.name


class TestLogLevel:

    def test_all_levels_exist(self):
        assert LogLevel.DEBUG.value == "DEBUG"
        assert LogLevel.INFO.value == "INFO"
        assert LogLevel.WARNING.value == "WARNING"
        assert LogLevel.ERROR.value == "ERROR"
        assert LogLevel.CRITICAL.value == "CRITICAL"


class TestLoggingManager:

    def test_setup_logging_returns_logger(self):
        cfg = AppConfig()
        manager = LoggingManager(cfg)
        logger = manager.setup_logging(LogLevel.DEBUG)
        assert logger is not None
        assert logger.name == cfg.APP_NAME

    def test_get_named_logger(self):
        cfg = AppConfig()
        manager = LoggingManager(cfg)
        manager.setup_logging()
        child = manager.get_logger("search")
        assert "search" in child.name
