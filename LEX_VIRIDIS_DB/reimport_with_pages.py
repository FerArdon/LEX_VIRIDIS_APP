
"""
Script de Re-Importación con Páginas Correctas
LEX VIRIDIS - Corrige el problema de "Página 1"
"""

import sqlite3
import fitz  # PyMuPDF
import re
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(message)s')

BASE_DIR = Path(__file__).resolve().parent.parent
PDF_DIR = BASE_DIR / "COMPENDIO LEYES FEMA"
DB_PATH = BASE_DIR / "LEX_VIRIDIS_DB" / "legislacion_ambiental.db"

def add_page_column():
    """Añade la columna 'pagina' a la tabla articulos si no existe."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Verificar si la columna ya existe
    cursor.execute("PRAGMA table_info(articulos)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'pagina' not in columns:
        logging.info("➕ Agregando columna 'pagina' a tabla articulos...")
        cursor.execute("ALTER TABLE articulos ADD COLUMN pagina INTEGER DEFAULT 1")
        conn.commit()
        logging.info("✅ Columna agregada.")
    else:
        logging.info("ℹ️ Columna 'pagina' ya existe.")
    
    conn.close()

def reimport_with_pages():
    """Re-importa artículos guardando el número de página correcto."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    logging.info("\n🔄 Re-importando PDFs con números de página correctos...")
    
    # Limpiar tablas existentes para re-importar limpio
    cursor.execute("DELETE FROM articulos")
    cursor.execute("DELETE FROM busqueda_fts")
    
    pdfs = list(PDF_DIR.glob("*.pdf"))
    logging.info(f"📚 Total PDFs: {len(pdfs)}")
    
    total_articulos = 0
    
    for pdf_path in pdfs:
        try:
            filename = pdf_path.name
            logging.info(f"📄 {filename}")
            
            # Obtener norma_id correspondiente
            cursor.execute("SELECT id FROM normas WHERE archivo_pdf LIKE ?", (f'%{filename}%',))
            result = cursor.fetchone()
            
            if not result:
                # Insertar nueva norma si no existe
                tipo = "Decreto" if "decreto" in filename.lower() else "Ley"
                cursor.execute("INSERT INTO normas (tipo, titulo, archivo_pdf) VALUES (?, ?, ?)",
                              (tipo, filename.replace('.pdf', ''), str(pdf_path)))
                norma_id = cursor.lastrowid
            else:
                norma_id = result[0]
            
            # Abrir PDF y extraer artículos POR PÁGINA
            doc = fitz.open(pdf_path)
            
            for page_num in range(doc.page_count):
                page = doc[page_num]
                text = page.get_text()
                
                if not text:
                    continue
                
                # Buscar artículos en esta página específica
                # Patrón: "Artículo 123" o "Art. 123" o "ARTÍCULO 123"
                pattern = r'(?:ART[ÍI]CULO|Art\.?)\s*(\d+(?:-[A-Za-z])?)'
                matches = re.findall(pattern, text, re.IGNORECASE)
                
                for art_num in matches:
                    # Extraer un snippet de contexto (100 chars después del match)
                    match_obj = re.search(rf'(?:ART[ÍI]CULO|Art\.?)\s*{re.escape(art_num)}[^\n]*(.{{0,200}})', text, re.IGNORECASE | re.DOTALL)
                    contenido = match_obj.group(1).strip() if match_obj else "..."
                    
                    # Insertar artículo CON número de página real (page_num + 1 porque es 0-indexed)
                    cursor.execute("""
                        INSERT INTO articulos (norma_id, numero_articulo, contenido, pagina)
                        VALUES (?, ?, ?, ?)
                    """, (norma_id, art_num.upper(), contenido, page_num + 1))
                    
                    total_articulos += 1
            
            doc.close()
            
        except Exception as e:
            logging.error(f"   ❌ Error: {e}")
    
    conn.commit()
    
    # Reconstruir índice FTS
    logging.info("\n🔧 Reconstruyendo índice de búsqueda...")
    cursor.execute("""
        INSERT INTO busqueda_fts(titulo_norma, contenido_articulo, tags)
        SELECT n.titulo, a.contenido, n.categoria
        FROM articulos a
        JOIN normas n ON a.norma_id = n.id
    """)
    
    conn.commit()
    conn.close()
    
    logging.info(f"\n✨ Importación completada:")
    logging.info(f"   - Total artículos: {total_articulos}")
    logging.info(f"   - Páginas correctas: SÍ")

if __name__ == "__main__":
    add_page_column()
    reimport_with_pages()
