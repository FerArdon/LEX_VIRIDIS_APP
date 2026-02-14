
import sqlite3
from pathlib import Path

DB = Path(r"c:\Users\frard\OneDrive\LEX_VIRIDIS_APP\LEX_VIRIDIS_DB\legislacion_ambiental.db")

conn = sqlite3.connect(DB)
c = conn.cursor()

print("=== DIAGNÓSTICO FTS ===")

# Test 1: Buscar "delito" en FTS
print("\n1. Buscar 'delito' en FTS:")
try:
    c.execute("SELECT rowid, titulo_norma FROM busqueda_fts WHERE busqueda_fts MATCH 'delito' LIMIT 5")
    rows = c.fetchall()
    print(f"   Encontrados: {len(rows)}")
    for r in rows:
        print(f"   - {r}")
except Exception as e:
    print(f"   Error: {e}")

# Test 2: Ver estructura de busqueda_fts
print("\n2. Estructura de busqueda_fts:")
c.execute("PRAGMA table_info(busqueda_fts)")
for col in c.fetchall():
    print(f"   - {col}")

# Test 3: Ver muestra de datos en FTS
print("\n3. Muestra de datos en FTS:")
c.execute("SELECT * FROM busqueda_fts LIMIT 2")
for row in c.fetchall():
    print(f"   - titulo: {str(row[0])[:50]}...")
    print(f"     contenido: {str(row[1])[:80]}...")

conn.close()
