
import flet as ft

# Compatibility layer for Flet versions (colors vs Colors)
try:
    Colors = ft.Colors
except AttributeError:
    Colors = ft.colors

# Add other renames here if necessary
