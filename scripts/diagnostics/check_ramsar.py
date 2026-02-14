import sqlite3

conn = sqlite3.connect(r'c:\Users\frard\OneDrive\LEX_VIRIDIS_APP\LEX_VIRIDIS_DB\legislacion_ambiental.db')
cur = conn.cursor()

# Buscar Ramsar en titulo de normas
print("=== Buscando 'ramsar' en normas.titulo ===")
cur.execute("SELECT id, titulo, tipo FROM normas WHERE titulo LIKE '%ramsar%' COLLATE NOCASE OR titulo LIKE '%humedales%' COLLATE NOCASE")
for r in cur.fetchall():
    print(f"  ID: {r[0]}, Tipo: {r[2]}, Titulo: {r[1][:80]}")

# Buscar en contenido de articulos
print("\n=== Buscando 'ramsar' en articulos.contenido ===")
cur.execute("SELECT a.id, a.titulo_articulo, n.titulo FROM articulos a JOIN normas n ON a.norma_id = n.id WHERE a.contenido LIKE '%ramsar%' COLLATE NOCASE LIMIT 5")
for r in cur.fetchall():
    print(f"  Art ID: {r[0]}, Titulo Art: {r[1][:40] if r[1] else 'Sin titulo'}, Norma: {r[2][:50] if r[2] else 'Sin norma'}")

# Buscar en FTS
print("\n=== Buscando en busqueda_fts ===")
try:
    cur.execute("SELECT * FROM busqueda_fts WHERE busqueda_fts MATCH 'ramsar' LIMIT 5")
    results = cur.fetchall()
    print(f"Resultados FTS: {len(results)}")
    for r in results:
        print(f"  {r}")
except Exception as e:
    print(f"Error FTS: {e}")

conn.close()
