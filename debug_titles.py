import sqlite3
import os

db_path = 'e:/LEX_VIRIDIS_APP/LEX_VIRIDIS_DB/legislacion_ambiental.db'
if not os.path.exists(db_path):
    print(f"Error: No existe {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
print("--- Listado de Normas (Títulos) ---")
res = conn.execute("SELECT id, titulo FROM normas LIMIT 20").fetchall()
for r in res:
    print(f"ID {r[0]}: {r[1]}")

print("\n--- Buscando 'reglamento' o '031-2010' en títulos ---")
res2 = conn.execute("SELECT id, titulo FROM normas WHERE titulo LIKE '%reglamento%' OR titulo LIKE '%031-2010%'").fetchall()
for r in res2:
    print(f"ENCONTRADO: ID {r[0]}: {r[1]}")
conn.close()
