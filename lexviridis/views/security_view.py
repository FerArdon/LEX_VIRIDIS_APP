"""
LEX VIRIDIS - License Activation View (CustomTkinter)
Interfaz nativa para validación y activación de licencias.
"""

import customtkinter as ctk
import sys
from pathlib import Path
from .base_view import BaseView
from ..design_system_ctk import Colors, Typography

# Asegurar acceso al LicenseManager
try:
    from ..config import config as _cfg
    _license_dir = str(_cfg.BASE_DIR / "LEX_VIRIDIS_LICENCIA")
except Exception:
    _license_dir = str(Path(__file__).parent.parent.parent / "LEX_VIRIDIS_LICENCIA")

if _license_dir not in sys.path:
    sys.path.insert(0, _license_dir)

try:
    from license_system import LicenseManager
except ImportError:
    class LicenseManager:
        @staticmethod
        def validate_license(key): return {"valid": False, "error": "Sistema de licencias no encontrado"}
        @staticmethod
        def save_license(key): pass
        @staticmethod
        def get_hardware_id(): return "ERR-ID"

class LicenseView(BaseView):
    def __init__(self, master, app, on_success=None, **kwargs):
        super().__init__(master, app, **kwargs)
        self.on_success = on_success
        self.setup_ui()

    def setup_ui(self):
        # Contenedor Central
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.place(relx=0.5, rely=0.5, anchor="center")
        
        # Título e ícono
        self.lbl_title = ctk.CTkLabel(
            self.container, 
            text="Activación de LEX VIRIDIS", 
            font=Typography.title(),
            text_color=Colors.PRIMARY
        )
        self.lbl_title.pack(pady=(0, 10))
        
        self.lbl_info = ctk.CTkLabel(
            self.container, 
            text="Ingrese su clave de licencia institucional para continuar", 
            font=Typography.body(),
            text_color=Colors.TEXT_SECONDARY
        )
        self.lbl_info.pack(pady=(0, 30))

        # Input de Licencia
        self.license_entry = ctk.CTkTextbox(
            self.container, 
            width=500, 
            height=100,
            font=Typography.body(),
            border_color=Colors.BORDER,
            border_width=2
        )
        self.license_entry.pack(pady=(0, 10))
        
        # Error Label
        self.lbl_error = ctk.CTkLabel(
            self.container, 
            text="", 
            font=Typography.caption(),
            text_color=Colors.ERROR
        )
        self.lbl_error.pack(pady=(0, 10))

        # Botones
        self.btn_activate = ctk.CTkButton(
            self.container, 
            text="Activar Licencia", 
            command=self.activate_license,
            fg_color=Colors.ACCENT_BLUE,
            hover_color=Colors.PRIMARY,
            height=45,
            width=200,
            font=Typography.bold()
        )
        self.btn_activate.pack(pady=10)

        self.btn_trial = ctk.CTkButton(
            self.container, 
            text="Solicitar Prueba", 
            command=self.request_trial,
            fg_color="transparent",
            text_color=Colors.TEXT_SECONDARY,
            border_width=1,
            border_color=Colors.BORDER,
            height=30
        )
        self.btn_trial.pack(pady=5)

        # ID de Hardware para soporte
        hw_id = LicenseManager.get_hardware_id()
        self.lbl_hwid = ctk.CTkLabel(
            self.container, 
            text=f"ID de Hardware: {hw_id}", 
            font=Typography.caption(),
            text_color=Colors.TEXT_SECONDARY
        )
        self.lbl_hwid.pack(pady=(20, 0))

    def activate_license(self):
        key = self.license_entry.get("1.0", "end-1c").strip()
        if not key:
            self.show_error("Por favor ingrese una clave.")
            return

        self.lbl_error.configure(text="")
        self.btn_activate.configure(state="disabled", text="Validando...")
        self.run_in_thread(self._verify_thread, (key,))

    def _reset_btn(self):
        self.btn_activate.configure(state="normal", text="Activar Licencia")

    def _verify_thread(self, key):
        try:
            result = LicenseManager.validate_license(key)
            if result.get("valid"):
                LicenseManager.save_license(key)
                self.update_ui(self._handle_success, result)
            else:
                self.update_ui(self.show_error, result.get("error", "Clave inválida"))
                self.update_ui(self._reset_btn)
        except Exception as e:
            self.update_ui(self.show_error, f"Error inesperado: {e}")
            self.update_ui(self._reset_btn)

    def _handle_success(self, result):
        try:
            client = result.get("client", "Usuario")
            self.app.show_toast(f"Bienvenido, {client}", "success")
            if self.on_success:
                self.on_success(result)
        except Exception as e:
            self.show_error(f"Error al activar: {e}")
            self._reset_btn()

    def request_trial(self):
        # Lógica de trial automática (como en Flet)
        from license_system import LicenseManager
        trial_key = LicenseManager.generate_license("PRUEBA", "Usuario de Prueba", 1)
        self.license_entry.delete("1.0", "end")
        self.license_entry.insert("1.0", trial_key)
        self.activate_license()

    def show_error(self, message):
        self.lbl_error.configure(text=f"❌ {message}")
