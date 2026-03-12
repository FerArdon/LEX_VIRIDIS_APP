import datetime
import os
import zipfile
from pathlib import Path


def create_project_backup():
    # Configuración
    SOURCE_DIR = Path.cwd()
    BACKUP_DIR = SOURCE_DIR / "backups"
    BACKUP_DIR.mkdir(exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"LEX_VIRIDIS_PROJECT_BACKUP_{timestamp}.zip"
    zip_path = BACKUP_DIR / zip_filename

    # Exclusiones (nombres de carpetas/archivos a ignorar)
    EXCLUDES = {
        ".venv",
        "venv",
        "env",
        ".git",
        ".vscode",
        ".idea",
        "__pycache__",
        "backups",
        "dist",
        "build",
        "temp_pdfs",
        ".tmp.driveupload",
        "node_modules",
        "coverage",
        ".pytest_cache",
        "installer",
        "logs",
        "COMPENDIO LEYES FEMA",  # Probablemente muy grande/duplicado
    }

    # Extensiones a ignorar
    EXCLUDE_EXTS = {".pyc", ".pyo", ".pyd", ".log", ".tmp", ".iso", ".rar"}

    print(f"📦 Iniciando backup en: {zip_path}")

    count = 0
    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(SOURCE_DIR):
                # Filtrar directorios in-place
                dirs[:] = [d for d in dirs if d not in EXCLUDES]

                rel_root = Path(root).relative_to(SOURCE_DIR)

                # Doble chequeo de seguridad
                if any(part in EXCLUDES for part in rel_root.parts):
                    continue

                for file in files:
                    if file in EXCLUDES:
                        continue
                    if any(file.endswith(ext) for ext in EXCLUDE_EXTS):
                        continue

                    # Excluir logs grandes
                    if "error_log" in file:
                        continue

                    file_path = Path(root) / file
                    arcname = rel_root / file

                    try:
                        # Si es la DB principal, intentar copiarla primero si falla lectura
                        if file == "lexviridis.db":
                            # Intentar lectura directa primero
                            try:
                                with open(file_path, "rb") as f:
                                    zipf.writestr(str(arcname), f.read())
                            except PermissionError:
                                print(f"⚠️ DB bloqueada, saltando: {file}")
                                continue
                        else:
                            zipf.write(file_path, arcname)

                        count += 1
                        if count % 100 == 0:
                            print(f"⏳ Procesados {count} archivos...", end="\r")

                    except Exception as e:
                        print(f"⚠️ Error {file}: {e}")

        print(f"\n✅ Backup completado! {count} archivos.")
        print(f"📂 Ubicación: {zip_path}")
        return str(zip_path)

    except KeyboardInterrupt:
        print("\n❌ Backup cancelado por el usuario.")
        if zip_path.exists():
            zip_path.unlink()
    except Exception as e:
        print(f"\n❌ Error fatal en backup: {e}")


if __name__ == "__main__":
    create_project_backup()
