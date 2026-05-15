"""
LEX VIRIDIS - AI Assistant View (CustomTkinter)
Chat asíncrono con Gemini, exportación multiformato y sugerencias de seguimiento.
"""

import customtkinter as ctk
from .base_view import BaseView
from ..design_system_ctk import Colors, Typography


class AIAssistantView(BaseView):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, app, **kwargs)
        self.last_response = ""
        self.last_query = ""
        self.setup_ui()

    def setup_ui(self):
        # 0. Banner de Sección
        if "banner_ai" in self.app.icons:
            ctk.CTkLabel(self, image=self.app.icons["banner_ai"], text="").pack(fill="x", pady=(0, 10))

        # 1. Header + Exportación
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=(10, 10))

        ctk.CTkLabel(
            self.header_frame,
            text="Asistente Legal IA | Consulta RAG",
            font=Typography.get_font(22, "bold"),
            text_color=Colors.PRIMARY, anchor="w"
        ).pack(side="left")

        export_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        export_frame.pack(side="right")

        self.format_menu = ctk.CTkOptionMenu(
            export_frame, values=["PDF", "EXCEL", "TXT"],
            width=90, height=32,
            font=Typography.caption(), fg_color=Colors.PRIMARY
        )
        self.format_menu.pack(side="left", padx=5)

        self.btn_export = ctk.CTkButton(
            export_frame, text=" Exportar",
            image=self.app.icons.get("settings"),
            width=110, height=32,
            fg_color="transparent", border_width=2,
            border_color=Colors.PRIMARY, text_color=Colors.PRIMARY,
            command=self.export_response,
            state="disabled"
        )
        self.btn_export.pack(side="left", padx=5)

        # 2. Historial de chat
        self.chat_display = ctk.CTkTextbox(
            self,
            fg_color=(Colors.SURFACE_LIGHT, Colors.SURFACE_DARK),
            border_color=Colors.BORDER, border_width=2,
            font=Typography.body(),
            corner_radius=10, padx=15, pady=15,
            wrap="word", state="disabled"
        )
        self.chat_display.pack(fill="both", expand=True, pady=(0, 8))
        self.add_context_menu(self.chat_display)

        # 3. Sugerencias de seguimiento (oculto hasta que haya respuesta)
        self.suggestions_frame = ctk.CTkFrame(self, fg_color="transparent")
        # Se muestra dinámicamente después de cada respuesta

        # 4. Input de consulta
        self.input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.input_frame.pack(fill="x", pady=(0, 10))

        self.entry_query = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Haz una pregunta legal sobre el compendio...",
            height=50, corner_radius=10,
            font=Typography.body(),
            border_width=2, border_color=Colors.BORDER
        )
        self.entry_query.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry_query.bind("<Return>", lambda e: self.send_query())

        self.btn_send = ctk.CTkButton(
            self.input_frame, text="  Consultar",
            image=self.app.icons.get("ai"),
            compound="left",
            command=self.send_query,
            fg_color=Colors.ACCENT_BLUE,
            hover_color=Colors.PRIMARY,
            height=50, width=145, corner_radius=10,
            font=Typography.bold()
        )
        self.btn_send.pack(side="right")

    # ── CHAT ───────────────────────────────────────────────────────────────────

    def append_chat(self, sender, text):
        self.chat_display.configure(state="normal")
        if sender == "LEX":
            prefix = "🤖 LEX VIRIDIS"
        else:
            prefix = "👤 TÚ"
        self.chat_display.insert("end", f"\n{prefix}:\n")
        self.chat_display.insert("end", f"{text}\n")
        self.chat_display.see("end")
        self.chat_display.configure(state="disabled")

    def send_query(self):
        query = self.entry_query.get().strip()
        if not query:
            return
        self.last_query = query
        self.append_chat("USER", query)
        self.entry_query.delete(0, "end")
        self.btn_send.configure(state="disabled", text="Procesando...")

        # Ocultar sugerencias anteriores
        self.suggestions_frame.pack_forget()

        self.run_in_thread(self._process_ai_logic, (query,))

    def _process_ai_logic(self, query):
        try:
            if not self.app.ai_assistant:
                self.update_ui(self.append_chat, "LEX", "Error: El motor de IA no está inicializado.")
                return
            response = self.app.ai_assistant.answer_question(query)
            answer = response.get("answer", "No se encontró solución.")
            suggestions = response.get("suggested_questions", [])

            self.last_response = answer
            self.update_ui(self.append_chat, "LEX", answer)
            self.update_ui(lambda: self.btn_export.configure(state="normal"))
            if suggestions:
                self.update_ui(self._show_suggestions, suggestions)
        except Exception as e:
            self.update_ui(self.append_chat, "LEX", f"Error crítico: {str(e)}")
        finally:
            self.update_ui(lambda: self.btn_send.configure(state="normal", text="  Consultar"))

    # ── SUGERENCIAS DE SEGUIMIENTO ─────────────────────────────────────────────

    def _show_suggestions(self, suggestions):
        for w in self.suggestions_frame.winfo_children():
            w.destroy()

        ctk.CTkLabel(
            self.suggestions_frame,
            text="Preguntas sugeridas:",
            font=Typography.caption(), text_color=Colors.TEXT_SECONDARY, anchor="w"
        ).pack(anchor="w", padx=5, pady=(0, 4))

        chips_row = ctk.CTkFrame(self.suggestions_frame, fg_color="transparent")
        chips_row.pack(fill="x")

        for sug in suggestions[:4]:
            def make_handler(q):
                def _handler():
                    self.entry_query.delete(0, "end")
                    self.entry_query.insert(0, q)
                    self.send_query()
                return _handler

            ctk.CTkButton(
                chips_row, text=sug[:60],
                height=28, corner_radius=14,
                fg_color="transparent", border_width=1,
                border_color=Colors.BORDER, text_color=Colors.TEXT_SECONDARY,
                hover_color=Colors.BORDER,
                font=Typography.caption(),
                command=make_handler(sug)
            ).pack(side="left", padx=4, pady=2)

        # Mostrar el frame antes del input
        self.suggestions_frame.pack(fill="x", pady=(0, 6), before=self.input_frame)

    # ── EXPORTACIÓN ────────────────────────────────────────────────────────────

    def export_response(self):
        if not self.last_response:
            self.show_toast("No hay respuesta para exportar", "warning")
            return
        from ..utils.export_manager import ExportManager
        query = self.last_query or "Consulta Asistente Legal"
        fmt = self.format_menu.get()

        ExportManager.export(
            self.last_response, format_type=fmt,
            query=query, origin="Asistente IA",
            callback=lambda ok, info: (
                self.update_ui(self.show_export_success_dialog, info) if ok
                else self.update_ui(self.show_toast, f"Fallo al exportar: {info}", "error")
            )
        )
