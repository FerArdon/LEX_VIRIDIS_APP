import sqlite3
import os
from pathlib import Path

db_path = r"c:\Users\frard\OneDrive\LEX_VIRIDIS_APP\LEX_VIRIDIS_DB\legislacion_ambiental.db"
if not os.path.exists(db_path):
    print(f"DB no encontrada en {os.getcwd()}")
    # Buscar .db files
    for f in os.listdir("."):
        if f.endswith(".db"):
            print(f"Found DB: {f}")
            db_path = f
            break

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    print("\n--- Buscando duplicados para Aguas y Forestal ---")
    searches = ["Aguas", "Forestal", "Penal"]
    for s in searches:
        print(f"\nBuscando '{s}':")
        cursor.execute("SELECT id, titulo, fecha_publicacion, archivo_pdf, (SELECT COUNT(*) FROM articulos WHERE norma_id = normas.id) as arts FROM normas WHERE titulo LIKE ?", (f"%{s}%",))
        for row in cursor.fetchall():
            print(f"   ID: {row[0]}, Arts: {row[4]}, PDF: {'SI' if row[3] else 'NO'}, Titulo: {row[1]}")
            
    conn.close()
except Exception as e:
    print(f"Error: {e}")
