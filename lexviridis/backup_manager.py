"""
LEX VIRIDIS - Gestor de Backups
Maneja la copia de seguridad y restauración de la base de datos.
"""

import logging
import shutil
import threading
import time
import zipfile
from datetime import datetime, timedelta
from pathlib import Path


class BackupManager:
    """Administra los backups de la base de datos SQLite."""

    def __init__(self, db_path: Path, backup_dir: Path = None):
        self.db_path = db_path
        self.backup_dir = backup_dir or db_path.parent / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        self.is_running = False

    def create_backup(self, label: str = "auto") -> Path | None:
        """
        Crea un backup comprimido de la base de datos actual.
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"lex_viridis_db_{label}_{timestamp}"

            # 1. Copia temporal de la DB para no bloquearla
            temp_db = self.backup_dir / f"{backup_name}.db"
            shutil.copy2(self.db_path, temp_db)

            # 2. Comprimir en ZIP
            zip_path = self.backup_dir / f"{backup_name}.zip"
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(temp_db, arcname=self.db_path.name)

            # 3. Eliminar temporal
            temp_db.unlink()

            logging.info(f"✅ Backup creado exitosamente: {zip_path.name}")
            return zip_path

        except Exception as e:
            logging.error(f"❌ Error creando backup: {e}")
            return None

    def list_backups(self) -> list[dict]:
        """Lista los backups disponibles con su metadata."""
        backups = []
        for file in self.backup_dir.glob("*.zip"):
            stats = file.stat()
            backups.append(
                {
                    "name": file.name,
                    "path": str(file),
                    "size_mb": round(stats.st_size / (1024 * 1024), 2),
                    "date": datetime.fromtimestamp(stats.st_mtime),
                }
            )

        # Ordenar por fecha descendente
        return sorted(backups, key=lambda x: x["date"], reverse=True)

    def cleanup_old_backups(self, keep_days: int = 7):
        """Elimina backups más antiguos que X días."""
        cutoff = datetime.now() - timedelta(days=keep_days)
        deleted_count = 0

        for backup in self.list_backups():
            if backup["date"] < cutoff:
                try:
                    Path(backup["path"]).unlink()
                    deleted_count += 1
                except Exception as e:
                    logging.warning(f"No se pudo eliminar backup viejo: {e}")

        if deleted_count > 0:
            logging.info(f"🧹 Limpieza: {deleted_count} backups viejos eliminados.")

    def restore_backup(self, zip_path: Path) -> bool:
        """
        Restaura la base de datos desde un archivo ZIP.
        Realiza un backup de seguridad antes de proceder.
        """
        try:
            if not zip_path.exists():
                raise FileNotFoundError(f"Archivo de backup no encontrado: {zip_path}")

            logging.info(f"🔄 Iniciando restauración desde: {zip_path.name}")

            # 1. Backup de seguridad obligatorio antes de restaurar
            self.create_backup(label="pre_restore")

            # 2. Extraer en directorio temporal
            temp_dir = self.backup_dir / "temp_restore"
            temp_dir.mkdir(exist_ok=True)

            with zipfile.ZipFile(zip_path, "r") as zipf:
                zipf.extractall(temp_dir)

            # 3. Localizar el archivo de DB extraído
            extracted_db = temp_dir / self.db_path.name
            if not extracted_db.exists():
                # Si el nombre no coincide, buscar el primer .db
                db_files = list(temp_dir.glob("*.db"))
                if not db_files:
                    raise ValueError("No se encontró archivo .db dentro del ZIP")
                extracted_db = db_files[0]

            # 4. Reemplazar DB actual (SQLite permite sobrescribir si el archivo no está bloqueado por otro proceso fuerte)
            shutil.copy2(extracted_db, self.db_path)

            # 5. Limpiar temporal
            shutil.rmtree(temp_dir)

            logging.info("✅ Restauración completada exitosamente.")
            return True

        except Exception as e:
            logging.error(f"❌ Error durante la restauración: {e}")
            return False

    def run_scheduler(self):
        """Inicia el programador de backups en un hilo separado."""
        if self.is_running:
            return

        def job():
            self.is_running = True
            logging.info("⏳ Programador de backups activado (Diario).")

            while self.is_running:
                # Ejecutar backup a las 2 AM
                now = datetime.now()
                if now.hour == 2 and now.minute == 0:
                    self.create_backup(label="auto")
                    self.cleanup_old_backups(keep_days=7)
                    time.sleep(65)  # Evitar múltiples ejecuciones en el mismo minuto

                time.sleep(30)  # Verificar cada 30 segundos

        thread = threading.Thread(target=job, daemon=True)
        thread.start()

    def stop_scheduler(self):
        self.is_running = False
