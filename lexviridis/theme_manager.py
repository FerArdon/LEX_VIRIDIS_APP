
import json
from dataclasses import dataclass
from pathlib import Path

import flet as ft


@dataclass
class ColorScheme:
    primary: str
    primary_light: str
    primary_dark: str
    secondary: str
    background: str
    surface: str
    surface_variant: str
    text_primary: str
    text_secondary: str
    divider: str
    border: str
    error: str = "#ef4444"
    success: str = "#22c55e"
    warning: str = "#f59e0b"

class Themes:
    LIGHT = ColorScheme(
        primary="#1B5E20", primary_light="#4CAF50", primary_dark="#0D3818",
        secondary="#0D47A1", background="#F5F5F5", surface="#FFFFFF",
        surface_variant="#FAFAFA", text_primary="#212121", text_secondary="#757575",
        divider="#E0E0E0", border="#BDBDBD"
    )

    DARK = ColorScheme(
        primary="#4CAF50", primary_light="#81C784", primary_dark="#2E7D32",
        secondary="#2196F3", background="#121212", surface="#1E1E1E",
        surface_variant="#2C2C2C", text_primary="#FFFFFF", text_secondary="#B0B0B0",
        divider="#3A3A3A", border="#4A4A4A"
    )

class ThemeManager:
    def __init__(self, page: ft.Page):
        self.page = page
        self.config_path = Path.home() / ".lexviridis" / "theme_config.json"
        self.current_theme_name = self.load_preference()
        self.current_scheme = getattr(Themes, self.current_theme_name.upper())
        self.apply_to_page()

    def load_preference(self) -> str:
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    return json.load(f).get("theme", "light")
            except (json.JSONDecodeError, OSError, KeyError):
                pass
        return "light"

    def save_preference(self, theme_name: str):
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            json.dump({"theme": theme_name}, f)

    def set_theme(self, theme_name: str):
        self.current_theme_name = theme_name
        self.current_scheme = getattr(Themes, theme_name.upper())
        self.save_preference(theme_name)
        self.apply_to_page()

    def apply_to_page(self):
        # Aplicar colores personalizados del esquema activo
        self.page.theme_mode = ft.ThemeMode.LIGHT if self.current_theme_name == "light" else ft.ThemeMode.DARK

        # Crear un tema completo con los colores personalizados
        self.page.theme = ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=self.current_scheme.primary,
                secondary=self.current_scheme.secondary,
                surface=self.current_scheme.surface,
                # background=self.current_scheme.background, # Deprecated
                error=self.current_scheme.error,
                on_primary="#FFFFFF",
                on_secondary="#FFFFFF",
                on_surface=self.current_scheme.text_primary,
                # on_background=self.current_scheme.text_primary, # Deprecated
            ),
            visual_density="comfortable",
        )

        # Aplicar color de fondo
        self.page.bgcolor = self.current_scheme.background

        # Forzar actualización completa
        self.page.update()
