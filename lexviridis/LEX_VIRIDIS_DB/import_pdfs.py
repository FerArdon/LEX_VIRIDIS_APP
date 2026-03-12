import logging
import re
import sqlite3
from pathlib import Path

import fitz  # PyMuPDF

# Configuración
BASE_DIR = Path(r"c:\Users\frard\OneDrive\LEX_VIRIDIS_APP")
PDF_DIR = BASE_DIR / "COMPENDIO LEYES FEMA"
DB_PATH = BASE_DIR / "LEX_VIRIDIS_DB" / "legislacion_ambiental.db"

logging.basicConfig(level=logging.INFO, format="%(message)s")


class PDFImporter:
    def __init__(self, db_path, pdf_dir):
        self.db_path = db_path
        self.pdf_dir = pdf_dir
        self.conn = None
        self.cursor = None

    def connect_db(self):
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def close_db(self):
        if self.conn:
            self.conn.commit()
            self.conn.close()

    def clean_text(self, text):
        """Limpia el texto extraído de saltos de línea innecesarios y espacios."""
        if not text:
            return ""
        # Unir líneas rotas por guiones
        text = re.sub(r"-\n", "", text)
        # Reemplazar múltiples saltos de línea y espacios por uno solo
        text = re.sub(r"\s+", " ", text).strip()
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

        if "forestal" in lower_name:
            categoria = "Forestal"
        elif "agua" in lower_name:
            categoria = "Agua"
        elif "penal" in lower_name:
            categoria = "Penal"
        elif "mina" in lower_name:
            categoria = "Minería"

        # Intentar extraer número (ej: 123-2020)
        num_match = re.search(r"(\d+-\d+)", filename)
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
        pattern = r"(?:ART[ÍI]CULO|Art\.)\s*((?:\d+(?:-[A-Za-z])?)|(?:PRIMERO|SEGUNDO|TERCERO|CUARTO|QUINTO|SEXTO|SEPTIMO|OCTAVO|NOVENO|DECIMO))\s*[\.\:\-]*"

        matches = list(re.finditer(pattern, full_text, re.IGNORECASE))

        if not matches:
            # Fallback simple si no encuentra estructura clara
            return []

        for i in range(len(matches)):
            start_idx = matches[i].end()
            article_num = matches[i].group(1).upper()

            # El contenido va hasta el inicio del siguiente match o el final del texto
            if i < len(matches) - 1:
                end_idx = matches[i + 1].start()
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
            # 2. Leer PDF
            doc = fitz.open(pdf_path)
            full_text = ""
            for page in doc:
                full_text += page.get_text() + "\n"
            doc.close()

            if not full_text.strip():
                logging.warning(f"⚠️ PDF vacío o imagen escaneada (OCR requerido): {filename}")
                return

            # 3. Insertar Norma
            # Verificar si ya existe por título para no duplicar (o borrar previo)
            self.cursor.execute("SELECT id FROM normas WHERE titulo = ?", (titulo,))
            res = self.cursor.fetchone()

            if res:
                norma_id = res[0]
                logging.info(f"   ℹ️ Actualizando norma existente (ID: {norma_id})")
                self.cursor.execute("DELETE FROM articulos WHERE norma_id = ?", (norma_id,))
                self.cursor.execute(
                    """
                    UPDATE normas SET texto_completo = ?, archivo_pdf = ?
                    WHERE id = ?
                """,
                    (self.clean_text(full_text), str(pdf_path), norma_id),
                )
            else:
                self.cursor.execute(
                    """
                    INSERT INTO normas (tipo, numero, titulo, categoria, texto_completo, archivo_pdf, estado)
                    VALUES (?, ?, ?, ?, ?, ?, 'VIGENTE')
                """,
                    (tipo, numero, titulo, categoria, self.clean_text(full_text), str(pdf_path)),
                )
                norma_id = self.cursor.lastrowid
                logging.info(f"   ✅ Nueva norma insertada (ID: {norma_id})")

            # 4. Extraer e Insertar Artículos
            articles = self.extract_articles(full_text)

            if articles:
                logging.info(f"   📝 Encontrados {len(articles)} artículos.")
                for num, content in articles:
                    self.cursor.execute(
                        """
                        INSERT INTO articulos (norma_id, numero_articulo, contenido)
                        VALUES (?, ?, ?)
                    """,
                        (norma_id, num, content),
                    )
            else:
                logging.warning(
                    "   ⚠️ No se detectaron artículos estructurados. Se confía en FTS sobre el texto completo."
                )

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

        self.close_db()
        logging.info("\n✨ Importación completada.")


if __name__ == "__main__":
    importer = PDFImporter(DB_PATH, PDF_DIR)
    importer.run()
