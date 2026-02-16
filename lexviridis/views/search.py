import flet as ft

from ..design_system import ResultCard, Spacing, Theme, Typography, UIComponents
from ..search_engine import SearchEngine, SearchStatus


class SearchView(ft.Container):
    """
    Search View Component.
    Handles search input, results list, and detailed view of articles.
    """
    def __init__(self, search_engine: SearchEngine, on_open_pdf: callable, on_view_article: callable):
        super().__init__(expand=True)
        self.search_engine = search_engine
        self.on_open_pdf = on_open_pdf
        self.on_view_article = on_view_article
        self.current_query = ""
        self.search_results = []
        self._build_ui()

    def _build_ui(self):
        # Search Input
        self.search_input = UIComponents.search_field(
            "Escribe una palabra clave (ej. forestal, licencia, agua)...",
            on_submit=lambda e: self.perform_search(e.control.value),
            on_change=self._on_search_change
        )
        self.suggestions_row = ft.Row(visible=False, wrap=True, spacing=Spacing.SM)

        # Hero
        hero = UIComponents.hero_header(
            "hero_search.png",
            "Buscador Inteligente",
            "Encuentra normas, acuerdos y decretos en segundos"
        )

        # Main Search Section
        search_section = ft.Container(
            content=ft.Column([
                ft.Container(height=Spacing.LG),
                ft.Container(
                    content=ft.Column([self.search_input, self.suggestions_row]),
                    width=600,
                ),
                ft.Container(height=Spacing.LG),
                ft.Row([
                    UIComponents.chip("Ley Forestal", on_click=lambda e: self.perform_search("Ley Forestal")),
                    UIComponents.chip("Licencia Ambiental", on_click=lambda e: self.perform_search("Licencia Ambiental")),
                    UIComponents.chip("Áreas Protegidas", on_click=lambda e: self.perform_search("áreas protegidas")),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=Spacing.SM),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.Alignment(0, 0),
        )

        self.results_list = ft.ListView(expand=True, spacing=Spacing.MD, padding=ft.padding.only(top=Spacing.MD))

        # Layout
        self.content = ft.Column([
            hero,
            search_section,
            self.results_list
        ], expand=True, scroll=ft.ScrollMode.ALWAYS)

    def _on_search_change(self, e):
        suggestions = self.search_engine.get_search_suggestions(e.data)
        if suggestions:
            self.suggestions_row.controls = [
                UIComponents.chip(s, on_click=lambda _, q=s: self.perform_search(q))
                for s in suggestions
            ]
            self.suggestions_row.visible = True
        else:
            self.suggestions_row.visible = False
        self.update()

    def perform_search(self, query: str):
        self.current_query = query
        self.content = UIComponents.loading_state("Buscando...")
        self.update()

        try:
            result = self.search_engine.search_safe(query)
            if result.status == SearchStatus.SUCCESS:
                self.search_results = result.results
                self._show_results_view()
            elif result.status == SearchStatus.NO_RESULTS:
                self._show_empty_results(query)
            else:
                self._show_error(result.message)
        except Exception as e:
            self._show_error(f"Error inesperado: {str(e)}")

        self.update()

    def _show_results_view(self):
        header = ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text("Resultados para:", size=Typography.CAPTION, color=Theme.TEXT_SECONDARY),
                    ft.Text(f'"{self.current_query}"', size=Typography.TITLE, weight=Typography.BOLD, color=Theme.PRIMARY),
                ], spacing=Spacing.XXS),
                ft.Container(expand=True),
                ft.Text(f"{len(self.search_results)} resultados", size=Typography.BODY, color=Theme.TEXT_SECONDARY),
                ft.Container(width=Spacing.SM),
                UIComponents.secondary_button("Nueva búsqueda", icon="refresh", on_click=lambda e: self._reset_search()),
            ]),
            padding=ft.padding.only(bottom=Spacing.LG),
        )

        self.results_list.controls.clear()
        for res in self.search_results:
            # Handle different result types with different callbacks
            if res.get('is_norma'):
                def on_click(e, r=res):
                    return self.on_open_pdf(r)
            else:
                def on_click(e, r=res):
                    return self.on_view_article(r, self.current_query)

            self.results_list.controls.append(ResultCard(res, on_click=on_click))

        self.content = ft.Column([header, ft.Container(self.results_list, expand=True)], expand=True)
        self.update()

    def _show_empty_results(self, query):
         self.content = ft.Container(
            content=ft.Column([
                ft.Icon("search_off", size=80, color=Theme.TEXT_DISABLED),
                ft.Container(height=Spacing.MD),
                ft.Text("Sin resultados", size=Typography.TITLE, weight=Typography.SEMIBOLD),
                ft.Text(
                    f'No encontramos resultados para "{query}"',
                    color=Theme.TEXT_SECONDARY,
                ),
                ft.Container(height=Spacing.LG),
                ft.Text("Sugerencias:", weight=Typography.MEDIUM),
                ft.Text("• Verifica la ortografía", color=Theme.TEXT_SECONDARY),
                ft.Text("• Usa términos más generales", color=Theme.TEXT_SECONDARY),
                ft.Text("• Prueba sinónimos", color=Theme.TEXT_SECONDARY),
                ft.Container(height=Spacing.LG),
                UIComponents.secondary_button("Nueva búsqueda", on_click=lambda e: self._reset_search()),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.Alignment(0, 0),
            expand=True,
        )

    def _show_error(self, message):
         self.content = UIComponents.error_state(
            "Error en la búsqueda",
            message,
            on_retry=lambda e: self._reset_search(),
        )

    def _reset_search(self):
        self._build_ui()
        self.update()
