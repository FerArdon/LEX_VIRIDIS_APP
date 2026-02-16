import re

import flet as ft

from ..design_system import Radius, Spacing, Theme, Typography, UIComponents


class ArticleDetailView(ft.Container):
    """
    Displays the content of an article with highlighting and navigation.
    """
    def __init__(self, article: dict, query: str = "", on_close: callable = None, on_open_pdf: callable = None):
        super().__init__(expand=True)
        self.article = article
        self.query = query
        self.on_close = on_close
        self.on_open_pdf = on_open_pdf
        self._build_ui()

    def _build_ui(self):
         # Encontrar todas las ocurrencias
        text = self.article.get('contenido', '')
        matches = []
        if self.query:
            pattern = re.compile(re.escape(self.query), re.IGNORECASE)
            matches = [m.start() for m in pattern.finditer(text)]

        self.match_idx = 0
        self.matches = matches

        # Header
        self.counter_text = ft.Text(size=Typography.CAPTION, color=Theme.TEXT_SECONDARY)

        # Check if matched text exists
        match_controls = []
        if matches:
            match_controls = [
                ft.IconButton("chevron_left", on_click=lambda _: self._nav_match(-1)),
                self.counter_text,
                ft.IconButton("chevron_right", on_click=lambda _: self._nav_match(1)),
            ]

        detail_header = ft.Row([
            UIComponents.icon_badge("description", Theme.PRIMARY),
            ft.Column([
                ft.Text(f"Artículo {self.article.get('numero_articulo', '')}", weight="bold"),
                ft.Text(self.article.get('norma_titulo', ''), size=12, color=Theme.TEXT_SECONDARY, max_lines=1, overflow="ellipsis"),
            ], expand=True),
            ft.VerticalDivider(),
            ft.Row(match_controls, spacing=0),
            ft.VerticalDivider(),
            UIComponents.primary_button("Abrir PDF", icon="picture_as_pdf", on_click=lambda _: self.on_open_pdf(self.article) if self.on_open_pdf else None),
            ft.IconButton("close", on_click=lambda _: self.on_close() if self.on_close else None),
        ])

        # Content
        # Sanitization for Markdown (optional, but good if content has issues)
        safe_text = text if text else "Sin contenido."

        self.markdown_view = ft.Markdown(
            safe_text,
            selectable=True,
            extension_set=ft.MarkdownExtensionSet.GITHUB_FLAVORED,
        )

        self.content = ft.Column([
            detail_header,
            UIComponents.divider(),
            ft.Container(
                content=ft.Column([self.markdown_view], scroll=ft.ScrollMode.AUTO),
                expand=True,
                padding=Spacing.MD,
                bgcolor=Theme.SURFACE,
                border_radius=Radius.MD,
                border=ft.border.all(1, Theme.BORDER)
            ),
        ], expand=True)

        self._highlight_text(0)

    def _nav_match(self, delta):
        if not self.matches: return
        self.match_idx = (self.match_idx + delta) % len(self.matches)
        self._highlight_text(self.match_idx)
        self.update()

    def _highlight_text(self, idx):
        if not self.matches:
            self.counter_text.value = ""
            return

        # Highlight Logic
        text = self.article.get('contenido', '')
        if self.query:
             pattern = re.compile(re.escape(self.query), re.IGNORECASE)
             # Replace all occurrences with bold markdown
             processed_text = pattern.sub(lambda m: f"**{m.group(0)}**", text)
             self.markdown_view.value = processed_text

        self.counter_text.value = f"{idx + 1} / {len(self.matches)}"
        # Note: Auto-scroll to match is complex in Flet without specific control support
        # We rely on visual bolding for now.
