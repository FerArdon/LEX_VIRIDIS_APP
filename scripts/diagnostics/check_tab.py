
import flet as ft
import inspect

print(f"Flet version: {ft.version}")
print(f"Tab init signature: {inspect.signature(ft.Tab.__init__)}")

try:
    t = ft.Tab(text="Test")
    print("ft.Tab(text='Test') works")
except Exception as e:
    print(f"ft.Tab(text='Test') FAILED: {e}")

try:
    t = ft.Tab(content=ft.Text("Content"))
    print("ft.Tab(content=...) works")
except Exception as e:
    print(f"ft.Tab(content=...) FAILED: {e}")
