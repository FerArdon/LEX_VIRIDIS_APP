"""
Pruebas del modulo de persistencia (persistence.py).
Cubre: DataManager, SearchCache, SearchHistory, FavoritesManager, AutoBackup.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch

from lexviridis.persistence import (
    DataManager,
    SearchCache,
    SearchHistory,
    FavoritesManager,
    AutoBackup,
)


# ============================================================
# DataManager base
# ============================================================

class TestDataManager:

    def test_creates_parent_directory(self, tmp_path):
        filepath = tmp_path / "subdir" / "data.json"
        dm = DataManager(filepath)
        assert filepath.parent.exists()

    def test_loads_default_data_when_file_missing(self, tmp_path):
        filepath = tmp_path / "missing.json"
        dm = DataManager(filepath)
        assert dm._data == {}

    def test_loads_existing_file(self, tmp_path):
        filepath = tmp_path / "existing.json"
        filepath.write_text('{"key": "value"}', encoding="utf-8")
        dm = DataManager(filepath)
        assert dm._data == {"key": "value"}

    def test_handles_corrupt_json(self, tmp_path):
        filepath = tmp_path / "corrupt.json"
        filepath.write_text("this is not json!!!", encoding="utf-8")
        dm = DataManager(filepath)
        assert dm._data == {}

    def test_save_data(self, tmp_path):
        filepath = tmp_path / "save_test.json"
        dm = DataManager(filepath)
        dm._data = {"saved": True}
        dm._save_data()
        loaded = json.loads(filepath.read_text(encoding="utf-8"))
        assert loaded == {"saved": True}


# ============================================================
# SearchCache (JSON-based, from persistence.py)
# ============================================================

class TestPersistenceSearchCache:

    def test_cache_miss_returns_none(self, tmp_path):
        with patch("lexviridis.persistence.config") as mock_cfg:
            mock_cfg.CACHE_FILE = tmp_path / "cache.json"
            cache = SearchCache()
            assert cache.get(["termino"]) is None

    def test_cache_set_and_get(self, tmp_path):
        with patch("lexviridis.persistence.config") as mock_cfg:
            mock_cfg.CACHE_FILE = tmp_path / "cache.json"
            cache = SearchCache()
            cache.set(["bosque"], [{"id": 1}])
            assert cache.get(["bosque"]) == [{"id": 1}]

    def test_cache_key_is_order_independent(self, tmp_path):
        with patch("lexviridis.persistence.config") as mock_cfg:
            mock_cfg.CACHE_FILE = tmp_path / "cache.json"
            cache = SearchCache()
            cache.set(["agua", "bosque"], [{"id": 1}])
            assert cache.get(["bosque", "agua"]) == [{"id": 1}]

    def test_cache_eviction(self, tmp_path):
        with patch("lexviridis.persistence.config") as mock_cfg:
            mock_cfg.CACHE_FILE = tmp_path / "cache.json"
            cache = SearchCache()
            cache.max_cache_size = 2
            cache.set(["q1"], [{"id": 1}])
            cache.set(["q2"], [{"id": 2}])
            cache.set(["q3"], [{"id": 3}])
            # Solo deben quedar 2 entradas
            assert len(cache._data) == 2


# ============================================================
# SearchHistory
# ============================================================

class TestSearchHistory:

    def test_empty_history(self, tmp_path):
        with patch("lexviridis.persistence.config") as mock_cfg:
            mock_cfg.HISTORY_FILE = tmp_path / "history.json"
            history = SearchHistory()
            assert history.get() == []

    def test_add_and_get(self, tmp_path):
        with patch("lexviridis.persistence.config") as mock_cfg:
            mock_cfg.HISTORY_FILE = tmp_path / "history.json"
            history = SearchHistory()
            history.add(["bosque"])
            entries = history.get()
            assert len(entries) == 1
            assert entries[0]["terms"] == ["bosque"]

    def test_no_duplicates_consecutive(self, tmp_path):
        with patch("lexviridis.persistence.config") as mock_cfg:
            mock_cfg.HISTORY_FILE = tmp_path / "history.json"
            history = SearchHistory()
            history.add(["bosque"])
            history.add(["bosque"])
            assert len(history.get()) == 1

    def test_different_queries_added(self, tmp_path):
        with patch("lexviridis.persistence.config") as mock_cfg:
            mock_cfg.HISTORY_FILE = tmp_path / "history.json"
            history = SearchHistory()
            history.add(["bosque"])
            history.add(["agua"])
            assert len(history.get()) == 2

    def test_clear_history(self, tmp_path):
        with patch("lexviridis.persistence.config") as mock_cfg:
            mock_cfg.HISTORY_FILE = tmp_path / "history.json"
            history = SearchHistory()
            history.add(["bosque"])
            history.clear()
            assert history.get() == []

    def test_max_size_respected(self, tmp_path):
        with patch("lexviridis.persistence.config") as mock_cfg:
            mock_cfg.HISTORY_FILE = tmp_path / "history.json"
            history = SearchHistory()
            history.max_size = 3
            for i in range(5):
                history.add([f"query{i}"])
            assert len(history.get()) == 3

    def test_empty_terms_ignored(self, tmp_path):
        with patch("lexviridis.persistence.config") as mock_cfg:
            mock_cfg.HISTORY_FILE = tmp_path / "history.json"
            history = SearchHistory()
            history.add([])
            assert history.get() == []


# ============================================================
# FavoritesManager
# ============================================================

class TestFavoritesManager:

    def test_empty_favorites(self, tmp_path):
        with patch("lexviridis.persistence.config") as mock_cfg:
            mock_cfg.FAVORITES_FILE = tmp_path / "favs.json"
            fav = FavoritesManager()
            assert fav.get_all() == {}

    def test_add_favorite(self, tmp_path):
        with patch("lexviridis.persistence.config") as mock_cfg:
            mock_cfg.FAVORITES_FILE = tmp_path / "favs.json"
            fav = FavoritesManager()
            fav.add("/path/doc.pdf", "Mi documento")
            assert fav.is_favorite("/path/doc.pdf")

    def test_remove_favorite(self, tmp_path):
        with patch("lexviridis.persistence.config") as mock_cfg:
            mock_cfg.FAVORITES_FILE = tmp_path / "favs.json"
            fav = FavoritesManager()
            fav.add("/path/doc.pdf")
            fav.remove("/path/doc.pdf")
            assert not fav.is_favorite("/path/doc.pdf")

    def test_remove_nonexistent_is_safe(self, tmp_path):
        with patch("lexviridis.persistence.config") as mock_cfg:
            mock_cfg.FAVORITES_FILE = tmp_path / "favs.json"
            fav = FavoritesManager()
            fav.remove("/no/existe.pdf")  # No debe lanzar excepcion

    def test_is_favorite_false_for_unknown(self, tmp_path):
        with patch("lexviridis.persistence.config") as mock_cfg:
            mock_cfg.FAVORITES_FILE = tmp_path / "favs.json"
            fav = FavoritesManager()
            assert not fav.is_favorite("/unknown.pdf")


# ============================================================
# AutoBackup
# ============================================================

class TestAutoBackup:

    def test_save_creates_file(self, tmp_path):
        with patch("lexviridis.persistence.config") as mock_cfg:
            mock_cfg.BACKUP_DIR = tmp_path / "backups"
            mock_cfg.APP_VERSION = "3.0.0"
            backup = AutoBackup()
            backup.save(["bosque"], [{"id": 1, "context": "test"}])
            files = list(tmp_path.glob("backups/search_*.json"))
            assert len(files) == 1

    def test_save_empty_results_does_nothing(self, tmp_path):
        with patch("lexviridis.persistence.config") as mock_cfg:
            mock_cfg.BACKUP_DIR = tmp_path / "backups"
            mock_cfg.APP_VERSION = "3.0.0"
            backup = AutoBackup()
            backup.save(["bosque"], [])
            files = list(tmp_path.glob("backups/search_*.json"))
            assert len(files) == 0

    def test_cleanup_old_backups(self, tmp_path):
        with patch("lexviridis.persistence.config") as mock_cfg:
            mock_cfg.BACKUP_DIR = tmp_path / "backups"
            mock_cfg.APP_VERSION = "3.0.0"
            backup = AutoBackup()
            backup.max_backups = 2
            for i in range(4):
                backup.save([f"q{i}"], [{"id": i}])
            files = list(tmp_path.glob("backups/search_*.json"))
            assert len(files) <= 2
