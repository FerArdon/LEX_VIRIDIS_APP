"""
Script de optimización para LEX VIRIDIS.
Optimiza la base de datos, limpia cachés y libera memoria.
"""
import argparse
import logging
import sqlite3
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lexviridis.config import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def optimize_database(db_path: Path) -> None:
    """Optimiza la base de datos SQLite."""
    logger.info(f"Optimizando base de datos: {db_path}")

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # 1. Analizar estadísticas
        logger.info("Analizando estadísticas...")
        cursor.execute("ANALYZE")

        # 2. Vacuum (reorganizar y compactar)
        logger.info("Ejecutando VACUUM...")
        cursor.execute("VACUUM")

        # 3. Optimizar índices FTS5
        logger.info("Optimizando índices FTS5...")
        try:
            cursor.execute("INSERT INTO busqueda_fts(busqueda_fts) VALUES('optimize')")
        except sqlite3.OperationalError:
            logger.warning("Tabla FTS5 no encontrada, saltando optimización FTS")

        # 4. Integridad de la base de datos
        logger.info("Verificando integridad...")
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        if result[0] == "ok":
            logger.info("✅ Integridad verificada correctamente")
        else:
            logger.warning(f"⚠️ Problemas de integridad: {result}")

        conn.commit()
        conn.close()

        logger.info("✅ Base de datos optimizada exitosamente")

    except Exception as e:
        logger.error(f"❌ Error optimizando base de datos: {e}")
        raise


def clean_cache() -> None:
    """Limpia archivos de caché antiguos."""
    logger.info("Limpiando archivos de caché...")

    try:
        cache_dir = config.CACHE_DIR
        if not cache_dir.exists():
            logger.info("Directorio de caché no existe, saltando...")
            return

        # Limpiar archivos .json y .pkl antiguos
        cache_files = list(cache_dir.glob("*.json")) + list(cache_dir.glob("*.pkl"))

        if not cache_files:
            logger.info("No hay archivos de caché para limpiar")
            return

        for cache_file in cache_files:
            try:
                cache_file.unlink()
                logger.info(f"  Eliminado: {cache_file.name}")
            except Exception as e:
                logger.warning(f"  No se pudo eliminar {cache_file.name}: {e}")

        logger.info(f"✅ {len(cache_files)} archivos de caché eliminados")

    except Exception as e:
        logger.error(f"❌ Error limpiando caché: {e}")


def clean_old_backups(max_backups: int = 10) -> None:
    """Limpia backups antiguos, manteniendo solo los más recientes."""
    logger.info(f"Limpiando backups antiguos (manteniendo {max_backups} más recientes)...")

    try:
        backup_dir = config.BACKUP_DIR
        if not backup_dir.exists():
            logger.info("Directorio de backups no existe, saltando...")
            return

        # Obtener todos los backups ordenados por fecha
        backups = sorted(
            backup_dir.glob("backup_*.db"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        if len(backups) <= max_backups:
            logger.info(f"Solo hay {len(backups)} backups, no es necesario limpiar")
            return

        # Eliminar backups antiguos
        backups_to_delete = backups[max_backups:]
        for backup in backups_to_delete:
            try:
                backup.unlink()
                logger.info(f"  Eliminado: {backup.name}")
            except Exception as e:
                logger.warning(f"  No se pudo eliminar {backup.name}: {e}")

        logger.info(f"✅ {len(backups_to_delete)} backups antiguos eliminados")

    except Exception as e:
        logger.error(f"❌ Error limpiando backups: {e}")


def get_database_stats(db_path: Path) -> None:
    """Muestra estadísticas de la base de datos."""
    logger.info(f"Estadísticas de base de datos: {db_path}")

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Tamaño del archivo
        file_size_mb = db_path.stat().st_size / (1024 * 1024)
        logger.info(f"  Tamaño: {file_size_mb:.2f} MB")

        # Contar tablas
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        table_count = cursor.fetchone()[0]
        logger.info(f"  Tablas: {table_count}")

        # Contar normas
        try:
            cursor.execute("SELECT COUNT(*) FROM normas")
            normas_count = cursor.fetchone()[0]
            logger.info(f"  Normas: {normas_count}")
        except sqlite3.OperationalError:
            pass

        # Contar artículos
        try:
            cursor.execute("SELECT COUNT(*) FROM articulos")
            articulos_count = cursor.fetchone()[0]
            logger.info(f"  Artículos: {articulos_count}")
        except sqlite3.OperationalError:
            pass

        conn.close()

    except Exception as e:
        logger.error(f"❌ Error obteniendo estadísticas: {e}")


def main():
    parser = argparse.ArgumentParser(description="Optimizar LEX VIRIDIS")
    parser.add_argument("--db", action="store_true", help="Optimizar base de datos")
    parser.add_argument("--cache", action="store_true", help="Limpiar caché")
    parser.add_argument("--backups", action="store_true", help="Limpiar backups antiguos")
    parser.add_argument("--stats", action="store_true", help="Mostrar estadísticas")
    parser.add_argument("--all", action="store_true", help="Ejecutar todas las optimizaciones")
    parser.add_argument("--max-backups", type=int, default=10, help="Número máximo de backups a mantener")

    args = parser.parse_args()

    # Si no se especifica nada, mostrar ayuda
    if not any([args.db, args.cache, args.backups, args.stats, args.all]):
        parser.print_help()
        return

    logger.info("="*60)
    logger.info("LEX VIRIDIS - Script de Optimización")
    logger.info("="*60)

    db_path = config.BASE_DIR / "LEX_VIRIDIS_DB" / "legislacion_ambiental.db"

    if args.stats or args.all:
        get_database_stats(db_path)

    if args.db or args.all:
        optimize_database(db_path)

    if args.cache or args.all:
        clean_cache()

    if args.backups or args.all:
        clean_old_backups(args.max_backups)

    logger.info("="*60)
    logger.info("✅ Optimización completada")
    logger.info("="*60)


if __name__ == "__main__":
    main()
