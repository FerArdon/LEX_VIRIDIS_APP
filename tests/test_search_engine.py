"""
Pruebas del motor de busqueda (search_engine.py).
Cubre: QueryValidator, SearchCache, SearchEngine, SearchStatus, SearchResult.
"""

import pytest
from lexviridis.search_engine import (
    QueryValidator,
    SearchCache,
    SearchStatus,
    SearchResult,
    SINONIMOS,
    MIN_QUERY_LENGTH,
    MAX_QUERY_LENGTH,
    DEFAULT_PAGE_SIZE,
)


# ============================================================
# QueryValidator
# ============================================================

class TestQueryValidator:

    def test_empty_query_is_invalid(self):
        valid, msg = QueryValidator.validate("")
        assert not valid
        assert "término" in msg.lower() or "ingresa" in msg.lower()

    def test_whitespace_only_is_invalid(self):
        valid, msg = QueryValidator.validate("   ")
        assert not valid

    def test_none_query_is_invalid(self):
        valid, msg = QueryValidator.validate(None)
        assert not valid

    def test_too_short_query(self):
        valid, msg = QueryValidator.validate("a")
        assert not valid
        assert str(MIN_QUERY_LENGTH) in msg

    def test_too_long_query(self):
        long_query = "a" * (MAX_QUERY_LENGTH + 1)
        valid, msg = QueryValidator.validate(long_query)
        assert not valid
        assert str(MAX_QUERY_LENGTH) in msg

    def test_valid_simple_query(self):
        valid, msg = QueryValidator.validate("bosque")
        assert valid
        assert msg == ""

    def test_valid_query_with_accents(self):
        valid, msg = QueryValidator.validate("contaminación ambiental")
        assert valid

    def test_valid_query_with_numbers(self):
        valid, msg = QueryValidator.validate("decreto 104")
        assert valid

    def test_invalid_special_chars(self):
        valid, msg = QueryValidator.validate("bosque@#$")
        assert not valid
        assert "caracteres" in msg.lower()

    def test_sql_injection_drop(self):
        valid, msg = QueryValidator.validate("bosque; DROP TABLE normas")
        assert not valid

    def test_sql_injection_union(self):
        valid, msg = QueryValidator.validate("agua UNION SELECT * FROM usuarios")
        assert not valid

    def test_sql_injection_delete(self):
        valid, msg = QueryValidator.validate("DELETE FROM normas")
        assert not valid

    def test_sql_injection_double_dash(self):
        valid, msg = QueryValidator.validate("agua -- comentario")
        assert not valid

    def test_sanitize_removes_special_chars(self):
        result = QueryValidator.sanitize("bosque!@#$ forestal")
        assert "@" not in result
        assert "#" not in result
        assert "bosque" in result
        assert "forestal" in result

    def test_sanitize_normalizes_whitespace(self):
        result = QueryValidator.sanitize("  bosque   forestal  ")
        assert result == "bosque forestal"


# ============================================================
# SearchCache
# ============================================================

class TestSearchCache:

    def test_cache_miss_returns_none(self):
        cache = SearchCache(maxsize=10)
        assert cache.get("no existe") is None

    def test_cache_set_and_get(self):
        cache = SearchCache(maxsize=10)
        data = [{"id": 1, "title": "test"}]
        cache.set("bosque", data)
        assert cache.get("bosque") == data

    def test_cache_is_case_insensitive(self):
        cache = SearchCache(maxsize=10)
        data = [{"id": 1}]
        cache.set("Bosque", data)
        assert cache.get("bosque") == data

    def test_cache_eviction_on_max_size(self):
        cache = SearchCache(maxsize=2)
        cache.set("query1", [{"id": 1}])
        cache.set("query2", [{"id": 2}])
        cache.set("query3", [{"id": 3}])
        # query1 debe haber sido desalojada
        assert cache.get("query1") is None
        assert cache.get("query2") is not None
        assert cache.get("query3") is not None

    def test_cache_clear(self):
        cache = SearchCache(maxsize=10)
        cache.set("query1", [{"id": 1}])
        cache.clear()
        assert cache.get("query1") is None

    def test_cache_different_pages_are_different_keys(self):
        cache = SearchCache(maxsize=10)
        cache.set("bosque", [{"id": 1}], page=1)
        cache.set("bosque", [{"id": 2}], page=2)
        assert cache.get("bosque", page=1) == [{"id": 1}]
        assert cache.get("bosque", page=2) == [{"id": 2}]


# ============================================================
# SearchResult dataclass
# ============================================================

class TestSearchResult:

    def test_search_result_creation(self):
        result = SearchResult(
            status=SearchStatus.SUCCESS,
            results=[{"id": 1}],
            message="1 resultado",
            query="bosque",
            duration_ms=15.5,
            total_found=1,
        )
        assert result.status == SearchStatus.SUCCESS
        assert len(result.results) == 1
        assert result.query == "bosque"
        assert result.cached is False  # default

    def test_search_result_defaults(self):
        result = SearchResult(
            status=SearchStatus.NO_RESULTS,
            results=[], message="sin resultados",
            query="xyz", duration_ms=0, total_found=0,
        )
        assert result.page == 1
        assert result.page_size == DEFAULT_PAGE_SIZE
        assert result.cached is False


# ============================================================
# SearchStatus enum
# ============================================================

class TestSearchStatus:

    def test_all_statuses_exist(self):
        assert SearchStatus.SUCCESS.value == "success"
        assert SearchStatus.NO_RESULTS.value == "no_results"
        assert SearchStatus.INVALID_QUERY.value == "invalid_query"
        assert SearchStatus.DB_ERROR.value == "db_error"
        assert SearchStatus.TIMEOUT.value == "timeout"
        assert SearchStatus.UNKNOWN_ERROR.value == "unknown_error"


# ============================================================
# SINONIMOS dictionary
# ============================================================

class TestSinonimos:

    def test_sinonimos_has_expected_categories(self):
        expected = {"delito", "ambiental", "bosque", "agua", "contaminacion", "tala", "licencia", "multa", "protegida"}
        assert expected.issubset(set(SINONIMOS.keys()))

    def test_each_category_has_synonyms(self):
        for category, synonyms in SINONIMOS.items():
            assert len(synonyms) >= 2, f"Categoria '{category}' tiene muy pocos sinonimos"


# ============================================================
# SearchEngine (integracion con BD temporal)
# ============================================================

class TestSearchEngine:

    def test_engine_is_ready(self, search_engine):
        assert search_engine.is_ready

    def test_search_invalid_query_returns_invalid_status(self, search_engine):
        result = search_engine.search_safe("")
        assert result.status == SearchStatus.INVALID_QUERY

    def test_search_sql_injection_blocked(self, search_engine):
        result = search_engine.search_safe("DROP TABLE normas")
        assert result.status == SearchStatus.INVALID_QUERY

    def test_search_returns_results(self, search_engine):
        result = search_engine.search_safe("ambiente")
        assert result.status in (SearchStatus.SUCCESS, SearchStatus.NO_RESULTS)

    def test_search_cache_hit(self, search_engine):
        # Primera busqueda - cache miss
        result1 = search_engine.search_safe("bosque")
        # Segunda busqueda - cache hit
        result2 = search_engine.search_safe("bosque")
        assert result2.cached is True

    def test_clear_cache(self, search_engine):
        search_engine.search_safe("agua")
        search_engine.clear_cache()
        result = search_engine.search_safe("agua")
        assert result.cached is False
