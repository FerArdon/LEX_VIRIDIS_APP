"""
LEX VIRIDIS - Main Controller (CustomTkinter)
Arquitectura nativa Windows 11 con Sidebar y ContentFrame.
"""

import customtkinter as ctk
import sys
import os
import threading
import ctypes
import json
from pathlib import Path

# --- DPI Awareness (Windows 11) ---
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass # No disponible en otras plataformas
from PIL import Image

# Configuración de Rutas para empaquetado
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).parent.resolve()

sys.path.append(str(BASE_DIR))

# Importar Componentes
try:
    from lexviridis.config import config
    from lexviridis.design_system_ctk import Colors, Typography, CTKTheme, Assets
    from lexviridis.search_engine import SearchEngine
    from lexviridis.ai_assistant import LegalAIAssistant, GeminiClient
    from lexviridis.security import AuthManager
    
    # Importar Vistas
    from lexviridis.views.search_view import SearchView
    from lexviridis.views.ai_assistant_view import AIAssistantView
    from lexviridis.views.security_view import LicenseView
    from lexviridis.views.library_view import LibraryView
    from lexviridis.views.settings_view import SettingsView
    from lexviridis.views.dashboard_view import DashboardView
    from lexviridis.views.help_view import HelpView
    from lexviridis.views.components.breadcrumb_bar import BreadcrumbBar
except ImportError as e:
    print(f"Error crítico cargando módulos: {e}")
    sys.exit(1)

# Inyectar path de licencia
_license_dir = str(config.BASE_DIR / "LEX_VIRIDIS_LICENCIA")
if _license_dir not in sys.path:
    sys.path.insert(0, _license_dir)
from license_system import LicenseManager

class SidebarButton(ctk.CTkButton):
    """Subclase para estandarizar el estilo de los botones del menú"""
    def __init__(self, master, active_indicator_color=Colors.ACCENT_BLUE, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(
            height=45,
            corner_radius=8,
            border_spacing=10,
            fg_color="transparent",
            text_color=(Colors.TEXT_LIGHT, Colors.TEXT_DARK),
            hover_color=(Colors.WINDOW_BG_LIGHT, "#3d3d3d"),
            anchor="w",
            font=Typography.get_font(13, "bold")
        )
        self.active_indicator_color = active_indicator_color

class SidebarFrame(ctk.CTkFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, width=240, corner_radius=0, **kwargs)
        self.app = app
        self.is_expanded = True
        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        
        # 1. Botón de Toggle / Logo
        self.logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.logo_frame.grid(row=0, column=0, pady=(30, 40), padx=20, sticky="ew")
        
        if "logo" in self.app.icons:
            self.logo_btn = ctk.CTkButton(
                self.logo_frame, 
                image=self.app.icons["logo"], 
                text="", 
                fg_color="transparent", 
                hover=False,
                width=40,
                command=self.toggle_sidebar
            )
            self.logo_btn.pack(side="left")
            
            self.logo_text = ctk.CTkLabel(self.logo_frame, text=" LEX VIRIDIS", font=Typography.title(), text_color=Colors.PRIMARY)
            self.logo_text.pack(side="left")
        else:
            self.logo_btn = ctk.CTkButton(self.logo_frame, text="LV", width=40, command=self.toggle_sidebar)
            self.logo_btn.pack(side="left")

        # 2. Botones de Navegación con Indicadores
        # Iconos Segoe MDL2 Assets (fuente estándar de Windows 11)
        ICON_FONT = ("Segoe MDL2 Assets", 14)
        self.nav_items = {}
        items = [
            ("\uE80F", "Dashboard",     "dashboard"),
            ("\uE71E", "Buscador",      "search"),
            ("\uE99A", "Asistente IA",  "ai"),
            ("\uE736", "Biblioteca",    "library"),
            ("\uE713", "Configuración", "settings"),
            ("\uE897", "Ayuda",         "help"),
        ]

        for i, (icon_char, label, view_id) in enumerate(items, 1):
            container = ctk.CTkFrame(self, fg_color="transparent")
            container.grid(row=i, column=0, sticky="ew", padx=10, pady=2)
            container.grid_columnconfigure(2, weight=1)

            # Indicador Vertical
            indicator = ctk.CTkFrame(container, width=4, height=25, corner_radius=2, fg_color="transparent")
            indicator.grid(row=0, column=0, sticky="w", padx=(0, 4))

            # Icono (Segoe MDL2 Assets)
            icon_lbl = ctk.CTkLabel(
                container, text=icon_char,
                font=ICON_FONT,
                text_color=(Colors.TEXT_LIGHT, Colors.TEXT_DARK),
                width=28, anchor="center"
            )
            icon_lbl.grid(row=0, column=1, sticky="w", padx=(2, 0))

            # Botón de texto
            btn = SidebarButton(
                container,
                text=label,
                command=lambda v=view_id: self.app.select_view(v)
            )
            btn.grid(row=0, column=2, sticky="ew", padx=(0, 8))

            # Click en el icono también navega
            icon_lbl.bind("<Button-1>", lambda e, v=view_id: self.app.select_view(v))

            self.nav_items[view_id] = {
                "btn": btn, "indicator": indicator,
                "icon": icon_lbl, "text": label
            }

        # 3. Footer: Selector de Tema
        self.appearance_mode_menu = ctk.CTkOptionMenu(
            self, 
            values=["Light", "Dark", "System"],
            command=self.change_appearance_mode,
            font=Typography.caption(),
            height=30
        )
        self.appearance_mode_menu.grid(row=10, column=0, pady=20, padx=20, sticky="s")
        self.appearance_mode_menu.set("System")
        self.grid_rowconfigure(10, weight=1)

    def toggle_sidebar(self):
        """Expansión/contracción instantánea del menú lateral."""
        self.is_expanded = not self.is_expanded
        target_width = 240 if self.is_expanded else 80
        self._update_sidebar_visibility()
        self.configure(width=target_width)

    def _update_sidebar_visibility(self):
        if self.is_expanded:
            # Modo expandido: mostrar texto del logo + botones de texto
            if hasattr(self, "logo_text"):
                self.logo_text.pack(side="left")
            for item in self.nav_items.values():
                item["btn"].configure(text=item["text"])
                item["btn"].grid()          # Restaurar botón de texto
                item["icon"].grid()
        else:
            # Modo colapsado: ocultar texto y botones — solo íconos
            if hasattr(self, "logo_text"):
                self.logo_text.forget()
            for item in self.nav_items.values():
                item["btn"].grid_remove()   # Ocultar botón (evita la caja azul vacía)
                item["icon"].grid()

    def change_appearance_mode(self, new_mode):
        ctk.set_appearance_mode(new_mode)

    def set_active(self, view_id):
        """Resalta el botón activo y el indicador vertical."""
        collapsed = not self.is_expanded
        for vid, item in self.nav_items.items():
            if vid == view_id:
                if not collapsed:
                    item["btn"].configure(fg_color=("#3a7ebf", "#1f538d"), text_color="white")
                item["indicator"].configure(fg_color=Colors.ACCENT_BLUE)
                item["icon"].configure(text_color=Colors.ACCENT_BLUE if collapsed else "white")
            else:
                if not collapsed:
                    item["btn"].configure(fg_color="transparent", text_color=(Colors.TEXT_LIGHT, Colors.TEXT_DARK))
                item["indicator"].configure(fg_color="transparent")
                item["icon"].configure(text_color=(Colors.TEXT_LIGHT, Colors.TEXT_DARK))

class LoginWindow(ctk.CTkToplevel):
    """Ventana de inicio de sesión — usuario y contraseña."""

    def __init__(self, master, auth_manager, on_success):
        super().__init__(master)
        self.auth = auth_manager
        self.on_success = on_success

        self.title("LEX VIRIDIS — Iniciar Sesión")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.grab_set()                        # modal: bloquea la ventana principal

        w, h = 420, 500
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.configure(fg_color=(Colors.WINDOW_BG_LIGHT, Colors.WINDOW_BG_DARK))

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        # Logo
        logo_path = Assets.get_asset_path("assets/LEXVIRIDIS_WHITE_BG.png")
        if os.path.exists(logo_path):
            img = Image.open(logo_path).resize((72, 72), Image.LANCZOS)
            self._logo = ctk.CTkImage(img, size=(72, 72))
            ctk.CTkLabel(self, image=self._logo, text="").pack(pady=(30, 6))

        ctk.CTkLabel(self, text="LEX VIRIDIS",
                     font=("Segoe UI", 22, "bold"),
                     text_color=Colors.PRIMARY).pack()
        ctk.CTkLabel(self, text="Ingresa tus credenciales para continuar",
                     font=Typography.caption(),
                     text_color=Colors.TEXT_SECONDARY).pack(pady=(2, 24))

        # Formulario
        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(padx=40, fill="x")

        ctk.CTkLabel(form, text="Usuario", font=Typography.bold(),
                     anchor="w").pack(fill="x")
        self._user_entry = ctk.CTkEntry(form, placeholder_text="Nombre de usuario",
                                        height=40, font=Typography.body())
        self._user_entry.pack(fill="x", pady=(4, 14))

        ctk.CTkLabel(form, text="Contraseña", font=Typography.bold(),
                     anchor="w").pack(fill="x")
        self._pass_entry = ctk.CTkEntry(form, placeholder_text="Contraseña",
                                        show="•", height=40, font=Typography.body())
        self._pass_entry.pack(fill="x", pady=(4, 6))

        # Mostrar/ocultar contraseña
        self._show_pass = ctk.CTkCheckBox(form, text="Mostrar contraseña",
                                          font=Typography.caption(),
                                          command=self._toggle_pass)
        self._show_pass.pack(anchor="w", pady=(0, 20))

        # Error
        self._lbl_error = ctk.CTkLabel(form, text="", font=Typography.caption(),
                                        text_color=Colors.ERROR, wraplength=340)
        self._lbl_error.pack(fill="x", pady=(0, 8))

        # Botón principal
        self._btn_login = ctk.CTkButton(form, text="Ingresar", height=44,
                                         font=Typography.bold(),
                                         fg_color=Colors.PRIMARY,
                                         hover_color=Colors.ACCENT_BLUE,
                                         command=self._do_login)
        self._btn_login.pack(fill="x")

        # Separador
        ctk.CTkLabel(form, text="── ó ──", font=Typography.caption(),
                     text_color=Colors.TEXT_SECONDARY).pack(pady=12)

        # Registro (primer uso)
        ctk.CTkButton(form, text="Crear cuenta nueva", height=36,
                      font=Typography.body(),
                      fg_color="transparent",
                      border_width=1, border_color=Colors.BORDER,
                      text_color=(Colors.TEXT_LIGHT, Colors.TEXT_DARK),
                      command=self._open_register).pack(fill="x")

        # Bind Enter
        self.bind("<Return>", lambda e: self._do_login())
        self._user_entry.focus()

    def _toggle_pass(self):
        self._pass_entry.configure(show="" if self._show_pass.get() else "•")

    def _do_login(self):
        username = self._user_entry.get().strip()
        password = self._pass_entry.get()

        if not username or not password:
            self._lbl_error.configure(text="Completa usuario y contraseña.")
            return

        self._btn_login.configure(state="disabled", text="Verificando…")
        self._lbl_error.configure(text="")
        threading.Thread(target=self._verify, args=(username, password), daemon=True).start()

    def _verify(self, username, password):
        try:
            user = self.auth.login(username, password)
            if user:
                self.after(0, self._handle_success, user)
            else:
                self.after(0, self._show_error, "Usuario o contraseña incorrectos.")
        except Exception as e:
            self.after(0, self._show_error, f"Error al verificar: {e}")

    def _handle_success(self, user):
        self.grab_release()
        self.destroy()
        self.on_success(user)

    def _show_error(self, msg):
        self._lbl_error.configure(text=f"❌ {msg}")
        self._btn_login.configure(state="normal", text="Ingresar")

    def _open_register(self):
        RegisterWindow(self, self.auth, on_registered=self._do_login)

    def _on_close(self):
        # Cerrar toda la app si el usuario cierra el login sin autenticarse
        self.master.destroy()


class RegisterWindow(ctk.CTkToplevel):
    """Ventana de registro de nuevo usuario."""

    def __init__(self, master, auth_manager, on_registered=None):
        super().__init__(master)
        self.auth = auth_manager
        self.on_registered = on_registered

        self.title("LEX VIRIDIS — Crear Cuenta")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.grab_set()

        w, h = 400, 420
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.configure(fg_color=(Colors.WINDOW_BG_LIGHT, Colors.WINDOW_BG_DARK))

        self._build_ui()

    def _build_ui(self):
        ctk.CTkLabel(self, text="Crear nueva cuenta",
                     font=("Segoe UI", 18, "bold"),
                     text_color=Colors.PRIMARY).pack(pady=(30, 4))
        ctk.CTkLabel(self, text="Solo para el primer administrador del sistema",
                     font=Typography.caption(),
                     text_color=Colors.TEXT_SECONDARY).pack(pady=(0, 20))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(padx=40, fill="x")

        for label, attr, placeholder, show in [
            ("Usuario",          "_r_user",  "Nombre de usuario", ""),
            ("Email",            "_r_email", "correo@ejemplo.com", ""),
            ("Contraseña",       "_r_pass",  "Contraseña",         "•"),
            ("Confirmar contraseña", "_r_pass2", "Repite la contraseña", "•"),
        ]:
            ctk.CTkLabel(form, text=label, font=Typography.bold(), anchor="w").pack(fill="x")
            entry = ctk.CTkEntry(form, placeholder_text=placeholder,
                                 show=show, height=38, font=Typography.body())
            entry.pack(fill="x", pady=(4, 12))
            setattr(self, attr, entry)

        self._lbl_error = ctk.CTkLabel(form, text="", font=Typography.caption(),
                                        text_color=Colors.ERROR, wraplength=320)
        self._lbl_error.pack(fill="x", pady=(0, 8))

        ctk.CTkButton(form, text="Registrar", height=42,
                      font=Typography.bold(),
                      fg_color=Colors.PRIMARY,
                      hover_color=Colors.ACCENT_BLUE,
                      command=self._do_register).pack(fill="x")

    def _do_register(self):
        username = self._r_user.get().strip()
        email    = self._r_email.get().strip()
        password = self._r_pass.get()
        confirm  = self._r_pass2.get()

        if not all([username, email, password, confirm]):
            self._lbl_error.configure(text="Todos los campos son requeridos.")
            return
        if password != confirm:
            self._lbl_error.configure(text="Las contraseñas no coinciden.")
            return
        if len(password) < 6:
            self._lbl_error.configure(text="La contraseña debe tener al menos 6 caracteres.")
            return

        try:
            self.auth.create_user(username, password, email, role="admin")
            self.grab_release()
            self.destroy()
            if self.on_registered:
                self.on_registered()
        except Exception as e:
            self._lbl_error.configure(text=f"Error al registrar: {e}")


class SplashScreen(ctk.CTkToplevel):
    """Ventana de carga inicial sin bordes, centrada en pantalla."""

    _BG       = "#1b5e20"   # verde oscuro LEX VIRIDIS
    _BAR_FG   = "#4caf50"   # barra verde claro
    _BAR_BG   = "#2e7d32"   # track de la barra
    _TEXT_DIM = "#a5d6a7"   # texto secundario

    def __init__(self, master):
        super().__init__(master)
        self.overrideredirect(True)
        self.attributes("-topmost", True)

        w, h = 480, 300
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.configure(fg_color=self._BG)
        self.resizable(False, False)

        # --- Logo ---
        logo_path = Assets.get_asset_path("assets/LEXVIRIDIS_WHITE_BG.png")
        if os.path.exists(logo_path):
            img = Image.open(logo_path).resize((90, 90), Image.LANCZOS)
            self._logo_img = ctk.CTkImage(img, size=(90, 90))
            ctk.CTkLabel(self, image=self._logo_img, text="").pack(pady=(30, 8))
        else:
            ctk.CTkFrame(self, width=90, height=90, fg_color=self._BAR_BG).pack(pady=(30, 8))

        # --- Nombre y subtítulo ---
        ctk.CTkLabel(
            self, text="LEX VIRIDIS",
            font=("Segoe UI", 26, "bold"), text_color="white"
        ).pack()
        ctk.CTkLabel(
            self, text="Plataforma de Gestión Legal Institucional",
            font=("Segoe UI", 11), text_color=self._TEXT_DIM
        ).pack(pady=(2, 20))

        # --- Barra de progreso ---
        self._bar = ctk.CTkProgressBar(
            self, width=360, height=5,
            progress_color=self._BAR_FG, fg_color=self._BAR_BG
        )
        self._bar.pack()
        self._bar.set(0)

        # --- Estado ---
        self._status = ctk.CTkLabel(
            self, text="Iniciando…",
            font=("Segoe UI", 10), text_color=self._TEXT_DIM
        )
        self._status.pack(pady=(6, 0))

        self._value = 0.0
        self._pulse()

    def _pulse(self):
        """Animación suave de la barra hasta el 88 % mientras espera el backend."""
        if self._value < 0.88:
            self._value = min(self._value + 0.008, 0.88)
            self._bar.set(self._value)
            self.after(40, self._pulse)

    def set_status(self, msg: str):
        self._status.configure(text=msg)

    def finish(self):
        """Completa la barra al 100 % y destruye la splash tras 350 ms."""
        self._value = 1.0
        self._bar.set(1.0)
        self._status.configure(text="¡Listo!")
        self.after(350, self.destroy)


class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.withdraw()          # ocultar ventana principal mientras carga la splash

        # 1. Configuración de Ventana
        self.title(f"{config.APP_NAME} V{config.APP_VERSION}")
        self.geometry("1100x700")
        self.configure(fg_color=(Colors.WINDOW_BG_LIGHT, Colors.WINDOW_BG_DARK))
        CTKTheme.setup()

        # Icono de Ventana Principal (.ico)
        ico_path = Assets.get_asset_path("assets/LEXVIRIDIS_WHITE_BG.ico")
        if os.path.exists(ico_path):
            self.iconbitmap(str(ico_path))

        # 2. Estado del Sistema e Impulsión de Motores
        self.icons = Assets.load_icons()
        self.engine = None
        self.gemini = None
        self.auth = None
        self.ai_assistant = None
        self.license_info = None
        self.current_user = None
        self._splash = None

        # 3. Layout Principal (Sidebar + Content)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = SidebarFrame(self, self)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # Contenedor de Contenido (Derecha) - Arquitectura V4.0
        self.content_area = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content_area.grid(row=0, column=1, sticky="nsew")
        self.content_area.grid_rowconfigure(1, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)

        # 3.1 Header (Breadcrumbs)
        self.header_frame = ctk.CTkFrame(self.content_area, height=50, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(10, 0))

        self.breadcrumbs = BreadcrumbBar(self.header_frame)
        self.breadcrumbs.pack(side="left", fill="y")

        # 3.2 Views Container
        self.views_container = ctk.CTkFrame(self.content_area, corner_radius=0, fg_color="transparent")
        self.views_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        self.views_container.grid_rowconfigure(0, weight=1)
        self.views_container.grid_columnconfigure(0, weight=1)

        self.views = {}
        self.current_view_name = None
        self.is_transitioning = False
        self.setup_toast_manager()

        # 4. Mostrar Splash y arrancar backend en paralelo
        self._splash = SplashScreen(self)
        self._splash.update()
        self.init_backend()

    def setup_toast_manager(self):
        self.toast_frame = ctk.CTkFrame(self, fg_color=Colors.ACCENT_BLUE, corner_radius=10, height=40)
        self.toast_label = ctk.CTkLabel(self.toast_frame, text="", text_color="white", font=Typography.bold())
        self.toast_label.pack(padx=20, pady=5)

    def show_toast(self, message, type="info", duration=3000):
        self.toast_label.configure(text=message)
        self.toast_frame.place(relx=0.5, rely=0.9, anchor="n")
        self.after(duration, lambda: self.toast_frame.place_forget())

    def _splash_status(self, msg: str):
        """Actualiza el texto de la splash desde cualquier hilo (thread-safe)."""
        if self._splash and self._splash.winfo_exists():
            self.after(0, lambda: self._splash.set_status(msg))

    def _close_splash_and_show(self):
        """Cierra la splash y muestra la ventana principal."""
        if self._splash and self._splash.winfo_exists():
            self._splash.finish()
        self.after(400, self._reveal_main)

    def _reveal_main(self):
        self.deiconify()
        self.state("zoomed")
        self.after(150, self._decide_initial_view)

    def _decide_initial_view(self):
        """Decide qué mostrar: login, licencia o app principal."""
        if not self.license_info:
            self.select_view("license")
            return

        # Intentar sesión guardada
        token = self._load_saved_session()
        if token and self.auth:
            user = self.auth.validate_session(token)
            if user:
                self.current_user = user
                self.select_view("search")
                self.show_toast(f"Bienvenido, {user['username']}", "success")
                return

        # Sin sesión válida → mostrar login
        if self.auth:
            LoginWindow(self, self.auth, on_success=self._on_login_success)
        else:
            # auth no cargó — ir directo (degraded mode)
            self.select_view("search")

    def _on_login_success(self, user):
        self.current_user = user
        self._save_session(user.get("token", ""))
        self.select_view("search")
        self.show_toast(f"Bienvenido, {user['username']}", "success")

    def _load_saved_session(self):
        try:
            session_file = config.DATA_DIR / "session.json"
            if session_file.exists():
                with open(session_file, "r") as f:
                    return json.load(f).get("token", "")
        except Exception:
            pass
        return ""

    def _save_session(self, token: str):
        try:
            session_file = config.DATA_DIR / "session.json"
            with open(session_file, "w") as f:
                json.dump({"token": token}, f)
        except Exception:
            pass

    def init_backend(self):
        def _load():
            try:
                # 1. Licencia
                self._splash_status("Verificando licencia…")
                saved_key = LicenseManager.load_saved_license()
                if saved_key:
                    res = LicenseManager.validate_license(saved_key)
                    if res.get("valid"):
                        self.license_info = res

                # 1b. Cargar banners en segundo plano
                self._splash_status("Cargando recursos gráficos…")
                banners = Assets.load_banners()
                self.icons.update(banners)

                # 2. Motores
                self._splash_status("Inicializando motor de búsqueda…")
                self.engine = SearchEngine()

                self._splash_status("Configurando asistente IA…")
                _gemini_key, _gemini_model, _groq_key, _groq_model, _provider = self._load_saved_api_key()
                if _provider == "groq":
                    from lexviridis.ai_assistant import GroqClient
                    self.gemini = GroqClient(api_key=_groq_key, model_name=_groq_model)
                else:
                    self.gemini = GeminiClient(api_key=_gemini_key, model_name=_gemini_model)
                self.auth = AuthManager(self.engine.db_manager)
                self.ai_assistant = LegalAIAssistant(self.engine, self.gemini)

                self._splash_status("Preparando interfaz…")

            except Exception as e:
                self.update_ui(self.show_toast, f"Fallo al cargar backend: {e}", "error")
            finally:
                self.update_ui(self._close_splash_and_show)

        threading.Thread(target=_load, daemon=True).start()

    def update_ui(self, func, *args):
        self.after(0, lambda: func(*args))

    def select_view(self, view_id):
        """Intercambio de frames con efecto Fading Animado."""
        if not self.license_info and view_id != "license":
            self.show_toast("Activación Requerida", "error")
            return

        if self.is_transitioning or view_id == self.current_view_name:
            return

        self.is_transitioning = True
        
        # 1. Preparar nueva vista (Lazy Loading)
        try:
            if view_id not in self.views:
                if view_id == "dashboard":
                    self.views[view_id] = DashboardView(self.views_container, self)
                elif view_id == "search":
                    self.views[view_id] = SearchView(self.views_container, self)
                elif view_id == "ai":
                    self.views[view_id] = AIAssistantView(self.views_container, self)
                elif view_id == "library":
                    self.views[view_id] = LibraryView(self.views_container, self)
                elif view_id == "settings":
                    self.views[view_id] = SettingsView(self.views_container, self)
                elif view_id == "help":
                    self.views[view_id] = HelpView(self.views_container, self)
                elif view_id == "license":
                    from lexviridis.views.security_view import LicenseView
                    self.views[view_id] = LicenseView(self.views_container, self, on_success=self.on_license_activated)
                else:
                    self.views[view_id] = ctk.CTkFrame(self.views_container)
                    ctk.CTkLabel(self.views[view_id], text=f"Módulo {view_id} en Desarrollo", font=Typography.subtitle()).pack(pady=100)
        except Exception as e:
            self.is_transitioning = False
            self.show_toast(f"Error cargando módulo '{view_id}': {e}", "error")
            import traceback
            traceback.print_exc()
            return

        # 2. Iniciar Animación
        self._animate_transition(view_id)

    def _animate_transition(self, view_id):
        """Implementa un efecto de Fading (Out -> In) mediante bucle after."""
        old_view = self.views.get(self.current_view_name)
        new_view = self.views[view_id]

        # 1. Fase Fade-Out (Hacia transparente)
        # Nota: Simulamos con parpadeo y cambio de estado para evitar lag en Tkinter
        def phase_out(step=0):
            if step < 5:
                if old_view:
                    # Alternar visibilidad para efecto parpadeo suave
                    if step % 2 == 0:
                        old_view.grid_forget()
                    else:
                        old_view.grid(row=0, column=0, sticky="nsew")
                self.after(30, lambda: phase_out(step + 1))
            else:
                complete_swap()

        def complete_swap():
            if old_view:
                old_view.grid_forget()
            
            # Actualizar Breadcrumbs y Sidebar antes del Fade-In
            self._update_navigation_meta(view_id)
            
            new_view.grid(row=0, column=0, sticky="nsew")
            phase_in(0)

        def phase_in(step=0):
            if step < 5:
                self.after(30, lambda: phase_in(step + 1))
            else:
                self.is_transitioning = False

        phase_out()

    def _update_navigation_meta(self, view_id):
        """Sincroniza metadatos de navegación."""
        routes = {
            "dashboard": ["Inicio", "Dashboard"],
            "search": ["Inicio", "Buscador Legal"],
            "ai": ["Inicio", "Asistente IA"],
            "license": ["Seguridad", "Activación"],
            "library": ["Gestión", "Biblioteca"],
            "settings": ["Configuración", "Sistema"],
            "help": ["Ayuda", "Tutorial y Guía"],
        }
        self.breadcrumbs.set_route(routes.get(view_id, ["Inicio", view_id.capitalize()]))
        self.sidebar.set_active(view_id)
        self.current_view_name = view_id

    def _load_saved_api_key(self):
        """Lee la API key, modelo y proveedor desde disco. Resultado en caché hasta que se llame reload_api_key()."""
        if hasattr(self, "_api_key_cache") and self._api_key_cache is not None:
            return self._api_key_cache
        import json
        _default = ("", "gemini-2.0-flash", "", "llama-3.3-70b-versatile", "groq")
        try:
            key_file = config.API_KEY_FILE
            if key_file.exists():
                with open(key_file, 'r') as f:
                    data = json.load(f)
                    result = (
                        data.get("gemini_api_key", ""),
                        data.get("gemini_model", "gemini-2.0-flash"),
                        data.get("groq_api_key", ""),
                        data.get("groq_model", "llama-3.3-70b-versatile"),
                        data.get("provider", "groq"),
                    )
                    self._api_key_cache = result
                    return result
        except Exception:
            pass
        self._api_key_cache = _default
        return _default

    def reload_api_key(self):
        """Invalida el caché de API key para forzar lectura desde disco en la próxima llamada."""
        self._api_key_cache = None

    def on_license_activated(self, info):
        self.license_info = info
        if self.engine:
            self.select_view("search")
        else:
            # Engine todavía cargando — reintentar cada 500ms
            self._wait_engine_then_navigate()

    def _wait_engine_then_navigate(self, attempts=0):
        if self.engine:
            self.select_view("search")
        elif attempts < 20:   # máx 10 segundos
            self.after(500, lambda: self._wait_engine_then_navigate(attempts + 1))
        else:
            self.show_toast("El motor tardó demasiado en cargar. Reinicia la app.", "error")

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
