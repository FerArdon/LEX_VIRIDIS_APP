import logging
import flet as ft

from ..design_system import Colors, Radius, Spacing, Theme, UIComponents
from ..services.stats_repository import StatsRepository


class DashboardView(ft.Container):
    """
    Dashboard View Component.
    Displays system statistics and charts.
    """
    def __init__(self, stats_repo: StatsRepository):
        super().__init__(expand=True)
        self.stats_repo = stats_repo
        self._build_ui()

    def _build_ui(self):
        # Fetch stats con manejo de errores
        try:
            stats = self.stats_repo.get_dashboard_stats()
        except Exception as e:
            logging.error(f"Error obteniendo dashboard stats: {e}")
            # Stats por defecto si falla
            stats = {
                'total_normas': 0,
                'total_articulos': 0,
                'total_favoritos': 0,
                'total_busquedas': 0,
                'distribucion_tipo': {},
                'top_searches': [],
                'timeline_busquedas': []
            }

        # Hero Header
        hero = UIComponents.hero_header(
            "hero_ai.png",
            "Panel de Control",
            "Monitoreo y estadísticas de la legislación ambiental"
        )

        # Stats Cards
        row_stats = self._build_stat_cards(stats)

        # Charts
        chart_dist = self._build_distribution_chart(stats)
        chart_top = self._build_top_searches_chart(stats)
        chart_timeline = self._build_timeline_chart(stats)

        # Layout
        self.content = ft.Column(
            controls=[
                hero,
                UIComponents.heading("Dashboard Principal", level=1, color=Theme.PRIMARY),
                ft.Divider(height=1, thickness=1),
                row_stats,
                ft.Container(height=Spacing.MD),
                chart_dist,
                ft.Container(height=Spacing.MD),
                chart_top,
                ft.Container(height=Spacing.MD),
                chart_timeline
            ],
            scroll=ft.ScrollMode.ALWAYS,
            expand=True
        )

    def _build_stat_cards(self, stats):
        def stat_card(icon, label, value, color):
            formatted_value = str(value)
            if isinstance(value, (int, float)):
                formatted_value = f"{value:,}" if isinstance(value, int) else f"{value:,.1f}"

            return ft.Container(
                content=ft.Row([
                    ft.Icon(icon, color=color, size=32),
                    ft.Column([
                        ft.Text(label, size=12, color=Theme.TEXT_SECONDARY),
                        ft.Text(formatted_value, size=24, weight="bold", color=color),
                    ], spacing=0)
                ], alignment=ft.MainAxisAlignment.CENTER),
                bgcolor=Theme.SURFACE,
                padding=Spacing.MD,
                border_radius=Radius.MD,
                expand=True,
                shadow=ft.BoxShadow(blur_radius=4, color=Colors.with_opacity(0.05, Colors.BLACK)),
            )

        return ft.Row([
            stat_card("library_books", "Normas", stats.get('total_normas', 0), Theme.PRIMARY),
            stat_card("article", "Artículos", stats.get('total_articulos', 0), Theme.SECONDARY),
            stat_card("star", "Favoritos", stats.get('total_favoritos', 0), Theme.ACCENT),
            stat_card("search", "Búsquedas", stats.get('total_busquedas', 0), Theme.INFO),
        ], spacing=Spacing.MD)

    def _build_distribution_chart(self, stats):
        # TODO: PieChart y PieChartSection han cambiado en Flet reciente.
        # Deshabilitado temporalmente para permitir arranque. 
        # Implementar nuevo ft.PieChart cuando se estabilice la API.
        
        return ft.Container(
             content=ft.Text("Gráfico de Estadísticas (Próximamente)", color=Theme.TEXT_SECONDARY),
             alignment=ft.Alignment(0,0),
             height=200
        )

    def _build_top_searches_chart(self, stats):
        # TODO: BarChart ha cambiado en Flet reciente.
        return ft.Container(
             content=ft.Text("Gráfico de Búsquedas (Próximamente)", color=Theme.TEXT_SECONDARY),
             alignment=ft.Alignment(0,0),
             height=200
        )

    def _build_timeline_chart(self, stats):
        # TODO: LineChart ha cambiado en Flet reciente.
        return ft.Container(
             content=ft.Text("Línea de Tiempo (Próximamente)", color=Theme.TEXT_SECONDARY),
             alignment=ft.Alignment(0,0),
             height=200
        )
