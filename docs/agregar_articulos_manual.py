"""
agregar_articulos_manual.py
============================
Script de utilidad para ingresar manualmente artículos de normas cuyos
PDFs son escaneados y no tienen texto seleccionable.

Uso:
    python docs/agregar_articulos_manual.py --norma-id 183 --articulo 48 \
        --titulo "Zonas de Exclusion" \
        --contenido "ARTICULO 48. ZONAS DE EXCLUSION: ..."

    python docs/agregar_articulos_manual.py --norma-id 183 --desde-archivo arts_mineria.txt

    python docs/agregar_articulos_manual.py --listar-vacias

Formato del archivo de texto:
    ===ARTICULO 48===
    TITULO: Zonas de Exclusión
    CONTENIDO:
    Texto del artículo...
    ===ARTICULO 49===
    ...
"""
import sys, os, re, sqlite3, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "LEX_VIRIDIS_DB", "legislacion_ambiental.db")


def get_norma(conn, norma_id):
    c = conn.cursor()
    c.execute("SELECT id, titulo, estado FROM normas WHERE id=?", (norma_id,))
    return c.fetchone()


def insert_article(conn, norma_id, titulo_norma, numero, titulo_art, contenido, estado="VIGENTE"):
    c = conn.cursor()
    # Verificar si ya existe
    c.execute(
        "SELECT id FROM articulos WHERE norma_id=? AND numero_articulo=?",
        (norma_id, str(numero))
    )
    existing = c.fetchone()
    if existing:
        c.execute(
            "UPDATE articulos SET contenido=?, titulo_articulo=?, estado=? WHERE id=?",
            (contenido, titulo_art, estado, existing["id"])
        )
        art_id = existing["id"]
        action = "UPDATED"
    else:
        c.execute("""
            INSERT INTO articulos (norma_id, numero_articulo, titulo_articulo, contenido, estado, pagina)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (norma_id, str(numero), titulo_art, contenido, estado))
        art_id = c.lastrowid
        action = "INSERTED"

    # Eliminar entrada FTS vieja si existe
    c.execute("DELETE FROM busqueda_fts WHERE articulo_id=?", (art_id,))
    # Insertar/actualizar FTS
    c.execute("""
        INSERT INTO busqueda_fts (titulo_norma, contenido_articulo, numero_articulo, articulo_id)
        VALUES (?, ?, ?, ?)
    """, (titulo_norma, contenido, str(numero), art_id))
    conn.commit()
    return action, art_id


def parse_from_file(filepath: str) -> list[dict]:
    """Lee artículos desde archivo con formato === ARTICULO N === ..."""
    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    articles = []
    blocks = re.split(r'={3,}ARTICULO\s+(\S+)={3,}', content, flags=re.IGNORECASE)
    # blocks: [prefix, num, body, num, body, ...]
    i = 1
    while i < len(blocks) - 1:
        num = blocks[i].strip()
        body = blocks[i + 1].strip()
        titulo_match = re.match(r'TITULO:\s*(.+)', body, re.IGNORECASE)
        titulo = titulo_match.group(1).strip() if titulo_match else None
        contenido_match = re.search(r'CONTENIDO:\s*([\s\S]+)', body, re.IGNORECASE)
        contenido = contenido_match.group(1).strip() if contenido_match else body
        articles.append({"numero": num, "titulo": titulo, "contenido": contenido})
        i += 2
    return articles


def cmd_listar_vacias(conn):
    c = conn.cursor()
    c.execute("""
        SELECT n.id, n.titulo, n.archivo_pdf, COUNT(a.id) as arts
        FROM normas n LEFT JOIN articulos a ON a.norma_id=n.id
        GROUP BY n.id HAVING arts=0
        ORDER BY n.id
    """)
    print("Normas sin articulos indexados:")
    for r in c.fetchall():
        print(f"  ID={r['id']} | {r['titulo'][:60]}")
        print(f"          PDF: {r['archivo_pdf'] or '(sin PDF)'}")


def main():
    parser = argparse.ArgumentParser(description="Agregar articulos manualmente a normas escaneadas")
    parser.add_argument("--norma-id", type=int, help="ID de la norma")
    parser.add_argument("--articulo", help="Numero del articulo (ej: 48, 32-A)")
    parser.add_argument("--titulo", default="", help="Titulo del articulo (opcional)")
    parser.add_argument("--contenido", help="Texto completo del articulo")
    parser.add_argument("--estado", default="VIGENTE", choices=["VIGENTE", "DEROGADA"])
    parser.add_argument("--desde-archivo", help="Ruta a archivo .txt con multiples articulos")
    parser.add_argument("--listar-vacias", action="store_true",
                        help="Lista todas las normas sin articulos")

    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    if args.listar_vacias:
        cmd_listar_vacias(conn)
        return

    if not args.norma_id:
        parser.error("--norma-id es requerido")

    norma = get_norma(conn, args.norma_id)
    if not norma:
        sys.exit(f"ERROR: No existe norma con ID={args.norma_id}")

    titulo_norma = norma["titulo"]
    print(f"Norma: {titulo_norma} (ID={args.norma_id})")

    if args.desde_archivo:
        articles = parse_from_file(args.desde_archivo)
        print(f"Leyendo {len(articles)} articulos desde {args.desde_archivo}...")
        for art in articles:
            action, art_id = insert_article(
                conn, args.norma_id, titulo_norma,
                art["numero"], art["titulo"], art["contenido"], args.estado
            )
            print(f"  [{action}] Art. {art['numero']} (id={art_id})")
    elif args.articulo and args.contenido:
        action, art_id = insert_article(
            conn, args.norma_id, titulo_norma,
            args.articulo, args.titulo, args.contenido, args.estado
        )
        print(f"[{action}] Art. {args.articulo} (id={art_id})")
    else:
        parser.error("Proporciona --articulo + --contenido, o bien --desde-archivo")

    conn.close()
    print("Listo.")


if __name__ == "__main__":
    main()
