import sys
import os
import time

print("STEP 1: Setting up paths...")
sys.path.append(os.getcwd())

print("STEP 2: Importing lexviridis.config...")
from lexviridis.config import config
print(f"DEBUG: Data Dir: {config.DATA_DIR}")

print("STEP 3: Importing flet...")
import flet as ft
print(f"DEBUG: Flet version: {ft.__version__ if hasattr(ft, '__version__') else 'unknown'}")

print("STEP 4: Importing lexviridis.ui_v2...")
from lexviridis.ui_v2 import LexViridisApp
print("DEBUG: ui_v2 imported successfully.")

def main(page: ft.Page):
    print("STEP 5: Inside Flet main.")
    try:
        print("STEP 6: Initializing LexViridisApp...")
        app = LexViridisApp(page)
        print("STEP 7: App initialized.")
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("STEP 8: Starting ft.app...")
    try:
        ft.app(target=main)
    except Exception as e:
        print(f"Error launching ft.app: {e}")
