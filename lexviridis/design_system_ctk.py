"""
LEX VIRIDIS - Design System (Windows 11 Fluent Design)
Centralización de estilos, colores y tipografía institucional.
"""

import customtkinter as ctk
from PIL import Image
import os
import sys

class Colors:
    # Paleta Windows 11 Fluent
    WINDOW_BG_LIGHT = "#f3f3f3"
    WINDOW_BG_DARK = "#202020"
    ACCENT_BLUE = "#0078d4"    # Azul Windows
    PRIMARY = "#006666"        # Teal institucional Lex Viridis
    SECONDARY = "#004D40"      # Dark Teal
    SURFACE_LIGHT = "#ffffff"
    SURFACE_DARK = "#2c2c2c"
    TEXT_LIGHT = "#000000"
    TEXT_DARK = "#ffffff"
    TEXT_SECONDARY = "#606060"
    BORDER = "#e5e5e5"
    SUCCESS = "#107c10"
    ERROR = "#d13438"

class Typography:
    # Prioridad: Segoe UI Variable -> Segoe UI -> Inter -> Arial
    FONT_FAMILY = "Segoe UI Variable" if sys.platform == "win32" else "Segoe UI"
    
    @classmethod
    def get_font(cls, size=14, weight="normal"):
        return (cls.FONT_FAMILY, size, weight)

    @classmethod
    def title(cls):
        return cls.get_font(24, "bold")

    @classmethod
    def subtitle(cls):
        return cls.get_font(18, "bold")

    @classmethod
    def body(cls):
        return cls.get_font(14, "normal")

    @classmethod
    def caption(cls):
        return cls.get_font(12, "normal")

    @classmethod
    def bold(cls):
        return cls.get_font(14, "bold")

class CTKTheme:
    @staticmethod
    def setup():
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

class Assets:
    # Configuración de Activos Visuales
    ICON_SIZE = (24, 24)
    LOGO_SIZE = (160, 180)  # Ratio cercano al nativo 665:745
    BANNER_SIZE = (800, 200) # Tamaño para banners decorativos

    @staticmethod
    def get_asset_path(relative_path):
        """ Gestiona rutas para modo desarrollo y modo PyInstaller """
        if getattr(sys, 'frozen', False):
            base_temp = getattr(sys, '_MEIPASS', None)
            if base_temp:
                return os.path.join(base_temp, relative_path)
        
        # Modo desarrollo: subir un nivel desde lexviridis/
        current_dir = os.path.dirname(os.path.abspath(__file__))
        base_path = os.path.dirname(current_dir)
        return os.path.join(base_path, relative_path)

    @classmethod
    def get_image(cls, path, size):
        """Carga segura de imágenes usando PIL y CTkImage."""
        full_path = cls.get_asset_path(path)
        try:
            pil_img = Image.open(full_path)
            # Para banners cuadrados (1024x1024), si el size es rectangular, 
            # realizamos un crop central para evitar deformación.
            if pil_img.width == pil_img.height and size[0] != size[1]:
                aspect_ratio = size[0] / size[1]
                if aspect_ratio > 1: # Ancho > Alto
                    new_height = pil_img.width / aspect_ratio
                    top = (pil_img.height - new_height) / 2
                    pil_img = pil_img.crop((0, top, pil_img.width, top + new_height))
                else: # Alto > Ancho
                    new_width = pil_img.height * aspect_ratio
                    left = (pil_img.width - new_width) / 2
                    pil_img = pil_img.crop((left, 0, left + new_width, pil_img.height))
            
            return ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
        except Exception as e:
            print(f"Error cargando {path}: {e}")
            return None

    @classmethod
    def load_icons(cls):
        """Carga solo los iconos del sidebar (pequeños). Los banners se cargan bajo demanda."""
        return {
            # ── Logos e iconos de la barra lateral (24x24 — carga rápida) ──
            "logo":      cls.get_image("assets/LEXVIRIDIS_WHITE_BG.png", cls.LOGO_SIZE),
            "search":    cls.get_image("assets/hero_search.png",    cls.ICON_SIZE),
            "ai":        cls.get_image("assets/hero_ai.png",        cls.ICON_SIZE),
            "library":   cls.get_image("assets/hero_library.png",   cls.ICON_SIZE),
            "settings":  cls.get_image("assets/hero_settings.png",  cls.ICON_SIZE),
            "dashboard": cls.get_image("assets/hero_dashboard.png", cls.ICON_SIZE),
            "favorites": cls.get_image("assets/hero_favorites.png", cls.ICON_SIZE),
            "study":     cls.get_image("assets/hero_study.png",     cls.ICON_SIZE),
        }

    @classmethod
    def load_banners(cls):
        """Carga los banners grandes (800x200). Llamar en hilo de fondo."""
        return {
            "banner_search":    cls.get_image("assets/hero_search.png",    cls.BANNER_SIZE),
            "banner_ai":        cls.get_image("assets/hero_ai.png",        cls.BANNER_SIZE),
            "banner_library":   cls.get_image("assets/hero_library.png",   cls.BANNER_SIZE),
            "banner_dashboard": cls.get_image("assets/hero_dashboard.png", cls.BANNER_SIZE),
            "banner_favorites": cls.get_image("assets/hero_favorites.png", cls.BANNER_SIZE),
            "banner_study":     cls.get_image("assets/hero_study.png",     cls.BANNER_SIZE),
            "banner_settings":  cls.get_image("assets/hero_settings.png",  cls.BANNER_SIZE),
        }
