
import flet as ft
try:
    print(f"Trying ft.icons.SPA: {ft.icons.SPA}")
except AttributeError as e:
    print(f"ft.icons.SPA FAILED: {e}")

try:
    print(f"Trying ft.Icons.SPA: {ft.Icons.SPA}")
except AttributeError as e:
    print(f"ft.Icons.SPA FAILED: {e}")
    
try:
    print(f"Trying ft.icons.FOREST: {ft.icons.FOREST}")
except AttributeError as e:
    print(f"ft.icons.FOREST FAILED: {e}")
