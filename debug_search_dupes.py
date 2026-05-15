import sqlite3
import re

db_path = 'E:/LEX_VIRIDIS_APP/LEX_VIRIDIS_DB/legislacion_ambiental.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

query = "sub productos"
fts_terms = ['"sub"', '"productos"']
fts_q = ' AND '.join(fts_terms)

print(f"--- FTS Query: {fts_q} ---")
cursor.execute("""
    SELECT
        f.articulo_id,
        f.titulo_norma,
        f.numero_articulo,
        snippet(busqueda_fts, 1, '<b>', '</b>', '...', 30) as fragmento,
        f.rank,
        a.pagina,
        a.contenido as contenido_completo,
        n.archivo_pdf
    FROM busqueda_fts f
    JOIN articulos a ON f.articulo_id = a.id
    JOIN normas n ON a.norma_id = n.id
    WHERE busqueda_fts MATCH ?
    ORDER BY rank
""", (fts_q,))

rows = cursor.fetchall()
print(f"Found {len(rows)} raw rows")
for row in rows:
    print(f"ID: {row['articulo_id']} | Art: {row['numero_articulo']} | Norma: {row['titulo_norma']}")

seen_ids = set()
unique_rows = []
for r in rows:
    if r['articulo_id'] not in seen_ids:
        unique_rows.append(r)
        seen_ids.add(r['articulo_id'])

print(f"After deduplication: {len(unique_rows)}")
for ur in unique_rows:
    print(f"ID: {ur['articulo_id']} | File: {ur['archivo_pdf']}")

conn.close()
