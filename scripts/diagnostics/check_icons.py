
import flet as ft
print("Checking relevant nature icons...")
icons = []
candidates = ["SPA", "NATURE", "XYLOGRAPH", "FOREST", "ECO", "LEAF", "GRASS", "ENERGY_SAVINGS_LEAF"]

for c in candidates:
    if hasattr(ft.icons, c):
        print(f"FOUND: {c}")
    else:
        print(f"MISSING: {c}")
