import os
import sys
import traceback
from pathlib import Path

# Sin consola (exe compilado con console=False) PyInstaller deja stdout/stderr en None
for _flujo in ("stdout", "stderr"):
    if getattr(sys, _flujo) is None:
        setattr(sys, _flujo, open(os.devnull, "w", encoding="utf-8"))  # noqa: SIM115


def _registrar_error_de_arranque() -> None:
    """Sin consola nadie ve el error: se guarda en un archivo para poder diagnosticarlo."""
    try:
        carpeta = Path(os.environ.get("APPDATA", Path.home())) / "LEX VIRIDIS"
        carpeta.mkdir(parents=True, exist_ok=True)
        (carpeta / "error_arranque.log").write_text(traceback.format_exc(), encoding="utf-8")
    except OSError:
        pass


if __name__ == "__main__":
    print("Iniciando LEX VIRIDIS V3...")
    try:
        print("Importing Flet...")
        import flet as ft

        print("Importing UI...")
        from lexviridis.ui_v2 import main

        print("Starting App...")
        ft.app(target=main)
    except Exception as e:
        print("\n" + "=" * 50)
        print("FATAL ERROR - LA APLICACIÓN NO PUDO INICIAR")
        print("=" * 50)
        traceback.print_exc()
        print("=" * 50)
        print(f"Detalle: {e}")
        _registrar_error_de_arranque()
