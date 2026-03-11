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
                "total_normas": 0,
                "total_articulos": 0,
                "total_favoritos": 0,
                "total_busquedas": 0,
                "distribucion_tipo": {},
                "top_searches": [],
                "timeline_busquedas": [],
            }

        # Hero Header
        hero = UIComponents.hero_header(
            "hero_ai.png", "Panel de Control", "Monitoreo y estadísticas de la legislación ambiental"
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
                chart_timeline,
            ],
            scroll=ft.ScrollMode.ALWAYS,
            expand=True,
        )

    def _build_stat_cards(self, stats):
        def stat_card(icon, label, value, color):
            formatted_value = str(value)
            if isinstance(value, int | float):
                formatted_value = f"{value:,}" if isinstance(value, int) else f"{value:,.1f}"

            return ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(icon, color=color, size=32),
                        ft.Column(
                            [
                                ft.Text(label, size=12, color=Theme.TEXT_SECONDARY),
                                ft.Text(formatted_value, size=24, weight="bold", color=color),
                            ],
                            spacing=0,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                bgcolor=Theme.SURFACE,
                padding=Spacing.MD,
                border_radius=Radius.MD,
                expand=True,
                shadow=ft.BoxShadow(blur_radius=4, color=Colors.with_opacity(0.05, Colors.BLACK)),
            )

        return ft.Row(
            [
                stat_card("library_books", "Normas", stats.get("total_normas", 0), Theme.PRIMARY),
                stat_card("article", "Artículos", stats.get("total_articulos", 0), Theme.SECONDARY),
                stat_card("star", "Favoritos", stats.get("total_favoritos", 0), Theme.ACCENT),
                stat_card("search", "Búsquedas", stats.get("total_busquedas", 0), Theme.INFO),
            ],
            spacing=Spacing.MD,
        )

    def _build_distribution_chart(self, stats):
        """Gráfico de distribución por tipo de norma."""
        try:
            colors_list = [Colors.GREEN_700, Colors.TEAL_700, Colors.AMBER_700, Colors.BLUE_700, Colors.GREY_500]

            dist = stats.get("distribucion_tipo", {})

            # Si no hay datos, mostrar mensaje
            if not dist:
                return UIComponents.card(
                    ft.Column(
                        [
                            ft.Text("Distribución por Tipo", weight="bold", size=16),
                            ft.Divider(),
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Icon("pie_chart", size=64, color=Theme.TEXT_SECONDARY),
                                        ft.Text("No hay datos disponibles", color=Theme.TEXT_SECONDARY, size=14),
                                    ],
                                    horizontal_alignment="center",
                                    spacing=Spacing.SM,
                                ),
                                alignment=ft.alignment.Alignment(0, 0),
                                padding=Spacing.XL,
                                height=300,
                            ),
                        ]
                    )
                )

            # Crear barras de distribución (PieChart no disponible en Flet 0.80.5)
            total = sum(dist.values()) or 1
            bars = []
            for i, (tipo, count) in enumerate(dist.items()):
                if i >= 5:
                    break
                color = colors_list[i % len(colors_list)]
                pct = count / total
                bars.append(
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(tipo[:20], size=13, expand=True),
                                    ft.Text(f"{count} ({pct:.0%})", size=13, color=Theme.TEXT_SECONDARY),
                                ]
                            ),
                            ft.ProgressBar(value=pct, color=color, bgcolor=Theme.SURFACE, height=12, border_radius=6),
                        ],
                        spacing=4,
                    )
                )

            return UIComponents.card(
                ft.Column(
                    [
                        ft.Text("Distribución por Tipo", weight="bold", size=16),
                        ft.Divider(),
                        ft.Column(bars, spacing=Spacing.MD),
                    ]
                )
            )

        except Exception as e:
            logging.error(f"Error creando gráfico de distribución: {e}")
            return UIComponents.card(
                ft.Column(
                    [
                        ft.Text("Distribución por Tipo", weight="bold", size=16),
                        ft.Divider(),
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Icon("error_outline", size=48, color=Theme.WARNING),
                                    ft.Text(f"Error: {str(e)[:50]}", color=Theme.TEXT_SECONDARY, size=12),
                                ],
                                horizontal_alignment="center",
                                spacing=Spacing.SM,
                            ),
                            alignment=ft.alignment.Alignment(0, 0),
                            padding=Spacing.XL,
                            height=300,
                        ),
                    ]
                )
            )

    def _build_top_searches_chart(self, stats):
        """Gráfico de barras con las búsquedas más frecuentes."""
        try:
            bar_groups = []
            top_searches = stats.get("top_searches", [])

            # Si no hay datos, mostrar mensaje
            if not top_searches:
                return UIComponents.card(
                    ft.Column(
                        [
                            ft.Text("Top Búsquedas", weight="bold", size=16),
                            ft.Divider(),
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Icon("bar_chart", size=64, color=Theme.TEXT_SECONDARY),
                                        ft.Text("No hay búsquedas registradas", color=Theme.TEXT_SECONDARY, size=14),
                                    ],
                                    horizontal_alignment="center",
                                    spacing=Spacing.SM,
                                ),
                                alignment=ft.alignment.Alignment(0, 0),
                                padding=Spacing.XL,
                                height=300,
                            ),
                        ]
                    )
                )

            # Crear grupos de barras (limitado a 6 búsquedas)
            for i, (_query, freq) in enumerate(top_searches[:6]):
                bar_groups.append(
                    ft.BarChartGroup(
                        x=i,
                        bar_rods=[
                            ft.BarChartRod(from_y=0, to_y=float(freq), color=Theme.PRIMARY, width=15, border_radius=4)
                        ],
                    )
                )

            # Crear etiquetas para el eje X
            labels = [
                ft.ChartAxisLabel(value=i, label=ft.Text(top_searches[i][0][:15], size=10, text_align="center"))
                for i in range(len(bar_groups))
            ]

            return UIComponents.card(
                ft.Column(
                    [
                        ft.Text("Top Búsquedas", weight="bold", size=16),
                        ft.Divider(),
                        ft.Container(
                            content=ft.BarChart(
                                bar_groups=bar_groups,
                                bottom_axis=ft.ChartAxis(labels=labels),
                                left_axis=ft.ChartAxis(
                                    labels=[
                                        ft.ChartAxisLabel(value=i, label=ft.Text(str(i), size=10))
                                        for i in range(0, max([s[1] for s in top_searches[:6]]) + 5, 5)
                                    ]
                                ),
                                border=ft.border.all(1, Theme.BORDER),
                                tooltip_bgcolor=Theme.SURFACE_VARIANT,
                            ),
                            height=400,
                            padding=20,
                        ),
                    ]
                )
            )

        except Exception as e:
            logging.error(f"Error creando gráfico de búsquedas: {e}")
            return UIComponents.card(
                ft.Column(
                    [
                        ft.Text("Top Búsquedas", weight="bold", size=16),
                        ft.Divider(),
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Icon("error_outline", size=48, color=Theme.WARNING),
                                    ft.Text(f"Error: {str(e)[:50]}", color=Theme.TEXT_SECONDARY, size=12),
                                ],
                                horizontal_alignment="center",
                                spacing=Spacing.SM,
                            ),
                            alignment=ft.alignment.Alignment(0, 0),
                            padding=Spacing.XL,
                            height=300,
                        ),
                    ]
                )
            )

    def _build_timeline_chart(self, stats):
        """Gráfico de línea temporal de actividad de búsqueda."""
        try:
            data_points = []
            timeline = stats.get("timeline_busquedas", [])

            # Si no hay datos, mostrar mensaje
            if not timeline:
                return UIComponents.card(
                    ft.Column(
                        [
                            ft.Text("Actividad de Búsqueda (Últimos 7 días)", weight="bold", size=16),
                            ft.Divider(),
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Icon("show_chart", size=64, color=Theme.TEXT_SECONDARY),
                                        ft.Text("No hay actividad registrada", color=Theme.TEXT_SECONDARY, size=14),
                                    ],
                                    horizontal_alignment="center",
                                    spacing=Spacing.SM,
                                ),
                                alignment=ft.alignment.Alignment(0, 0),
                                padding=Spacing.XL,
                                height=300,
                            ),
                        ]
                    )
                )

            # Crear puntos de datos para la línea
            for i, (_fecha, count) in enumerate(timeline):
                data_points.append(ft.LineChartDataPoint(i, float(count)))

            # Crear etiquetas para fechas
            labels = [
                ft.ChartAxisLabel(value=i, label=ft.Text(timeline[i][0][5:] if i < len(timeline) else "", size=10))
                for i in range(len(data_points))
            ]

            return UIComponents.card(
                ft.Column(
                    [
                        ft.Text("Actividad de Búsqueda (Últimos 7 días)", weight="bold", size=16),
                        ft.Divider(),
                        ft.Container(
                            content=ft.LineChart(
                                data_series=[
                                    ft.LineChartData(
                                        data_points=data_points,
                                        color=Theme.SECONDARY,
                                        curved=True,
                                        stroke_width=4,
                                        point=True,
                                    )
                                ],
                                bottom_axis=ft.ChartAxis(labels=labels),
                                left_axis=ft.ChartAxis(
                                    labels=[
                                        ft.ChartAxisLabel(value=i, label=ft.Text(str(i), size=10))
                                        for i in range(0, max([c for _, c in timeline]) + 5, 5)
                                    ]
                                    if timeline
                                    else []
                                ),
                                border=ft.border.all(1, Theme.BORDER),
                                tooltip_bgcolor=Theme.SURFACE_VARIANT,
                            ),
                            height=400,
                            padding=20,
                        ),
                    ]
                )
            )

        except Exception as e:
            logging.error(f"Error creando gráfico de timeline: {e}")
            return UIComponents.card(
                ft.Column(
                    [
                        ft.Text("Actividad de Búsqueda (Últimos 7 días)", weight="bold", size=16),
                        ft.Divider(),
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Icon("error_outline", size=48, color=Theme.WARNING),
                                    ft.Text(f"Error: {str(e)[:50]}", color=Theme.TEXT_SECONDARY, size=12),
                                ],
                                horizontal_alignment="center",
                                spacing=Spacing.SM,
                            ),
                            alignment=ft.alignment.Alignment(0, 0),
                            padding=Spacing.XL,
                            height=300,
                        ),
                    ]
                )
            )
