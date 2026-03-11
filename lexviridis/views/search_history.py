"""
Vista de Historial de Búsquedas.
Muestra todas las búsquedas realizadas con opción de repetir y exportar.
"""

from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import flet as ft

from ..design_system import Colors, Radius, Spacing, Theme, UIComponents


class SearchHistoryView(ft.Container):
    """
    Vista de Historial de Búsquedas.
    Muestra el historial completo con opciones de filtrado y exportación.
    """

    def __init__(self, search_engine, on_search_again: Callable):
        super().__init__(expand=True)
        self.search_engine = search_engine
        self.on_search_again = on_search_again
        self._build_ui()

    def _build_ui(self):
        # Hero Header
        hero = UIComponents.hero_header(
            "hero_ai.png", "Historial de Búsquedas", "Consulta y repite búsquedas anteriores"
        )

        # Obtener historial
        history = self._get_search_history()

        # Search bar para filtrar
        self.filter_input = ft.TextField(
            hint_text="Filtrar por término de búsqueda...",
            prefix_icon="search",
            border_radius=Radius.MD,
            on_change=lambda e: self._filter_history(e.control.value),
        )

        # Botones de acción
        action_buttons = ft.Row(
            [
                UIComponents.primary_button(
                    "Exportar a TXT", icon="download", on_click=lambda _: self._export_history()
                ),
                UIComponents.secondary_button(
                    "Limpiar Historial", icon="delete_outline", on_click=lambda _: self._confirm_clear_history()
                ),
            ],
            spacing=Spacing.SM,
        )

        # Tabla de historial
        self.history_list = ft.ListView(
            controls=self._build_history_items(history), spacing=Spacing.SM, padding=Spacing.MD, expand=True
        )

        # Layout
        self.content = ft.Column(
            [
                hero,
                ft.Row(
                    [
                        UIComponents.heading("Historial de Búsquedas", level=1, color=Theme.PRIMARY),
                        ft.Container(expand=True),
                        ft.Text(f"{len(history)} búsquedas", size=14, color=Theme.TEXT_SECONDARY),
                    ]
                ),
                UIComponents.divider(),
                ft.Row(
                    [
                        ft.Container(content=self.filter_input, expand=True),
                        action_buttons,
                    ],
                    spacing=Spacing.MD,
                ),
                ft.Container(height=Spacing.MD),
                ft.Container(
                    content=self.history_list,
                    expand=True,
                    bgcolor=Theme.SURFACE_VARIANT,
                    border_radius=Radius.LG,
                    border=ft.border.all(1, Theme.BORDER),
                ),
            ],
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )

        self.full_history = history

    def _get_search_history(self):
        """Obtiene el historial de búsquedas desde la base de datos."""
        try:
            conn = self.search_engine.db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, query, timestamp, results_count
                FROM historial_busquedas
                ORDER BY timestamp DESC
                LIMIT 500
            """)
            history = cursor.fetchall()
            conn.close()
            return [dict(row) for row in history]
        except Exception as e:
            import logging

            logging.error(f"Error obteniendo historial: {e}")
            return []

    def _build_history_items(self, history):
        """Construye los items del historial."""
        if not history:
            return [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon("history", size=64, color=Theme.TEXT_SECONDARY),
                            ft.Text("No hay búsquedas en el historial", size=16, color=Theme.TEXT_SECONDARY),
                        ],
                        horizontal_alignment="center",
                        spacing=Spacing.MD,
                    ),
                    alignment=ft.alignment.Alignment(0, 0),
                    padding=Spacing.XL,
                    height=300,
                )
            ]

        items = []
        for entry in history:
            # Parse timestamp
            try:
                dt = datetime.fromisoformat(entry["timestamp"])
                date_str = dt.strftime("%d/%m/%Y")
                time_str = dt.strftime("%H:%M:%S")
            except:
                date_str = "Fecha desconocida"
                time_str = ""

            # Create card
            card = UIComponents.card(
                ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon("search", size=20, color=Theme.PRIMARY),
                                ft.Container(
                                    content=ft.Column(
                                        [
                                            ft.Text(
                                                entry["query"], size=16, weight="bold", max_lines=1, overflow="ellipsis"
                                            ),
                                            ft.Text(f"{date_str} {time_str}", size=12, color=Theme.TEXT_SECONDARY),
                                        ],
                                        spacing=2,
                                    ),
                                    expand=True,
                                ),
                                ft.Container(
                                    content=ft.Row(
                                        [
                                            ft.Icon("article", size=16, color=Theme.INFO),
                                            ft.Text(
                                                f"{entry.get('results_count', 0)}",
                                                size=14,
                                                color=Theme.INFO,
                                                weight="bold",
                                            ),
                                        ],
                                        spacing=4,
                                    ),
                                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                    bgcolor=Colors.with_opacity(0.1, Theme.INFO),
                                    border_radius=Radius.SM,
                                ),
                                ft.IconButton(
                                    icon="refresh",
                                    tooltip="Repetir búsqueda",
                                    icon_size=20,
                                    on_click=lambda e, q=entry["query"]: self._repeat_search(q),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                            spacing=Spacing.SM,
                        ),
                    ],
                    spacing=Spacing.XS,
                ),
                padding=Spacing.SM,
            )
            items.append(card)

        return items

    def _filter_history(self, filter_text):
        """Filtra el historial por término de búsqueda."""
        if not filter_text:
            filtered = self.full_history
        else:
            filter_lower = filter_text.lower()
            filtered = [entry for entry in self.full_history if filter_lower in entry["query"].lower()]

        self.history_list.controls = self._build_history_items(filtered)
        self.update()

    def _repeat_search(self, query):
        """Repite una búsqueda del historial."""
        if self.on_search_again:
            self.on_search_again(query)

    def _export_history(self):
        """Exporta el historial a un archivo TXT."""
        try:
            # Crear directorio de exportaciones
            export_dir = Path.home() / "Documents" / "LEX_VIRIDIS" / "Exportaciones"
            export_dir.mkdir(parents=True, exist_ok=True)

            # Generar nombre de archivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"historial_busquedas_{timestamp}.txt"
            filepath = export_dir / filename

            # Formatear contenido
            content = []
            content.append("=" * 80)
            content.append("LEX VIRIDIS - Historial de Búsquedas")
            content.append("=" * 80)
            content.append(f"\nFecha de exportación: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
            content.append(f"Total de búsquedas: {len(self.full_history)}")
            content.append("\n" + "=" * 80)
            content.append("")

            for i, entry in enumerate(self.full_history, 1):
                try:
                    dt = datetime.fromisoformat(entry["timestamp"])
                    date_str = dt.strftime("%d/%m/%Y %H:%M:%S")
                except:
                    date_str = "Fecha desconocida"

                content.append(f"{i}. {entry['query']}")
                content.append(f"   Fecha: {date_str}")
                content.append(f"   Resultados: {entry.get('results_count', 0)}")
                content.append("")

            content.append("=" * 80)
            content.append("Generado por LEX VIRIDIS - Sistema de Investigación Legal Ambiental")
            content.append("Copyright © 2026 FEMA Honduras")
            content.append("=" * 80)

            # Guardar archivo
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(content))

            # Mostrar confirmación
            if hasattr(self, "page") and self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"✓ Historial exportado: {filename}"), bgcolor=Theme.SUCCESS)
                self.page.snack_bar.open = True
                self.page.update()

            # Abrir carpeta
            import os
            import platform

            if platform.system() == "Windows":
                os.startfile(export_dir)
            elif platform.system() == "Darwin":
                os.system(f'open "{export_dir}"')  # nosec B605
            else:
                os.system(f'xdg-open "{export_dir}"')  # nosec B605

        except Exception as e:
            import logging

            logging.error(f"Error exportando historial: {e}")
            if hasattr(self, "page") and self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Error al exportar: {e}"), bgcolor=Theme.ERROR)
                self.page.snack_bar.open = True
                self.page.update()

    def _confirm_clear_history(self):
        """Muestra un diálogo de confirmación antes de limpiar el historial."""

        def clear_confirmed(e):
            self._clear_history()
            dialog.open = False
            if hasattr(self, "page") and self.page:
                self.page.update()

        def cancel(e):
            dialog.open = False
            if hasattr(self, "page") and self.page:
                self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Confirmar acción"),
            content=ft.Text(
                "¿Estás seguro de que deseas eliminar todo el historial de búsquedas? Esta acción no se puede deshacer."
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cancel),
                ft.ElevatedButton("Eliminar", on_click=clear_confirmed, bgcolor=Theme.ERROR, color="white"),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        if hasattr(self, "page") and self.page:
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()

    def _clear_history(self):
        """Limpia todo el historial de búsquedas."""
        try:
            self.search_engine.clear_history()
            self.full_history = []
            self.history_list.controls = self._build_history_items([])

            if hasattr(self, "page") and self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text("✓ Historial eliminado"), bgcolor=Theme.SUCCESS)
                self.page.snack_bar.open = True
                self.page.update()
        except Exception as e:
            import logging

            logging.error(f"Error limpiando historial: {e}")
            if hasattr(self, "page") and self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Error: {e}"), bgcolor=Theme.ERROR)
                self.page.snack_bar.open = True
                self.page.update()
