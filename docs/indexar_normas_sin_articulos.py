"""
indexar_normas_sin_articulos.py
================================
Parsea los PDFs de normas que tienen 0 artículos indexados y texto seleccionable.
Para cada norma:
  1. Extrae el texto completo del PDF y guarda en normas.texto_completo
  2. Detecta artículos (ARTÍCULO N / ARTÍCULO N.- / Art. N) y los inserta
     en la tabla articulos con su contenido.
  3. Actualiza busqueda_fts con todos los artículos nuevos.

Uso:
    python docs/indexar_normas_sin_articulos.py
    python docs/indexar_normas_sin_articulos.py --norma-id 183
    python docs/indexar_normas_sin_articulos.py --dry-run
"""
import sys, os, re, sqlite3, argparse

# Asegura que corremos desde la raíz del proyecto
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "LEX_VIRIDIS_DB", "legislacion_ambiental.db")
PDF_DIR = os.path.join(ROOT, "COMPENDIO LEYES FEMA")

try:
    import fitz  # PyMuPDF
except ImportError:
    sys.exit("ERROR: Instala PyMuPDF →  pip install pymupdf")


# ── Regex para detectar inicio de artículo ─────────────────────────────────
ART_PATTERN = re.compile(
    r'^(?:ARTÍCULO|ARTICULO|Art\.?)\s*\.?\s*(\d+[\w\-]*)\s*[\.\-:]?\s*(.*)',
    re.IGNORECASE | re.MULTILINE
)


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extrae todo el texto de un PDF con PyMuPDF."""
    try:
        doc = fitz.open(pdf_path)
        pages = [doc[i].get_text() for i in range(doc.page_count)]
        return "\n".join(pages)
    except Exception as e:
        print(f"    ERROR leyendo PDF: {e}")
        return ""


def parse_articles(full_text: str) -> list[dict]:
    """
    Divide el texto completo en artículos numerados.
    Retorna lista de {numero, titulo, contenido}.
    Si no detecta ningún ARTÍCULO, retorna lista vacía.
    """
    articles = []
    # Buscar todos los inicios de artículo
    matches = list(ART_PATTERN.finditer(full_text))
    if not matches:
        return []

    for i, m in enumerate(matches):
        num = m.group(1).strip()
        titulo_inline = m.group(2).strip() if m.group(2) else ""
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
        contenido = full_text[start:end].strip()
        # Limpiar saltos de página y exceso de espacios
        contenido = re.sub(r'\n{3,}', '\n\n', contenido)
        contenido = contenido[:6000]  # Límite de seguridad
        articles.append({
            "numero": num,
            "titulo": titulo_inline[:200] if titulo_inline else None,
            "contenido": contenido,
        })
    return articles


def find_pdf(pdf_path_db: str) -> str | None:
    """Resuelve la ruta del PDF priorizando la carpeta local."""
    if not pdf_path_db:
        return None
    fname = os.path.basename(pdf_path_db)
    local = os.path.join(PDF_DIR, fname)
    if os.path.exists(local):
        return local
    if os.path.exists(pdf_path_db):
        return pdf_path_db
    return None


def index_norma(conn: sqlite3.Connection, norma: dict, dry_run: bool) -> dict:
    """Procesa una norma: extrae texto + artículos → inserta en BD."""
    c = conn.cursor()
    norma_id = norma["id"]
    titulo = norma["titulo"]

    pdf_path = find_pdf(norma["archivo_pdf"])
    if not pdf_path:
        return {"status": "NO_FILE", "arts": 0}

    full_text = extract_text_from_pdf(pdf_path)
    if not full_text.strip():
        return {"status": "SCAN/EMPTY", "arts": 0}

    articles = parse_articles(full_text)
    status = "TEXT_ONLY" if not articles else "PARSED"

    if not dry_run:
        # 1. Guardar texto_completo
        c.execute(
            "UPDATE normas SET texto_completo=? WHERE id=?",
            (full_text[:500_000], norma_id)  # límite 500k chars
        )
        # 2. Insertar artículos
        for art in articles:
            c.execute("""
                INSERT OR IGNORE INTO articulos
                    (norma_id, numero_articulo, titulo_articulo, contenido, estado, pagina)
                VALUES (?, ?, ?, ?, 'VIGENTE', 1)
            """, (norma_id, art["numero"], art["titulo"], art["contenido"]))

        # 3. Actualizar FTS para los artículos nuevos
        c.execute("""
            INSERT INTO busqueda_fts (titulo_norma, contenido_articulo, numero_articulo, articulo_id)
            SELECT ?, a.contenido, a.numero_articulo, a.id
            FROM articulos a
            WHERE a.norma_id = ?
              AND a.id NOT IN (SELECT articulo_id FROM busqueda_fts)
        """, (titulo, norma_id))

        # 4. Si no hay artículos pero sí texto, al menos indexar el texto_completo
        #    como un "artículo" virtual para que el FTS lo encuentre
        if not articles and full_text.strip():
            c.execute("""
                SELECT COUNT(*) FROM articulos WHERE norma_id=?
            """, (norma_id,))
            if c.fetchone()[0] == 0:
                c.execute("""
                    INSERT INTO articulos (norma_id, numero_articulo, titulo_articulo, contenido, estado, pagina)
                    VALUES (?, 'Documento completo', ?, ?, 'VIGENTE', 1)
                """, (norma_id, titulo[:200], full_text[:6000]))
                art_id = c.lastrowid
                c.execute("""
                    INSERT INTO busqueda_fts (titulo_norma, contenido_articulo, numero_articulo, articulo_id)
                    VALUES (?, ?, 'Documento completo', ?)
                """, (titulo, full_text[:6000], art_id))

        conn.commit()

    return {"status": status, "arts": len(articles)}


def main():
    parser = argparse.ArgumentParser(description="Indexa normas sin artículos")
    parser.add_argument("--norma-id", type=int, help="Procesar solo esta norma")
    parser.add_argument("--dry-run", action="store_true", help="Solo reporta, no modifica BD")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Obtener normas con 0 artículos
    c = conn.cursor()
    if args.norma_id:
        c.execute("""
            SELECT n.id, n.titulo, n.archivo_pdf, COUNT(a.id) as arts
            FROM normas n LEFT JOIN articulos a ON a.norma_id=n.id
            WHERE n.id=?
            GROUP BY n.id
        """, (args.norma_id,))
    else:
        c.execute("""
            SELECT n.id, n.titulo, n.archivo_pdf, COUNT(a.id) as arts
            FROM normas n LEFT JOIN articulos a ON a.norma_id=n.id
            WHERE n.archivo_pdf IS NOT NULL AND n.archivo_pdf != ''
            GROUP BY n.id HAVING arts=0
            ORDER BY n.id
        """)

    normas = [dict(r) for r in c.fetchall()]
    print(f"{'[DRY-RUN] ' if args.dry_run else ''}Procesando {len(normas)} normas...\n")

    totals = {"processed": 0, "arts_added": 0, "scans": 0, "no_file": 0}

    for norma in normas:
        print(f"  ID={norma['id']} | {norma['titulo'][:60]}")
        result = index_norma(conn, norma, args.dry_run)
        print(f"    -> {result['status']} | articulos: {result['arts']}")
        totals["processed"] += 1
        totals["arts_added"] += result["arts"]
        if result["status"] == "SCAN/EMPTY":
            totals["scans"] += 1
        elif result["status"] == "NO_FILE":
            totals["no_file"] += 1

    conn.close()

    print(f"\n{'='*60}")
    print(f"  Normas procesadas : {totals['processed']}")
    print(f"  Artículos añadidos: {totals['arts_added']}")
    print(f"  PDFs escaneados   : {totals['scans']} (no procesables sin OCR)")
    print(f"  Sin archivo local : {totals['no_file']}")
    if args.dry_run:
        print("\n  [DRY-RUN] No se realizaron cambios. Ejecuta sin --dry-run para aplicar.")


if __name__ == "__main__":
    main()
