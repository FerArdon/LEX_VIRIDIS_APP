# lexviridis/persistence.py

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path

from .config import config
from .utils import normalize_text


# -----------------------------
# Base para manejo de datos JSON
# -----------------------------
class DataManager:
    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self._data = self._load_data()

    def _load_data(self):
        if self.filepath.exists():
            try:
                with open(self.filepath, encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logging.warning(f"Archivo corrupto {self.filepath}: {e}")
        return self._default_data()

    def _save_data(self):
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"No se pudo guardar {self.filepath}: {e}")

    def _default_data(self):
        return {}

# -----------------------------
# Caché de búsqueda
# -----------------------------
class SearchCache(DataManager):
    def __init__(self):
        super().__init__(config.CACHE_FILE)
        self.max_cache_size = 500

    def _default_data(self):
        return {}

    def _generate_key(self, terms: list[str]) -> str:
        key = "_".join(sorted(t.lower() for t in terms))
        return hashlib.md5(key.encode('utf-8')).hexdigest()

    def get(self, terms: list[str]) -> list[dict] | None:
        return self._data.get(self._generate_key(terms))

    def set(self, terms: list[str], results: list[dict]):
        key = self._generate_key(terms)
        self._data[key] = results
        if len(self._data) > self.max_cache_size:
            self._data = dict(list(self._data.items())[-self.max_cache_size:])
        self._save_data()

# -----------------------------
# Historial de búsqueda
# -----------------------------
class SearchHistory(DataManager):
    def __init__(self):
        super().__init__(config.HISTORY_FILE)
        self.max_size = 100

    def _default_data(self):
        return []

    def add(self, terms: list[str]):
        if not terms: return
        timestamp = datetime.now().isoformat()
        normalized = sorted(normalize_text(t) for t in terms)
        if not self._data or normalized != sorted(normalize_text(t) for t in self._data[-1]['terms']):
            self._data.append({'terms': terms, 'timestamp': timestamp})
            self._data = self._data[-self.max_size:]
            self._save_data()

    def get(self) -> list[dict]:
        return list(self._data)

    def clear(self):
        self._data = self._default_data()
        self._save_data()

# -----------------------------
# Favoritos
# -----------------------------
class FavoritesManager(DataManager):
    def __init__(self):
        super().__init__(config.FAVORITES_FILE)

    def _default_data(self):
        return {}

    def add(self, path: str, description: str = ""):
        self._data[path] = {'description': description, 'added': datetime.now().isoformat()}
        self._save_data()

    def remove(self, path: str):
        if path in self._data:
            del self._data[path]
            self._save_data()

    def is_favorite(self, path: str) -> bool:
        return path in self._data

    def get_all(self) -> dict[str, dict]:
        return self._data

# -----------------------------
# Guardado automático de búsquedas
# -----------------------------
class AutoBackup:
    def __init__(self):
        self.dir = config.BACKUP_DIR
        self.dir.mkdir(parents=True, exist_ok=True)
        self.max_backups = 30

    def save(self, terms: list[str], results: list[dict]):
        if not results: return
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = "_".join(terms[:3]).replace(" ", "_")[:50]
        filename = f"search_{ts}_{slug}.json" if slug else f"search_{ts}.json"
        path = self.dir / filename

        data = {
            "timestamp": ts,
            "search_terms": terms,
            "results": results,
            "app_version": config.APP_VERSION
        }

        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logging.info(f"Backup automático: {path.name}")
        except Exception as e:
            logging.error(f"Error guardando backup: {e}")

        self._cleanup()

    def _cleanup(self):
        backups = sorted(self.dir.glob("search_*.json"), key=lambda p: p.stat().st_mtime)
        while len(backups) > self.max_backups:
            try:
                old = backups.pop(0)
                old.unlink()
                logging.info(f"Backup eliminado: {old.name}")
            except Exception as e:
                logging.warning(f"No se pudo eliminar {old.name}: {e}")
