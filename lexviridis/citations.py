from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class CitationStyle(Enum):
    APA = "apa"
    ISO_690 = "iso690"
    BLUEBOOK = "bluebook"
    HONDURAN = "honduran"


@dataclass
class LegalDocument:
    tipo: str
    numero: str
    titulo: str
    fecha_publicacion: datetime
    institucion: str = "Congreso Nacional de Honduras"
    articulo: str | None = None


class CitationGenerator:
    """Generador de citas legales automáticas."""

    @staticmethod
    def generate(doc: LegalDocument, style: CitationStyle) -> str:
        if style == CitationStyle.APA:
            return CitationGenerator._format_apa(doc)
        elif style == CitationStyle.ISO_690:
            return CitationGenerator._format_iso690(doc)
        elif style == CitationStyle.BLUEBOOK:
            return CitationGenerator._format_bluebook(doc)
        return CitationGenerator._format_honduran(doc)

    @staticmethod
    def _format_apa(doc: LegalDocument) -> str:
        year = doc.fecha_publicacion.year
        citation = f"{doc.institucion}. ({year}). {doc.titulo} ({doc.tipo} No. {doc.numero}). La Gaceta."
        if doc.articulo:
            citation += f" Art. {doc.articulo}."
        return citation

    @staticmethod
    def _format_iso690(doc: LegalDocument) -> str:
        fecha = doc.fecha_publicacion.strftime("%d de %B de %Y")
        citation = f"HONDURAS. {doc.tipo} No. {doc.numero}, {doc.titulo}. La Gaceta, {fecha}."
        if doc.articulo:
            citation += f" art. {doc.articulo}."
        return citation

    @staticmethod
    def _format_bluebook(doc: LegalDocument) -> str:
        year = doc.fecha_publicacion.year
        citation = f"{doc.titulo}, {doc.tipo} {doc.numero}"
        if doc.articulo:
            citation += f", art. {doc.articulo}"
        citation += f" (Honduras {year})"
        return citation

    @staticmethod
    def _format_honduran(doc: LegalDocument) -> str:
        fecha = doc.fecha_publicacion.strftime("%d de %B de %Y")
        prefix = f"Art. {doc.articulo} del " if doc.articulo else ""
        return f"{prefix}{doc.tipo} No. {doc.numero}, {doc.titulo}, publicado en La Gaceta el {fecha}."


class BibliographyManager:
    """Gestiona una lista de documentos citados."""

    def __init__(self):
        self.entries: list[LegalDocument] = []

    def add_entry(self, doc: LegalDocument):
        if not any(e.numero == doc.numero and e.articulo == doc.articulo for e in self.entries):
            self.entries.append(doc)

    def remove_entry(self, index: int):
        if 0 <= index < len(self.entries):
            self.entries.pop(index)

    def generate_all(self, style: CitationStyle) -> list[str]:
        # Ordenar alfabéticamente por título
        sorted_docs = sorted(self.entries, key=lambda x: x.titulo)
        return [CitationGenerator.generate(d, style) for d in sorted_docs]
