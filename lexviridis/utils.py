# lexviridis/utils.py

import re
import sys
import io
import unicodedata
import platform
import subprocess
import contextlib
import gc
import fitz  # PyMuPDF
from pathlib import Path
import logging

# -----------------------------
# Normalización de texto
# -----------------------------
def normalize_text(text: str) -> str:
    """Normaliza texto: minúsculas, sin acentos, sin símbolos."""
    text = text.lower()
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'[^a-z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# -----------------------------
# Supresor de stderr temporal
# -----------------------------
@contextlib.contextmanager
def suppress_stderr():
    original_stderr = sys.stderr
    sys.stderr = io.StringIO()
    try:
        yield
    finally:
        sys.stderr = original_stderr

# -----------------------------
# Validación de PDFs
# -----------------------------
class PDFValidator:
    @staticmethod
    def validate_pdf(pdf_path: Path) -> tuple[bool, str]:
        if not pdf_path.exists():
            return False, f"Archivo no encontrado: {pdf_path}"
        try:
            with fitz.open(pdf_path) as doc:
                if doc.is_encrypted:
                    return False, "El documento está protegido"
                if doc.page_count == 0:
                    return False, "El documento no tiene páginas"
                return True, ""
        except Exception as e:
            return False, f"Error al abrir el archivo: {e}"

# -----------------------------
# Optimización de memoria
# -----------------------------
class MemoryOptimizer:
    @staticmethod
    def clear():
        gc.collect()

    @staticmethod
    @contextlib.contextmanager
    def operation():
        try:
            yield
        finally:
            MemoryOptimizer.clear()

# -----------------------------
# Abrir PDF en visor externo
# -----------------------------
def open_with_native_viewer(pdf_path: Path):
    try:
        if platform.system() == "Windows":
            import os
            os.startfile(str(pdf_path))
        elif platform.system() == "Darwin":
            subprocess.run(["open", str(pdf_path)])
        else:
            subprocess.run(["xdg-open", str(pdf_path)])
    except Exception as e:
        logging.error(f"Error abriendo PDF: {e}")

