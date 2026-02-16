import traceback

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
        print("\n" + "="*50)
        print("FATAL ERROR - LA APLICACIÓN NO PUDO INICIAR")
        print("="*50)
        traceback.print_exc()
        print("="*50)
        print(f"Detalle: {e}")
        print("\nPor favor, tome una captura de esta pantalla y envíela a soporte.")
        input("Presione ENTER para salir...")

