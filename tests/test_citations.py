"""
Pruebas del modulo de citas legales (citations.py).
Cubre: CitationGenerator, CitationStyle, LegalDocument, BibliographyManager.
"""

import pytest
from datetime import datetime

from lexviridis.citations import (
    CitationGenerator,
    CitationStyle,
    LegalDocument,
    BibliographyManager,
)


@pytest.fixture
def sample_doc():
    return LegalDocument(
        tipo="Decreto Legislativo",
        numero="104-93",
        titulo="Ley General del Ambiente",
        fecha_publicacion=datetime(1993, 6, 27),
        institucion="Congreso Nacional de Honduras",
    )


@pytest.fixture
def sample_doc_with_article():
    return LegalDocument(
        tipo="Decreto Legislativo",
        numero="104-93",
        titulo="Ley General del Ambiente",
        fecha_publicacion=datetime(1993, 6, 27),
        articulo="5",
    )


class TestCitationGenerator:

    def test_apa_format(self, sample_doc):
        citation = CitationGenerator.generate(sample_doc, CitationStyle.APA)
        assert "1993" in citation
        assert "Ley General del Ambiente" in citation
        assert "Decreto Legislativo" in citation
        assert "La Gaceta" in citation

    def test_apa_with_article(self, sample_doc_with_article):
        citation = CitationGenerator.generate(sample_doc_with_article, CitationStyle.APA)
        assert "Art. 5" in citation

    def test_iso690_format(self, sample_doc):
        citation = CitationGenerator.generate(sample_doc, CitationStyle.ISO_690)
        assert "HONDURAS" in citation
        assert "No. 104-93" in citation

    def test_bluebook_format(self, sample_doc):
        citation = CitationGenerator.generate(sample_doc, CitationStyle.BLUEBOOK)
        assert "Honduras 1993" in citation
        assert "Ley General del Ambiente" in citation

    def test_bluebook_with_article(self, sample_doc_with_article):
        citation = CitationGenerator.generate(sample_doc_with_article, CitationStyle.BLUEBOOK)
        assert "art. 5" in citation

    def test_honduran_format(self, sample_doc):
        citation = CitationGenerator.generate(sample_doc, CitationStyle.HONDURAN)
        assert "publicado en La Gaceta" in citation
        assert "No. 104-93" in citation

    def test_honduran_with_article(self, sample_doc_with_article):
        citation = CitationGenerator.generate(sample_doc_with_article, CitationStyle.HONDURAN)
        assert "Art. 5 del" in citation


class TestBibliographyManager:

    def test_add_entry(self, sample_doc):
        bm = BibliographyManager()
        bm.add_entry(sample_doc)
        assert len(bm.entries) == 1

    def test_no_duplicate_entries(self, sample_doc):
        bm = BibliographyManager()
        bm.add_entry(sample_doc)
        bm.add_entry(sample_doc)
        assert len(bm.entries) == 1

    def test_different_articles_are_not_duplicates(self):
        doc1 = LegalDocument("DL", "104", "Ley", datetime(1993, 1, 1), articulo="1")
        doc2 = LegalDocument("DL", "104", "Ley", datetime(1993, 1, 1), articulo="2")
        bm = BibliographyManager()
        bm.add_entry(doc1)
        bm.add_entry(doc2)
        assert len(bm.entries) == 2

    def test_remove_entry(self, sample_doc):
        bm = BibliographyManager()
        bm.add_entry(sample_doc)
        bm.remove_entry(0)
        assert len(bm.entries) == 0

    def test_remove_invalid_index_is_safe(self, sample_doc):
        bm = BibliographyManager()
        bm.add_entry(sample_doc)
        bm.remove_entry(99)  # No debe lanzar excepcion
        assert len(bm.entries) == 1

    def test_generate_all(self):
        doc_a = LegalDocument("DL", "200", "Ley Forestal", datetime(2007, 1, 1))
        doc_b = LegalDocument("DL", "100", "Ley del Ambiente", datetime(1993, 1, 1))
        bm = BibliographyManager()
        bm.add_entry(doc_a)
        bm.add_entry(doc_b)
        citations = bm.generate_all(CitationStyle.APA)
        assert len(citations) == 2
        # Debe estar ordenado alfabeticamente por titulo
        # "Ley Forestal" < "Ley del Ambiente" (F < d en ASCII)
        assert "Forestal" in citations[0]
        assert "Ambiente" in citations[1]
