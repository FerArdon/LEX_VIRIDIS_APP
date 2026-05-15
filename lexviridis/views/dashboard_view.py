"""
LEX VIRIDIS - Dashboard View (CustomTkinter)
Panel de control con estadísticas, gráficos simulados y exportación.
"""

import customtkinter as ctk
from .base_view import BaseView
from ..design_system_ctk import Colors, Typography


class DashboardView(BaseView):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, app, **kwargs)
        self.setup_ui()
        self.run_in_thread(self._load_stats_thread)

    def setup_ui(self):
        # 0. Banner de Sección
        if "banner_dashboard" in self.app.icons:
            ctk.CTkLabel(self, image=self.app.icons["banner_dashboard"], text="").pack(fill="x", pady=(0, 10))

        # 1. Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(10, 5))

        ctk.CTkLabel(
            header_frame,
            text="Panel de Control",
            font=Typography.title(),
            text_color=Colors.PRIMARY,
            anchor="w"
        ).pack(side="left")

        # Botones de exportación en el header
        export_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        export_frame.pack(side="right")

        ctk.CTkButton(
            export_frame, text="Exportar Excel",
            fg_color="transparent", border_width=2, border_color=Colors.PRIMARY,
            text_color=Colors.PRIMARY, height=32, width=130, corner_radius=8,
            command=self._export_excel
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            export_frame, text="Exportar PDF",
            fg_color=Colors.PRIMARY, height=32, width=130, corner_radius=8,
            command=self._export_dashboard
        ).pack(side="left", padx=5)

        # 2. Tabview: Resumen / Analytics
        self.tabview = ctk.CTkTabview(self, corner_radius=10)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=10)

        self.tab_resumen = self.tabview.add("Resumen")
        self.tab_analytics = self.tabview.add("Analytics")

        # Placeholder de carga
        self.loading_label = ctk.CTkLabel(
            self.tab_resumen,
            text="Cargando estadísticas...",
            font=Typography.body(),
            text_color=Colors.TEXT_SECONDARY
        )
        self.loading_label.pack(pady=60)

        self._setup_analytics_tab()

    # ── ANALYTICS TAB ──────────────────────────────────────────────────────────

    def _setup_analytics_tab(self):
        scroll = ctk.CTkScrollableFrame(self.tab_analytics, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(
            scroll, text="Acciones Rápidas",
            font=Typography.subtitle(), text_color=Colors.PRIMARY, anchor="w"
        ).pack(fill="x", padx=20, pady=(20, 10))

        btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkButton(
            btn_row, text="📄  Exportar Reporte PDF",
            fg_color=Colors.PRIMARY, height=42, corner_radius=10, font=Typography.bold(),
            command=self._export_dashboard
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_row, text="📊  Exportar a Excel",
            fg_color=Colors.ACCENT_BLUE, height=42, corner_radius=10, font=Typography.bold(),
            command=self._export_excel
        ).pack(side="left")

        # Historial de exportaciones
        ctk.CTkLabel(
            scroll, text="Historial de Exportaciones Recientes",
            font=Typography.subtitle(), text_color=Colors.PRIMARY, anchor="w"
        ).pack(fill="x", padx=20, pady=(10, 5))

        self.history_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self.history_frame.pack(fill="x", padx=20)
        self._load_export_history()

    def _load_export_history(self):
        for w in self.history_frame.winfo_children():
            w.destroy()
        try:
            from ..utils.export_manager import ExportLogManager
            history = ExportLogManager.get_history()
        except Exception:
            history = []

        if not history:
            ctk.CTkLabel(
                self.history_frame,
                text="No hay exportaciones recientes.",
                text_color=Colors.TEXT_SECONDARY
            ).pack(pady=10)
            return

        for item in history:
            row = ctk.CTkFrame(self.history_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            fmt_color = Colors.ACCENT_BLUE if item.get("format") == "PDF" else Colors.PRIMARY
            ctk.CTkLabel(
                row, text=f" {item.get('format','?')} ",
                fg_color=fmt_color, text_color="white",
                corner_radius=4, font=Typography.get_font(10, "bold")
            ).pack(side="left", padx=(0, 8))
            ctk.CTkLabel(row, text=item.get("filename", ""), font=Typography.body(), anchor="w").pack(side="left")
            ctk.CTkLabel(
                row, text=item.get("date", ""), font=Typography.caption(),
                text_color=Colors.TEXT_SECONDARY
            ).pack(side="right")

    # ── CARGA DE DATOS ─────────────────────────────────────────────────────────

    def _load_stats_thread(self):
        try:
            stats = self.app.engine.get_dashboard_stats()
            self.update_ui(self._render_stats, stats)
        except Exception as e:
            self.update_ui(self.show_toast, f"Error cargando dashboard: {e}", "error")
            self.update_ui(lambda: self.loading_label.configure(
                text="No se pudieron cargar las estadísticas."
            ))

    # ── RENDERIZADO DE RESUMEN ─────────────────────────────────────────────────

    def _render_stats(self, stats):
        self.loading_label.destroy()

        scroll = ctk.CTkScrollableFrame(self.tab_resumen, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        self._render_stat_cards(scroll, stats)
        self._render_distribution(scroll, stats.get("distribucion_tipo", {}))
        self._render_top_searches(scroll, stats.get("top_searches", []))
        self._render_recent_activity(scroll, stats.get("most_viewed", []))
        self._render_timeline(scroll, stats.get("timeline_busquedas", []))

    def _render_stat_cards(self, parent, stats):
        cards_frame = ctk.CTkFrame(parent, fg_color="transparent")
        cards_frame.pack(fill="x", padx=10, pady=(10, 5))
        cards_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        stat_data = [
            ("Normas",     stats.get("total_normas", 0),     Colors.PRIMARY),
            ("Artículos",  stats.get("total_articulos", 0),  Colors.SECONDARY),
            ("Favoritos",  stats.get("total_favoritos", 0),  Colors.ACCENT_BLUE),
            ("Búsquedas",  stats.get("total_busquedas", 0),  Colors.SUCCESS),
        ]
        for idx, (label, value, color) in enumerate(stat_data):
            card = ctk.CTkFrame(
                cards_frame, corner_radius=12,
                border_width=1, border_color=Colors.BORDER
            )
            card.grid(row=0, column=idx, padx=6, pady=5, sticky="ew")
            ctk.CTkLabel(
                card, text=str(value),
                font=Typography.get_font(28, "bold"), text_color=color
            ).pack(pady=(15, 0))
            ctk.CTkLabel(
                card, text=label,
                font=Typography.caption(), text_color=Colors.TEXT_SECONDARY
            ).pack(pady=(0, 15))

    def _render_distribution(self, parent, data):
        if not data:
            return
        group = self._make_group(parent, "Distribución por Tipo")
        total = sum(data.values()) or 1
        bar_colors = [Colors.PRIMARY, Colors.SECONDARY, Colors.ACCENT_BLUE, Colors.SUCCESS, "#9e4b8e"]

        for i, (tipo, count) in enumerate(list(data.items())[:5]):
            row = ctk.CTkFrame(group, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=3)
            ctk.CTkLabel(row, text=tipo[:22], width=160, anchor="w", font=Typography.body()).pack(side="left")

            bar_bg = ctk.CTkFrame(row, height=14, corner_radius=4, fg_color=Colors.BORDER)
            bar_bg.pack(side="left", fill="x", expand=True, padx=8)
            pct = max(count / total, 0.02)
            ctk.CTkFrame(
                bar_bg, height=14, corner_radius=4,
                fg_color=bar_colors[i % len(bar_colors)]
            ).place(relx=0, rely=0, relwidth=pct, relheight=1.0)

            ctk.CTkLabel(
                row, text=str(count), width=40, anchor="e",
                font=Typography.caption(), text_color=Colors.TEXT_SECONDARY
            ).pack(side="right")
        ctk.CTkFrame(group, height=1, fg_color="transparent").pack(pady=5)

    def _render_top_searches(self, parent, data):
        if not data:
            return
        group = self._make_group(parent, "Top Búsquedas")
        max_val = max((f for _, f in data[:6]), default=1) or 1

        for query, freq in data[:6]:
            row = ctk.CTkFrame(group, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=3)
            ctk.CTkLabel(row, text=query[:25], width=160, anchor="w", font=Typography.body()).pack(side="left")

            bar_bg = ctk.CTkFrame(row, height=14, corner_radius=4, fg_color=Colors.BORDER)
            bar_bg.pack(side="left", fill="x", expand=True, padx=8)
            ctk.CTkFrame(
                bar_bg, height=14, corner_radius=4, fg_color=Colors.ACCENT_BLUE
            ).place(relx=0, rely=0, relwidth=max(freq / max_val, 0.02), relheight=1.0)

            ctk.CTkLabel(
                row, text=str(freq), width=30, anchor="e",
                font=Typography.caption(), text_color=Colors.TEXT_SECONDARY
            ).pack(side="right")
        ctk.CTkFrame(group, height=1, fg_color="transparent").pack(pady=5)

    def _render_recent_activity(self, parent, data):
        group = self._make_group(parent, "Normas más consultadas")
        if not data:
            ctk.CTkLabel(
                group, text="Sin actividad reciente.",
                text_color=Colors.TEXT_SECONDARY, font=Typography.body()
            ).pack(pady=10)
        else:
            for title, views in data[:8]:
                row = ctk.CTkFrame(group, fg_color="transparent")
                row.pack(fill="x", padx=15, pady=2)
                ctk.CTkLabel(
                    row, text="▸ " + str(title)[:55],
                    anchor="w", font=Typography.body()
                ).pack(side="left")
                ctk.CTkLabel(
                    row, text=f"{views} vistas",
                    font=Typography.caption(), text_color=Colors.TEXT_SECONDARY
                ).pack(side="right")
        ctk.CTkFrame(group, height=1, fg_color="transparent").pack(pady=5)

    def _render_timeline(self, parent, data):
        if not data:
            return
        group = self._make_group(parent, "Actividad de Búsqueda (Últimos 7 días)")
        max_val = max((c for _, c in data), default=1) or 1

        bars_row = ctk.CTkFrame(group, fg_color="transparent")
        bars_row.pack(fill="x", padx=15, pady=(5, 12))

        for fecha, count in data:
            col = ctk.CTkFrame(bars_row, fg_color="transparent", width=55)
            col.pack(side="left", expand=True)
            bar_h = max(int(70 * count / max_val), 4)
            ctk.CTkFrame(
                col, height=bar_h, width=32, corner_radius=4, fg_color=Colors.SECONDARY
            ).pack(pady=(0, 3))
            ctk.CTkLabel(col, text=str(count), font=Typography.get_font(10, "bold"), text_color=Colors.TEXT_SECONDARY).pack()
            short_date = str(fecha)[5:] if len(str(fecha)) > 5 else str(fecha)
            ctk.CTkLabel(col, text=short_date, font=Typography.get_font(9), text_color=Colors.TEXT_SECONDARY).pack()
        ctk.CTkFrame(group, height=1, fg_color="transparent").pack(pady=5)

    def _make_group(self, parent, title):
        group = ctk.CTkFrame(parent, corner_radius=10, border_width=1, border_color=Colors.BORDER)
        group.pack(fill="x", padx=10, pady=6)
        ctk.CTkLabel(group, text=title, font=Typography.bold(), anchor="w").pack(fill="x", padx=15, pady=(12, 6))
        return group

    # ── EXPORTACIÓN ────────────────────────────────────────────────────────────

    def _build_export_data(self):
        """Construye lista de datos del dashboard para exportación."""
        try:
            stats = self.app.engine.get_dashboard_stats()
            return [
                {"norma_titulo": "Total Normas",    "context": str(stats.get("total_normas", 0)),    "page": "-", "relevance": 1.0},
                {"norma_titulo": "Total Artículos", "context": str(stats.get("total_articulos", 0)), "page": "-", "relevance": 1.0},
                {"norma_titulo": "Favoritos",       "context": str(stats.get("total_favoritos", 0)), "page": "-", "relevance": 1.0},
                {"norma_titulo": "Búsquedas",       "context": str(stats.get("total_busquedas", 0)), "page": "-", "relevance": 1.0},
            ]
        except Exception:
            return []

    def _export_dashboard(self):
        from ..utils.export_manager import ExportManager
        data = self._build_export_data()
        ExportManager.export(
            data, format_type="PDF", query="Dashboard", origin="Dashboard",
            callback=lambda ok, info: (
                self.update_ui(self.show_export_success_dialog, info) if ok
                else self.update_ui(self.show_toast, f"Fallo: {info}", "error")
            )
        )

    def _export_excel(self):
        from ..utils.export_manager import ExportManager
        data = self._build_export_data()
        ExportManager.export(
            data, format_type="EXCEL", query="Dashboard", origin="Dashboard",
            callback=lambda ok, info: (
                self.update_ui(self.show_export_success_dialog, info) if ok
                else self.update_ui(self.show_toast, f"Fallo: {info}", "error")
            )
        )
