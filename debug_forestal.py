import sqlite3

db_path = 'E:/LEX_VIRIDIS_APP/LEX_VIRIDIS_DB/legislacion_ambiental.db'
conn = sqlite3.connect(db_path)
print("--- Buscando 'ley forestal' en normas.titulo ---")
res = conn.execute("SELECT titulo FROM normas WHERE titulo LIKE '%ley%' AND titulo LIKE '%forestal%'").fetchall()
if not res:
    print("No se encontró NADA con 'ley' + 'forestal' en el título.")
    print("\n--- Buscando solo 'forestal' ---")
    res = conn.execute("SELECT titulo FROM normas WHERE titulo LIKE '%forestal%' LIMIT 10").fetchall()
    for r in res:
        print(f" - {r[0]}")
else:
    for r in res:
        print(f" - {r[0]}")

print("\n--- Buscando 'ley forestal' en articulos.contenido (FTS) ---")
res2 = conn.execute("SELECT COUNT(*) FROM busqueda_fts WHERE busqueda_fts MATCH 'ley forestal'").fetchone()
print(f"Resultados en contenido (FTS): {res2[0]}")

conn.close()
