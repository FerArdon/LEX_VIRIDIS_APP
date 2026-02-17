"""Vista de detalle de un caso legal."""

import flet as ft
from datetime import datetime
from lexviridis.repositories.casos_repository import CasosRepository
from lexviridis.design_system import Theme, Spacing


class CasoDetailView(ft.Container):
    """Vista detallada de un caso con artículos vinculados y notas."""

    def __init__(self, caso, casos_repo: CasosRepository, on_close, on_open_pdf):
        super().__init__(expand=True)
        self.caso = caso
        self.casos_repo = casos_repo
        self.on_close = on_close
        self.on_open_pdf = on_open_pdf
        self.articulos = []
        self.notas = []
        self._build_view()

    def _build_view(self):
        """Construye la interfaz del detalle del caso."""
        self._load_data()

        # Header con información del caso
        header = self._build_header()

        # Tabs para diferentes secciones
        tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text="Información",
                    icon=ft.Icons.INFO_OUTLINE,
                    content=self._build_info_tab(),
                ),
                ft.Tab(
                    text="Artículos Vinculados",
                    icon=ft.Icons.LINK,
                    content=self._build_articulos_tab(),
                ),
                ft.Tab(
                    text="Notas y Anotaciones",
                    icon=ft.Icons.NOTE_ADD,
                    content=self._build_notas_tab(),
                ),
                ft.Tab(
                    text="Timeline",
                    icon=ft.Icons.TIMELINE,
                    content=self._build_timeline_tab(),
                ),
            ],
            expand=1,
        )

        self.content = ft.Column([
            header,
            ft.Container(height=Spacing.MD),
            tabs,
        ], expand=True, spacing=0)

    def _load_data(self):
        """Carga los datos del caso."""
        self.articulos = self.casos_repo.obtener_articulos_caso(self.caso['id'])
        self.notas = self.casos_repo.obtener_notas_caso(self.caso['id'])

    def _build_header(self):
        """Construye el header con información del caso."""
        # Color según prioridad
        prioridad_colors = {
            'ALTA': '#F44336',
            'MEDIA': '#FF9800',
            'BAJA': '#4CAF50',
        }
        prioridad_color = prioridad_colors.get(self.caso.get('prioridad', 'MEDIA'), '#FF9800')

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.IconButton(
                        icon="arrow_back",
                        icon_size=24,
                        tooltip="Volver",
                        on_click=lambda _: self.on_close()
                    ),
                    ft.Icon("folder_special", size=32, color=Theme.PRIMARY),
                    ft.Column([
                        ft.Text(
                            self.caso.get('numero_expediente', 'N/A'),
                            size=12,
                            color=Theme.TEXT_SECONDARY,
                            weight="bold"
                        ),
                        ft.Text(
                            self.caso.get('titulo', 'Sin título'),
                            size=20,
                            weight="bold",
                            color=Theme.TEXT_PRIMARY
                        ),
                    ], spacing=0),
                    ft.Container(expand=True),
                    ft.Container(
                        content=ft.Text(
                            self.caso.get('estado', 'ABIERTO'),
                            size=12,
                            weight="bold",
                            color="white"
                        ),
                        bgcolor=Theme.PRIMARY if self.caso.get('estado') == 'ABIERTO' else Theme.TEXT_SECONDARY,
                        padding=ft.padding.symmetric(horizontal=12, vertical=6),
                        border_radius=16,
                    ),
                    ft.Container(
                        content=ft.Text(
                            self.caso.get('prioridad', 'MEDIA'),
                            size=12,
                            weight="bold",
                            color="white"
                        ),
                        bgcolor=prioridad_color,
                        padding=ft.padding.symmetric(horizontal=12, vertical=6),
                        border_radius=16,
                    ),
                ]),
            ]),
            padding=Spacing.MD,
            bgcolor=Theme.SURFACE,
            border_radius=8,
        )

    def _build_info_tab(self):
        """Construye la pestaña de información general."""
        fecha_inicio = self.caso.get('fecha_inicio', '')
        if fecha_inicio:
            try:
                fecha_obj = datetime.strptime(fecha_inicio.split()[0], "%Y-%m-%d")
                fecha_display = fecha_obj.strftime("%d de %B de %Y")
            except (ValueError, IndexError):
                fecha_display = fecha_inicio
        else:
            fecha_display = "N/A"

        info_items = [
            ("Descripción", self.caso.get('descripcion', 'Sin descripción')),
            ("Categoría", self.caso.get('categoria', 'N/A')),
            ("Responsable", self.caso.get('responsable', 'N/A')),
            ("Fecha de Inicio", fecha_display),
            ("Artículos Vinculados", str(len(self.articulos))),
            ("Notas y Anotaciones", str(len(self.notas))),
        ]

        return ft.Container(
            content=ft.Column([
                *[self._build_info_row(label, value) for label, value in info_items],
            ], spacing=Spacing.MD),
            padding=Spacing.MD,
        )

    def _build_info_row(self, label, value):
        """Construye una fila de información."""
        return ft.Column([
            ft.Text(label, size=12, weight="bold", color=Theme.TEXT_SECONDARY),
            ft.Text(value, size=14, color=Theme.TEXT_PRIMARY),
            ft.Divider(height=1, color=Theme.BORDER),
        ], spacing=Spacing.XS)

    def _build_articulos_tab(self):
        """Construye la pestaña de artículos vinculados."""
        if not self.articulos:
            return ft.Container(
                content=ft.Column([
                    ft.Icon("link_off", size=64, color=Theme.TEXT_SECONDARY),
                    ft.Text(
                        "No hay artículos vinculados",
                        size=16,
                        color=Theme.TEXT_SECONDARY
                    ),
                    ft.Text(
                        "Vincula artículos desde los resultados de búsqueda",
                        size=12,
                        color=Theme.TEXT_SECONDARY
                    ),
                ], horizontal_alignment="center", spacing=Spacing.SM),
                padding=Spacing.XL,
                alignment=ft.Alignment(0, 0),
            )

        articulos_list = ft.Column(
            [self._build_articulo_card(art) for art in self.articulos],
            spacing=Spacing.SM,
            scroll=ft.ScrollMode.AUTO,
        )

        return ft.Container(
            content=articulos_list,
            padding=Spacing.MD,
        )

    def _build_articulo_card(self, articulo):
        """Construye una tarjeta de artículo vinculado."""
        relevancia_colors = {
            'ALTA': '#F44336',
            'MEDIA': '#FF9800',
            'BAJA': '#4CAF50',
        }
        relevancia_color = relevancia_colors.get(articulo.get('relevancia', 'MEDIA'), '#FF9800')

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon("article", size=20, color=Theme.PRIMARY),
                    ft.Text(
                        f"Art. {articulo.get('numero_articulo', 'N/A')}",
                        size=14,
                        weight="bold",
                        color=Theme.PRIMARY
                    ),
                    ft.Container(expand=True),
                    ft.Container(
                        content=ft.Text(
                            articulo.get('relevancia', 'MEDIA'),
                            size=10,
                            weight="bold",
                            color="white"
                        ),
                        bgcolor=relevancia_color,
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                        border_radius=12,
                    ),
                ]),
                ft.Text(
                    articulo.get('norma_titulo', 'Sin título'),
                    size=13,
                    weight="bold",
                    color=Theme.TEXT_PRIMARY
                ),
                ft.Text(
                    articulo.get('contenido_completo', '')[:200] + '...',
                    size=11,
                    color=Theme.TEXT_SECONDARY,
                    max_lines=3,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                ft.Divider(height=1, color=Theme.BORDER) if articulo.get('notas') else ft.Container(),
                ft.Text(
                    f"📝 {articulo.get('notas', '')}",
                    size=11,
                    color=Theme.TEXT_SECONDARY,
                    italic=True,
                ) if articulo.get('notas') else ft.Container(),
                ft.Row([
                    ft.TextButton(
                        "Ver PDF",
                        icon="picture_as_pdf",
                        on_click=lambda _, a=articulo: self.on_open_pdf({'file': a.get('archivo_pdf')})
                    ),
                    ft.Container(expand=True),
                    ft.IconButton(
                        icon="delete",
                        icon_size=18,
                        icon_color=Theme.ERROR,
                        tooltip="Desvincular",
                        on_click=lambda _, a=articulo: self._desvincular_articulo(a)
                    ),
                ]),
            ], spacing=Spacing.XS, tight=True),
            padding=Spacing.MD,
            bgcolor=Theme.BACKGROUND,
            border=ft.border.all(1, Theme.BORDER),
            border_radius=8,
        )

    def _build_notas_tab(self):
        """Construye la pestaña de notas y anotaciones."""
        self.notas_list = ft.Column(spacing=Spacing.SM, scroll=ft.ScrollMode.AUTO)
        self._update_notas_list()

        return ft.Column([
            ft.Container(
                content=ft.Row([
                    ft.ElevatedButton(
                        "Nueva Nota",
                        icon="add",
                        on_click=lambda _: self._show_nueva_nota_dialog(),
                        bgcolor=Theme.PRIMARY,
                        color="white"
                    ),
                ]),
                padding=Spacing.MD,
            ),
            ft.Container(
                content=self.notas_list,
                padding=Spacing.MD,
                expand=True,
            ),
        ], expand=True, spacing=0)

    def _update_notas_list(self):
        """Actualiza la lista de notas."""
        self.notas_list.controls.clear()

        if not self.notas:
            self.notas_list.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon("note", size=64, color=Theme.TEXT_SECONDARY),
                        ft.Text(
                            "No hay notas",
                            size=16,
                            color=Theme.TEXT_SECONDARY
                        ),
                    ], horizontal_alignment="center", spacing=Spacing.SM),
                    padding=Spacing.XL,
                    alignment=ft.Alignment(0, 0),
                )
            )
        else:
            for nota in self.notas:
                self.notas_list.controls.append(self._build_nota_card(nota))

    def _build_nota_card(self, nota):
        """Construye una tarjeta de nota."""
        fecha = nota.get('created_at', '')
        if fecha:
            try:
                fecha_obj = datetime.strptime(fecha, "%Y-%m-%d %H:%M:%S")
                fecha_display = fecha_obj.strftime("%d/%m/%Y %H:%M")
            except ValueError:
                fecha_display = fecha
        else:
            fecha_display = "N/A"

        tipo_icons = {
            'NOTA': 'note',
            'OBSERVACION': 'visibility',
            'CONCLUSION': 'check_circle',
            'PENDIENTE': 'schedule',
        }
        icon = tipo_icons.get(nota.get('tipo', 'NOTA'), 'note')

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(icon, size=20, color=Theme.PRIMARY),
                    ft.Text(
                        nota.get('titulo', 'Sin título'),
                        size=14,
                        weight="bold",
                        color=Theme.TEXT_PRIMARY
                    ),
                    ft.Container(expand=True),
                    ft.IconButton(
                        icon="delete",
                        icon_size=18,
                        icon_color=Theme.ERROR,
                        tooltip="Eliminar nota",
                        on_click=lambda _, n=nota: self._eliminar_nota(n)
                    ),
                ]),
                ft.Text(
                    nota.get('contenido', ''),
                    size=12,
                    color=Theme.TEXT_SECONDARY,
                ),
                ft.Divider(height=1, color=Theme.BORDER),
                ft.Row([
                    ft.Text(
                        f"📅 {fecha_display}",
                        size=10,
                        color=Theme.TEXT_SECONDARY,
                    ),
                    ft.Text(
                        f"👤 {nota.get('autor', 'Anónimo')}",
                        size=10,
                        color=Theme.TEXT_SECONDARY,
                    ) if nota.get('autor') else ft.Container(),
                ]),
            ], spacing=Spacing.XS, tight=True),
            padding=Spacing.MD,
            bgcolor=Theme.BACKGROUND,
            border=ft.border.all(1, Theme.BORDER),
            border_radius=8,
        )

    def _build_timeline_tab(self):
        """Construye la pestaña de timeline."""
        # Combinar artículos y notas en un timeline cronológico
        timeline_events = []

        # Agregar artículos vinculados
        for art in self.articulos:
            timeline_events.append({
                'tipo': 'articulo',
                'fecha': art.get('vinculado_en', ''),
                'data': art
            })

        # Agregar notas
        for nota in self.notas:
            timeline_events.append({
                'tipo': 'nota',
                'fecha': nota.get('created_at', ''),
                'data': nota
            })

        # Ordenar por fecha descendente
        timeline_events.sort(key=lambda x: x['fecha'], reverse=True)

        if not timeline_events:
            return ft.Container(
                content=ft.Column([
                    ft.Icon("timeline", size=64, color=Theme.TEXT_SECONDARY),
                    ft.Text(
                        "No hay actividad registrada",
                        size=16,
                        color=Theme.TEXT_SECONDARY
                    ),
                ], horizontal_alignment="center", spacing=Spacing.SM),
                padding=Spacing.XL,
                alignment=ft.Alignment(0, 0),
            )

        return ft.Container(
            content=ft.Column(
                [self._build_timeline_event(event) for event in timeline_events],
                spacing=Spacing.SM,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=Spacing.MD,
        )

    def _build_timeline_event(self, event):
        """Construye un evento del timeline."""
        fecha = event['fecha']
        if fecha:
            try:
                fecha_obj = datetime.strptime(fecha.split('.')[0], "%Y-%m-%d %H:%M:%S")
                fecha_display = fecha_obj.strftime("%d/%m/%Y %H:%M")
            except (ValueError, IndexError):
                fecha_display = fecha
        else:
            fecha_display = "N/A"

        if event['tipo'] == 'articulo':
            icon = "link"
            color = "#2196F3"
            title = f"Artículo {event['data'].get('numero_articulo')} vinculado"
            subtitle = event['data'].get('norma_titulo', '')
        else:  # nota
            icon = "note_add"
            color = "#4CAF50"
            title = event['data'].get('titulo', '')
            subtitle = event['data'].get('contenido', '')[:100] + '...'

        return ft.Container(
            content=ft.Row([
                ft.Container(
                    width=4,
                    bgcolor=color,
                    border_radius=2,
                ),
                ft.Container(width=Spacing.SM),
                ft.Icon(icon, size=24, color=color),
                ft.Container(width=Spacing.SM),
                ft.Column([
                    ft.Text(title, size=13, weight="bold", color=Theme.TEXT_PRIMARY),
                    ft.Text(subtitle, size=11, color=Theme.TEXT_SECONDARY),
                    ft.Text(fecha_display, size=10, color=Theme.TEXT_SECONDARY, italic=True),
                ], spacing=2),
            ]),
            padding=Spacing.MD,
            bgcolor=Theme.BACKGROUND,
            border_radius=8,
        )

    def _show_nueva_nota_dialog(self):
        """Muestra el diálogo para agregar una nueva nota."""
        titulo_field = ft.TextField(label="Título*", hint_text="Título de la nota")
        contenido_field = ft.TextField(
            label="Contenido*",
            multiline=True,
            min_lines=4,
            max_lines=8,
            hint_text="Escribe tu nota aquí..."
        )
        tipo_dropdown = ft.Dropdown(
            label="Tipo",
            options=[
                ft.dropdown.Option("NOTA"),
                ft.dropdown.Option("OBSERVACION"),
                ft.dropdown.Option("CONCLUSION"),
                ft.dropdown.Option("PENDIENTE"),
            ],
            value="NOTA",
        )
        autor_field = ft.TextField(label="Autor", hint_text="Tu nombre")

        def crear_nota(e):
            if not titulo_field.value or not contenido_field.value:
                self.page.snack_bar = ft.SnackBar(
                    ft.Text("El título y contenido son obligatorios"),
                    bgcolor=Theme.ERROR
                )
                self.page.snack_bar.open = True
                self.page.update()
                return

            try:
                self.casos_repo.agregar_nota(
                    caso_id=self.caso['id'],
                    titulo=titulo_field.value,
                    contenido=contenido_field.value,
                    tipo=tipo_dropdown.value,
                    autor=autor_field.value or ""
                )

                dialog.open = False
                self.page.update()

                # Recargar notas
                self.notas = self.casos_repo.obtener_notas_caso(self.caso['id'])
                self._update_notas_list()
                self.update()

                self.page.snack_bar = ft.SnackBar(
                    ft.Text("✓ Nota agregada exitosamente"),
                    bgcolor=Theme.SUCCESS
                )
                self.page.snack_bar.open = True
                self.page.update()

            except Exception as ex:
                self.page.snack_bar = ft.SnackBar(
                    ft.Text(f"Error: {ex}"),
                    bgcolor=Theme.ERROR
                )
                self.page.snack_bar.open = True
                self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Nueva Nota"),
            content=ft.Column([
                titulo_field,
                contenido_field,
                tipo_dropdown,
                autor_field,
            ], tight=True, spacing=Spacing.SM, scroll=ft.ScrollMode.AUTO, height=350),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self._close_dialog(dialog)),
                ft.ElevatedButton("Agregar Nota", on_click=crear_nota, bgcolor=Theme.PRIMARY, color="white"),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def _desvincular_articulo(self, articulo):
        """Desvincula un artículo del caso."""
        try:
            self.casos_repo.desvincular_articulo(self.caso['id'], articulo['articulo_id'])

            # Recargar artículos
            self.articulos = self.casos_repo.obtener_articulos_caso(self.caso['id'])
            self.update()

            self.page.snack_bar = ft.SnackBar(
                ft.Text("✓ Artículo desvinculado"),
                bgcolor=Theme.SUCCESS
            )
            self.page.snack_bar.open = True
            self.page.update()

        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(
                ft.Text(f"Error: {ex}"),
                bgcolor=Theme.ERROR
            )
            self.page.snack_bar.open = True
            self.page.update()

    def _eliminar_nota(self, nota):
        """Elimina una nota."""
        try:
            self.casos_repo.eliminar_nota(nota['id'])

            # Recargar notas
            self.notas = self.casos_repo.obtener_notas_caso(self.caso['id'])
            self._update_notas_list()
            self.update()

            self.page.snack_bar = ft.SnackBar(
                ft.Text("✓ Nota eliminada"),
                bgcolor=Theme.SUCCESS
            )
            self.page.snack_bar.open = True
            self.page.update()

        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(
                ft.Text(f"Error: {ex}"),
                bgcolor=Theme.ERROR
            )
            self.page.snack_bar.open = True
            self.page.update()

    def _close_dialog(self, dialog):
        """Cierra un diálogo."""
        dialog.open = False
        self.page.update()
