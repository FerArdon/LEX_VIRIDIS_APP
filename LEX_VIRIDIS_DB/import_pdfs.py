
import sqlite3
import os
import re
import sys
import fitz  # PyMuPDF
from pathlib import Path
import logging

# Centralizar rutas usando config de la app
_APP_ROOT = Path(__file__).resolve().parent.parent
if str(_APP_ROOT) not in sys.path:
    sys.path.insert(0, str(_APP_ROOT))

try:
    from lexviridis.config import config as _app_config
    DB_PATH = _app_config.DB_DIR / "legislacion_ambiental.db"
    PDF_DIR = _app_config.PDF_DIR
except Exception:
    # Fallback para ejecución directa sin módulo config
    DB_PATH = _APP_ROOT / "LEX_VIRIDIS_DB" / "legislacion_ambiental.db"
    PDF_DIR = _APP_ROOT / "COMPENDIO LEYES FEMA"

logging.basicConfig(level=logging.INFO, format='%(message)s')

class PDFImporter:
    def __init__(self, db_path, pdf_dir):
        self.db_path = db_path
        self.pdf_dir = pdf_dir
        self.conn = None
        self.cursor = None

    def connect_db(self):
        self.conn = sqlite3.connect(str(self.db_path), timeout=15)
        self.conn.execute("PRAGMA journal_mode = WAL")
        self.conn.execute("PRAGMA synchronous = NORMAL")
        self.cursor = self.conn.cursor()

    def close_db(self):
        if self.conn:
            self.conn.commit()
            self.conn.close()

    def clean_text(self, text):
        """Limpia el texto extraído de saltos de línea innecesarios y espacios."""
        if not text: return ""
        # Unir líneas rotas por guiones
        text = re.sub(r'-\n', '', text)
        # Reemplazar múltiples saltos de línea y espacios por uno solo
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def extract_metadata_from_filename(self, filename):
        """Intenta inferir metadatos del nombre del archivo."""
        # Patrón simple: "Tipo Numero Titulo.pdf"
        # Ej: "Decreto 104-93 Ley General del Ambiente.pdf"
        
        tipo = "Desconocido"
        numero = ""
        titulo = filename.replace(".pdf", "")
        categoria = "General"

        lower_name = filename.lower()
        
        if "decreto" in lower_name:
            tipo = "Decreto"
        elif "ley" in lower_name:
            tipo = "Ley"
        elif "acuerdo" in lower_name:
            tipo = "Acuerdo"
        elif "reglamento" in lower_name:
            tipo = "Reglamento"
        
        if "forestal" in lower_name: categoria = "Forestal"
        elif "agua" in lower_name: categoria = "Agua"
        elif "penal" in lower_name: categoria = "Penal"
        elif "mina" in lower_name: categoria = "Minería"

        # Intentar extraer número (ej: 123-2020)
        num_match = re.search(r'(\d+-\d+)', filename)
        if num_match:
            numero = num_match.group(1)

        return tipo, numero, titulo, categoria

    def extract_articles(self, full_text):
        """
        Extrae artículos usando expresiones regulares robustas.
        Soporta: "ARTÍCULO 1.", "Art. 1", "ARTICULO PRIMERO:-"
        """
        articles = []
        
        # Patrón para el inicio de un artículo
        # Captura 1: Etiqueta (Artículo, Art.)
        # Captura 2: Número (1, 32-A, Primero)
        # Captura 3: Separador (.-, :, etc, opcional)
        pattern = r'(?:ART[ÍI]CULO|Art\.)\s*((?:\d+(?:-[A-Za-z])?)|(?:PRIMERO|SEGUNDO|TERCERO|CUARTO|QUINTO|SEXTO|SEPTIMO|OCTAVO|NOVENO|DECIMO))\s*[\.\:\-]*'
        
        matches = list(re.finditer(pattern, full_text, re.IGNORECASE))
        
        if not matches:
             # Fallback simple si no encuentra estructura clara
             return []

        for i in range(len(matches)):
            start_idx = matches[i].end()
            article_num = matches[i].group(1).upper()
            
            # El contenido va hasta el inicio del siguiente match o el final del texto
            if i < len(matches) - 1:
                end_idx = matches[i+1].start()
            else:
                end_idx = len(full_text)
            
            content = full_text[start_idx:end_idx].strip()
            
            # Limpieza básica
            content = self.clean_text(content)
            
            if content:
                articles.append((article_num, content))
        
        return articles

    def process_pdf(self, pdf_path):
        filename = pdf_path.name
        logging.info(f"📄 Procesando: {filename}")

        # 1. Extraer Metadatos
        tipo, numero, titulo, categoria = self.extract_metadata_from_filename(filename)

        try:
            # 2. Leer PDF — con fallback de stream para PDFs corrompidos/con encoding no estándar
            doc = None
            try:
                doc = fitz.open(str(pdf_path))
            except Exception as open_err:
                logging.warning(f"   ⚠️ fitz.open() falló ({open_err}), reintentando vía stream...")
                try:
                    raw_bytes = Path(pdf_path).read_bytes()
                    doc = fitz.open(stream=raw_bytes, filetype="pdf")
                except Exception as stream_err:
                    logging.error(f"❌ No se pudo abrir el PDF ni como stream: {stream_err}")
                    # Registrar la norma sin texto para que aparezca en el catálogo
                    self.cursor.execute("SELECT id FROM normas WHERE titulo = ?", (titulo,))
                    if not self.cursor.fetchone():
                        self.cursor.execute("""
                            INSERT OR IGNORE INTO normas
                                (tipo, numero, titulo, categoria, texto_completo, archivo_pdf, estado)
                            VALUES (?, ?, ?, ?, '', ?, 'VIGENTE')
                        """, (tipo, numero, titulo, categoria, Path(pdf_path).name))
                    return

            full_text = ""
            for page in doc:
                try:
                    page_text = page.get_text()
                except Exception:
                    try:
                        # Fallback: extraer texto como bytes y decodificar con tolerancia
                        page_text = page.get_text("rawdict")
                        page_text = str(page_text).encode("utf-8", errors="ignore").decode("utf-8")
                    except Exception:
                        page_text = ""
                # Sanitizar encoding: eliminar caracteres nulos y no imprimibles
                page_text = page_text.encode("utf-8", errors="ignore").decode("utf-8")
                full_text += page_text + "\n"
            doc.close()

            if not full_text.strip():
                logging.warning(f"⚠️ PDF escaneado (sin texto extraíble): {filename} — se registra la norma sin contenido")
                # Insertar la norma con metadatos del nombre aunque no haya texto,
                # para que aparezca en el catálogo y el usuario pueda abrirla.
                self.cursor.execute("SELECT id FROM normas WHERE titulo = ?", (titulo,))
                if not self.cursor.fetchone():
                    self.cursor.execute("""
                        INSERT OR IGNORE INTO normas
                            (tipo, numero, titulo, categoria, texto_completo, archivo_pdf, estado)
                        VALUES (?, ?, ?, ?, '', ?, 'VIGENTE')
                    """, (tipo, numero, titulo, categoria, str(pdf_path)))
                    logging.info(f"   ✅ Norma registrada sin texto (PDF escaneado): {titulo}")
                return

            # 3. Insertar Norma
            # Verificar si ya existe por título para no duplicar (o borrar previo)
            self.cursor.execute("SELECT id FROM normas WHERE titulo = ?", (titulo,))
            res = self.cursor.fetchone()
            
            if res:
                norma_id = res[0]
                logging.info(f"   ℹ️ Actualizando norma existente (ID: {norma_id})")
                self.cursor.execute("DELETE FROM articulos WHERE norma_id = ?", (norma_id,))
                self.cursor.execute("""
                    UPDATE normas SET texto_completo = ?, archivo_pdf = ?
                    WHERE id = ?
                """, (self.clean_text(full_text), Path(pdf_path).name, norma_id))
            else:
                self.cursor.execute("""
                    INSERT INTO normas (tipo, numero, titulo, categoria, texto_completo, archivo_pdf, estado)
                    VALUES (?, ?, ?, ?, ?, ?, 'VIGENTE')
                """, (tipo, numero, titulo, categoria, self.clean_text(full_text), Path(pdf_path).name))
                norma_id = self.cursor.lastrowid
                logging.info(f"   ✅ Nueva norma insertada (ID: {norma_id})")

            # 4. Extraer e Insertar Artículos
            articles = self.extract_articles(full_text)
            
            if articles:
                logging.info(f"   📝 Encontrados {len(articles)} artículos.")
                for num, content in articles:
                    self.cursor.execute("""
                        INSERT INTO articulos (norma_id, numero_articulo, contenido)
                        VALUES (?, ?, ?)
                    """, (norma_id, num, content))
            else:
                logging.warning("   ⚠️ No se detectaron artículos estructurados. Se confía en FTS sobre el texto completo.")
                
        except Exception as e:
            logging.error(f"❌ Error procesando {filename}: {e}")

    def run(self):
        if not self.pdf_dir.exists():
            logging.error(f"Directorio PDF no encontrado: {self.pdf_dir}")
            return
            
        self.connect_db()
        
        logging.info("🚀 Iniciando importación masiva...")
        
        pdfs = list(self.pdf_dir.glob("*.pdf"))
        logging.info(f"📚 Total PDFs encontrados: {len(pdfs)}")
        
        for pdf in pdfs:
            self.process_pdf(pdf)
            self.conn.commit()  # Commit por archivo: evita una transacción gigante que bloquea la BD

        self.close_db()
        logging.info("\n✨ Importación completada.")

if __name__ == "__main__":
    importer = PDFImporter(DB_PATH, PDF_DIR)
    importer.run()
