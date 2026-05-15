"""
LEX VIRIDIS - PDF Highlighter
Resalta términos de búsqueda en PDFs usando PyMuPDF (fitz).
Soporta búsqueda case-insensitive Y accent-insensitive (carbón ↔ carbon).
"""

import fitz
import hashlib
import logging
import re
import unicodedata
from pathlib import Path
from .config import config

_pdf_logger = logging.getLogger("lexviridis.pdf")


# ── Utilidades de normalización ──────────────────────────────────────────────

def _norm(text: str) -> str:
    """Normaliza para comparación: minúsculas + sin tildes/diacríticos."""
    return unicodedata.normalize("NFD", text.lower()).encode("ascii", "ignore").decode()


def _find_rects(page: fitz.Page, term: str) -> list:
    """
    Busca 'term' en la página de forma case-insensitive Y accent-insensitive.
    Retorna lista de fitz.Rect con las posiciones de cada coincidencia.

    Estrategia:
      1) Intenta search_for nativo de PyMuPDF (rápido, case-insensitive).
      2) Si no encuentra nada, hace búsqueda palabra-a-palabra comparando
         versiones normalizadas (sin tildes) → funciona para "carbon" ↔ "Carbón".
    """
    term = term.strip()
    if not term:
        return []

    # ── Paso 1: búsqueda nativa (rápida) ────────────────────────────────────
    try:
        rects = page.search_for(term, quads=False)
        if rects:
            return rects
    except Exception:
        return []

    # ── Paso 2: búsqueda accent-insensitive por palabras ────────────────────
    term_norm   = _norm(term)
    term_words  = term_norm.split()
    n           = len(term_words)

    # "words" = [(x0, y0, x1, y1, texto, nº_bloque, nº_línea, nº_palabra), ...]
    try:
        words = page.get_text("words")
    except Exception:
        return []
    if not words:
        return []

    results = []

    if n == 1:
        # Coincidencia de una sola palabra (permite prefijos parciales también)
        t_norm = term_words[0]
        for w in words:
            w_norm = _norm(w[4])
            # Exacto o contenido (p.ej. "carbón" dentro de "hidrocarbón")
            if w_norm == t_norm or t_norm in w_norm:
                results.append(fitz.Rect(w[:4]))
    else:
        # Coincidencia de frase multi-palabra: busca palabras consecutivas
        # en el mismo bloque y línea
        for i in range(len(words) - n + 1):
            chunk = words[i: i + n]
            # Mismo bloque y misma línea para todas
            if not all(c[5] == chunk[0][5] and c[6] == chunk[0][6] for c in chunk):
                continue
            chunk_norm = " ".join(_norm(c[4]) for c in chunk)
            if chunk_norm == term_norm:
                # Fusionar los rectángulos de la frase en uno solo
                merged = fitz.Rect(chunk[0][:4])
                for c in chunk[1:]:
                    merged |= fitz.Rect(c[:4])
                results.append(merged)

    return results


# ── Clase principal ──────────────────────────────────────────────────────────

class PDFHighlighter:
    @staticmethod
    def highlight_terms(pdf_path: str, term: str, output_path: str = None) -> str:
        """
        Resalta 'term' en todas las páginas del PDF.
        - Búsqueda case-insensitive Y accent-insensitive (carbón ↔ carbon).
        - Si 'term' tiene varias palabras, intenta la frase completa; si no
          encuentra nada, resalta cada palabra significativa (> 3 letras) por
          separado.
        - Caché con clave (pdf + término) para evitar conflictos en Foxit/Edge
          cuando el mismo archivo está abierto.
        - Si el archivo caché ya existe, lo reutiliza sin regenerar.

        Retorna la ruta del PDF resaltado o el original si no hay coincidencias.
        """
        if not pdf_path or not term or pdf_path == "None":
            return pdf_path

        cache_dir = config.CACHE_DIR

        # Clave única por (pdf, término) ─ evita reutilizar el mismo archivo
        # para distintos términos, lo que haría que Foxit muestre la pestaña
        # vieja sin los nuevos resaltados.
        if not output_path:
            filename  = Path(pdf_path).name
            cache_key = hashlib.md5(
                f"{pdf_path}:{term.lower()}".encode("utf-8", errors="ignore"),
                usedforsecurity=False,
            ).hexdigest()[:10]
            output_path = str(cache_dir / f"hl_{cache_key}_{filename}")

        # Si ya está en caché, devolver directamente (evita escribir sobre un
        # archivo que Foxit pueda tener abierto en pestaña).
        if Path(output_path).exists():
            return output_path

        # Construir lista de variantes a buscar:
        #   • frase completa
        #   • palabras individuales significativas (> 3 letras)
        term_clean = term.strip()
        variants: list[str] = [term_clean]
        for word in re.split(r"\s+", term_clean):
            if len(word) > 3 and word != term_clean:
                variants.append(word)

        try:
            doc       = fitz.open(pdf_path)
            found_any = False

            for page in doc:
                for variant in variants:
                    for rect in _find_rects(page, variant):
                        try:
                            annot = page.add_highlight_annot(rect)
                            annot.set_colors(stroke=(1, 0.9, 0))   # Amarillo
                            annot.update()
                            found_any = True
                        except Exception:
                            pass

            if found_any:
                try:
                    doc.save(output_path, garbage=4, deflate=True)
                    doc.close()
                    return output_path
                except Exception as save_err:
                    doc.close()
                    import logging
                    _pdf_logger.warning(
                        f"PDFHighlighter: no se pudo guardar caché ({save_err})"
                    )
                    return pdf_path
            else:
                doc.close()
                return pdf_path   # Sin coincidencias → abrir original

        except Exception as e:
            import logging
            _pdf_logger.warning(f"PDFHighlighter error: {e}")
            return pdf_path
