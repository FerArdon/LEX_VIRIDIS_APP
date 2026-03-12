"""Reconstruir índice FTS5 - Método Agresivo"""

import shutil
import sqlite3
from pathlib import Path

DB = Path(r"c:\Users\frard\OneDrive\LEX_VIRIDIS_APP\LEX_VIRIDIS_DB\legislacion_ambiental.db")
DB_BACKUP = Path(r"c:\Users\frard\OneDrive\LEX_VIRIDIS_APP\LEX_VIRIDIS_DB\legislacion_ambiental_repair.db")

print("🔧 Reparando base de datos con método de reconstrucción...")

# 1. Crear nueva DB sin las tablas FTS corruptas
print("1. Creando copia limpia de la base de datos...")

conn_old = sqlite3.connect(DB)
conn_new = sqlite3.connect(DB_BACKUP)

# Copiar todas las tablas excepto las FTS corruptas
conn_old.backup(conn_new)
conn_old.close()
conn_new.close()

# 2. Ahora trabajar con la copia
conn = sqlite3.connect(DB_BACKUP)
c = conn.cursor()

# Obtener lista de tablas FTS a eliminar
c.execute("SELECT name FROM sqlite_master WHERE name LIKE 'busqueda_fts%'")
fts_tables = [row[0] for row in c.fetchall()]
print(f"   Tablas FTS encontradas: {fts_tables}")

# Usar PRAGMA para forzar eliminación
conn.execute("PRAGMA writable_schema = ON")

for table in fts_tables:
    try:
        c.execute(f"DELETE FROM sqlite_master WHERE name = '{table}'")
        print(f"   ✓ Eliminada de schema: {table}")
    except Exception as e:
        print(f"   ✗ {table}: {e}")

conn.execute("PRAGMA writable_schema = OFF")
conn.commit()

# Integrity check
c.execute("PRAGMA integrity_check")
print(f"   Integridad: {c.fetchone()[0]}")

# Vacuum para limpiar
conn.close()
conn = sqlite3.connect(DB_BACKUP, isolation_level=None)
c = conn.cursor()
c.execute("VACUUM")
print("   ✓ VACUUM completado")

# 3. Recrear FTS5
print("\n2. Recreando índice FTS5...")
c.execute("""
    CREATE VIRTUAL TABLE busqueda_fts USING fts5(
        titulo_norma,
        contenido_articulo,
        tags,
        articulo_id UNINDEXED,
        tokenize='porter'
    )
""")
print("   ✓ Tabla FTS5 creada")

# 4. Poblar FTS
print("3. Poblando índice...")
c.execute("""
    INSERT INTO busqueda_fts(titulo_norma, contenido_articulo, tags, articulo_id)
    SELECT n.titulo, a.contenido, n.categoria, a.id
    FROM articulos a
    JOIN normas n ON a.norma_id = n.id
""")
c.execute("SELECT COUNT(*) FROM busqueda_fts")
count = c.fetchone()[0]
print(f"   ✓ {count} registros indexados")

conn.close()

# 5. Reemplazar original con reparada
print("\n4. Reemplazando base de datos original...")
shutil.copy(DB_BACKUP, DB)
print("   ✓ Base de datos reparada")

print("\n✅ ¡Reparación completada exitosamente!")
