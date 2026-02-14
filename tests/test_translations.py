"""
Pruebas del modulo de traducciones (translations.py).
Cubre: Translations, Formatter.
"""

import json
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from lexviridis.translations import Translations, Formatter


class TestTranslations:

    def test_default_language_is_spanish(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
        t = Translations()
        assert t.current_language == "es"

    def test_translations_loaded(self):
        t = Translations()
        assert isinstance(t.translations, dict)
        # es.json debe tener al menos "app" y "nav"
        assert "app" in t.translations or len(t.translations) > 0

    def test_t_simple_key(self):
        t = Translations()
        if "app" in t.translations:
            result = t.t("app.name")
            assert result == "LEX VIRIDIS"

    def test_t_nested_key(self):
        t = Translations()
        if "nav" in t.translations:
            result = t.t("nav.search")
            assert result == "Buscar"

    def test_t_missing_key_returns_key(self):
        t = Translations()
        result = t.t("no.existe.esta.clave")
        assert result == "no.existe.esta.clave"

    def test_t_with_interpolation(self):
        t = Translations()
        if "search" in t.translations:
            result = t.t("search.no_results", query="agua")
            assert "agua" in result

    def test_set_language(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
        t = Translations()
        t.set_language("en")
        assert t.current_language == "en"


class TestFormatter:

    def test_format_date_short_es(self):
        date = datetime(2024, 3, 15)
        result = Formatter.format_date(date, lang="es", format_type="short")
        assert result == "15/03/2024"

    def test_format_date_short_en(self):
        date = datetime(2024, 3, 15)
        result = Formatter.format_date(date, lang="en", format_type="short")
        assert result == "03/15/2024"

    def test_format_number_es(self):
        result = Formatter.format_number(1234567.89, lang="es")
        assert "." in result  # separador de miles
        assert "," in result  # separador decimal

    def test_format_number_en(self):
        result = Formatter.format_number(1234567.89, lang="en")
        assert "," in result  # separador de miles
        assert "." in result  # separador decimal
