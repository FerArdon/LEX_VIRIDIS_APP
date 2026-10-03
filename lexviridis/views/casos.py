"""Vista para gestión de casos y expedientes legales."""

from datetime import datetime
from pathlib import Path
from typing import Any

import flet as ft

from lexviridis.design_system import Spacing, Theme
from lexviridis.repositories.casos_repository import CasosRepository


class CasosView(ft.Container):
    """Vista principal para gestionar casos legales."""

    def __init__(self, casos_repo: CasosRepository, on_open_caso_detail, page=None):
        super().__init__(expand=True)
        self.casos_repo = casos_repo
        self.on_open_caso_detail = on_open_caso_detail
        self._page = page  # Se asignará en did_mount si no se pasa
        self.casos: list[Any] = []
        self.filtro_estado = None
        self.filtro_prioridad = None
        self.filtro_fecha_inicio = None
        self.filtro_fecha_fin = None
        # Checkboxes para selección múltiple { caso_id: Checkbox }
        self._checkboxes: dict[Any, Any] = {}
        # Pendiente de exportación cuando el usuario elige carpeta
        self._pending_export_casos = None
        self._pending_export_titulo = None
        # FilePicker para elegir carpeta de destino
        self._dir_picker = ft.FilePicker(on_result=self._on_dir_selected)
        self._build_view()

    def did_mount(self):
        """Se llama cuando el widget se monta en la página."""
        if not self._page:
            self._page = self.page
        # Registrar el FilePicker en el overlay de la página
        p = self._p
        if p and self._dir_picker not in p.services:
            p.services.append(self._dir_picker)
            p.update()

    @property
    def _p(self):
        """Acceso seguro a page."""
        return self._page or self.page

    # ─────────────────────────────────────────────────────────
    # CONSTRUCCIÓN DE VISTA
    # ─────────────────────────────────────────────────────────
    def _build_view(self):
        """Construye la interfaz de la vista de casos."""
        self._load_casos()

        hero_image = Path(__file__).parent.parent.parent / "assets" / "hero_search.png"

        hero_banner = ft.Container(
            content=ft.Stack(
                [
                    ft.Image(
                        src=str(hero_image),
                        width=float("inf"),
                        height=120,
                        fit="cover",
                        border_radius=8,
                    ),
                    ft.Container(
                        gradient=ft.LinearGradient(
                            begin=ft.Alignment(0, -1), end=ft.Alignment(0, 1), colors=["#00000000", "#000000CC"]
                        ),
                        border_radius=8,
                    ),
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Row(
                                            [
                                                ft.Icon("folder_special", size=40, color="white"),
                                                ft.Text("Casos y Expedientes", size=28, weight="bold", color="white"),
                                            ]
                                        ),
                                        ft.Text(
                                            "Organiza y gestiona casos legales con artículos vinculados y timeline",
                                            size=14,
                                            color=ft.Colors.with_opacity(0.95, "white"),
                                        ),
                                    ],
                                    spacing=Spacing.SM,
                                ),
                                ft.Container(expand=True),
                                ft.Row(
                                    [
                                        ft.ElevatedButton(
                                            "Exportar Todos",
                                            icon="picture_as_pdf",
                                            on_click=lambda _: self._exportar_todos(),
                                            bgcolor="#1B5E20",
                                            color="white",
                                            height=42,
                                            tooltip="Exportar todos los casos a PDF",
                                        ),
                                        ft.ElevatedButton(
                                            "Exportar Selección",
                                            icon="checklist",
                                            on_click=lambda _: self._exportar_seleccion(),
                                            bgcolor="#FF9800",
                                            color="white",
                                            height=42,
                                            tooltip="Exportar casos marcados a PDF",
                                        ),
                                        ft.ElevatedButton(
                                            "Nuevo Caso",
                                            icon="add",
                                            on_click=lambda _: self._show_nuevo_caso_dialog(),
                                            bgcolor="white",
                                            color=Theme.PRIMARY,
                                            height=42,
                                        ),
                                    ],
                                    spacing=Spacing.SM,
                                ),
                            ]
                        ),
                        padding=Spacing.LG,
                        alignment=ft.Alignment(-1, 1),
                    ),
                ]
            ),
            height=120,
            border_radius=8,
            shadow=ft.BoxShadow(
                spread_radius=1, blur_radius=8, color=ft.Colors.with_opacity(0.1, "black"), offset=ft.Offset(0, 2)
            ),
        )

        filtros = self._build_filtros()
        stats = self._build_estadisticas()

        self.casos_list = ft.Column(spacing=Spacing.SM, scroll=ft.ScrollMode.AUTO)
        self._update_casos_list()

        self.content = ft.Column(
            [
                hero_banner,
                ft.Container(height=Spacing.MD),
                stats,
                ft.Container(height=Spacing.MD),
                filtros,
                ft.Container(height=Spacing.MD),
                ft.Container(
                    content=self.casos_list,
                    padding=Spacing.MD,
                    bgcolor=Theme.SURFACE,
                    border_radius=8,
                    expand=True,
                ),
            ],
            expand=True,
            spacing=0,
        )

    # ─────────────────────────────────────────────────────────
    # ESTADÍSTICAS
    # ─────────────────────────────────────────────────────────
    def _build_estadisticas(self):
        stats = self.casos_repo.obtener_estadisticas()
        total = stats.get("total_casos", 0)
        abiertos = stats.get("por_estado", {}).get("ABIERTO", 0)
        cerrados = stats.get("por_estado", {}).get("CERRADO", 0)
        alta_prioridad = stats.get("por_prioridad", {}).get("ALTA", 0)

        return ft.Row(
            [
                self._build_stat_card("Total Casos", str(total), "folder", "#2196F3"),
                self._build_stat_card("Abiertos", str(abiertos), "folder_open", "#4CAF50"),
                self._build_stat_card("Cerrados", str(cerrados), "check_circle", "#9E9E9E"),
                self._build_stat_card("Alta Prioridad", str(alta_prioridad), "priority_high", "#F44336"),
            ],
            spacing=Spacing.MD,
            wrap=True,
        )

    def _build_stat_card(self, label, value, icon, color):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(icon, color=color, size=24),
                            ft.Text(value, size=28, weight="bold", color=color),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Text(label, size=12, color=Theme.TEXT_SECONDARY),
                ],
                spacing=Spacing.XS,
                tight=True,
            ),
            padding=Spacing.MD,
            bgcolor=Theme.SURFACE,
            border_radius=8,
            width=180,
            height=100,
        )

    # ─────────────────────────────────────────────────────────
    # FILTROS
    # ─────────────────────────────────────────────────────────
    def _build_filtros(self):
        estado_dropdown = ft.Dropdown(
            label="Estado",
            options=[
                ft.dropdown.Option("TODOS", "Todos"),
                ft.dropdown.Option("ABIERTO", "Abiertos"),
                ft.dropdown.Option("EN_PROCESO", "En Proceso"),
                ft.dropdown.Option("CERRADO", "Cerrados"),
            ],
            value="TODOS",
            on_change=lambda e: self._on_filtro_change("estado", e.control.value),
            width=150,
        )
        prioridad_dropdown = ft.Dropdown(
            label="Prioridad",
            options=[
                ft.dropdown.Option("TODOS", "Todas"),
                ft.dropdown.Option("ALTA", "Alta"),
                ft.dropdown.Option("MEDIA", "Media"),
                ft.dropdown.Option("BAJA", "Baja"),
            ],
            value="TODOS",
            on_change=lambda e: self._on_filtro_change("prioridad", e.control.value),
            width=150,
        )
        self.fecha_inicio_field = ft.TextField(
            label="Fecha Inicio (desde)",
            hint_text="DD-MM-YYYY",
            width=150,
            on_change=lambda e: self._on_filtro_change("fecha_inicio", e.control.value),
        )
        self.fecha_fin_field = ft.TextField(
            label="Fecha Inicio (hasta)",
            hint_text="DD-MM-YYYY",
            width=150,
            on_change=lambda e: self._on_filtro_change("fecha_fin", e.control.value),
        )
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon("filter_list", color=Theme.TEXT_SECONDARY),
                            ft.Text("Filtros:", weight="bold", color=Theme.TEXT_SECONDARY),
                            estado_dropdown,
                            prioridad_dropdown,
                            ft.TextButton("Limpiar filtros", icon="clear", on_click=lambda _: self._limpiar_filtros()),
                        ],
                        spacing=Spacing.MD,
                    ),
                    ft.Container(height=Spacing.SM),
                    ft.Row(
                        [
                            ft.Icon("date_range", color=Theme.TEXT_SECONDARY),
                            ft.Text("Rango de Fechas:", weight="bold", color=Theme.TEXT_SECONDARY),
                            self.fecha_inicio_field,
                            self.fecha_fin_field,
                        ],
                        spacing=Spacing.MD,
                    ),
                ],
                tight=True,
            ),
            padding=Spacing.MD,
            bgcolor=Theme.SURFACE,
            border_radius=8,
        )

    def _on_filtro_change(self, tipo, valor):
        if tipo == "estado":
            self.filtro_estado = None if valor == "TODOS" else valor
        elif tipo == "prioridad":
            self.filtro_prioridad = None if valor == "TODOS" else valor
        elif tipo == "fecha_inicio":
            self.filtro_fecha_inicio = valor if valor else None
        elif tipo == "fecha_fin":
            self.filtro_fecha_fin = valor if valor else None
        self._load_casos()
        self._update_casos_list()

    def _limpiar_filtros(self):
        self.filtro_estado = None
        self.filtro_prioridad = None
        self.filtro_fecha_inicio = None
        self.filtro_fecha_fin = None
        self.fecha_inicio_field.value = ""
        self.fecha_fin_field.value = ""
        self._load_casos()
        self._update_casos_list()
        self.update()

    # ─────────────────────────────────────────────────────────
    # CARGA DE DATOS
    # ─────────────────────────────────────────────────────────
    def _load_casos(self):
        self.casos = self.casos_repo.obtener_casos(
            estado=self.filtro_estado, prioridad=self.filtro_prioridad, limit=200
        )
        if self.filtro_fecha_inicio or self.filtro_fecha_fin:
            casos_filtrados = []
            for caso in self.casos:
                fecha_inicio = caso.get("fecha_inicio", "")
                if not fecha_inicio:
                    continue
                try:
                    fecha_caso = datetime.strptime(fecha_inicio.split()[0], "%Y-%m-%d")
                    if self.filtro_fecha_inicio:
                        if fecha_caso < datetime.strptime(self.filtro_fecha_inicio, "%d-%m-%Y"):
                            continue
                    if self.filtro_fecha_fin:
                        if fecha_caso > datetime.strptime(self.filtro_fecha_fin, "%d-%m-%Y"):
                            continue
                    casos_filtrados.append(caso)
                except (ValueError, IndexError):
                    continue
            self.casos = casos_filtrados

    # ─────────────────────────────────────────────────────────
    # LISTA DE CASOS
    # ─────────────────────────────────────────────────────────
    def _update_casos_list(self):
        self._checkboxes.clear()
        self.casos_list.controls.clear()
        if not self.casos:
            self.casos_list.controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon("inbox", size=64, color=Theme.TEXT_SECONDARY),
                            ft.Text("No hay casos para mostrar", size=16, color=Theme.TEXT_SECONDARY),
                            ft.Text("Crea un nuevo caso para comenzar", size=12, color=Theme.TEXT_SECONDARY),
                        ],
                        horizontal_alignment="center",
                        spacing=Spacing.SM,
                    ),
                    padding=Spacing.XL,
                    alignment=ft.Alignment(0, 0),
                )
            )
        else:
            for caso in self.casos:
                self.casos_list.controls.append(self._build_caso_card(caso))

    def _build_caso_card(self, caso):
        prioridad_colors = {"ALTA": "#F44336", "MEDIA": "#FF9800", "BAJA": "#4CAF50"}
        estado_colors = {"ABIERTO": "#4CAF50", "EN_PROCESO": "#2196F3", "CERRADO": "#9E9E9E"}

        prioridad_badge = ft.Container(
            content=ft.Text(caso.get("prioridad", "MEDIA"), size=10, weight="bold", color="white"),
            bgcolor=prioridad_colors.get(caso.get("prioridad", "MEDIA"), "#FF9800"),
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border_radius=12,
        )
        estado_badge = ft.Container(
            content=ft.Text(caso.get("estado", "ABIERTO"), size=10, weight="bold", color="white"),
            bgcolor=estado_colors.get(caso.get("estado", "ABIERTO"), "#4CAF50"),
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border_radius=12,
        )

        fecha_inicio = caso.get("fecha_inicio", "")
        try:
            fecha_display = datetime.strptime(fecha_inicio.split()[0], "%Y-%m-%d").strftime("%d/%m/%Y")
        except (ValueError, IndexError, AttributeError):
            fecha_display = fecha_inicio or "N/A"

        # Checkbox de selección para exportar
        cb = ft.Checkbox(value=False, label="")
        self._checkboxes[caso["id"]] = cb

        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            cb,
                            ft.Icon("folder_special", size=20, color=Theme.PRIMARY),
                            ft.Text(caso.get("numero_expediente", "N/A"), size=14, weight="bold", color=Theme.PRIMARY),
                            ft.Container(expand=True),
                            prioridad_badge,
                            estado_badge,
                        ]
                    ),
                    ft.Text(caso.get("titulo", "Sin título"), size=16, weight="bold", color=Theme.TEXT_PRIMARY),
                    ft.Text(
                        (caso.get("descripcion", "") or "")[:150]
                        + ("..." if len(caso.get("descripcion", "") or "") > 150 else ""),
                        size=12,
                        color=Theme.TEXT_SECONDARY,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Divider(height=1, color=Theme.BORDER),
                    ft.Row(
                        [
                            ft.Row(
                                [
                                    ft.Icon("event", size=14, color=Theme.TEXT_SECONDARY),
                                    ft.Text(f"Inicio: {fecha_display}", size=11, color=Theme.TEXT_SECONDARY),
                                ]
                            ),
                            ft.Container(expand=True),
                            ft.Row(
                                [
                                    ft.IconButton(
                                        icon="visibility",
                                        icon_size=18,
                                        icon_color="#2196F3",
                                        tooltip="Ver detalles",
                                        on_click=lambda _, c=caso: self._ver_caso(c),
                                    ),
                                    ft.IconButton(
                                        icon="edit",
                                        icon_size=18,
                                        icon_color="#FF9800",
                                        tooltip="Editar caso",
                                        on_click=lambda _, c=caso: self._show_editar_caso_dialog(c),
                                    ),
                                    ft.IconButton(
                                        icon="picture_as_pdf",
                                        icon_size=18,
                                        icon_color="#1B5E20",
                                        tooltip="Exportar este caso a PDF",
                                        on_click=lambda _, c=caso: self._exportar_caso(c),
                                    ),
                                    ft.IconButton(
                                        icon="delete",
                                        icon_size=18,
                                        icon_color=Theme.ERROR,
                                        tooltip="Eliminar",
                                        on_click=lambda _, c=caso: self._confirmar_eliminar(c),
                                    ),
                                ]
                            ),
                        ]
                    ),
                ],
                spacing=Spacing.XS,
                tight=True,
            ),
            padding=Spacing.MD,
            bgcolor=Theme.BACKGROUND,
            border=ft.border.all(1, Theme.BORDER),
            border_radius=8,
        )

    # ─────────────────────────────────────────────────────────
    # ACCIONES DE CASO
    # ─────────────────────────────────────────────────────────
    def _ver_caso(self, caso):
        """Abre el detalle del caso."""
        if self.on_open_caso_detail:
            self.on_open_caso_detail(caso)

    # ─────────────────────────────────────────────────────────
    # DIÁLOGO NUEVO CASO
    # ─────────────────────────────────────────────────────────
    def _show_nuevo_caso_dialog(self):
        numero_field = ft.TextField(label="Número de Expediente*", hint_text="EXP-2026-001")
        titulo_field = ft.TextField(label="Título del Caso*", hint_text="Caso de contaminación industrial")
        descripcion_field = ft.TextField(label="Descripción", multiline=True, min_lines=3, max_lines=5)
        estado_dropdown = ft.Dropdown(
            label="Estado",
            options=[ft.dropdown.Option("ABIERTO"), ft.dropdown.Option("EN_PROCESO"), ft.dropdown.Option("CERRADO")],
            value="ABIERTO",
        )
        prioridad_dropdown = ft.Dropdown(
            label="Prioridad",
            options=[ft.dropdown.Option("ALTA"), ft.dropdown.Option("MEDIA"), ft.dropdown.Option("BAJA")],
            value="MEDIA",
        )
        categoria_field = ft.TextField(label="Categoría", hint_text="Ambiental, Forestal, etc.")
        responsable_field = ft.TextField(label="Responsable")

        def crear(e):
            if not numero_field.value or not titulo_field.value:
                self._snack("El número y título son obligatorios", error=True)
                return
            try:
                self.casos_repo.crear_caso(
                    numero_expediente=numero_field.value,
                    titulo=titulo_field.value,
                    descripcion=descripcion_field.value or "",
                    estado=estado_dropdown.value,
                    prioridad=prioridad_dropdown.value,
                    categoria=categoria_field.value or "",
                    responsable=responsable_field.value or "",
                )
                dialog.open = False
                self._p.update()
                self._reload()
                self._snack("✓ Caso creado exitosamente")
            except Exception as ex:
                self._snack(f"Error: {ex}", error=True)

        dialog = ft.AlertDialog(
            title=ft.Text("Nuevo Caso"),
            content=ft.Column(
                [
                    numero_field,
                    titulo_field,
                    descripcion_field,
                    ft.Row([estado_dropdown, prioridad_dropdown]),
                    categoria_field,
                    responsable_field,
                ],
                tight=True,
                spacing=Spacing.SM,
                scroll=ft.ScrollMode.AUTO,
                height=400,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self._close_dialog(dialog)),
                ft.ElevatedButton("Crear Caso", on_click=crear, bgcolor=Theme.PRIMARY, color="white"),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self._open_dialog(dialog)

    # ─────────────────────────────────────────────────────────
    # DIÁLOGO EDITAR CASO  ← IMPLEMENTADO
    # ─────────────────────────────────────────────────────────
    def _show_editar_caso_dialog(self, caso):
        """Muestra el diálogo para editar un caso existente con datos pre-cargados."""
        numero_label = ft.Text(
            f"Expediente: {caso.get('numero_expediente', '')}",
            size=13,
            weight="bold",
            color=Theme.TEXT_SECONDARY,
        )
        titulo_field = ft.TextField(label="Título del Caso*", value=caso.get("titulo", ""))
        descripcion_field = ft.TextField(
            label="Descripción", multiline=True, min_lines=3, max_lines=5, value=caso.get("descripcion", "") or ""
        )
        estado_dropdown = ft.Dropdown(
            label="Estado",
            options=[
                ft.dropdown.Option("ABIERTO"),
                ft.dropdown.Option("EN_PROCESO"),
                ft.dropdown.Option("CERRADO"),
            ],
            value=caso.get("estado", "ABIERTO"),
        )
        prioridad_dropdown = ft.Dropdown(
            label="Prioridad",
            options=[
                ft.dropdown.Option("ALTA"),
                ft.dropdown.Option("MEDIA"),
                ft.dropdown.Option("BAJA"),
            ],
            value=caso.get("prioridad", "MEDIA"),
        )
        categoria_field = ft.TextField(label="Categoría", value=caso.get("categoria", "") or "")
        responsable_field = ft.TextField(label="Responsable", value=caso.get("responsable", "") or "")

        def guardar(e):
            if not titulo_field.value:
                self._snack("El título es obligatorio", error=True)
                return
            try:
                self.casos_repo.actualizar_caso(
                    caso_id=caso["id"],
                    titulo=titulo_field.value,
                    descripcion=descripcion_field.value or "",
                    estado=estado_dropdown.value,
                    prioridad=prioridad_dropdown.value,
                    categoria=categoria_field.value or "",
                    responsable=responsable_field.value or "",
                )
                dialog.open = False
                self._p.update()
                self._reload()
                self._snack("✓ Caso actualizado exitosamente")
            except Exception as ex:
                self._snack(f"Error al guardar: {ex}", error=True)

        dialog = ft.AlertDialog(
            title=ft.Row(
                [
                    ft.Icon("edit", color=Theme.PRIMARY),
                    ft.Text("Editar Caso", weight="bold"),
                ]
            ),
            content=ft.Column(
                [
                    numero_label,
                    ft.Divider(height=1),
                    titulo_field,
                    descripcion_field,
                    ft.Row([estado_dropdown, prioridad_dropdown], spacing=Spacing.MD),
                    categoria_field,
                    responsable_field,
                ],
                tight=True,
                spacing=Spacing.SM,
                scroll=ft.ScrollMode.AUTO,
                height=420,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self._close_dialog(dialog)),
                ft.ElevatedButton(
                    "Guardar Cambios", icon="save", on_click=guardar, bgcolor=Theme.PRIMARY, color="white"
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self._open_dialog(dialog)

    # ─────────────────────────────────────────────────────────
    # ELIMINAR CASO
    # ─────────────────────────────────────────────────────────
    def _confirmar_eliminar(self, caso):
        def eliminar(e):
            try:
                self.casos_repo.eliminar_caso(caso["id"])
                dialog.open = False
                self._p.update()
                self._reload()
                self._snack("✓ Caso eliminado")
            except Exception as ex:
                self._snack(f"Error: {ex}", error=True)

        dialog = ft.AlertDialog(
            title=ft.Text("Confirmar Eliminación"),
            content=ft.Text(
                f"¿Eliminar el caso '{caso.get('numero_expediente')}'?\n\n"
                "Esta acción eliminará también todas las vinculaciones y notas asociadas."
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self._close_dialog(dialog)),
                ft.ElevatedButton("Eliminar", on_click=eliminar, bgcolor=Theme.ERROR, color="white"),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self._open_dialog(dialog)

    # ─────────────────────────────────────────────────────────
    # EXPORTACIÓN PDF
    # ─────────────────────────────────────────────────────────
    def _exportar_caso(self, caso):
        """Exporta un solo caso a PDF — primero pide carpeta."""
        self._pending_export_casos = [caso]
        self._pending_export_titulo = f"Expediente_{caso.get('numero_expediente', 'caso')}"
        self._dir_picker.get_directory_path(dialog_title="Selecciona dónde guardar el PDF")

    def _exportar_seleccion(self):
        """Exporta los casos marcados con checkbox — primero pide carpeta."""
        seleccionados = [c for c in self.casos if self._checkboxes.get(c["id"]) and self._checkboxes[c["id"]].value]
        if not seleccionados:
            self._snack("Marca al menos un caso con el checkbox para exportar", error=True)
            return
        self._pending_export_casos = seleccionados
        self._pending_export_titulo = f"Seleccion_{len(seleccionados)}_casos"
        self._dir_picker.get_directory_path(dialog_title="Selecciona dónde guardar el PDF")

    def _exportar_todos(self):
        """Exporta todos los casos visibles a PDF — primero pide carpeta."""
        if not self.casos:
            self._snack("No hay casos para exportar", error=True)
            return
        self._pending_export_casos = self.casos
        self._pending_export_titulo = "Todos_los_Casos"
        self._dir_picker.get_directory_path(dialog_title="Selecciona dónde guardar el PDF")

    def _on_dir_selected(self, e):
        """Callback cuando el usuario elige (o cancela) la carpeta destino."""
        if not e.path:
            # Usuario canceló el diálogo
            self._pending_export_casos = None
            self._pending_export_titulo = None
            return
        casos = self._pending_export_casos
        titulo = self._pending_export_titulo
        self._pending_export_casos = None
        self._pending_export_titulo = None
        if casos:
            self._exportar_lista(casos, titulo, destino=Path(e.path))

    def _exportar_lista(self, casos_lista: list, titulo_doc: str, destino: Path = None):
        """Genera el PDF de una lista de casos usando reportlab.

        Args:
            casos_lista: Lista de casos a exportar.
            titulo_doc:  Título del documento / nombre base del archivo.
            destino:     Carpeta elegida por el usuario. Si None usa /exports.
        """
        try:
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
            from reportlab.lib.units import inch
            from reportlab.platypus import (
                HRFlowable,
                PageBreak,
                Paragraph,
                SimpleDocTemplate,
                Spacer,
                Table,
                TableStyle,
            )

            # Carpeta de exportación: la elegida por el usuario o /exports por defecto
            if destino:
                exports_dir = destino
            else:
                exports_dir = Path(__file__).parent.parent.parent / "exports"
            exports_dir = Path(exports_dir)
            exports_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = titulo_doc.replace(" ", "_").replace("/", "-")
            output_path = exports_dir / f"LEXV_{safe_title}_{timestamp}.pdf"

            # Estilos
            styles = getSampleStyleSheet()
            VERDE = colors.HexColor("#1B5E20")
            VERDE2 = colors.HexColor("#4CAF50")
            DORADO = colors.HexColor("#D4AF37")
            GRIS = colors.HexColor("#424242")
            GRIS_L = colors.HexColor("#BDBDBD")

            s_title = ParagraphStyle(
                "LVTitle",
                parent=styles["Heading1"],
                fontSize=22,
                textColor=VERDE,
                alignment=TA_CENTER,
                fontName="Helvetica-Bold",
                spaceAfter=4,
            )
            s_sub = ParagraphStyle(
                "LVSub", parent=styles["Normal"], fontSize=13, textColor=GRIS, alignment=TA_CENTER, spaceAfter=18
            )
            s_fecha = ParagraphStyle(
                "LVFecha", parent=styles["Normal"], fontSize=9, textColor=GRIS_L, alignment=TA_CENTER, spaceAfter=20
            )
            s_exp = ParagraphStyle(
                "LVExp",
                parent=styles["Heading2"],
                fontSize=14,
                textColor=VERDE,
                fontName="Helvetica-Bold",
                spaceBefore=16,
                spaceAfter=4,
            )
            s_label = ParagraphStyle(
                "LVLabel", parent=styles["Normal"], fontSize=9, textColor=GRIS_L, fontName="Helvetica-Bold"
            )
            s_value = ParagraphStyle(
                "LVValue",
                parent=styles["Normal"],
                fontSize=11,
                textColor=GRIS,
                alignment=TA_JUSTIFY,
                spaceAfter=6,
                leading=14,
            )
            s_notas_title = ParagraphStyle(
                "LVNotaT",
                parent=styles["Normal"],
                fontSize=10,
                textColor=DORADO,
                fontName="Helvetica-Bold",
                spaceBefore=8,
                spaceAfter=2,
            )
            s_notas_body = ParagraphStyle(
                "LVNotaB", parent=styles["Normal"], fontSize=10, textColor=GRIS, spaceAfter=4, leading=13
            )

            def add_footer(canvas, doc):
                canvas.saveState()
                canvas.setStrokeColor(GRIS_L)
                canvas.setLineWidth(0.5)
                canvas.line(inch, 0.65 * inch, doc.pagesize[0] - inch, 0.65 * inch)
                canvas.setFillColor(GRIS_L)
                canvas.setFont("Helvetica", 9)
                canvas.drawString(inch, 0.45 * inch, f"Página {doc.page}")
                canvas.drawRightString(doc.pagesize[0] - inch, 0.45 * inch, "LEX VIRIDIS Pro")
                canvas.restoreState()

            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=letter,
                leftMargin=inch,
                rightMargin=inch,
                topMargin=inch,
                bottomMargin=0.8 * inch,
            )

            story = []

            # — Portada —
            story.append(Paragraph("🌿 LEX VIRIDIS", s_title))
            story.append(Paragraph(titulo_doc.upper(), s_sub))
            story.append(
                HRFlowable(width="80%", thickness=2, color=VERDE, spaceBefore=4, spaceAfter=4, hAlign="CENTER")
            )
            fecha_gen = datetime.now().strftime("%d/%m/%Y %H:%M")
            story.append(Paragraph(f"Documento generado el {fecha_gen}", s_fecha))
            story.append(Paragraph(f"Total de expedientes: {len(casos_lista)}", s_fecha))
            story.append(PageBreak())

            # — Un bloque por caso —
            for idx, caso in enumerate(casos_lista, 1):
                num_exp = caso.get("numero_expediente", "N/A")
                titulo = caso.get("titulo", "Sin título")

                # Encabezado del caso
                story.append(Paragraph(f"Expediente {idx}: {num_exp}", s_exp))
                story.append(
                    Paragraph(
                        titulo,
                        ParagraphStyle(
                            "LVTit2", parent=s_value, fontSize=13, fontName="Helvetica-Bold", textColor=GRIS
                        ),
                    )
                )
                story.append(HRFlowable(width="100%", thickness=1, color=VERDE2, spaceBefore=2, spaceAfter=6))

                # Tabla de metadatos
                estado = caso.get("estado", "N/A")
                prioridad = caso.get("prioridad", "N/A")
                categoria = caso.get("categoria", "") or "—"
                responsable = caso.get("responsable", "") or "—"
                fecha_i = caso.get("fecha_inicio", "")
                try:
                    fecha_i = datetime.strptime(fecha_i.split()[0], "%Y-%m-%d").strftime("%d/%m/%Y")
                except Exception:
                    pass

                meta_data = [
                    ["Estado", estado, "Prioridad", prioridad],
                    ["Categoría", categoria, "Responsable", responsable],
                    ["Fecha Inicio", fecha_i, "", ""],
                ]
                meta_table = Table(meta_data, colWidths=[1.2 * inch, 2.2 * inch, 1.2 * inch, 2.2 * inch])
                meta_table.setStyle(
                    TableStyle(
                        [
                            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                            ("FONTSIZE", (0, 0), (-1, -1), 10),
                            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                            ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                            ("TEXTCOLOR", (0, 0), (0, -1), VERDE),
                            ("TEXTCOLOR", (2, 0), (2, -1), VERDE),
                            ("TEXTCOLOR", (1, 0), (-1, -1), GRIS),
                            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#F5F5F5"), colors.white]),
                            ("GRID", (0, 0), (-1, -1), 0.5, GRIS_L),
                            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                            ("TOPPADDING", (0, 0), (-1, -1), 4),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ]
                    )
                )
                story.append(meta_table)
                story.append(Spacer(1, 8))

                # Descripción
                desc = caso.get("descripcion", "") or "Sin descripción"
                story.append(Paragraph("DESCRIPCIÓN", s_label))
                story.append(Paragraph(desc, s_value))

                # Artículos vinculados
                try:
                    articulos = self.casos_repo.obtener_articulos_caso(caso["id"])
                except Exception:
                    articulos = []

                if articulos:
                    story.append(Spacer(1, 6))
                    story.append(Paragraph(f"ARTÍCULOS VINCULADOS ({len(articulos)})", s_label))
                    for art in articulos:
                        norma = art.get("norma_titulo", "N/A")
                        num_art = art.get("numero_articulo", "N/A")
                        rel = art.get("relevancia", "MEDIA")
                        contenido = (art.get("contenido_completo", "") or "")[:400]
                        nota_art = art.get("notas", "") or ""
                        story.append(Paragraph(f"• Art. {num_art} — {norma}  [Relevancia: {rel}]", s_notas_title))
                        if contenido:
                            story.append(
                                Paragraph(
                                    contenido + ("..." if len(art.get("contenido_completo", "") or "") > 400 else ""),
                                    s_notas_body,
                                )
                            )
                        if nota_art:
                            story.append(
                                Paragraph(
                                    f"📝 {nota_art}",
                                    ParagraphStyle(
                                        "LVNota", parent=s_notas_body, textColor=colors.HexColor("#757575"), italic=True
                                    ),
                                )
                            )

                # Notas y anotaciones
                try:
                    notas = self.casos_repo.obtener_notas_caso(caso["id"])
                except Exception:
                    notas = []

                if notas:
                    story.append(Spacer(1, 6))
                    story.append(Paragraph(f"NOTAS Y ANOTACIONES ({len(notas)})", s_label))
                    for nota in notas:
                        titulo_nota = nota.get("titulo", "Sin título")
                        tipo_nota = nota.get("tipo", "NOTA")
                        autor_nota = nota.get("autor", "") or "Anónimo"
                        fecha_nota = nota.get("created_at", "")
                        try:
                            fecha_nota = datetime.strptime(fecha_nota, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y")
                        except Exception:
                            pass
                        story.append(
                            Paragraph(f"[{tipo_nota}] {titulo_nota} — {autor_nota} ({fecha_nota})", s_notas_title)
                        )
                        story.append(Paragraph(nota.get("contenido", ""), s_notas_body))

                # Separador entre casos
                if idx < len(casos_lista):
                    story.append(PageBreak())

            # Generar PDF
            doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)

            # Abrir la carpeta con el archivo
            import subprocess
            import sys

            if sys.platform == "win32":
                subprocess.Popen(f'explorer /select,"{output_path}"')
            elif sys.platform == "darwin":
                subprocess.Popen(["open", "-R", str(output_path)])
            else:
                subprocess.Popen(["xdg-open", str(exports_dir)])

            self._snack(f"✓ PDF generado: {output_path.name}")

        except ImportError:
            self._snack("Error: reportlab no está instalado. Ejecuta: pip install reportlab", error=True)
        except Exception as ex:
            self._snack(f"Error al generar PDF: {ex}", error=True)

    # ─────────────────────────────────────────────────────────
    # UTILIDADES
    # ─────────────────────────────────────────────────────────
    def _reload(self):
        """Recarga la lista de casos y actualiza la UI."""
        self._load_casos()
        self._update_casos_list()
        self.update()

    def _snack(self, msg: str, error: bool = False):
        p = self._p
        if not p:
            return
        p.snack_bar = ft.SnackBar(
            ft.Text(msg),
            bgcolor=Theme.ERROR if error else Theme.SUCCESS,
        )
        p.snack_bar.open = True
        p.update()

    def _open_dialog(self, dialog):
        p = self._p
        if not p:
            return
        p.dialog = dialog
        dialog.open = True
        p.update()

    def _close_dialog(self, dialog):
        dialog.open = False
        if self._p:
            self._p.update()
