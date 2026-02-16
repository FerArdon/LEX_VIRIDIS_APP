# lexviridis/utils.py

import contextlib
import gc
import io
import logging
import platform
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

import fitz  # PyMuPDF


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


# -----------------------------
# Búsqueda inteligente de PDFs
# -----------------------------
def find_pdf_path(filename_or_path: str) -> Path | None:
    """
    Intenta localizar un PDF usando varias estrategias.
    1. Ruta absoluta si existe.
    2. En el directorio configurado de PDFs.
    3. Búsqueda recursiva en el directorio de PDFs.
    4. Normalización de caracteres confusos (OneDrive/Windows).
    """
    if not filename_or_path:
        return None

    # Limpiar el path de caracteres confusos de OneDrive/Windows
    cleaned_path = filename_or_path.replace('VlRlDlS', 'VIRIDIS')
    cleaned_path = cleaned_path.replace('COMPENDlO', 'COMPENDIO')
    cleaned_path = cleaned_path.replace('COMPENDIO LEYES FEMA', 'COMPENDIO_LEYES_FEMA')

    path = Path(cleaned_path)

    # 1. Ruta directa
    if path.exists() and path.is_file():
        return path

    # Necesitamos config para saber el directorio base
    # Importamos aquí para evitar ciclos
    from .config import config

    pdf_dir = config.PDF_DIR
    if not pdf_dir.exists():
        logging.warning(f"PDF directory not found: {pdf_dir}")
        return None

    name = path.name

    # 2. En directorio PDF raíz
    candidate = pdf_dir / name
    if candidate.exists():
        return candidate

    # 3. Búsqueda recursiva (costosa, usar con cuidado)
    try:
        matches = list(pdf_dir.rglob(name))
        if matches:
            logging.info(f"PDF found via recursive search: {matches[0]}")
            return matches[0]
    except Exception as e:
        logging.warning(f"Error en búsqueda recursiva de PDF: {e}")

    logging.warning(f"PDF not found: {name} in {pdf_dir}")
    return None
