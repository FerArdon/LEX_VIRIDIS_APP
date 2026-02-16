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
        # Fetch stats
        stats = self.stats_repo.get_dashboard_stats()

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
        pie_sections = []
        colors_list = [Colors.GREEN_700, Colors.TEAL_700, Colors.AMBER_700, Colors.BLUE_700, Colors.GREY_500]

        dist = stats.get('distribucion_tipo', {})
        for i, (tipo, count) in enumerate(dist.items()):
            if i >= 5: break
            pie_sections.append(ft.PieChartSection(
                value=count,
                title=f"{tipo[:10]}",
                title_style=ft.TextStyle(size=10, color=Colors.WHITE, weight="bold"),
                color=colors_list[i % len(colors_list)],
                radius=100
            ))

        return UIComponents.card(
            ft.Column([
                ft.Text("Distribución por Tipo", weight="bold"),
                ft.Container(
                    ft.PieChart(sections=pie_sections, sections_space=2, center_space_radius=80),
                    height=500, alignment=ft.Alignment(0, 0)
                )
            ])
        )

    def _build_top_searches_chart(self, stats):
        bar_groups = []
        top_searches = stats.get('top_searches', [])

        for i, (_query, freq) in enumerate(top_searches[:6]):
            bar_groups.append(ft.BarChartGroup(
                x=i,
                bar_rods=[ft.BarChartRod(from_y=0, to_y=freq, color=Theme.PRIMARY, width=15)]
            ))

        return UIComponents.card(
            ft.Column([
                ft.Text("Top Búsquedas", weight="bold"),
                ft.Container(
                    ft.BarChart(
                        bar_groups=bar_groups,
                        bottom_axis=ft.ChartAxis(
                            labels=[ft.ChartAxisLabel(value=i, label=ft.Text(top_searches[i][0][:15], size=10, rotate=45)) for i in range(len(bar_groups))],
                        ),
                    ),
                    height=500, padding=20
                )
            ])
        )

    def _build_timeline_chart(self, stats):
        data_points = []
        timeline = stats.get('timeline_busquedas', [])

        for i, (_fecha, count) in enumerate(timeline):
            data_points.append(ft.LineChartDataPoint(i, count))

        return UIComponents.card(
            ft.Column([
                ft.Text("Actividad de Búsqueda (Últimos 7 días)", weight="bold"),
                ft.Container(
                    ft.LineChart(
                        data_series=[ft.LineChartData(data_points=data_points, color=Theme.SECONDARY, curved=True, stroke_width=4)],
                        bottom_axis=ft.ChartAxis(
                            labels=[ft.ChartAxisLabel(value=i, label=ft.Text(timeline[i][0][5:] if timeline else "", size=10)) for i in range(len(data_points))]
                        )
                    ),
                    height=450, padding=20
                )
            ])
        )
