
"""
Reconstruye el índice FTS5 correctamente (sin content sync).
"""
import sqlite3
from pathlib import Path

DB = Path(r"c:\Users\frard\OneDrive\LEX_VIRIDIS_APP\LEX_VIRIDIS_DB\legislacion_ambiental.db")

conn = sqlite3.connect(DB)
c = conn.cursor()

print("🔧 Reconstruyendo índice FTS5...")

# 1. Borrar tabla FTS anterior
print("1. Eliminando FTS anterior...")
c.execute("DROP TABLE IF EXISTS busqueda_fts")

# 2. Crear tabla FTS simple (sin content sync para permitir JOIN)
print("2. Creando nueva tabla FTS5...")
c.execute("""
    CREATE VIRTUAL TABLE busqueda_fts USING fts5(
        titulo_norma,
        contenido_articulo,
        numero_articulo,
        articulo_id UNINDEXED
    )
""")

# 3. Poblar FTS con datos de artículos + normas
print("3. Poblando índice FTS...")
c.execute("""
    INSERT INTO busqueda_fts(titulo_norma, contenido_articulo, numero_articulo, articulo_id)
    SELECT n.titulo, a.contenido, a.numero_articulo, a.id
    FROM articulos a
    JOIN normas n ON a.norma_id = n.id
""")

conn.commit()

# 4. Verificar
c.execute("SELECT COUNT(*) FROM busqueda_fts")
count = c.fetchone()[0]
print(f"4. Registros indexados: {count}")

# 5. Test búsqueda
c.execute("SELECT articulo_id, titulo_norma FROM busqueda_fts WHERE busqueda_fts MATCH 'delito' LIMIT 3")
rows = c.fetchall()
print(f"5. Test 'delito': {len(rows)} resultados")
for r in rows:
    print(f"   - Art ID: {r[0]}, Norma: {r[1][:50]}...")

conn.close()

print("\n✅ Índice FTS5 reconstruido!")
