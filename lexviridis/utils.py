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
# Normalización de Rutas (OneDrive/Windows Fix)
# -----------------------------
def normalize_path(path_str: str) -> Path:
    """
    Normaliza rutas corrigiendo corrupción de caracteres común en OneDrive/Windows.
    Ej: 'VlRlDlS' -> 'VIRIDIS', 'COMPENDlO' -> 'COMPENDIO', 'LEX_VlRlDlS APP' -> 'LEX_VIRIDIS_APP'
    """
    if not path_str:
        return Path(".")

    # 1. Correcciones específicas
    fixed_str = str(path_str).replace("VlRlDlS", "VIRIDIS") \
                             .replace("COMPENDlO", "COMPENDIO") \
                             .replace("lLEX", "LEX") \
                             .replace("LEX_VIRIDIS APP", "LEX_VIRIDIS_APP") \
                             .replace("COMPENDIO LEYES FEMA", "COMPENDIO_LEYES_FEMA")

    return Path(fixed_str)

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

    # Usar normalización centralizada
    path = normalize_path(filename_or_path)
    # Corrección legacy específica de find_pdf_path si es necesario
    if 'COMPENDIO LEYES FEMA' in str(path):
        path = Path(str(path).replace('COMPENDIO LEYES FEMA', 'COMPENDIO_LEYES_FEMA'))

    # 1. Ruta directa
    if path.exists() and path.is_file():
        return path

    # 1.5. Si la ruta original contenía OneDrive, buscar en ubicaciones de OneDrive
    if 'OneDrive' in str(filename_or_path):
        onedrive_bases = [
            Path(r"C:\Users\frard\OneDrive\LEX_VIRIDIS_APP"),
            Path(r"F:\LEX_VIRIDIS_APP"),
        ]

        name = path.name
        for base in onedrive_bases:
            if base.exists():
                # Buscar en COMPENDIO_LEYES_FEMA
                candidate = base / "COMPENDIO_LEYES_FEMA" / name
                if candidate.exists():
                    logging.info(f"✓ PDF found in OneDrive: {candidate}")
                    return candidate

                # Búsqueda recursiva en OneDrive (puede ser lenta)
                try:
                    matches = list(base.rglob(name))
                    if matches:
                        logging.info(f"✓ PDF found via OneDrive recursive search: {matches[0]}")
                        return matches[0]
                except Exception:
                    pass

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
