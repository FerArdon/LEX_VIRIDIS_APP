
import json
from datetime import datetime
from pathlib import Path


class Translations:
    """Gestor de traducciones para Lex Viridis."""

    def __init__(self):
        self.current_language = self.load_language()
        self.translations = self.load_translations(self.current_language)

    def load_language(self) -> str:
        config_file = Path.home() / ".lexviridis" / "language.json"
        if config_file.exists():
            try:
                with open(config_file) as f:
                    return json.load(f).get('language', 'es')
            except (json.JSONDecodeError, OSError, KeyError):
                pass
        return 'es'

    def _get_i18n_dir(self) -> Path:
        """Obtiene directorio i18n compatible con .exe y desarrollo."""
        try:
            from .config import config as _cfg
            i18n_dir = _cfg.BASE_DIR / "lexviridis" / "i18n"
            if i18n_dir.exists():
                return i18n_dir
        except Exception:
            pass
        return Path(__file__).parent / "i18n"

    def load_translations(self, language: str) -> dict:
        i18n_dir = self._get_i18n_dir()
        trans_file = i18n_dir / f"{language}.json"
        if not trans_file.exists():
            trans_file = i18n_dir / "es.json"
        try:
            with open(trans_file, encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError, UnicodeDecodeError):
            return {}

    def t(self, key: str, **kwargs) -> str:
        keys = key.split('.')
        value = self.translations
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, key)
            else:
                return key
        if isinstance(value, str) and kwargs:
            try:
                return value.format(**kwargs)
            except (KeyError, ValueError):
                pass
        return str(value)

    def set_language(self, language: str):
        self.current_language = language
        self.translations = self.load_translations(language)
        config_file = Path.home() / ".lexviridis" / "language.json"
        config_file.parent.mkdir(exist_ok=True)
        with open(config_file, 'w') as f:
            json.dump({'language': language}, f)

class Formatter:
    """Formateador localizado para Lex Viridis."""

    @staticmethod
    def format_date(date: datetime, lang: str = 'es', format_type: str = 'short') -> str:
        if lang == 'es':
            return date.strftime("%d/%m/%Y") if format_type == 'short' else date.strftime("%d de %B de %Y")
        else:
            return date.strftime("%m/%d/%Y") if format_type == 'short' else date.strftime("%B %d, %Y")

    @staticmethod
    def format_number(number: float, lang: str = 'es') -> str:
        if lang == 'es':
            return f"{number:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{number:,.2f}"

# Instancia global para ser usada en toda la app
i18n = Translations()
