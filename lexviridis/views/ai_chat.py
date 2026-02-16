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
        api_input = ft.TextField(
            label="API Key de Gemini",
            password=True,
            can_reveal_password=True,
            width=500,
            hint_text="AIza..."
        )

        def save_key(e):
            val = api_input.value
            if val:
                self.gemini.set_api_key(val)
                self._build_ui()
                self.update()

        def open_gemini_link(e):
            import webbrowser
            webbrowser.open("https://aistudio.google.com/app/apikey")

        self.content = ft.Container(
             content=ft.Column([
                ft.Icon("key_outlined", size=64, color=Theme.SECONDARY),
                ft.Container(height=Spacing.SM),
                UIComponents.heading("Configurar Asistente IA", level=2),
                ft.Container(height=Spacing.SM),
                UIComponents.body_text(
                    "Ingresa tu API Key de Google Gemini para habilitar el asistente de IA.",
                    secondary=True
                ),
                ft.Container(height=Spacing.MD),

                # Instrucciones
                UIComponents.card(
                    ft.Column([
                        ft.Row([
                            ft.Icon("info_outline", size=20, color=Theme.INFO),
                            ft.Text("¿Cómo obtener tu API Key?", weight="bold", size=14)
                        ], spacing=8),
                        ft.Container(height=Spacing.SM),
                        ft.Text("1. Haz clic en el botón 'Obtener API Key' abajo", size=13),
                        ft.Text("2. Inicia sesión con tu cuenta de Google", size=13),
                        ft.Text("3. Haz clic en 'Create API Key' o 'Get API Key'", size=13),
                        ft.Text("4. Copia la clave generada y pégala aquí", size=13),
                        ft.Container(height=Spacing.SM),
                        ft.TextButton(
                            "🔗 Obtener API Key de Google Gemini",
                            on_click=open_gemini_link,
                            style=ft.ButtonStyle(
                                color=Theme.PRIMARY,
                            )
                        ),
                    ], spacing=4),
                    padding=Spacing.MD
                ),

                ft.Container(height=Spacing.LG),
                api_input,
                ft.Container(height=Spacing.MD),
                UIComponents.primary_button("Guardar", icon="save", on_click=save_key),
                ft.Container(height=Spacing.SM),
                ft.Text(
                    "⚠️ La API Key se guardará localmente de forma segura",
                    size=12,
                    color=Theme.TEXT_SECONDARY,
                    italic=True
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
            alignment=ft.Alignment(0, 0),
            expand=True,
            padding=Spacing.XL
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
