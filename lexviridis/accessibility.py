
import flet as ft


class AccessibilityManager:
    """Gestiona opciones de accesibilidad."""

    def __init__(self, page: ft.Page):
        self.page = page
        self.high_contrast = False
        self.large_text = False
        self.screen_reader = False

    def toggle_high_contrast(self, value: bool):
        self.high_contrast = value
        # Implementación de cambio de colores agresivo
        if value:
            self.page.theme = ft.Theme(
                color_scheme=ft.ColorScheme(
                    primary=ft.Colors.YELLOW,
                    surface=ft.Colors.BLACK,
                    on_surface=ft.Colors.YELLOW,
                    background=ft.Colors.BLACK,
                )
            )
        else:
            self.page.theme = None # Volver al default
        self.page.update()

    def toggle_large_text(self, value: bool):
        self.large_text = value
        # Esto afectaría a componentes que usen variables de tipografía escalables
        self.page.update()

    def announce(self, message: str):
        """Usa mecanismos nativos o visuales para anunciar cambios."""
        # Flet no tiene TTS nativo cross-platform fácil sin dependencias extra (pyttsx3)
        # Usamos un snackbar como fallback accesible o exploramos Semantics
        self.page.show_snack_bar(ft.SnackBar(ft.Text(f"Aviso: {message}"), open=True))

def add_accessibility_shortcuts(page: ft.Page, app_instance):
    """Agrega shortcuts globales de teclado."""
    def on_keyboard(e: ft.KeyboardEvent):
        if e.ctrl and e.key == "F":
            app_instance.nav_rail.selected_index = 1 # Buscar
            app_instance._on_nav_change(ft.ControlEvent(target=app_instance.nav_rail, name="change", data="1", control=app_instance.nav_rail))
        elif e.ctrl and e.key == "H":
            app_instance.nav_rail.selected_index = 0 # Dashboard
            app_instance._on_nav_change(ft.ControlEvent(target=app_instance.nav_rail, name="change", data="0", control=app_instance.nav_rail))

    page.on_keyboard_event = on_keyboard
