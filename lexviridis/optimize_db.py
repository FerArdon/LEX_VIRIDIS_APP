
"""
Script de optimización de base de datos para LEX VIRIDIS.
Crea índices y optimiza la estructura para búsquedas rápidas.
"""
import sqlite3
import time
from pathlib import Path

DB = Path(r"c:\Users\frard\OneDrive\LEX_VIRIDIS_APP\LEX_VIRIDIS_DB\legislacion_ambiental.db")

def benchmark_search(cursor, query):
    """Mide el tiempo de una búsqueda."""
    start = time.perf_counter()
    cursor.execute("""
        SELECT articulo_id, titulo_norma
        FROM busqueda_fts
        WHERE busqueda_fts MATCH ?
        LIMIT 20
    """, (f'"{query}"',))
    results = cursor.fetchall()
    elapsed = (time.perf_counter() - start) * 1000
    return len(results), elapsed

def optimize_database():
    print("⚡ Optimización de Base de Datos LEX VIRIDIS")
    print("=" * 60)

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    # Benchmark antes
    print("\n📊 BENCHMARK ANTES de optimización:")
    queries = ["licencia", "delito ambiental", "forestal", "agua"]
    for q in queries:
        count, ms = benchmark_search(cursor, q)
        print(f"   '{q}': {count} resultados en {ms:.2f}ms")

    # 1. Crear índices compuestos
    print("\n🔧 Creando índices SQL...")
    indices = [
        ("idx_articulos_norma_id", "articulos(norma_id)"),
        ("idx_articulos_numero", "articulos(numero_articulo)"),
        ("idx_articulos_pagina", "articulos(pagina)"),
        ("idx_normas_tipo", "normas(tipo)"),
        ("idx_normas_titulo", "normas(titulo)"),
    ]

    for idx_name, idx_def in indices:
        try:
            cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {idx_def}")
            print(f"   ✅ {idx_name}")
        except Exception as e:
            print(f"   ⚠️ {idx_name}: {e}")

    # 2. Optimizar FTS5
    print("\n🔧 Optimizando índice FTS5...")
    try:
        cursor.execute("INSERT INTO busqueda_fts(busqueda_fts) VALUES('optimize')")
        print("   ✅ FTS5 optimizado")
    except Exception as e:
        print(f"   ⚠️ FTS5: {e}")

    # 3. Ejecutar VACUUM y ANALYZE
    print("\n🔧 Ejecutando VACUUM y ANALYZE...")
    conn.commit()
    cursor.execute("ANALYZE")
    print("   ✅ ANALYZE completado")

    # VACUUM requiere estar fuera de transacción
    conn.close()
    conn = sqlite3.connect(DB, isolation_level=None)
    cursor = conn.cursor()
    cursor.execute("VACUUM")
    print("   ✅ VACUUM completado")

    # Benchmark después
    print("\n📊 BENCHMARK DESPUÉS de optimización:")
    for q in queries:
        count, ms = benchmark_search(cursor, q)
        print(f"   '{q}': {count} resultados en {ms:.2f}ms")

    # Estadísticas finales
    cursor.execute("SELECT COUNT(*) FROM articulos")
    art_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM normas")
    norm_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM busqueda_fts")
    fts_count = cursor.fetchone()[0]

    print("\n📈 ESTADÍSTICAS:")
    print(f"   - Normas: {norm_count}")
    print(f"   - Artículos: {art_count}")
    print(f"   - Entradas FTS: {fts_count}")

    # Tamaño del archivo
    db_size = DB.stat().st_size / (1024 * 1024)
    print(f"   - Tamaño DB: {db_size:.2f} MB")

    conn.close()
    print("\n✅ Optimización completada!")

if __name__ == "__main__":
    optimize_database()
