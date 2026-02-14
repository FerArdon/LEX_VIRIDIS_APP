"""
LEX VIRIDIS - Interfaz de Licencias
Componentes UI para activación y estado de licencia.
"""

import flet as ft
Colors = getattr(ft, "Colors", getattr(ft, "colors", None))
if Colors is None:
    raise ImportError("No se pudo cargar el módulo de colores de Flet.")
from pathlib import Path
import sys

# Agregar path del sistema de licencias (compatible con .exe y desarrollo)
try:
    from .config import config as _license_config
    _license_dir = str(_license_config.BASE_DIR / "LEX_VIRIDIS_LICENCIA")
except Exception:
    _license_dir = str(Path(__file__).parent.parent / "LEX_VIRIDIS_LICENCIA")

sys.path.insert(0, _license_dir)

try:
    from license_system import LicenseManager
except ImportError:
    # Fallback: si el módulo de licencias no está disponible (e.g. no empaquetado)
    class LicenseManager:
        @staticmethod
        def validate_license(key): return {"valid": True, "client": "Usuario", "type": "DESARROLLO", "days_left": 999}
        @staticmethod
        def save_license(key): pass
        @staticmethod
        def load_saved_license(): return "dev-key"
        @staticmethod
        def get_hardware_id(): return "dev"
        @staticmethod
        def generate_license(*a, **k): return "dev-trial-key"

from .design_system import Theme, Spacing, Radius, UIComponents


class LicenseActivationScreen:
    """Pantalla de activación de licencia."""
    
    def __init__(self, page: ft.Page, on_success: callable):
        self.page = page
        self.on_success = on_success
        self.license_input = None
        self.error_text = None
    
    def build(self) -> ft.Control:
        """Construye la pantalla de activación."""
        try:
            from .config import config as _cfg
            logo_path = _cfg.BASE_DIR / "assets" / "LEXVIRIDIS_WHITE_BG.png"
        except Exception:
            logo_path = Path(__file__).parent.parent / "assets" / "LEXVIRIDIS_WHITE_BG.png"
        
        self.license_input = ft.TextField(
            label="Clave de Licencia",
            hint_text="Ingrese su clave de activación",
            width=500,
            multiline=True,
            min_lines=3,
            max_lines=5,
            border_color=Theme.PRIMARY,
            focused_border_color=Theme.PRIMARY,
        )
        
        self.error_text = ft.Text("", color=Theme.ERROR, size=12, visible=False)
        
        return ft.Container(
            content=ft.Column([
                # Logo
                ft.Image(src=str(logo_path), width=150, height=150) if logo_path.exists() else ft.Icon(ft.Icons.GAVEL, size=100, color=Theme.PRIMARY),
                ft.Container(height=Spacing.LG),
                
                # Título
                ft.Text("Activar LEX VIRIDIS", size=28, weight="bold", color=Theme.PRIMARY),
                ft.Text("Ingrese su clave de licencia para continuar", size=14, color=Theme.TEXT_SECONDARY),
                ft.Container(height=Spacing.XL),
                
                # Input de licencia
                self.license_input,
                self.error_text,
                ft.Container(height=Spacing.MD),
                
                # Botones
                ft.Row([
                    ft.ElevatedButton(
                        "Activar Licencia",
                        icon=ft.Icons.KEY,
                        bgcolor=Theme.PRIMARY,
                        color="white",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=Radius.MD)),
                        on_click=self._on_activate
                    ),
                    ft.TextButton(
                        "Solicitar Prueba Gratuita",
                        icon=ft.Icons.ACCESS_TIME,
                        on_click=self._on_request_trial
                    ),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=Spacing.MD),
                
                ft.Container(height=Spacing.XL),
                
                # Info de contacto
                ft.Container(
                    content=ft.Column([
                        ft.Text("¿No tiene licencia?", size=12, weight="bold"),
                        ft.Text("Contacte a: soporte@lexviridis.hn", size=11, color=Theme.TEXT_SECONDARY),
                        ft.Text("Tel: +504 XXXX-XXXX", size=11, color=Theme.TEXT_SECONDARY),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                    padding=Spacing.MD,
                    bgcolor=Theme.SURFACE_VARIANT,
                    border_radius=Radius.MD,
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            expand=True,
            alignment=ft.Alignment.CENTER,
            bgcolor=Theme.BACKGROUND,
        )
    
    def _on_activate(self, e):
        """Maneja la activación de licencia."""
        license_key = self.license_input.value.strip()
        
        if not license_key:
            self._show_error("Por favor ingrese una clave de licencia.")
            return
        
        # Validar licencia
        result = LicenseManager.validate_license(license_key)
        
        if result.get("valid"):
            # Guardar licencia localmente
            LicenseManager.save_license(license_key)
            
            # Mostrar éxito y continuar
            self.page.show_snack_bar(ft.SnackBar(
                ft.Text(f"✅ Licencia activada para: {result.get('client')}"),
                bgcolor=Theme.SUCCESS
            ))
            
            # Callback de éxito con datos de licencia
            self.on_success(result)
        else:
            self._show_error(result.get("error", "Licencia inválida."))
    
    def _on_request_trial(self, e):
        """Genera y activa una licencia de prueba."""
        hw_id = LicenseManager.get_hardware_id()
        trial_key = LicenseManager.generate_license("PRUEBA", "Usuario de Prueba", 1)
        
        # Auto-llenar y activar
        self.license_input.value = trial_key
        self.page.update()
        
        # Activar automáticamente
        self._on_activate(None)
    
    def _show_error(self, message: str):
        """Muestra mensaje de error."""
        self.error_text.value = f"❌ {message}"
        self.error_text.visible = True
        self.page.update()


class LicenseStatusBadge:
    """Badge que muestra el estado de la licencia en la sidebar."""
    
    def __init__(self, license_info: dict):
        self.info = license_info
    
    def build(self) -> ft.Control:
        """Construye el badge de estado."""
        if not self.info or not self.info.get("valid"):
            return ft.Container()  # Invisible si no hay licencia
        
        days_left = self.info.get("days_left", 0)
        license_type = self.info.get("type", "DESCONOCIDA")
        client = self.info.get("client", "")
        
        # Color según días restantes
        if days_left <= 7:
            color = Theme.ERROR
            icon = ft.Icons.WARNING
        elif days_left <= 30:
            color = Colors.ORANGE_600
            icon = ft.Icons.ACCESS_TIME
        else:
            color = Theme.SUCCESS
            icon = ft.Icons.VERIFIED
        
        # Texto según tipo
        if license_type == "PERMANENTE":
            status_text = "Licencia Permanente"
            days_text = ""
        else:
            status_text = f"Licencia {license_type.title()}"
            days_text = f"{days_left} días restantes"
        
        return ft.Container(
            content=ft.Row([
                ft.Icon(icon, color=color, size=16),
                ft.Column([
                    ft.Text(status_text, size=10, weight="bold", color=color),
                    ft.Text(days_text, size=9, color=Theme.TEXT_SECONDARY) if days_text else ft.Container(),
                ], spacing=0, tight=True),
            ], spacing=Spacing.XS),
            padding=ft.padding.symmetric(horizontal=Spacing.SM, vertical=Spacing.XS),
            bgcolor=Theme.SURFACE_VARIANT,
            border_radius=Radius.SM,
            border=ft.border.all(1, color),
        )


class LicenseExpiredDialog:
    """Diálogo para cuando la licencia expira."""
    
    @staticmethod
    def show(page: ft.Page, on_renew: callable, on_exit: callable):
        """Muestra el diálogo de licencia expirada."""
        def close_and_exit(e):
            dlg.open = False
            page.update()
            on_exit()
        
        def close_and_renew(e):
            dlg.open = False
            page.update()
            on_renew()
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.WARNING, color=Theme.ERROR),
                ft.Text("Licencia Expirada", color=Theme.ERROR, weight="bold"),
            ]),
            content=ft.Column([
                ft.Text("Su licencia de LEX VIRIDIS ha expirado."),
                ft.Text("Para continuar usando la aplicación, por favor renueve su licencia."),
                ft.Container(height=Spacing.MD),
                ft.Text("Contacto: soporte@lexviridis.hn", size=12, color=Theme.TEXT_SECONDARY),
            ], tight=True),
            actions=[
                ft.TextButton("Salir", on_click=close_and_exit),
                ft.ElevatedButton("Ingresar Nueva Licencia", on_click=close_and_renew, bgcolor=Theme.PRIMARY, color="white"),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        page.dialog = dlg
        dlg.open = True
        page.update()


def check_license_on_startup(page: ft.Page) -> dict:
    """
    Verifica la licencia al iniciar la aplicación.
    Retorna los datos de licencia si es válida, o None si no.
    """
    saved_license = LicenseManager.load_saved_license()
    
    if saved_license:
        result = LicenseManager.validate_license(saved_license)
        if result.get("valid"):
            return result
        elif result.get("expired"):
            return {"valid": False, "expired": True, "error": result.get("error")}
    
    return None
