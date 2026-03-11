import logging
import sys
import traceback
from pathlib import Path

# Configurar logging a archivo (funciona siempre, con o sin consola)
_log_dir = Path.home() / ".lexviridis" / "logs"
_log_dir.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=str(_log_dir / "app.log"),
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

if __name__ == "__main__":
    logging.info("=== LEX VIRIDIS STARTING ===")
    logging.info(f"sys.frozen: {getattr(sys, 'frozen', False)}")
    logging.info(f"sys.executable: {sys.executable}")

    try:
        logging.info("Importing flet...")
        import flet as ft

        logging.info("Importing UI...")
        from lexviridis.ui_v2 import main

        logging.info("Calling ft.app()...")
        ft.app(target=main, assets_dir="assets")
    except Exception as e:
        logging.exception(f"FATAL ERROR: {e}")
        # Guardar crash log junto al ejecutable
        try:
            with open("crash_log.txt", "w", encoding="utf-8") as f:
                f.write("=" * 50 + "\n")
                f.write("FATAL ERROR - LA APLICACIÓN NO PUDO INICIAR\n")
                f.write("=" * 50 + "\n")
                traceback.print_exc(file=f)
                f.write("=" * 50 + "\n")
                f.write(f"Detalle: {e}\n")
        except Exception:
            pass
