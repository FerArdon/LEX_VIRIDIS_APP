# lexviridis/pdf_viewer_fixed.py

import logging
import os
import platform
import subprocess
import tempfile
from pathlib import Path

import fitz  # PyMuPDF

from .utils import open_with_native_viewer


class PDFViewerFixed:
    """
    Visor de PDF mejorado que funciona correctamente en ejecutables PyInstaller.
    Soluciona problemas de directorios temporales y permisos.
    """

    @staticmethod
    def get_temp_directory() -> Path:
        """
        Obtiene un directorio temporal confiable que funciona en ejecutables.
        """
        try:
            # Intentar usar directorio de la aplicación primero
            if hasattr(sys, "_MEIPASS"):
                # Estamos en un ejecutable PyInstaller
                app_dir = Path(sys._MEIPASS).parent
                temp_dir = app_dir / "temp_pdfs"
            else:
                # Desarrollo normal
                temp_dir = Path.cwd() / "temp_pdfs"

            # Crear directorio si no existe
            temp_dir.mkdir(exist_ok=True)

            # Verificar permisos de escritura
            test_file = temp_dir / "test_write.tmp"
            try:
                test_file.write_text("test")
                test_file.unlink()
                return temp_dir
            except:
                # Si no podemos escribir, usar directorio temporal del sistema
                return Path(tempfile.gettempdir()) / "lex_viridis_temp"

        except Exception as e:
            logging.warning(f"Error obteniendo directorio temporal personalizado: {e}")
            # Fallback al directorio temporal del sistema
            temp_dir = Path(tempfile.gettempdir()) / "lex_viridis_temp"
            temp_dir.mkdir(exist_ok=True)
            return temp_dir

    @staticmethod
    def highlight_and_open_pdf(
        pdf_path: Path,
        page_number: int,
        search_term: str,
        highlight_color: tuple[float, float, float] = (0.7, 0.9, 0.9),  # Azul turquesa pálido
        temp_dir: Path | None = None,
    ) -> None:
        """
        Abre un PDF en la página específica con el término de búsqueda resaltado.
        Versión mejorada para ejecutables.
        """
        try:
            # Validar PDF
            if not pdf_path.exists():
                raise FileNotFoundError(f"PDF no encontrado: {pdf_path}")

            logging.info(f"[FIXED] Abriendo PDF: {pdf_path.name}, página {page_number}, término: '{search_term}'")

            # Usar directorio temporal confiable
            if temp_dir is None:
                temp_dir = PDFViewerFixed.get_temp_directory()

            # Crear PDF temporal con resaltados
            temp_pdf = PDFViewerFixed._create_highlighted_pdf_safe(
                pdf_path,
                page_number - 1,  # PyMuPDF usa base 0
                search_term,
                highlight_color,
                temp_dir,
            )

            if temp_pdf and temp_pdf.exists():
                # Abrir PDF temporal
                PDFViewerFixed._open_pdf_safe(temp_pdf)
                logging.info(f"✅ [FIXED] PDF con resaltado abierto: {temp_pdf.name}")
            else:
                # Fallback: abrir PDF original
                logging.warning("[FIXED] No se pudo crear PDF temporal, abriendo original")
                open_with_native_viewer(pdf_path)

        except Exception as e:
            logging.error(f"❌ [FIXED] Error al abrir PDF: {e}")
            # Fallback: abrir PDF original sin resaltado
            try:
                logging.info("[FIXED] Usando fallback: PDF original")
                open_with_native_viewer(pdf_path)
            except Exception as fallback_error:
                logging.error(f"❌ [FIXED] Error en fallback: {fallback_error}")
                raise

    @staticmethod
    def open_pdf_simple(pdf_path: Path):
        """
        Abre un PDF directamente sin resaltado.
        """
        try:
            if not pdf_path.exists():
                logging.error(f"PDF no encontrado: {pdf_path}")
                raise FileNotFoundError(f"PDF no encontrado: {pdf_path}")

            logging.info(f"[FIXED] Abriendo PDF simple: {pdf_path.name}")
            open_with_native_viewer(pdf_path)
        except Exception as e:
            logging.error(f"Error abriendo PDF: {e}")
            raise

    @staticmethod
    def _create_highlighted_pdf_safe(
        pdf_path: Path, page_index: int, search_term: str, highlight_color: tuple[float, float, float], temp_dir: Path
    ) -> Path | None:
        """
        Genera un PDF temporal con el texto resaltado de forma segura.
        """
        doc = None
        temp_pdf = None

        try:
            logging.info(f"[FIXED] Creando PDF resaltado para: {search_term}")

            # Abrir documento
            doc = fitz.open(pdf_path)

            # Validar índice de página
            if page_index < 0 or page_index >= doc.page_count:
                logging.warning(f"[FIXED] Página {page_index + 1} fuera de rango. Total páginas: {doc.page_count}")
                page_index = 0  # Usar primera página como fallback

            # Buscar todas las instancias del término en la página
            page = doc[page_index]

            # Buscar término completo y palabras individuales
            search_terms = PDFViewerFixed._prepare_search_terms(search_term)
            total_highlights = 0

            for term in search_terms:
                try:
                    # Buscar término (case insensitive)
                    text_instances = page.search_for(term, quads=True)

                    # También buscar en minúsculas
                    if not text_instances:
                        text_instances = page.search_for(term.lower(), quads=True)

                    # También buscar en mayúsculas
                    if not text_instances:
                        text_instances = page.search_for(term.upper(), quads=True)

                    if text_instances:
                        # Resaltar cada coincidencia
                        for quad in text_instances:
                            try:
                                annot = page.add_highlight_annot(quad)
                                annot.set_colors(stroke=highlight_color)
                                annot.update()
                                total_highlights += 1
                            except Exception as e:
                                logging.warning(f"[FIXED] Error al resaltar '{term}': {e}")

                except Exception as e:
                    logging.warning(f"[FIXED] Error buscando término '{term}': {e}")

            logging.info(f"[FIXED] Resaltadas {total_highlights} coincidencias de '{search_term}'")

            # Crear nombre único para el archivo temporal
            import time

            timestamp = int(time.time())
            safe_filename = "".join(c for c in pdf_path.stem if c.isalnum() or c in (" ", "-", "_")).rstrip()
            temp_pdf = temp_dir / f"highlighted_{timestamp}_{safe_filename}.pdf"

            # Asegurar que el directorio existe
            temp_dir.mkdir(parents=True, exist_ok=True)

            # Guardar PDF temporal
            doc.save(str(temp_pdf))

            if temp_pdf.exists():
                logging.info(f"✅ [FIXED] PDF temporal creado: {temp_pdf}")
                return temp_pdf
            else:
                logging.error("❌ [FIXED] PDF temporal no se creó correctamente")
                return None

        except Exception as e:
            logging.error(f"❌ [FIXED] Error creando PDF resaltado: {e}")
            return None
        finally:
            if doc:
                try:
                    doc.close()
                except:
                    pass

    @staticmethod
    def _prepare_search_terms(search_term: str) -> list[str]:
        """
        Prepara términos de búsqueda para resaltado mejorado.
        """
        terms = []

        # Limpiar término
        clean_term = search_term.strip()
        if not clean_term:
            return terms

        # Agregar término completo
        terms.append(clean_term)

        # Agregar palabras individuales si es una frase (solo palabras > 2 caracteres)
        if " " in clean_term:
            words = [word.strip() for word in clean_term.split() if len(word.strip()) > 2]
            terms.extend(words)

        # Remover duplicados manteniendo orden
        seen = set()
        unique_terms = []
        for term in terms:
            if term and term.lower() not in seen:
                seen.add(term.lower())
                unique_terms.append(term)

        logging.info(f"[FIXED] Términos de búsqueda preparados: {unique_terms}")
        return unique_terms

    @staticmethod
    def _open_pdf_safe(pdf_path: Path) -> None:
        """
        Abre el PDF de forma segura y confiable.
        """
        try:
            logging.info(f"[FIXED] Abriendo PDF: {pdf_path}")

            if platform.system() == "Windows":
                # Windows: usar start con comillas para manejar espacios
                os.system(f'start "" "{str(pdf_path)}"')
            elif platform.system() == "Darwin":
                # macOS
                subprocess.run(["open", str(pdf_path)], check=True)
            else:
                # Linux
                subprocess.run(["xdg-open", str(pdf_path)], check=True)

            logging.info("✅ [FIXED] PDF abierto exitosamente")

        except Exception as e:
            logging.error(f"❌ [FIXED] Error abriendo PDF: {e}")
            # Fallback usando el método original
            open_with_native_viewer(pdf_path)

    @staticmethod
    def open_pdf_simple(pdf_path: Path, page_number: int = 1) -> None:
        """
        Abre un PDF sin resaltado en la página específica.
        """
        try:
            if not pdf_path.exists():
                raise FileNotFoundError(f"PDF no encontrado: {pdf_path}")

            logging.info(f"[FIXED] Abriendo PDF simple: {pdf_path.name}, página {page_number}")
            PDFViewerFixed._open_pdf_safe(pdf_path)

        except Exception as e:
            logging.error(f"❌ [FIXED] Error abriendo PDF simple: {e}")
            raise

    @staticmethod
    def cleanup_temp_files(temp_dir: Path | None = None, max_age_hours: int = 24) -> None:
        """
        Elimina archivos PDF temporales antiguos de forma segura.
        """
        try:
            if temp_dir is None:
                temp_dir = PDFViewerFixed.get_temp_directory()

            if not temp_dir.exists():
                return

            import time

            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            cleaned_count = 0

            for file in temp_dir.glob("highlighted_*.pdf"):
                try:
                    # Verificar edad del archivo
                    file_age = current_time - file.stat().st_mtime

                    if file_age > max_age_seconds:
                        file.unlink()
                        cleaned_count += 1
                        logging.debug(f"[FIXED] Archivo temporal eliminado: {file.name}")

                except Exception as e:
                    logging.warning(f"[FIXED] No se pudo eliminar {file}: {e}")

            if cleaned_count > 0:
                logging.info(f"✅ [FIXED] Limpieza completada: {cleaned_count} archivos temporales eliminados")

        except Exception as e:
            logging.error(f"❌ [FIXED] Error en limpieza de archivos temporales: {e}")


# Función de conveniencia mejorada
def open_pdf_with_highlight_fixed(pdf_path: Path, page_number: int, search_term: str) -> None:
    """
    Función de conveniencia mejorada para abrir PDF con resaltado.
    """
    PDFViewerFixed.highlight_and_open_pdf(pdf_path, page_number, search_term)


# Importar sys para detectar PyInstaller
# Limpieza automática al importar el módulo
import atexit
import sys

atexit.register(lambda: PDFViewerFixed.cleanup_temp_files())
