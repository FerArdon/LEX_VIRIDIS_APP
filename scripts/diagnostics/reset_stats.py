"""Reset de estadísticas del Dashboard"""
import sqlite3
from pathlib import Path

# Buscar en ambas rutas posibles
db_paths = [
    Path("data/lex_viridis.db"),
    Path("lexviridis.db"),
    Path("LEX_VIRIDIS_DB/legislacion_ambiental.db")
]

for db_path in db_paths:
    if db_path.exists():
        print(f"\n=== Procesando: {db_path} ===")
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # Ver tablas
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in c.fetchall()]
        print(f"Tablas: {tables[:10]}...")  # Solo primeras 10
        
        # Limpiar tablas de stats
        stats_keywords = ['historial', 'busqueda', 'visto', 'analytics', 'activity', 'view', 'search', 'log']
        for table in tables:
            table_lower = table.lower()
            if any(kw in table_lower for kw in stats_keywords):
                try:
                    c.execute(f"DELETE FROM [{table}]")
                    print(f"✓ Limpiada: {table}")
                except Exception as e:
                    print(f"✗ Error: {e}")
        
        conn.commit()
        conn.close()

print("\n¡Proceso completado!")
