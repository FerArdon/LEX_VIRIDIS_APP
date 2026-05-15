"""
LEX VIRIDIS - Settings View
Panel de configuración y preferencias del sistema.
"""

import customtkinter as ctk
from .base_view import BaseView
from ..design_system_ctk import Colors, Typography
from ..config import config

class SettingsView(BaseView):
    def __init__(self, master, app):
        super().__init__(master, app)
        self.setup_ui()

    def setup_ui(self):
        # 1. Título de Sección
        self.lbl_title = ctk.CTkLabel(
            self, 
            text="Configuración del Sistema", 
            font=Typography.get_font(22, "bold"),
            text_color=Colors.PRIMARY,
            anchor="w"
        )
        self.lbl_title.pack(fill="x", padx=30, pady=(30, 20))

        self.scroll_main = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_main.pack(fill="both", expand=True, padx=20, pady=10)

        # --- IA & API KEY ---
        self.ai_group = self.create_group(self.scroll_main, "Inteligencia Artificial")

        # ── Selector de proveedor ──
        provider_row = ctk.CTkFrame(self.ai_group, fg_color="transparent")
        provider_row.pack(anchor="w", padx=20, pady=(14, 8))
        ctk.CTkLabel(provider_row, text="Proveedor de IA:", font=Typography.bold()).pack(side="left", padx=(0, 12))
        self._provider_var = ctk.StringVar(value=self._load_saved_provider())
        self.provider_seg = ctk.CTkSegmentedButton(
            provider_row,
            values=["Groq (Recomendado)", "Gemini (Google)"],
            variable=self._provider_var,
            command=self._on_provider_change,
            font=Typography.get_font(12),
            height=30,
        )
        self.provider_seg.pack(side="left")

        # ── Frame Groq ──
        self.frame_groq = ctk.CTkFrame(self.ai_group, fg_color="transparent")

        groq_info_box = ctk.CTkFrame(self.frame_groq, fg_color=("#e8f4f8", "#1a2f3a"), corner_radius=8)
        groq_info_box.pack(fill="x", padx=0, pady=(4, 6))

        ctk.CTkLabel(
            groq_info_box,
            text="ℹ  ¿Cómo obtener tu API Key de Groq? (100% gratuita, sin tarjeta)",
            font=Typography.bold(),
            text_color=Colors.ACCENT_BLUE, anchor="w"
        ).pack(anchor="w", padx=14, pady=(10, 4))

        ctk.CTkLabel(
            groq_info_box,
            text=(
                "1. Abre el enlace de abajo → crea una cuenta en Groq\n"
                "2. Ve a 'API Keys' → haz clic en 'Create API Key'\n"
                "3. Copia la clave generada (comienza con  gsk_...)\n"
                "4. Pégala en el campo de abajo y presiona  'Guardar API Key'"
            ),
            font=Typography.get_font(12),
            text_color=Colors.TEXT_SECONDARY,
            anchor="w", justify="left"
        ).pack(anchor="w", padx=14, pady=(0, 6))

        groq_link_row = ctk.CTkFrame(groq_info_box, fg_color="transparent")
        groq_link_row.pack(anchor="w", padx=14, pady=(0, 10))

        ctk.CTkLabel(
            groq_link_row, text="Enlace directo: ",
            font=Typography.get_font(12), text_color=Colors.TEXT_SECONDARY
        ).pack(side="left")

        lbl_groq_link = ctk.CTkLabel(
            groq_link_row,
            text="https://console.groq.com/keys",
            font=Typography.get_font(12, "bold"),
            text_color=Colors.ACCENT_BLUE,
            cursor="hand2"
        )
        lbl_groq_link.pack(side="left")
        lbl_groq_link.bind("<Button-1>", lambda e: self._open_url("https://console.groq.com/keys"))

        ctk.CTkButton(
            groq_link_row, text="Abrir en navegador",
            fg_color="transparent", border_width=1, border_color=Colors.ACCENT_BLUE,
            text_color=Colors.ACCENT_BLUE, height=26, corner_radius=6,
            font=Typography.get_font(11),
            command=lambda: self._open_url("https://console.groq.com/keys")
        ).pack(side="left", padx=(12, 0))

        ctk.CTkLabel(self.frame_groq, text="Groq API Key", font=Typography.bold()).pack(anchor="w", pady=(10, 5))
        self.entry_groq_api = ctk.CTkEntry(self.frame_groq, placeholder_text="Pega aquí tu clave  gsk_...", width=400, show="*")
        self.entry_groq_api.pack(anchor="w", pady=(0, 8))

        saved_groq_key = self._load_groq_api_key()
        if saved_groq_key:
            self.entry_groq_api.insert(0, saved_groq_key)

        groq_model_row = ctk.CTkFrame(self.frame_groq, fg_color="transparent")
        groq_model_row.pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(groq_model_row, text="Modelo Groq:", font=Typography.caption(),
                     text_color=Colors.TEXT_SECONDARY).pack(side="left", padx=(0, 8))
        self.groq_model_menu = ctk.CTkOptionMenu(
            groq_model_row,
            values=["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768", "gemma2-9b-it"],
            width=240, height=28, font=Typography.caption(), fg_color=Colors.PRIMARY,
        )
        self.groq_model_menu.pack(side="left")
        self.groq_model_menu.set(self._load_saved_groq_model())

        ctk.CTkLabel(
            self.frame_groq,
            text="· Llama 3.3 70B: mejor calidad (recomendado)  · Llama 3.1 8B: más rápido",
            font=Typography.get_font(11),
            text_color=Colors.TEXT_SECONDARY,
            anchor="w"
        ).pack(anchor="w", pady=(0, 10))

        # ── Frame Gemini ──
        self.frame_gemini = ctk.CTkFrame(self.ai_group, fg_color="transparent")

        gemini_info_box = ctk.CTkFrame(self.frame_gemini, fg_color=("#e8f4f8", "#1a2f3a"), corner_radius=8)
        gemini_info_box.pack(fill="x", padx=0, pady=(4, 6))

        ctk.CTkLabel(
            gemini_info_box,
            text="ℹ  ¿Cómo obtener tu API Key de Google Gemini? (es gratuita)",
            font=Typography.bold(),
            text_color=Colors.ACCENT_BLUE, anchor="w"
        ).pack(anchor="w", padx=14, pady=(10, 4))

        ctk.CTkLabel(
            gemini_info_box,
            text=(
                "1. Abre el enlace de abajo → inicia sesión con tu cuenta de Google\n"
                "2. Haz clic en  'Get API Key'  →  'Create API key in new project'\n"
                "3. Copia la clave generada (comienza con  AIza...)\n"
                "4. Pégala en el campo de abajo y presiona  'Guardar API Key'"
            ),
            font=Typography.get_font(12),
            text_color=Colors.TEXT_SECONDARY,
            anchor="w", justify="left"
        ).pack(anchor="w", padx=14, pady=(0, 6))

        gemini_link_row = ctk.CTkFrame(gemini_info_box, fg_color="transparent")
        gemini_link_row.pack(anchor="w", padx=14, pady=(0, 10))

        ctk.CTkLabel(
            gemini_link_row, text="Enlace directo: ",
            font=Typography.get_font(12), text_color=Colors.TEXT_SECONDARY
        ).pack(side="left")

        lbl_gemini_link = ctk.CTkLabel(
            gemini_link_row,
            text="https://aistudio.google.com/app/apikey",
            font=Typography.get_font(12, "bold"),
            text_color=Colors.ACCENT_BLUE,
            cursor="hand2"
        )
        lbl_gemini_link.pack(side="left")
        lbl_gemini_link.bind("<Button-1>", lambda e: self._open_url("https://aistudio.google.com/app/apikey"))

        ctk.CTkButton(
            gemini_link_row, text="Abrir en navegador",
            fg_color="transparent", border_width=1, border_color=Colors.ACCENT_BLUE,
            text_color=Colors.ACCENT_BLUE, height=26, corner_radius=6,
            font=Typography.get_font(11),
            command=lambda: self._open_url("https://aistudio.google.com/app/apikey")
        ).pack(side="left", padx=(12, 0))

        ctk.CTkLabel(self.frame_gemini, text="Gemini API Key", font=Typography.bold()).pack(anchor="w", pady=(10, 5))
        self.entry_api = ctk.CTkEntry(self.frame_gemini, placeholder_text="Pega aquí tu clave  AIza...", width=400, show="*")
        self.entry_api.pack(anchor="w", pady=(0, 8))

        saved_key = self._load_api_key()
        if saved_key:
            self.entry_api.insert(0, saved_key)

        gemini_model_row = ctk.CTkFrame(self.frame_gemini, fg_color="transparent")
        gemini_model_row.pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(gemini_model_row, text="Modelo Gemini:", font=Typography.caption(),
                     text_color=Colors.TEXT_SECONDARY).pack(side="left", padx=(0, 8))
        self.model_menu = ctk.CTkOptionMenu(
            gemini_model_row,
            values=["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-flash-8b", "gemini-1.5-pro"],
            width=200, height=28, font=Typography.caption(), fg_color=Colors.PRIMARY,
            command=self._update_model_hint
        )
        self.model_menu.pack(side="left")
        self.model_menu.set(self._load_saved_model())

        self.lbl_model_hint = ctk.CTkLabel(
            self.frame_gemini,
            text=self._get_model_hint(self._load_saved_model()),
            font=Typography.get_font(11),
            text_color=Colors.TEXT_SECONDARY,
            anchor="w", justify="left", wraplength=520
        )
        self.lbl_model_hint.pack(anchor="w", pady=(0, 10))

        # ── Mostrar frame según proveedor guardado ──
        if self._provider_var.get() == "Gemini (Google)":
            self.frame_gemini.pack(fill="x", padx=20, pady=(0, 4))
        else:
            self.frame_groq.pack(fill="x", padx=20, pady=(0, 4))

        # ── Botón guardar y estado (compartido) ──
        self.api_btn_row = ctk.CTkFrame(self.ai_group, fg_color="transparent")
        api_btn_row = self.api_btn_row
        api_btn_row.pack(anchor="w", padx=20, pady=(0, 15))

        ctk.CTkButton(
            api_btn_row, text="Guardar API Key",
            fg_color=Colors.PRIMARY, height=32, corner_radius=8,
            command=self._save_api_key
        ).pack(side="left", padx=(0, 10))

        _active_key = saved_groq_key if self._provider_var.get() != "Gemini (Google)" else saved_key
        self.lbl_api_status = ctk.CTkLabel(
            api_btn_row, text="✓ Clave activa" if _active_key else "Sin clave configurada",
            font=Typography.caption(),
            text_color=Colors.SUCCESS if _active_key else Colors.TEXT_SECONDARY
        )
        self.lbl_api_status.pack(side="left")
        
        # --- RUTAS DE SISTEMA ---
        self.path_group = self.create_group(self.scroll_main, "Rutas de Datos")
        
        ctk.CTkLabel(self.path_group, text="Directorio de Base de Datos", font=Typography.bold()).pack(anchor="w", padx=20, pady=(15, 5))
        self.lbl_db_path = ctk.CTkLabel(self.path_group, text=str(config.DB_DIR), text_color=Colors.TEXT_SECONDARY)
        self.lbl_db_path.pack(anchor="w", padx=20, pady=(0, 10))

        # --- HISTORIAL DE EXPORTACIONES ---
        self.history_group = self.create_group(self.scroll_main, "Historial de Exportaciones Recientes")
        self._load_export_history()

        # --- SEGURIDAD & ACCESO ---
        self.security_group = self.create_group(self.scroll_main, "Seguridad y Acceso")
        
        # Cambio de Usuario
        ctk.CTkLabel(self.security_group, text="Nuevo Nombre de Usuario", font=Typography.bold()).pack(anchor="w", padx=20, pady=(15, 5))
        self.entry_new_user = ctk.CTkEntry(self.security_group, placeholder_text="Nombre de usuario...", width=300)
        self.entry_new_user.pack(anchor="w", padx=20, pady=(0, 10))
        
        self.btn_change_user = ctk.CTkButton(
            self.security_group, 
            text="Actualizar Usuario", 
            command=self._update_username,
            fg_color=Colors.PRIMARY,
            height=32,
            corner_radius=8
        )
        self.btn_change_user.pack(anchor="w", padx=20, pady=(0, 20))

        # Cambio de Contraseña
        ctk.CTkLabel(self.security_group, text="Cambiar Contraseña", font=Typography.bold()).pack(anchor="w", padx=20, pady=(10, 5))
        self.entry_current_pass = ctk.CTkEntry(self.security_group, placeholder_text="Contraseña actual...", width=300, show="*")
        self.entry_current_pass.pack(anchor="w", padx=20, pady=(0, 10))
        
        self.entry_new_pass = ctk.CTkEntry(self.security_group, placeholder_text="Nueva contraseña...", width=300, show="*")
        self.entry_new_pass.pack(anchor="w", padx=20, pady=(0, 10))
        
        self.btn_change_pass = ctk.CTkButton(
            self.security_group, 
            text="Actualizar Contraseña", 
            command=self._update_password,
            fg_color=Colors.PRIMARY,
            height=32,
            corner_radius=8
        )
        self.btn_change_pass.pack(anchor="w", padx=20, pady=(0, 20))

        # --- LICENCIA ---
        self.lic_group = self.create_group(self.scroll_main, "Licencia de Uso")
        self._render_license_info()

        # --- INFORMACIÓN ---
        self.info_group = self.create_group(self.scroll_main, "Sobre LEX VIRIDIS")

        info_text = (
            f"Versión: {config.APP_VERSION}\n"
            "Desarrollado para: Gestión Técnica Institucional\n"
            "Soporte: Fer Ardón | Transformación Digital"
        )
        ctk.CTkLabel(self.info_group, text=info_text, justify="left", font=Typography.body()).pack(anchor="w", padx=20, pady=15)

    def _load_api_key(self):
        """Lee la API key de Gemini guardada en disco."""
        import json
        try:
            key_file = config.API_KEY_FILE
            if key_file.exists():
                with open(key_file, 'r') as f:
                    return json.load(f).get("gemini_api_key", "")
        except Exception:
            pass
        return ""

    def _load_groq_api_key(self):
        """Lee la API key de Groq guardada en disco."""
        import json
        try:
            if config.API_KEY_FILE.exists():
                with open(config.API_KEY_FILE, 'r') as f:
                    return json.load(f).get("groq_api_key", "")
        except Exception:
            pass
        return ""

    def _load_saved_model(self):
        """Lee el modelo Gemini guardado."""
        import json
        try:
            if config.API_KEY_FILE.exists():
                with open(config.API_KEY_FILE, 'r') as f:
                    return json.load(f).get("gemini_model", "gemini-2.0-flash")
        except Exception:
            pass
        return "gemini-2.0-flash"

    def _load_saved_groq_model(self):
        """Lee el modelo Groq guardado."""
        import json
        try:
            if config.API_KEY_FILE.exists():
                with open(config.API_KEY_FILE, 'r') as f:
                    return json.load(f).get("groq_model", "llama-3.3-70b-versatile")
        except Exception:
            pass
        return "llama-3.3-70b-versatile"

    def _load_saved_provider(self):
        """Lee el proveedor guardado. Retorna 'Groq (Recomendado)' o 'Gemini (Google)'."""
        import json
        try:
            if config.API_KEY_FILE.exists():
                with open(config.API_KEY_FILE, 'r') as f:
                    provider = json.load(f).get("provider", "groq")
                    return "Gemini (Google)" if provider == "gemini" else "Groq (Recomendado)"
        except Exception:
            pass
        return "Groq (Recomendado)"

    def _on_provider_change(self, value):
        """Muestra/oculta el panel según el proveedor seleccionado."""
        if value == "Gemini (Google)":
            self.frame_groq.pack_forget()
            self.frame_gemini.pack(fill="x", padx=20, pady=(0, 4), before=self.api_btn_row)
        else:
            self.frame_gemini.pack_forget()
            self.frame_groq.pack(fill="x", padx=20, pady=(0, 4), before=self.api_btn_row)

    def _save_api_key(self):
        """Persiste la API key + modelo + proveedor y recarga el cliente de IA."""
        import json
        provider_label = self._provider_var.get()
        provider = "gemini" if provider_label == "Gemini (Google)" else "groq"

        if provider == "groq":
            key = self.entry_groq_api.get().strip()
            model = self.groq_model_menu.get()
        else:
            key = self.entry_api.get().strip()
            model = self.model_menu.get()

        if not key:
            self.show_toast("Introduce una clave válida", "error")
            return
        try:
            # Leer claves existentes para no borrar la del otro proveedor
            existing = {}
            if config.API_KEY_FILE.exists():
                with open(config.API_KEY_FILE, 'r') as f:
                    existing = json.load(f)

            existing["provider"] = provider
            if provider == "groq":
                existing["groq_api_key"] = key
                existing["groq_model"] = model
            else:
                existing["gemini_api_key"] = key
                existing["gemini_model"] = model

            with open(config.API_KEY_FILE, 'w') as f:
                json.dump(existing, f)

            # Recargar el cliente de IA
            from ..ai_assistant import GeminiClient, GroqClient, LegalAIAssistant
            if provider == "groq":
                self.app.gemini = GroqClient(api_key=key, model_name=model)
            else:
                self.app.gemini = GeminiClient(api_key=key, model_name=model)

            # Si el motor de búsqueda no cargó al inicio (ej: error de rutas), intentar re-inicializarlo
            if self.app.engine is None:
                try:
                    from ..search_engine import SearchEngine
                    self.app.engine = SearchEngine()
                except Exception as e:
                    print(f"Error re-inicializando motor: {e}")

            self.app.ai_assistant = LegalAIAssistant(self.app.engine, self.app.gemini)

            # Invalidar caché de api key en main para reflejar el nuevo valor
            if hasattr(self.app, 'reload_api_key'):
                self.app.reload_api_key()

            self.lbl_api_status.configure(text=f"✓ Activo ({model})", text_color=Colors.SUCCESS)
            self.show_toast(f"API Key guardada · {provider_label} · {model}", "success")
        except Exception as e:
            self.show_toast(f"Error guardando clave: {e}", "error")

    def _load_export_history(self):
        """Carga y muestra el historial de exportaciones desde el gestor."""
        from ..utils.export_manager import ExportLogManager
        history = ExportLogManager.get_history()
        
        if not history:
            ctk.CTkLabel(self.history_group, text="No hay exportaciones recientes.", text_color=Colors.TEXT_SECONDARY).pack(pady=10)
            return

        for item in history:
            row = ctk.CTkFrame(self.history_group, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=2)
            
            fmt_color = Colors.ACCENT_BLUE if item['format'] == "PDF" else Colors.PRIMARY
            
            lbl_type = ctk.CTkLabel(row, text=f" {item['format']} ", fg_color=fmt_color, text_color="white", corner_radius=4, font=Typography.get_font(10, "bold"))
            lbl_type.pack(side="left", padx=(0, 10))
            
            lbl_name = ctk.CTkLabel(row, text=item['filename'], font=Typography.body(), anchor="w")
            lbl_name.pack(side="left")
            
            lbl_date = ctk.CTkLabel(row, text=item['date'], font=Typography.caption(), text_color=Colors.TEXT_SECONDARY)
            lbl_date.pack(side="right")

    def _update_username(self):
        new_name = self.entry_new_user.get().strip()
        if not new_name:
            self.show_toast("Nombre inválido", "error")
            return
        
        # Nota: En una app real pediríamos pass para confirmar, 
        # pero aquí implementaremos el flujo directo solicitado por Fer
        try:
            conn = self.app.engine.db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE usuarios SET username = ?", (new_name,))
            conn.commit()
            conn.close()
            self.show_toast(f"Usuario actualizado a: {new_name}", "success")
        except Exception as e:
            self.show_toast(f"Error: {e}", "error")

    def _update_password(self):
        curr_pass = self.entry_current_pass.get()
        new_pass = self.entry_new_pass.get()
        
        if not curr_pass or not new_pass:
            self.show_toast("Complete los campos", "warning")
            return
            
        if self.app.auth.change_password(1, curr_pass, new_pass): # Asumimos ID 1 para Fer
            self.show_toast("Contraseña actualizada", "success")
            self.entry_current_pass.delete(0, 'end')
            self.entry_new_pass.delete(0, 'end')
        else:
            self.show_toast("Contraseña actual incorrecta", "error")

    def _render_license_info(self):
        """Muestra el estado actual de la licencia registrada."""
        info = getattr(self.app, "license_info", None)

        if not info:
            ctk.CTkLabel(
                self.lic_group,
                text="⚠  Sin licencia activa.",
                font=Typography.bold(), text_color="orange"
            ).pack(anchor="w", padx=20, pady=(15, 5))
            ctk.CTkButton(
                self.lic_group, text="Activar Licencia",
                fg_color=Colors.PRIMARY, height=32, corner_radius=8,
                command=lambda: self.app.select_view("license")
            ).pack(anchor="w", padx=20, pady=(0, 15))
            return

        # Datos de la licencia
        client   = info.get("client", "—")
        lic_type = info.get("type", "—")
        expires  = info.get("expires", "Sin vencimiento")
        status   = info.get("status", "Activa")

        # Badge de estado
        badge_row = ctk.CTkFrame(self.lic_group, fg_color="transparent")
        badge_row.pack(anchor="w", padx=20, pady=(15, 8))

        badge = ctk.CTkFrame(badge_row, fg_color=Colors.SUCCESS, corner_radius=6)
        badge.pack(side="left")
        ctk.CTkLabel(badge, text=f"  ✓ {status}  ",
                     font=Typography.get_font(11, "bold"), text_color="white").pack(padx=6, pady=3)

        # Detalles
        details = (
            f"Cliente:      {client}\n"
            f"Tipo:         {lic_type}\n"
            f"Vencimiento:  {expires}"
        )
        ctk.CTkLabel(
            self.lic_group, text=details,
            font=Typography.body(), justify="left",
            text_color=Colors.TEXT_SECONDARY
        ).pack(anchor="w", padx=20, pady=(0, 10))

        ctk.CTkButton(
            self.lic_group, text="Renovar / Cambiar Licencia",
            fg_color="transparent", border_width=1, border_color=Colors.BORDER,
            text_color=Colors.TEXT_SECONDARY, height=30, corner_radius=8,
            command=lambda: self.app.select_view("license")
        ).pack(anchor="w", padx=20, pady=(0, 15))

    @staticmethod
    def _get_model_hint(model: str) -> str:
        """Retorna una descripción breve del modelo seleccionado."""
        hints = {
            "gemini-2.0-flash": (
                "⭐ RECOMENDADO  —  El más rápido y actualizado. "
                "Cuota diaria generosa (~1,500 consultas). "
                "Ideal para uso diario en LEX VIRIDIS."
            ),
            "gemini-1.5-flash": (
                "Equilibrado entre velocidad y precisión. "
                "Buena opción si gemini-2.0-flash no está disponible en tu región."
            ),
            "gemini-1.5-flash-8b": (
                "Ultra ligero y rápido. Respuestas casi instantáneas. "
                "Recomendado si tienes conexión lenta o quieres ahorrar cuota."
            ),
            "gemini-1.5-pro": (
                "El más preciso para análisis complejos y respuestas largas. "
                "Cuota diaria menor (~50 consultas gratuitas). "
                "Úsalo solo para consultas legales muy detalladas."
            ),
        }
        return hints.get(model, "Selecciona un modelo para ver su descripción.")

    def _update_model_hint(self, selected_model: str):
        """Actualiza la etiqueta de descripción al cambiar el modelo."""
        if hasattr(self, "lbl_model_hint"):
            self.lbl_model_hint.configure(text=self._get_model_hint(selected_model))

    def _open_url(self, url: str):
        """Abre un enlace en el navegador predeterminado del sistema."""
        import webbrowser
        try:
            webbrowser.open(url)
        except Exception as e:
            self.show_toast(f"No se pudo abrir el navegador: {e}", "error")

    def create_group(self, master, title):
        group = ctk.CTkFrame(master, corner_radius=12, border_width=1, border_color=Colors.BORDER)
        group.pack(fill="x", pady=10, padx=10)
        
        header = ctk.CTkLabel(group, text=title, font=Typography.bold(), text_color=Colors.ACCENT_BLUE)
        header.pack(anchor="w", padx=20, pady=(15, 5))
        
        line = ctk.CTkFrame(group, height=1, fg_color=Colors.BORDER)
        line.pack(fill="x", padx=20, pady=0)
        
        return group
