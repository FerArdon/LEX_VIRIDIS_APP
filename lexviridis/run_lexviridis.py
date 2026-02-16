print("Importing main_flet...")
from lexviridis.main_flet import main

print("Importing flet...")
import flet as ft

if __name__ == "__main__":
    print("Starting app...")
    try:
        ft.app(target=main)
    except Exception as e:
        print(f"Error launching app: {e}")
