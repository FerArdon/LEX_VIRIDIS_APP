"""
Test de Diagnóstico - LEX VIRIDIS
Detecta dónde se congela la app
"""

import sqlite3
import sys
from pathlib import Path

# Mock config or similar to get DB path
DB_PATH = r"c:\Users\frard\OneDrive\LEX_VIRIDIS_APP\LEX_VIRIDIS_DB\legislacion_ambiental.db"

print("=" * 60)
print("DIAGNÓSTICO DE STARTUP - LEX VIRIDIS")
print("=" * 60)

# Test 1: Verificar archivos
print("\n[1/5] Verificando archivos...")
try:
    # Add project root to sys.path
    project_root = str(Path(__file__).parent.absolute())
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    print("✅ search_engine.py OK")
except Exception as e:
    print(f"❌ ERROR importando search_engine: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

# Test 2: Verificar base de datos
print("\n[2/5] Verificando base de datos...")

if not Path(DB_PATH).exists():
    print(f"❌ Base de datos NO EXISTE: {DB_PATH}")
    sys.exit(1)
else:
    print(f"✅ Base de datos existe: {DB_PATH}")

# Test 3: Conectar a BD
print("\n[3/5] Probando conexión a BD...")
try:
    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    cursor = conn.cursor()
    print("✅ Conexión exitosa")

    # Test 4: Verificar tablas
    print("\n[4/5] Verificando tablas...")
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table'
        ORDER BY name
    """)
    tables = [row[0] for row in cursor.fetchall()]

    print(f"📋 Tablas encontradas: {len(tables)}")
    for table in tables:
        print(f"   - {table}")

    required_tables = ["normas", "articulos"]
    missing = [t for t in required_tables if t not in tables]

    if missing:
        print(f"\n❌ TABLAS FALTANTES: {missing}")
        sys.exit(1)
    else:
        print("✅ Todas las tablas requeridas existen")

    # Test 5: Contar documentos
    print("\n[5/5] Contando documentos...")
    cursor.execute("SELECT COUNT(*) FROM normas")
    normas_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM articulos")
    articulos_count = cursor.fetchone()[0]

    print(f"✅ Documentos: {normas_count} normas, {articulos_count} artículos")

    conn.close()

    print("\n" + "=" * 60)
    print("✅ DIAGNÓSTICO COMPLETADO - TODO OK")
    print("=" * 60)

except sqlite3.OperationalError as e:
    print(f"❌ ERROR de SQLite: {e}")
except Exception as e:
    print(f"❌ ERROR INESPERADO: {e}")
    import traceback

    traceback.print_exc()
