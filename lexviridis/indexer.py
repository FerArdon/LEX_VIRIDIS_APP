# lexviridis/indexer.py

import logging
import pickle
import threading
from pathlib import Path

import fitz

from .config import config
from .utils import MemoryOptimizer, PDFValidator, normalize_text, suppress_stderr


class Indexer:
    def __init__(self, update_callback=None):
        self.text_index: dict[str, dict[int, str]] = {}
        self.index_ready = False
        self.update_callback = update_callback  # Para GUI opcional

    def load_or_create_index(self, force_rebuild=False):
        should_reindex = True
        last_modified: dict[str, float] = {}

        if not force_rebuild and config.INDEX_FILE.exists():
            try:
                with open(config.INDEX_FILE, 'rb') as f:
                    data = pickle.load(f)
                if data.get('version') == config.database.index_version:
                    self.text_index = data.get('index', {})
                    last_modified = data.get('last_modified', {})
                    should_reindex = self._needs_update(last_modified)
                    if not should_reindex:
                        self.index_ready = True
                        logging.info("Índice cargado y actualizado.")
                else:
                    logging.info("Versión de índice diferente, se regenerará.")
            except Exception as e:
                logging.warning(f"No se pudo cargar índice: {e}")

        if should_reindex:
            self._create_new_index(last_modified)

        self._save_index()

    def _needs_update(self, old_modified: dict[str, float]) -> bool:
        current_files = {str(p.resolve()): p.stat().st_mtime for p in config.PDF_DIR.glob("*.pdf")}
        for path, mtime in current_files.items():
            if path not in old_modified or old_modified[path] < mtime:
                return True
        if any(path not in current_files for path in old_modified):
            return True
        return False

    def _create_new_index(self, last_modified: dict[str, float]):
        self.text_index.clear()
        last_modified.clear()

        pdf_files = list(config.PDF_DIR.glob("*.pdf"))
        total = len(pdf_files)
        logging.info(f"Indexando {total} archivos...")

        for i, pdf_path in enumerate(pdf_files):
            path_str = str(pdf_path.resolve())
            try:
                is_valid, msg = PDFValidator.validate_pdf(pdf_path)
                if not is_valid:
                    logging.warning(f"{pdf_path.name} omitido: {msg}")
                    continue

                with MemoryOptimizer.operation():
                    doc = fitz.open(pdf_path)
                    self.text_index[path_str] = {}

                    for page_num in range(doc.page_count):
                        try:
                            with suppress_stderr():
                                try:
                                    text = doc[page_num].get_text("text")
                                except RuntimeError as re:
                                    if "unknown colorspace" in str(re).lower():
                                        logging.warning(f"Colorespace desconocido en página {page_num} de {pdf_path.name}, página omitida.")
                                        continue
                                    else:
                                        raise
                                if text:
                                    self.text_index[path_str][page_num] = normalize_text(text)
                        except Exception as pe:
                            logging.warning(f"Error en página {page_num} de {pdf_path.name}: {pe}")
                    doc.close()
                    last_modified[path_str] = pdf_path.stat().st_mtime
            except Exception as e:
                logging.error(f"Error procesando {pdf_path.name}: {e}")

            if self.update_callback:
                self.update_callback(i + 1, total)

        self.index_ready = True

    def _save_index(self):
        try:
            config.INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(config.INDEX_FILE, 'wb') as f:
                pickle.dump({
                    'version': config.database.index_version,
                    'index': self.text_index,
                    'last_modified': {
                        path: Path(path).stat().st_mtime
                        for path in self.text_index
                        if Path(path).exists()
                    }
                }, f)
            logging.info("Índice guardado correctamente.")
        except Exception as e:
            logging.error(f"No se pudo guardar el índice: {e}")

    def start_indexing(self):
        thread = threading.Thread(target=self.load_or_create_index, daemon=True)
        thread.start()
