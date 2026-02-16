import os
import sys
import traceback

# Agregar directorio actual al path
sys.path.append(os.getcwd())

def main():
    print("Iniciando LEX VIRIDIS V3...")

    try:
        # Importación tardía para mostrar print antes
        print("Cargando componentes...")
        import flet as ft

        from lexviridis.ui_v2 import main as ui_main

        print("Lanzando interfaz...")
        ft.app(target=ui_main)

    except ImportError as e:
        print(f"\nERROR DE DEPENDENCIAS: {e}")
        print("Asegúrate de estar en el entorno virtual (.venv)")
        input("Presiona ENTER para salir...")
    except Exception:
        print("\n" + "="*50)
        print("ERROR FATAL")
        print("="*50)
        traceback.print_exc()
        print("="*50)
        input("Presiona ENTER para salir...")

if __name__ == "__main__":
    main()
