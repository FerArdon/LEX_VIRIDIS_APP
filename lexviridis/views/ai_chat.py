import threading

import flet as ft

from ..ai_assistant import LegalAIAssistant
from ..design_system import Colors, Radius, Spacing, Theme, UIComponents
from ..ia_gemini import GeminiClient


class AIChatView(ft.Container):
    """
    AI Chat View Component.
    Handles chat interaction with Gemini (RAG).
    """
    def __init__(self, gemini_client: GeminiClient, ai_assistant: LegalAIAssistant, on_open_article: callable):
        super().__init__(expand=True)
        self.gemini = gemini_client
        self.ai_assistant = ai_assistant
        self.on_open_article = on_open_article
        self._build_ui()

    def _build_ui(self):
        # Hero
        hero = UIComponents.hero_header(
            "hero_ai.png",
            "Asistente IA Legal",
            "Consulta tus dudas sobre legislación ambiental con inteligencia artificial"
        )

        # Check API Key
        if not self.gemini or not self.gemini.api_key:
            self._render_api_key_prompt()
            return

        # Chat Area
        self.chat_messages = ft.ListView(expand=True, spacing=Spacing.MD, padding=Spacing.MD, auto_scroll=True)

        # Suggestions
        sugerencias = [
            "¿Cuál es la multa por tala ilegal?",
            "¿Qué documentos necesito para licencia ambiental?",
            "¿Cuándo aplica evaluación de impacto ambiental?",
            "¿Qué leyes protegen áreas protegidas?"
        ]
        chips_row = ft.Row([
            UIComponents.chip(s, on_click=lambda e, q=s: self.send_message(q))
            for s in sugerencias
        ], spacing=Spacing.SM, wrap=True)

        # Input Area
        self.chat_input = ft.TextField(
            hint_text="Haz una consulta legal sobre medio ambiente...",
            expand=True,
            border_radius=Radius.XL,
            bgcolor=Theme.SURFACE,
            content_padding=Spacing.MD,
            on_submit=lambda e: self.send_message(e.control.value),
        )

        # Layout
        self.content = ft.Column([
            hero,
            ft.Row([
                UIComponents.heading("Asistente Legal IA", level=1, color=Theme.PRIMARY),
                ft.Container(expand=True),
                UIComponents.chip("Modo RAG Activo", icon="reply_all", selected=True)
            ]),
            ft.Container(
                content=self.chat_messages,
                expand=True,
                bgcolor=Theme.SURFACE_VARIANT,
                border_radius=Radius.LG,
                border=ft.border.all(1, Theme.BORDER),
            ),
            ft.Container(height=Spacing.MD),
            chips_row,
            ft.Row([
                self.chat_input,
                UIComponents.primary_button(
                    "Preguntar",
                    icon="auto_awesome",
                    on_click=lambda e: self.send_message(self.chat_input.value),
                ),
            ]),
        ], expand=True)

    def _render_api_key_prompt(self):
        api_input = ft.TextField(label="API Key de Gemini", password=True, can_reveal_password=True)

        def save_key(e):
            val = api_input.value
            if val:
                self.gemini.set_api_key(val)
                self._build_ui()
                self.update()

        self.content = ft.Container(
             content=ft.Column([
                ft.Icon("key_outlined", size=64, color=Theme.SECONDARY),
                UIComponents.heading("Configurar Asistente IA", level=2),
                UIComponents.body_text("Ingresa tu API Key de Google Gemini para habilitar el asistente.", secondary=True),
                ft.Container(height=Spacing.LG),
                ft.Container(content=api_input, width=400),
                ft.Container(height=Spacing.MD),
                UIComponents.primary_button("Guardar", on_click=save_key),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.Alignment(0, 0),
            expand=True,
        )

    def send_message(self, text):
        if not text: return

        # Add user message
        self.chat_input.value = ""
        self._add_message(text, True)

        # Loading
        loading = ft.Row([UIComponents.progress_indicator(20), ft.Text("Consultando base legal...")])
        self.chat_messages.controls.append(loading)
        self.update()

        def process():
            try:
                result = self.ai_assistant.answer_question(text)
                self.chat_messages.controls.remove(loading)

                # Format Response
                response_card = ft.Column([
                    ft.Row([
                        ft.Icon("auto_awesome", size=16, color=Theme.PRIMARY),
                        ft.Text("Respuesta Inteligente", size=12, weight="bold", color=Theme.PRIMARY),
                    ]),
                    ft.Divider(height=1, color=Theme.BORDER),
                    ft.Markdown(result['answer'], selectable=True),
                    ft.Container(height=Spacing.SM),
                    ft.Divider(height=1, color=Theme.BORDER),
                    ft.Text("📚 Fuentes consultadas:", size=11, weight="bold", color=Theme.TEXT_SECONDARY),
                    ft.Row([
                        ft.TextButton(
                            f"• {res.get('file', '?')} (Art. {res.get('id', '?')})",
                            on_click=lambda e, r=res: self.on_open_article(r)
                        ) for res in result.get('sources', [])[:3]
                    ], wrap=True)
                ], spacing=Spacing.XS)

                self._add_ai_bubble(response_card)
            except Exception as e:
                import traceback; traceback.print_exc()
                if loading in self.chat_messages.controls:
                    self.chat_messages.controls.remove(loading)
                self._add_message(f"Error: {e}", False)
                self.update()

        threading.Thread(target=process, daemon=True).start()

    def _add_message(self, text, is_user):
        bubble = ft.Container(
            content=ft.Markdown(text, selectable=True) if not is_user else ft.Text(text),
            bgcolor=Colors.BLUE_50 if is_user else Theme.SURFACE,
            padding=Spacing.MD,
            border_radius=Radius.LG,
            width=500 if not is_user else None,
        )
        alignment = ft.MainAxisAlignment.END if is_user else ft.MainAxisAlignment.START
        self.chat_messages.controls.append(ft.Row([bubble], alignment=alignment))
        self.update()

    def _add_ai_bubble(self, content):
        bubble = ft.Container(
            content=content,
            bgcolor=Theme.SURFACE,
            padding=Spacing.MD,
            border_radius=Radius.LG,
            border=ft.border.all(1, Theme.BORDER),
            width=650,
        )
        self.chat_messages.controls.append(ft.Row([bubble], alignment=ft.MainAxisAlignment.START))
        self.update()
