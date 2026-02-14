import sys
import os
import traceback
import logging

# Configurar logging basico
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

if __name__ == "__main__":
    print("Iniciando LEX VIRIDIS V3 (Modo Ejecutable)...")
    try:
        print("Importing Flet...")
        import flet as ft
        print("Importing UI...")
        from lexviridis.ui_v2 import main
        
        # Calcular ruta de assets
        assets_path = "assets"
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # En modo PyInstaller (onedir), los assets estan en _internal/assets (sys._MEIPASS)
            assets_path = os.path.join(sys._MEIPASS, "assets")
            print(f"Running in frozen mode. Assets path set to: {assets_path}")
        
        print(f"Starting App with assets_dir='{assets_path}'...")
        # CRITICO: assets_dir debe ser absoluto en modo frozen si esta en _internal
        ft.app(target=main, assets_dir=assets_path)
        
    except Exception as e:
        print("\n" + "="*50)
        print("FATAL ERROR - LA APLICACIÓN NO PUDO INICIAR")
        print("="*50)
        traceback.print_exc()
        print("="*50)
        print(f"Detalle: {e}")
        print("\nPor favor, tome una captura de esta pantalla y envíela a soporte.")
        input("Presione ENTER para salir...")
