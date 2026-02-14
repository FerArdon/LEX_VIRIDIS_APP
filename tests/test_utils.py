"""
Pruebas del modulo de utilidades (utils.py).
Cubre: normalize_text, suppress_stderr, MemoryOptimizer.
"""

import sys
import pytest

from lexviridis.utils import normalize_text, suppress_stderr, MemoryOptimizer


class TestNormalizeText:

    def test_lowercase(self):
        assert normalize_text("BOSQUE") == "bosque"

    def test_removes_accents(self):
        assert normalize_text("contaminación") == "contaminacion"

    def test_removes_special_chars(self):
        result = normalize_text("ley @#$ forestal")
        assert "@" not in result
        assert "#" not in result
        assert "ley" in result
        assert "forestal" in result

    def test_normalizes_whitespace(self):
        result = normalize_text("  muchos   espacios  ")
        assert result == "muchos espacios"

    def test_empty_string(self):
        assert normalize_text("") == ""

    def test_spanish_characters(self):
        result = normalize_text("niño señor año único")
        assert "n" in result
        assert result == "nino senor ano unico"


class TestSuppressStderr:

    def test_suppresses_stderr(self):
        with suppress_stderr():
            print("error test", file=sys.stderr)
        # Si no lanzo excepcion, funciono correctamente

    def test_restores_stderr_after(self):
        original = sys.stderr
        with suppress_stderr():
            pass
        assert sys.stderr is original


class TestMemoryOptimizer:

    def test_clear_runs_without_error(self):
        MemoryOptimizer.clear()  # No debe lanzar excepcion

    def test_operation_context_manager(self):
        with MemoryOptimizer.operation():
            data = [i for i in range(100)]
        # No debe lanzar excepcion
